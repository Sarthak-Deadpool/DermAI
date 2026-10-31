from threading import Event, Thread

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.user import User, UserRole
from app.services.admin_invariant_service import lock_admin_access_changes


def test_concurrent_admin_demotions_preserve_one_active_administrator(tmp_path):
    database_file = tmp_path / "admin-invariant.sqlite"
    engine = create_engine(
        f"sqlite+pysqlite:///{database_file}",
        connect_args={"check_same_thread": False, "timeout": 10},
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    with factory() as db:
        admins = [
            User(username=f"admin-{index}", email=f"admin-{index}@example.com", password_hash="hash", role=UserRole.ADMIN)
            for index in (1, 2)
        ]
        db.add_all(admins)
        db.commit()
        admin_ids = [admin.id for admin in admins]

    first_locked = Event()
    allow_first_commit = Event()
    second_entered = Event()
    results = []
    errors = []

    def demote(target_id, *, is_first):
        try:
            with factory() as db:
                if not is_first:
                    second_entered.set()
                lock_admin_access_changes(db)
                active_admins = db.scalar(
                    select(func.count()).select_from(User).where(
                        User.role == UserRole.ADMIN, User.is_active.is_(True)
                    )
                )
                if is_first:
                    first_locked.set()
                    assert allow_first_commit.wait(timeout=5)
                if active_admins <= 1:
                    db.rollback()
                    results.append(False)
                    return
                target = db.get(User, target_id)
                target.is_active = False
                db.commit()
                results.append(True)
        except Exception as exc:  # surface thread assertions/errors in the test
            errors.append(exc)

    first = Thread(target=demote, args=(admin_ids[0],), kwargs={"is_first": True})
    second = Thread(target=demote, args=(admin_ids[1],), kwargs={"is_first": False})
    first.start()
    assert first_locked.wait(timeout=5)
    second.start()
    assert second_entered.wait(timeout=5)
    allow_first_commit.set()
    first.join(timeout=10)
    second.join(timeout=10)

    assert not first.is_alive() and not second.is_alive()
    assert errors == []
    assert sorted(results) == [False, True]
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(User).where(
            User.role == UserRole.ADMIN, User.is_active.is_(True)
        )) == 1
    engine.dispose()
