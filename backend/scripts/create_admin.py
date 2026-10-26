"""
Administrative user provisioning script.

Usage:
    python scripts/create_admin.py --email admin@example.com --name "System Administrator"

Security rules:
- Password is read via getpass prompt or ADMIN_PASSWORD environment variable (never as CLI flag)
- Never prints or logs the password
- Validates email address syntax (.local, .test, and private test domains are rejected)
- Rejects duplicate email addresses
- Strictly assigns the 'admin' role
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path

# Ensure backend root is on sys.path
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from email_validator import EmailNotValidError, validate_email

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User

REJECTED_DOMAINS = (".local", ".test", ".example", ".invalid", ".localhost")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for email and name."""
    parser = argparse.ArgumentParser(
        description="Provision a HireLens system administrator user.",
    )
    parser.add_argument(
        "--email",
        required=True,
        type=str,
        help="Administrator email address",
    )
    parser.add_argument(
        "--name",
        required=True,
        type=str,
        help="Administrator full display name",
    )
    return parser.parse_args()


def validate_admin_email(raw_email: str) -> str:
    """
    Validate and normalize administrative email.

    Rejects test and local top-level domains.
    """
    clean_email = raw_email.strip().lower()

    try:
        validated = validate_email(clean_email, check_deliverability=False)
        email = validated.normalized
    except EmailNotValidError as exc:
        print(
            f"Error: Invalid email format ({exc}). Validation cannot be bypassed.",
            file=sys.stderr,
        )
        sys.exit(1)

    domain = email.split("@")[-1]
    for rejected in REJECTED_DOMAINS:
        if domain == rejected.lstrip(".") or domain.endswith(rejected):
            print(
                f"Error: Email domain '{domain}' is not allowed ({rejected} domains are rejected).",
                file=sys.stderr,
            )
            sys.exit(1)

    return email


def get_admin_password() -> str:
    """
    Securely obtain administrator password from environment or interactive prompt.

    Never accepts passwords from CLI flags.
    """
    password = os.environ.get("ADMIN_PASSWORD")
    if not password:
        password = getpass.getpass("Enter administrator password: ")
        confirm = getpass.getpass("Confirm administrator password: ")
        if password != confirm:
            print("Error: Passwords do not match.", file=sys.stderr)
            sys.exit(1)

    if len(password) < 8 or len(password) > 128:
        print("Error: Password must be between 8 and 128 characters.", file=sys.stderr)
        sys.exit(1)

    return password


def main() -> None:
    """Provision administrator in the database."""
    args = parse_args()
    email = validate_admin_email(args.email)
    name = args.name.strip()
    if not name:
        print("Error: Name cannot be empty.", file=sys.stderr)
        sys.exit(1)

    password = get_admin_password()

    if SessionLocal is None:
        print("Error: Database connection is not configured.", file=sys.stderr)
        sys.exit(1)

    with SessionLocal() as db:
        # Duplicate check
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(
                f"Error: An account with email '{email}' already exists.",
                file=sys.stderr,
            )
            sys.exit(1)

        hashed = hash_password(password)
        admin_user = User(
            email=email,
            full_name=name,
            hashed_password=hashed,
            role="admin",
            is_active=True,
            token_version=1,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print(f"Administrator successfully created with ID: {admin_user.id}")


if __name__ == "__main__":
    main()
