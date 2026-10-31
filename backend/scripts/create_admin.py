"""Create the first administrator interactively after applying migrations."""
from getpass import getpass
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.models.user import User, UserRole


def main() -> None:
    email = input("Admin email: ").strip().lower()
    username = input("Admin display name: ").strip()
    password = getpass("Admin password (12+ characters): ")
    confirmation = getpass("Confirm password: ")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise SystemExit("Enter a valid email address.")
    if len(username) < 3 or len(username) > 50:
        raise SystemExit("Display name must be 3–50 characters.")
    if len(password) < 12 or password != confirmation:
        raise SystemExit("Password must be at least 12 characters and both entries must match.")

    with SessionLocal() as db:
        if db.query(User).filter(User.role == UserRole.ADMIN, User.is_active.is_(True)).first():
            raise SystemExit("An active administrator already exists; no account was changed.")
        if db.query(User).filter(User.email == email).first():
            raise SystemExit("That email already belongs to an account; no account was changed.")
        db.add(User(username=username, email=email, password_hash=hash_password(password), role=UserRole.ADMIN, is_active=True))
        db.commit()
    print("Administrator created.")


if __name__ == "__main__":
    main()
