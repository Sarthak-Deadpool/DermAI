from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.config import Settings
from app.core.security import create_access_token, hash_password
from app.db.database import Base
from app.dependencies.database import get_db
from app.main import app
from app.models.auth_session import AuthSession
from app.models.auth_rate_limit import AuthRateLimitBucket
from app.models.case import Case, CaseEvent
from app.models.image import Image
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.case import CaseCreate, CaseNoteCreate
from app.schemas.user import AdminUserUpdate
from app.services.session_service import hash_session_id
from app.services.image_service import upload_case_image
from fastapi import UploadFile
from io import BytesIO
from PIL import Image as PILImage
from sqlalchemy.orm import Session


@pytest.fixture
def test_environment(monkeypatch):
    """Use a private in-memory DB; never connect to settings.DB_* targets."""
    monkeypatch.setattr(settings, "APP_ENV", "test")
    monkeypatch.setattr(settings, "SESSION_COOKIE_SECURE", False)
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(app.state, "session_factory", test_session_factory, raising=False)

    def override_get_db():
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app, base_url="http://testserver.local") as client:
            yield client, test_session_factory
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(engine)
        engine.dispose()


def create_user(factory, *, role=UserRole.USER, active=True, password="TestPassword123!"):
    user = User(
        username=f"test-{uuid4().hex[:10]}",
        email=f"{uuid4().hex}@example.com",
        password_hash=hash_password(password),
        role=role,
        is_active=active,
    )
    with factory() as db:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id, user.email


def post_with_csrf(client, url, payload=None):
    response = client.get("/auth/csrf")
    assert response.status_code == 200
    csrf_token = response.json()["csrf_token"]
    return client.post(
        url,
        json=payload,
        headers={"X-CSRF-Token": csrf_token, "Origin": settings.trusted_origins[0]},
    )


def delete_with_csrf(client, url):
    response = client.get("/auth/csrf")
    return client.delete(
        url,
        headers={
            "X-CSRF-Token": response.json()["csrf_token"],
            "Origin": settings.trusted_origins[0],
        },
    )


def clear_cookie(client, name):
    client.cookies.delete(name, domain="testserver.local", path="/")


def login(client, email, password="TestPassword123!"):
    response = post_with_csrf(
        client,
        "/auth/login",
        {"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response


def test_csrf_endpoint_and_rejections(test_environment):
    client, _ = test_environment
    response = client.get("/auth/csrf")
    assert response.status_code == 200
    assert response.json().get("csrf_token")
    assert "dermai_csrf_token" in response.cookies

    missing = client.post(
        "/auth/logout",
        headers={"Origin": settings.trusted_origins[0]},
    )
    assert missing.status_code == 403
    assert missing.json()["detail"] == "CSRF token missing"

    client.cookies.set("dermai_csrf_token", "invalid-token", domain="testserver.local", path="/")
    invalid = client.post(
        "/auth/logout",
        headers={"X-CSRF-Token": "invalid-token", "Origin": settings.trusted_origins[0]},
    )
    assert invalid.status_code == 403


def test_registration_and_invalid_email(test_environment):
    client, _ = test_environment
    payload = {
        "username": f"testuser_{uuid4().hex[:8]}",
        "email": f"{uuid4().hex[:10]}@example.com",
        "password": "TestPassword123!",
    }
    response = post_with_csrf(client, "/auth/register", payload)
    assert response.status_code == 201
    assert response.json()["role"] == UserRole.USER.value
    assert "password" not in response.json()

    invalid = post_with_csrf(
        client,
        "/auth/register",
        {"username": "testuser", "email": "not-an-email", "password": "TestPassword123!"},
    )
    assert invalid.status_code == 422


def test_login_creates_opaque_cookie_after_credentials_and_hides_identifier(test_environment):
    client, factory = test_environment
    user_id, email = create_user(factory)
    client.cookies.set(
        settings.SESSION_COOKIE_NAME,
        "attacker-supplied-session-id",
        domain="testserver.local",
        path="/",
    )

    response = login(client, email)

    raw_session_id = client.cookies.get(settings.SESSION_COOKIE_NAME)
    assert raw_session_id
    assert raw_session_id != "attacker-supplied-session-id"
    assert raw_session_id not in response.text
    assert "access_token" not in response.text
    assert settings.SESSION_COOKIE_NAME in response.cookies
    set_cookie = response.headers.get("set-cookie", "").lower()
    assert "httponly" in set_cookie
    assert f"samesite={settings.SESSION_COOKIE_SAMESITE}" in set_cookie
    assert f"path={settings.SESSION_COOKIE_PATH}" in set_cookie
    assert ("secure" in set_cookie) is settings.SESSION_COOKIE_SECURE
    assert f"max-age={settings.SESSION_ABSOLUTE_TIMEOUT_HOURS * 3600}" in set_cookie

    with factory() as db:
        row = db.get(AuthSession, hash_session_id(raw_session_id))
        assert row is not None
        assert row.user_id == user_id
        assert row.id_hash != raw_session_id
        assert db.get(AuthSession, hash_session_id("attacker-supplied-session-id")) is None
        assert row.absolute_expires_at > row.idle_expires_at


def test_invalid_or_inactive_credentials_do_not_create_sessions(test_environment):
    client, factory = test_environment
    _, email = create_user(factory)
    invalid = post_with_csrf(
        client,
        "/auth/login",
        {"email": email, "password": "IncorrectPassword!"},
    )
    assert invalid.status_code == 401
    assert settings.SESSION_COOKIE_NAME not in invalid.cookies

    _, inactive_email = create_user(factory, active=False)
    inactive = post_with_csrf(
        client,
        "/auth/login",
        {"email": inactive_email, "password": "TestPassword123!"},
    )
    assert inactive.status_code == 401
    assert inactive.json() == invalid.json()
    assert settings.SESSION_COOKIE_NAME not in inactive.cookies

    with factory() as db:
        assert db.query(AuthSession).count() == 0


def test_authentication_rejects_missing_invalid_revoked_expired_and_old_jwt(test_environment):
    client, factory = test_environment
    user_id, email = create_user(factory)

    assert client.get("/auth/me").status_code == 401

    client.cookies.set(settings.SESSION_COOKIE_NAME, "not-a-real-session", domain="testserver.local", path="/")
    assert client.get("/auth/me").status_code == 401
    clear_cookie(client, settings.SESSION_COOKIE_NAME)

    # The old JWT cookie is deliberately not accepted as a compatibility path.
    client.cookies.set(settings.JWT_COOKIE_NAME, create_access_token(str(user_id)), domain="testserver.local", path="/")
    assert client.get("/auth/me").status_code == 401
    clear_cookie(client, settings.JWT_COOKIE_NAME)

    login(client, email)
    raw_id = client.cookies.get(settings.SESSION_COOKIE_NAME)
    assert client.get("/auth/me").json()["id"] == str(user_id)
    with factory() as db:
        row = db.get(AuthSession, hash_session_id(raw_id))
        row.revoked_at = datetime.now(timezone.utc)
        row.revoke_reason = "test_revoked"
        db.commit()
    assert client.get("/auth/me").status_code == 401

    clear_cookie(client, settings.SESSION_COOKIE_NAME)
    login(client, email)
    raw_id = client.cookies.get(settings.SESSION_COOKIE_NAME)
    with factory() as db:
        row = db.get(AuthSession, hash_session_id(raw_id))
        row.idle_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
    assert client.get("/auth/me").status_code == 401


def test_inactive_user_and_role_changes_take_effect_on_next_request(test_environment):
    client, factory = test_environment
    user_id, email = create_user(factory)
    login(client, email)

    assert client.get("/auth/admin/users").status_code == 403
    with factory() as db:
        user = db.get(User, user_id)
        user.role = UserRole.ADMIN
        db.commit()
    assert client.get("/auth/admin/users").status_code == 200

    with factory() as db:
        user = db.get(User, user_id)
        user.is_active = False
        db.commit()
    assert client.get("/auth/me").status_code == 401


def test_admin_deactivation_revokes_target_sessions(test_environment):
    client, factory = test_environment
    _, admin_email = create_user(factory, role=UserRole.ADMIN)
    target_id, target_email = create_user(factory)
    target_client = TestClient(app, base_url="http://testserver.local")
    try:
        login(client, admin_email)
        login(target_client, target_email)
        assert target_client.get("/auth/me").status_code == 200

        response = client.patch(
            f"/auth/admin/users/{target_id}",
            json={"is_active": False},
            headers={
                "X-CSRF-Token": client.get("/auth/csrf").json()["csrf_token"],
                "Origin": settings.trusted_origins[0],
            },
        )
        assert response.status_code == 200, response.text
        assert target_client.get("/auth/me").status_code == 401
        with factory() as db:
            sessions = db.query(AuthSession).filter(AuthSession.user_id == target_id).all()
            assert sessions
            assert all(row.revoked_at is not None for row in sessions)
    finally:
        target_client.close()


def test_logout_revokes_only_presented_session_and_is_idempotent(test_environment):
    client, factory = test_environment
    first_id, first_email = create_user(factory)
    second_id, second_email = create_user(factory)
    other_client = TestClient(app, base_url="http://testserver.local")
    try:
        login(client, first_email)
        login(other_client, second_email)
        first_session_id = client.cookies.get(settings.SESSION_COOKIE_NAME)
        second_session_id = other_client.cookies.get(settings.SESSION_COOKIE_NAME)

        response = post_with_csrf(client, "/auth/logout")
        assert response.status_code == 200
        assert settings.SESSION_COOKIE_NAME not in client.cookies
        assert client.get("/auth/me").status_code == 401
        assert other_client.get("/auth/me").status_code == 200

        with factory() as db:
            first_row = db.get(AuthSession, hash_session_id(first_session_id))
            second_row = db.get(AuthSession, hash_session_id(second_session_id))
            assert first_row.revoked_at is not None
            assert second_row.revoked_at is None
            assert first_row.user_id == first_id
            assert second_row.user_id == second_id

        # The client refreshes pre-auth CSRF after logout cleared that cookie.
        repeated = post_with_csrf(client, "/auth/logout")
        assert repeated.status_code == 200
        assert repeated.json()["message"] == "Logout successful"
    finally:
        other_client.close()


def test_logout_with_expired_or_missing_session_still_clears_cookie(test_environment):
    client, _ = test_environment
    client.cookies.set(
        settings.SESSION_COOKIE_NAME,
        "expired-or-unknown",
        domain="testserver.local",
        path="/",
    )
    response = post_with_csrf(client, "/auth/logout")
    assert response.status_code == 200
    assert settings.SESSION_COOKIE_NAME not in client.cookies


def test_session_list_uses_public_ids_and_revocation_is_owner_scoped(test_environment):
    client, factory = test_environment
    user_id, email = create_user(factory)
    other_user_id, other_email = create_user(factory)
    second_client = TestClient(app, base_url="http://testserver.local")
    unrelated_client = TestClient(app, base_url="http://testserver.local")
    try:
        login(client, email)
        login(second_client, email)
        login(unrelated_client, other_email)

        sessions = client.get("/auth/sessions")
        assert sessions.status_code == 200
        assert len(sessions.json()) == 2
        assert sum(row["is_current"] for row in sessions.json()) == 1
        assert client.cookies.get(settings.SESSION_COOKIE_NAME) not in sessions.text
        assert all("id_hash" not in row for row in sessions.json())

        second_public_id = next(row["id"] for row in sessions.json() if not row["is_current"])
        revoked = delete_with_csrf(client, f"/auth/sessions/{second_public_id}")
        assert revoked.status_code == 200
        assert client.get("/auth/me").status_code == 200
        assert second_client.get("/auth/me").status_code == 401

        unrelated_public_id = unrelated_client.get("/auth/sessions").json()[0]["id"]
        denied = delete_with_csrf(client, f"/auth/sessions/{unrelated_public_id}")
        assert denied.status_code == 404
        assert unrelated_client.get("/auth/me").status_code == 200
        with factory() as db:
            assert db.query(AuthSession).filter(AuthSession.user_id == user_id).count() == 2
            assert db.query(AuthSession).filter(AuthSession.user_id == other_user_id).count() == 1
    finally:
        second_client.close()
        unrelated_client.close()


def test_revoke_others_and_logout_all(test_environment):
    client, factory = test_environment
    user_id, email = create_user(factory)
    other_client = TestClient(app, base_url="http://testserver.local")
    try:
        login(client, email)
        login(other_client, email)

        revoked = post_with_csrf(client, "/auth/sessions/revoke-others")
        assert revoked.status_code == 200
        assert revoked.json()["revoked_count"] == 1
        assert client.get("/auth/me").status_code == 200
        assert other_client.get("/auth/me").status_code == 401

        login(other_client, email)
        logout_all = post_with_csrf(client, "/auth/logout-all")
        assert logout_all.status_code == 200
        assert logout_all.json()["revoked_count"] == 2
        assert settings.SESSION_COOKIE_NAME not in client.cookies
        assert client.get("/auth/me").status_code == 401
        assert other_client.get("/auth/me").status_code == 401
        with factory() as db:
            rows = db.query(AuthSession).filter(AuthSession.user_id == user_id).all()
            assert len(rows) == 3
            assert all(row.revoked_at is not None for row in rows)
    finally:
        other_client.close()


def test_session_auth_preserves_case_patient_and_image_ownership(test_environment, monkeypatch):
    client, factory = test_environment
    owner_id, owner_email = create_user(factory, role=UserRole.CLINICIAN)
    _, other_email = create_user(factory, role=UserRole.CLINICIAN)
    image_path = Path(__file__).with_name(f".synthetic-{uuid4().hex}.png")
    monkeypatch.setattr("app.routes.image.UPLOAD_DIR", Path(__file__).parent)
    image_path.write_bytes(b"synthetic-test-image")

    patient = Patient(
        patient_code=f"PAT-{uuid4().hex[:8]}",
        age=40,
        gender="unknown",
        clinician_id=owner_id,
    )
    with factory() as db:
        db.add(patient)
        db.flush()
        case = Case(owner_user_id=owner_id, patient_id=patient.id, status="created")
        db.add(case)
        db.flush()
        image = Image(
            case_id=case.id,
            file_path=str(image_path),
            original_filename="fixture.png",
            content_type="image/png",
            file_size=image_path.stat().st_size,
            width=10,
            height=10,
            sha256="a" * 64,
        )
        db.add(image)
        db.commit()
        case_id, image_id = case.id, image.id

    try:
        login(client, owner_email)
        assert client.get("/api/v1/patients/").status_code == 200
        assert len(client.get("/api/v1/cases").json()) == 1
        images = client.get(f"/api/v1/cases/{case_id}/images")
        assert images.status_code == 200
        assert images.json()[0]["id"] == str(image_id)
        assert client.get(f"/api/v1/cases/{case_id}/images/{image_id}/file").content == image_path.read_bytes()

        other_client = TestClient(app, base_url="http://testserver.local")
        try:
            login(other_client, other_email)
            assert other_client.get("/api/v1/cases").json() == []
            assert other_client.get(f"/api/v1/cases/{case_id}/images").status_code == 404
            assert other_client.get(f"/api/v1/cases/{case_id}/images/{image_id}/file").status_code == 404
        finally:
            other_client.close()
    finally:
        image_path.unlink(missing_ok=True)


def test_csrf_token_is_session_bound_and_rotates_at_login(test_environment):
    client, factory = test_environment
    _, email = create_user(factory)
    anonymous_token = client.get("/auth/csrf").json()["csrf_token"]
    login_response = login(client, email)
    first_session_token = login_response.json()["csrf_token"]
    assert first_session_token != anonymous_token

    rejected = client.patch(
        "/auth/me",
        json={"username": "changed-name"},
        headers={
            "X-CSRF-Token": anonymous_token,
            "Origin": settings.trusted_origins[0],
        },
    )
    assert rejected.status_code == 403

    other_client = TestClient(app, base_url="http://testserver.local")
    try:
        _, other_email = create_user(factory)
        login(other_client, other_email)
        other_client.cookies.set(
            settings.CSRF_COOKIE_NAME,
            first_session_token,
            domain="testserver.local",
            path="/",
        )
        cross_session = other_client.patch(
            "/auth/me",
            json={"username": "cross-session"},
            headers={
                "X-CSRF-Token": first_session_token,
                "Origin": settings.trusted_origins[0],
            },
        )
        assert cross_session.status_code == 403
    finally:
        other_client.close()


def test_untrusted_and_missing_origins_are_rejected(test_environment):
    client, factory = test_environment
    _, email = create_user(factory)
    client.get("/auth/csrf")

    untrusted = client.post(
        "/auth/login",
        json={"email": email, "password": "wrong"},
        headers={
            "X-CSRF-Token": client.cookies.get(settings.CSRF_COOKIE_NAME),
            "Origin": "https://attacker.example",
        },
    )
    assert untrusted.status_code == 403
    assert untrusted.json()["detail"] == "Untrusted request origin"

    missing = client.post(
        "/auth/login",
        json={"email": email, "password": "wrong"},
        headers={
            "X-CSRF-Token": client.cookies.get(settings.CSRF_COOKIE_NAME),
            "Referer": settings.trusted_origins[0] + "/login",
        },
    )
    assert missing.status_code == 403
    assert missing.json()["detail"] == "Origin header required"


def test_cors_preflight_uses_explicit_origins_methods_and_headers(test_environment):
    client, _ = test_environment
    origin = settings.trusted_origins[0]
    allowed = client.options(
        "/auth/login",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-csrf-token",
        },
    )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == origin
    assert allowed.headers["access-control-allow-credentials"] == "true"
    assert "*" not in allowed.headers.get("access-control-allow-methods", "")
    assert "*" not in allowed.headers.get("access-control-allow-headers", "")

    denied = client.options(
        "/auth/login",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert denied.status_code == 400
    assert "access-control-allow-origin" not in denied.headers


def test_production_cors_settings_require_https_exact_origins():
    base = {
        "DB_HOST": "localhost",
        "DB_NAME": "unit_test",
        "DB_USER": "unit_test",
        "DB_PASSWORD": "not-a-real-password",
        "JWT_SECRET_KEY": "j" * 40,
        "CSRF_SECRET_KEY": "c" * 40,
    }
    production = Settings(
        **base,
        APP_ENV="production",
        SESSION_COOKIE_SECURE=True,
        CORS_PRODUCTION_ORIGINS="https://dermai.example",
    )
    assert production.trusted_origins == ["https://dermai.example"]

    with pytest.raises(ValidationError):
        Settings(
            **base,
            APP_ENV="production",
            SESSION_COOKIE_SECURE=True,
            CORS_PRODUCTION_ORIGINS="http://dermai.example",
        )
    with pytest.raises(ValidationError):
        Settings(
            **base,
            APP_ENV="production",
            SESSION_COOKIE_SECURE=True,
            CORS_PRODUCTION_ORIGINS="*",
        )
    with pytest.raises(ValidationError):
        Settings(
            **base,
            APP_ENV="production",
            SESSION_COOKIE_SECURE=True,
            CORS_PRODUCTION_ORIGINS="",
        )
    with pytest.raises(ValidationError):
        Settings(
            **base,
            APP_ENV="production",
            SESSION_COOKIE_SECURE=True,
            CORS_PRODUCTION_ORIGINS="https://dermai.example",
            CORS_ALLOWED_METHODS="*",
        )
    with pytest.raises(ValidationError):
        Settings(
            **base,
            APP_ENV="production",
            SESSION_COOKIE_SECURE=True,
            CORS_PRODUCTION_ORIGINS="https://dermai.example",
            CORS_ALLOWED_HEADERS="*",
        )


def test_database_backed_login_rate_limit_is_case_normalized_and_non_enumerating(
    test_environment, monkeypatch
):
    client, factory = test_environment
    monkeypatch.setattr(settings, "LOGIN_RATE_LIMIT_PER_ACCOUNT", 2)
    monkeypatch.setattr(settings, "LOGIN_RATE_LIMIT_PER_IP", 20)
    _, existing_email = create_user(factory)
    unknown_email = f"unknown-{uuid4().hex}@example.com"

    existing_responses = []
    for attempt_email in (existing_email, existing_email.upper(), existing_email):
        existing_responses.append(
            post_with_csrf(
                client,
                "/auth/login",
                {"email": attempt_email, "password": "wrong-password"},
            )
        )
    unknown_responses = [
        post_with_csrf(
            client,
            "/auth/login",
            {"email": unknown_email, "password": "wrong-password"},
        )
        for _ in range(3)
    ]

    assert [response.status_code for response in existing_responses] == [401, 401, 429]
    assert [response.status_code for response in unknown_responses] == [401, 401, 429]
    assert existing_responses[0].json() == unknown_responses[0].json()
    assert existing_responses[-1].json() == unknown_responses[-1].json()
    assert existing_responses[-1].headers["retry-after"]
    with factory() as db:
        assert db.query(AuthRateLimitBucket).count() >= 3


def test_csrf_bootstrap_rate_limit_uses_shared_database_counter(test_environment, monkeypatch):
    client, factory = test_environment
    monkeypatch.setattr(settings, "CSRF_BOOTSTRAP_RATE_LIMIT_PER_IP", 2)
    assert client.get("/auth/csrf").status_code == 200
    assert client.get("/auth/csrf").status_code == 200
    limited = client.get("/auth/csrf")
    assert limited.status_code == 429
    assert limited.headers["retry-after"]
    with factory() as db:
        assert db.query(AuthRateLimitBucket).count() == 1


def test_revoking_a_session_invalidates_its_session_csrf_token(test_environment):
    client, factory = test_environment
    user_id, email = create_user(factory)
    login(client, email)
    session_id = client.cookies.get(settings.SESSION_COOKIE_NAME)
    csrf_token = client.cookies.get(settings.CSRF_COOKIE_NAME)

    with factory() as db:
        row = db.get(AuthSession, hash_session_id(session_id))
        row.revoked_at = datetime.now(timezone.utc)
        row.revoke_reason = "test_revocation"
        db.commit()

    response = client.patch(
        "/auth/me",
        json={"username": "should-not-update"},
        headers={
            "X-CSRF-Token": csrf_token,
            "Origin": settings.trusted_origins[0],
        },
    )
    assert response.status_code == 403


def test_case_status_requires_image_and_keeps_m2_states_unavailable(test_environment):
    client, factory = test_environment
    user_id, email = create_user(factory)
    login(client, email)
    created_patient = post_with_csrf(
        client,
        "/api/v1/patients/me",
        {"age": 35, "gender": "prefer_not_to_say"},
    )
    assert created_patient.status_code == 201
    created_case = post_with_csrf(
        client,
        "/api/v1/cases",
        {"patient_id": created_patient.json()["id"], "case_label": "M1 test"},
    )
    assert created_case.status_code == 201
    case_id = created_case.json()["id"]

    csrf = client.get("/auth/csrf").json()["csrf_token"]
    without_image = client.patch(
        f"/api/v1/cases/{case_id}/status",
        json={"status": "image_uploaded"},
        headers={"X-CSRF-Token": csrf, "Origin": settings.trusted_origins[0]},
    )
    assert without_image.status_code == 409

    csrf = client.get("/auth/csrf").json()["csrf_token"]
    m2_transition = client.patch(
        f"/api/v1/cases/{case_id}/status",
        json={"status": "quality_assessed"},
        headers={"X-CSRF-Token": csrf, "Origin": settings.trusted_origins[0]},
    )
    assert m2_transition.status_code == 409

    with factory() as db:
        case = db.get(Case, UUID(case_id))
        db.add(Image(
            case_id=case.id,
            file_path="/isolated/test/image.png",
            original_filename="upload",
            content_type="image/png",
            file_size=3,
            width=100,
            height=100,
            sha256="a" * 64,
        ))
        db.commit()

    csrf = client.get("/auth/csrf").json()["csrf_token"]
    with_image = client.patch(
        f"/api/v1/cases/{case_id}/status",
        json={"status": "image_uploaded"},
        headers={"X-CSRF-Token": csrf, "Origin": settings.trusted_origins[0]},
    )
    assert with_image.status_code == 200
    assert with_image.json()["status"] == "image_uploaded"
    history = client.get(f"/api/v1/cases/{case_id}/events")
    assert history.status_code == 200
    assert any(row["event_type"] == "image_uploaded" for row in history.json())


def test_admin_role_aliases_are_accepted_without_changing_persisted_values():
    assert AdminUserUpdate(role="patient_user").role == UserRole.USER
    assert AdminUserUpdate(role="ml_engineer").role == UserRole.DATA_SCIENTIST
    assert UserRole.PATIENT_USER is UserRole.USER
    assert UserRole.ML_ENGINEER is UserRole.DATA_SCIENTIST


def test_case_free_text_rejects_obvious_identifiers():
    with pytest.raises(ValidationError):
        CaseCreate(patient_id=uuid4(), description="Contact test@example.com")
    with pytest.raises(ValidationError):
        CaseNoteCreate(note="Call +1 (555) 123-4567")
    assert CaseNoteCreate(note="  de-identified observation  ").note == "de-identified observation"


def test_last_active_admin_cannot_be_demoted_or_deactivated(test_environment):
    client, factory = test_environment
    admin_id, email = create_user(factory, role=UserRole.ADMIN)
    login(client, email)
    csrf_token = client.get("/auth/csrf").json()["csrf_token"]
    response = client.patch(
        f"/auth/admin/users/{admin_id}",
        json={"is_active": False},
        headers={"X-CSRF-Token": csrf_token, "Origin": settings.trusted_origins[0]},
    )
    assert response.status_code == 409
    with factory() as db:
        assert db.get(User, admin_id).is_active is True


def test_every_protected_api_route_rejects_anonymous_requests(test_environment):
    client, _ = test_environment
    case_id = str(uuid4())
    patient_id = str(uuid4())
    image_id = str(uuid4())
    session_id = str(uuid4())
    protected = [
        ("GET", "/auth/me", None, None),
        ("PATCH", "/auth/me", {"username": "anonymous"}, None),
        ("GET", "/auth/sessions", None, None),
        ("GET", "/auth/admin/users", None, None),
        ("GET", "/auth/admin/audit", None, None),
        ("PATCH", f"/auth/admin/users/{uuid4()}", {"is_active": False}, None),
        ("DELETE", f"/auth/sessions/{session_id}", None, None),
        ("POST", "/auth/sessions/revoke-others", {}, None),
        ("POST", "/auth/logout-all", {}, None),
        ("GET", "/api/v1/patients/me", None, None),
        ("POST", "/api/v1/patients/me", {"age": 40}, None),
        ("PATCH", "/api/v1/patients/me", {"age": 41}, None),
        ("DELETE", "/api/v1/patients/me", None, None),
        ("GET", "/api/v1/patients/", None, None),
        ("POST", "/api/v1/patients/", {"age": 40}, None),
        ("GET", f"/api/v1/patients/{patient_id}", None, None),
        ("PATCH", f"/api/v1/patients/{patient_id}", {"age": 41}, None),
        ("DELETE", f"/api/v1/patients/{patient_id}", None, None),
        ("GET", "/api/v1/cases", None, None),
        ("POST", "/api/v1/cases", {"patient_id": patient_id}, None),
        ("GET", f"/api/v1/cases/patient/{patient_id}", None, None),
        ("GET", f"/api/v1/cases/{case_id}", None, None),
        ("PATCH", f"/api/v1/cases/{case_id}/status", {"status": "analyzed"}, None),
        ("POST", f"/api/v1/cases/{case_id}/notes", {"note": "synthetic"}, None),
        ("GET", f"/api/v1/cases/{case_id}/notes", None, None),
        ("GET", f"/api/v1/cases/{case_id}/events", None, None),
        ("GET", f"/api/v1/cases/{case_id}/images", None, None),
        ("POST", f"/api/v1/cases/{case_id}/images", None, None),
        ("GET", f"/api/v1/cases/{case_id}/images/{image_id}/file", None, None),
    ]
    image_bytes = BytesIO()
    PILImage.new("RGB", (100, 100), "red").save(image_bytes, format="PNG")
    valid_png = image_bytes.getvalue()
    csrf = client.get("/auth/csrf").json()["csrf_token"]
    headers = {"X-CSRF-Token": csrf, "Origin": settings.trusted_origins[0]}

    for method, path, payload, _ in protected:
        if method == "GET":
            response = client.get(path)
        elif method == "DELETE":
            response = client.delete(path, headers=headers)
        elif method == "POST" and path.endswith("/images"):
            response = client.post(
                path,
                files={"file": ("synthetic.png", valid_png, "image/png")},
                headers=headers,
            )
        else:
            response = client.request(method, path, json=payload, headers=headers)
        assert response.status_code == 401, f"{method} {path}: {response.status_code} {response.text}"


def test_upload_event_failure_rolls_back_metadata_status_and_file(test_environment, monkeypatch, tmp_path):
    _, factory = test_environment
    user_id, _ = create_user(factory)
    with factory() as db:
        patient = Patient(
            patient_code=f"PAT-{uuid4().hex.upper()}", age=42,
            gender="prefer_not_to_say", user_id=user_id, clinician_id=None,
        )
        db.add(patient)
        db.flush()
        case = Case(owner_user_id=user_id, patient_id=patient.id, status="created")
        db.add(case)
        db.commit()
        case_id = case.id

    image_bytes = BytesIO()
    PILImage.new("RGB", (100, 100), "red").save(image_bytes, format="PNG")
    image_bytes.seek(0)
    upload = UploadFile(
        filename="fixture.png", file=image_bytes,
        headers={"content-type": "image/png"},
    )

    def fail_case_event(session, _flush_context, _instances):
        if any(isinstance(item, CaseEvent) and item.event_type == "image_uploaded" for item in session.new):
            raise RuntimeError("Injected case event failure")

    monkeypatch.setattr("app.services.image_service.UPLOAD_DIR", tmp_path)
    event.listen(Session, "before_flush", fail_case_event)
    try:
        with factory() as db, pytest.raises(RuntimeError, match="Injected case event failure"):
            upload_case_image(db, case_id, user_id, upload)
    finally:
        event.remove(Session, "before_flush", fail_case_event)

    with factory() as db:
        assert db.query(Image).filter(Image.case_id == case_id).count() == 0
        assert db.get(Case, case_id).status == "created"
        assert db.query(CaseEvent).filter(CaseEvent.case_id == case_id).count() == 0


@pytest.mark.parametrize(
    "role,patient_list_status,own_patient_status,admin_status",
    [
        (UserRole.USER, 403, 404, 403),
        (UserRole.CLINICIAN, 200, 403, 403),
        (UserRole.RESEARCHER, 403, 403, 403),
        (UserRole.DATA_SCIENTIST, 403, 403, 403),
        (UserRole.ADMIN, 403, 403, 200),
    ],
)
def test_role_endpoint_acceptance_matrix(
    test_environment, role, patient_list_status, own_patient_status, admin_status,
    monkeypatch, tmp_path,
):
    _, factory = test_environment
    user_id, email = create_user(factory, role=role)
    monkeypatch.setattr("app.services.image_service.UPLOAD_DIR", tmp_path)
    monkeypatch.setattr("app.routes.image.UPLOAD_DIR", tmp_path)
    with TestClient(app, base_url="http://testserver.local") as role_client:
        login(role_client, email)
        assert role_client.get("/auth/me").status_code == 200
        assert role_client.get("/api/v1/cases").status_code == 200
        assert role_client.get("/auth/sessions").status_code == 200
        assert role_client.get("/api/v1/patients/").status_code == patient_list_status
        assert role_client.get("/api/v1/patients/me").status_code == own_patient_status
        assert role_client.get("/auth/admin/users").status_code == admin_status
        assert role_client.get("/auth/admin/audit").status_code == admin_status

        target_id, _ = create_user(factory)
        admin_change = role_client.patch(
            f"/auth/admin/users/{target_id}",
            json={"role": "clinician"},
            headers={
                "X-CSRF-Token": role_client.get("/auth/csrf").json()["csrf_token"],
                "Origin": settings.trusted_origins[0],
            },
        )
        assert admin_change.status_code == (200 if role == UserRole.ADMIN else 403)

        if role == UserRole.USER:
            patient_response = post_with_csrf(
                role_client, "/api/v1/patients/me", {"age": 38}
            )
            assert patient_response.status_code == 201
            patient_id = patient_response.json()["id"]
        else:
            assert post_with_csrf(
                role_client, "/api/v1/patients/me", {"age": 38}
            ).status_code == 403
            with factory() as db:
                patient = Patient(
                    patient_code=f"PAT-{uuid4().hex.upper()}", age=38,
                    gender="prefer_not_to_say", user_id=user_id, clinician_id=None,
                )
                db.add(patient)
                db.commit()
                patient_id = str(patient.id)

        if role == UserRole.CLINICIAN:
            clinician_patient = post_with_csrf(
                role_client, "/api/v1/patients/", {"age": 55}
            )
            assert clinician_patient.status_code == 201
            clinician_patient_id = clinician_patient.json()["id"]
            assert role_client.get(
                f"/api/v1/patients/{clinician_patient_id}"
            ).status_code == 200
            changed = role_client.patch(
                f"/api/v1/patients/{clinician_patient_id}",
                json={"age": 56},
                headers={
                    "X-CSRF-Token": role_client.get("/auth/csrf").json()["csrf_token"],
                    "Origin": settings.trusted_origins[0],
                },
            )
            assert changed.status_code == 200
            assert role_client.delete(
                f"/api/v1/patients/{clinician_patient_id}",
                headers={
                    "X-CSRF-Token": role_client.get("/auth/csrf").json()["csrf_token"],
                    "Origin": settings.trusted_origins[0],
                },
            ).status_code == 204
        else:
            fake_patient = str(uuid4())
            assert role_client.get(f"/api/v1/patients/{fake_patient}").status_code == 403
            assert role_client.patch(
                f"/api/v1/patients/{fake_patient}",
                json={"age": 56},
                headers={
                    "X-CSRF-Token": role_client.get("/auth/csrf").json()["csrf_token"],
                    "Origin": settings.trusted_origins[0],
                },
            ).status_code == 403
            assert role_client.delete(
                f"/api/v1/patients/{fake_patient}",
                headers={
                    "X-CSRF-Token": role_client.get("/auth/csrf").json()["csrf_token"],
                    "Origin": settings.trusted_origins[0],
                },
            ).status_code == 403

        case_response = post_with_csrf(
            role_client, "/api/v1/cases", {"patient_id": patient_id, "case_label": "Role matrix"}
        )
        assert case_response.status_code == 201
        case_id = case_response.json()["id"]
        assert role_client.get(f"/api/v1/cases/{case_id}").status_code == 200
        assert role_client.get(f"/api/v1/cases/{case_id}/events").status_code == 200
        assert role_client.get(f"/api/v1/cases/{case_id}/notes").status_code == 200
        assert role_client.get(f"/api/v1/cases/patient/{patient_id}").status_code == 200
        assert role_client.patch(
            f"/api/v1/cases/{case_id}/status",
            json={"status": "analyzed"},
            headers={
                "X-CSRF-Token": role_client.get("/auth/csrf").json()["csrf_token"],
                "Origin": settings.trusted_origins[0],
            },
        ).status_code == 409

        note_response = role_client.post(
            f"/api/v1/cases/{case_id}/notes",
            json={"note": "synthetic matrix note"},
            headers={
                "X-CSRF-Token": role_client.get("/auth/csrf").json()["csrf_token"],
                "Origin": settings.trusted_origins[0],
            },
        )
        assert note_response.status_code == (
            201 if role in {UserRole.CLINICIAN, UserRole.ADMIN} else 403
        )

        image_bytes = BytesIO()
        PILImage.new("RGB", (100, 100), "green").save(image_bytes, format="PNG")
        upload = role_client.post(
            f"/api/v1/cases/{case_id}/images",
            files={"file": ("matrix.png", image_bytes.getvalue(), "image/png")},
            headers={
                "X-CSRF-Token": role_client.get("/auth/csrf").json()["csrf_token"],
                "Origin": settings.trusted_origins[0],
            },
        )
        assert upload.status_code == 201
        image_id = upload.json()["id"]
        assert role_client.get(
            f"/api/v1/cases/{case_id}/images/{image_id}/file"
        ).status_code == 200

        if role == UserRole.USER:
            changed_profile = role_client.patch(
                "/api/v1/patients/me",
                json={"age": 39},
                headers={
                    "X-CSRF-Token": role_client.get("/auth/csrf").json()["csrf_token"],
                    "Origin": settings.trusted_origins[0],
                },
            )
            assert changed_profile.status_code == 200
            assert role_client.delete(
                "/api/v1/patients/me",
                headers={
                    "X-CSRF-Token": role_client.get("/auth/csrf").json()["csrf_token"],
                    "Origin": settings.trusted_origins[0],
                },
            ).status_code == 204


def test_clinician_patient_case_search_pagination_notes_archive(test_environment):
    client, factory = test_environment
    clinician_id, email = create_user(factory, role=UserRole.CLINICIAN)
    login(client, email)

    patients = []
    for age in (31, 42, 53):
        response = post_with_csrf(
            client,
            "/api/v1/patients/",
            {"age": age, "gender": "prefer_not_to_say"},
        )
        assert response.status_code == 201
        patients.append(response.json())

    first_page = client.get("/api/v1/patients/?offset=0&limit=1")
    second_page = client.get("/api/v1/patients/?offset=1&limit=1")
    assert first_page.status_code == second_page.status_code == 200
    assert len(first_page.json()) == len(second_page.json()) == 1
    assert first_page.json()[0]["id"] != second_page.json()[0]["id"]
    searched = client.get(f"/api/v1/patients/?search={patients[1]['patient_code']}")
    assert [item["id"] for item in searched.json()] == [patients[1]["id"]]

    patient_id = patients[1]["id"]
    updated = client.patch(
        f"/api/v1/patients/{patient_id}",
        json={"age": 43},
        headers={
            "X-CSRF-Token": client.get("/auth/csrf").json()["csrf_token"],
            "Origin": settings.trusted_origins[0],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["age"] == 43

    case = post_with_csrf(
        client,
        "/api/v1/cases",
        {"patient_id": patient_id, "case_label": "Linked record"},
    )
    assert case.status_code == 201
    case_id = case.json()["id"]
    linked_cases = client.get(f"/api/v1/cases/patient/{patient_id}")
    assert [item["id"] for item in linked_cases.json()] == [case_id]
    assert client.get("/api/v1/cases?status=created&limit=100").json()
    assert client.get("/api/v1/cases?status=analyzed&limit=100").json() == []

    note = client.post(
        f"/api/v1/cases/{case_id}/notes",
        json={"note": "  synthetic follow-up note  "},
        headers={
            "X-CSRF-Token": client.get("/auth/csrf").json()["csrf_token"],
            "Origin": settings.trusted_origins[0],
        },
    )
    assert note.status_code == 201
    assert note.json()["note"] == "synthetic follow-up note"
    assert len(client.get(f"/api/v1/cases/{case_id}/notes").json()) == 1
    assert client.get(f"/api/v1/cases/{case_id}/events").json()[0]["event_type"] == "case_created"

    archived = client.delete(
        f"/api/v1/patients/{patient_id}",
        headers={
            "X-CSRF-Token": client.get("/auth/csrf").json()["csrf_token"],
            "Origin": settings.trusted_origins[0],
        },
    )
    assert archived.status_code == 204
    assert client.get(f"/api/v1/patients/{patient_id}").status_code == 404
    assert client.get("/api/v1/patients/").json()
    with factory() as db:
        assert db.get(Patient, UUID(patient_id)).archived_at is not None
        assert db.get(Case, UUID(case_id)).owner_user_id == clinician_id


def test_isolated_m1_workflow_register_upload_preprocess_and_revoke(
    test_environment, monkeypatch, tmp_path
):
    import base64
    import hashlib

    import numpy as np

    from app.services.image_preprocessing import preprocess_image

    client, factory = test_environment
    monkeypatch.setattr("app.services.image_service.UPLOAD_DIR", tmp_path)
    monkeypatch.setattr("app.routes.image.UPLOAD_DIR", tmp_path)

    registration = post_with_csrf(
        client,
        "/auth/register",
        {
            "username": f"m1-{uuid4().hex[:10]}",
            "email": f"{uuid4().hex}@example.com",
            "password": "TestPassword123!",
        },
    )
    assert registration.status_code == 201
    email = registration.json()["email"]
    invalid_login = post_with_csrf(
        client, "/auth/login", {"email": email, "password": "wrong-password"}
    )
    assert invalid_login.status_code == 401

    authenticated = login(client, email)
    session_cookie = client.cookies.get(settings.SESSION_COOKIE_NAME)
    assert session_cookie
    assert client.get("/auth/me").status_code == 200  # Session restoration.
    patient = post_with_csrf(
        client, "/api/v1/patients/me", {"age": 44, "gender": "unknown"}
    )
    assert patient.status_code == 201
    assert client.get("/api/v1/patients/me").json()["id"] == patient.json()["id"]

    case = post_with_csrf(
        client,
        "/api/v1/cases",
        {"patient_id": patient.json()["id"], "case_label": "Acceptance fixture"},
    )
    assert case.status_code == 201
    case_id = case.json()["id"]
    assert client.get(f"/api/v1/cases/{case_id}").status_code == 200
    assert client.get("/api/v1/cases?offset=0&limit=10").json()[0]["id"] == case_id

    image_bytes = BytesIO()
    pixels = np.random.default_rng(4).integers(0, 256, (160, 180, 3), dtype=np.uint8)
    PILImage.fromarray(pixels, "RGB").save(image_bytes, format="PNG")
    image_content = image_bytes.getvalue()
    csrf = client.get("/auth/csrf").json()["csrf_token"]
    invalid_upload = client.post(
        f"/api/v1/cases/{case_id}/images",
        files={"file": ("invalid.txt", b"not an image", "text/plain")},
        headers={"X-CSRF-Token": csrf, "Origin": settings.trusted_origins[0]},
    )
    assert invalid_upload.status_code == 415

    from app.services import image_service

    original_max_bytes = image_service.MAX_FILE_SIZE
    monkeypatch.setattr(image_service, "MAX_FILE_SIZE", 1024)
    csrf = client.get("/auth/csrf").json()["csrf_token"]
    oversized_upload = client.post(
        f"/api/v1/cases/{case_id}/images",
        files={"file": ("large.png", image_content, "image/png")},
        headers={"X-CSRF-Token": csrf, "Origin": settings.trusted_origins[0]},
    )
    assert oversized_upload.status_code == 413
    monkeypatch.setattr(image_service, "MAX_FILE_SIZE", original_max_bytes)

    csrf = client.get("/auth/csrf").json()["csrf_token"]
    upload = client.post(
        f"/api/v1/cases/{case_id}/images",
        files={"file": ("capture.png", image_content, "image/png")},
        headers={"X-CSRF-Token": csrf, "Origin": settings.trusted_origins[0]},
    )
    assert upload.status_code == 201, upload.text
    image = upload.json()
    # Storage names are random; resolve only within the isolated case directory.
    stored_files = list((Path(tmp_path) / case_id).glob("*.png"))
    assert len(stored_files) == 1
    stored_path = stored_files[0]
    stored_bytes = stored_path.read_bytes()
    assert image["sha256"] == hashlib.sha256(stored_bytes).hexdigest()
    assert image["file_size"] == len(stored_bytes)
    fetched = client.get(f"/api/v1/cases/{case_id}/images/{image['id']}/file")
    assert fetched.status_code == 200
    assert fetched.content == stored_bytes

    csrf = client.get("/auth/csrf").json()["csrf_token"]
    preprocessing = client.post(
        f"/api/v1/cases/{case_id}/images/{image['id']}/preprocessing",
        headers={
            "X-CSRF-Token": csrf,
            "Origin": settings.trusted_origins[0],
        },
    )
    assert preprocessing.status_code == 200, preprocessing.text
    report = preprocessing.json()
    assert report["status"] == "completed"
    assert report["history_persisted"] is False
    assert report["preprocessing_version"] == "m1.2-imagenet-rgb224"
    assert [step["name"] for step in report["steps"]] == [
        "Decode image",
        "EXIF orientation handling",
        "Convert to RGB",
        "Resize and pad",
        "Scale pixel values",
        "ImageNet normalization",
    ]
    assert all(step["status"] == "completed" for step in report["steps"])
    preview_data = report["preview_data_url"].split(",", 1)[1]
    preview = PILImage.open(BytesIO(base64.b64decode(preview_data)))
    assert preview.size == (224, 224)

    preprocessed = preprocess_image(stored_path)
    assert preprocessed.shape == (224, 224, 3)
    assert preprocessed.dtype == np.float32
    assert np.isfinite(preprocessed).all()
    assert client.get(f"/api/v1/cases/{case_id}/events").json()
    assert client.get(f"/api/v1/cases/{case_id}/images").json()[0]["sha256"] == image["sha256"]

    blocked_transition = client.patch(
        f"/api/v1/cases/{case_id}/status",
        json={"status": "analyzed"},
        headers={"Origin": settings.trusted_origins[0]},
    )
    assert blocked_transition.status_code == 403  # Missing CSRF token.
    csrf = client.get("/auth/csrf").json()["csrf_token"]
    invalid_transition = client.patch(
        f"/api/v1/cases/{case_id}/status",
        json={"status": "analyzed"},
        headers={"X-CSRF-Token": csrf, "Origin": settings.trusted_origins[0]},
    )
    assert invalid_transition.status_code == 409

    _, other_clinician_email = create_user(factory, role=UserRole.CLINICIAN)
    with TestClient(app, base_url="http://testserver.local") as other_client:
        login(other_client, other_clinician_email)
        assert other_client.get(f"/api/v1/patients/{patient.json()['id']}").status_code == 404
        other_csrf = other_client.get("/auth/csrf").json()["csrf_token"]
        assert other_client.patch(
            f"/api/v1/patients/{patient.json()['id']}",
            json={"age": 90},
            headers={"X-CSRF-Token": other_csrf, "Origin": settings.trusted_origins[0]},
        ).status_code == 404
        assert other_client.delete(
            f"/api/v1/patients/{patient.json()['id']}",
            headers={"X-CSRF-Token": other_csrf, "Origin": settings.trusted_origins[0]},
        ).status_code == 404
        assert other_client.get(f"/api/v1/cases/{case_id}").status_code == 404
        assert other_client.get(f"/api/v1/cases/patient/{patient.json()['id']}").status_code == 403
        assert other_client.get(f"/api/v1/cases/{case_id}/notes").status_code == 404
        assert other_client.get(f"/api/v1/cases/{case_id}/events").status_code == 404
        assert other_client.post(
            f"/api/v1/cases/{case_id}/notes",
            json={"note": "unauthorized synthetic note"},
            headers={"X-CSRF-Token": other_csrf, "Origin": settings.trusted_origins[0]},
        ).status_code == 404
        assert other_client.get(
            f"/api/v1/cases/{case_id}/images/{image['id']}/file"
        ).status_code == 404
        assert other_client.post(
            f"/api/v1/cases/{case_id}/images/{image['id']}/preprocessing",
            headers={
                "X-CSRF-Token": other_csrf,
                "Origin": settings.trusted_origins[0],
            },
        ).status_code == 404

    client.cookies.set(settings.SESSION_COOKIE_NAME, "invalid-session", domain="testserver.local", path="/")
    assert client.get("/auth/me").status_code == 401
    client.cookies.set(settings.SESSION_COOKIE_NAME, session_cookie, domain="testserver.local", path="/")
    csrf = authenticated.json()["csrf_token"]
    logout = client.post(
        "/auth/logout",
        headers={"X-CSRF-Token": csrf, "Origin": settings.trusted_origins[0]},
    )
    assert logout.status_code == 200
    assert client.get("/auth/me").status_code == 401
