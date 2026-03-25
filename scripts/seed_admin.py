#!/usr/bin/env python3
"""Seed the initial admin user for a fresh Reconix deployment.

Usage:
    pipenv run python scripts/seed_admin.py
    pipenv run python scripts/seed_admin.py --email admin@reconix.ng --name "System Admin"

Security:
    - Password read from ADMIN_PASSWORD env var or prompted interactively
    - Never accepts password via CLI arguments (prevents shell history leak)
    - Validates password meets 12-char minimum
"""

import asyncio
import getpass
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("reconix.seed")


async def seed_admin(email: str, full_name: str, password: str, organization: str) -> None:
    os.environ.setdefault("ENVIRONMENT", "development")

    from fast_api.db import init_db, close_db, get_session_factory
    from fast_api.models.user import User
    from fast_api.auth.authlib.password import PasswordManager
    from sqlalchemy import select

    await init_db()
    factory = get_session_factory()

    async with factory() as session:
        existing = await session.execute(
            select(User).where(User.email == email)
        )
        if existing.scalar_one_or_none():
            logger.warning(f"User {email} already exists — skipping")
            await close_db()
            return

        admin = User(
            email=email,
            hashed_password=PasswordManager.hash_password(password),
            full_name=full_name,
            role="admin",
            organization=organization,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        logger.info(f"Admin user created: {email} (role=admin)")

    await close_db()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Seed initial admin user")
    parser.add_argument("--email", default="admin@reconix.ng", help="Admin email")
    parser.add_argument("--name", default="System Administrator", help="Admin full name")
    parser.add_argument("--org", default="Reconix", help="Organization name")
    args = parser.parse_args()

    password = os.environ.get("ADMIN_PASSWORD", "")
    if not password:
        password = getpass.getpass("Enter admin password (min 12 chars): ")

    if len(password) < 12:
        logger.error("Password must be at least 12 characters")
        sys.exit(1)

    asyncio.run(seed_admin(args.email, args.name, password, args.org))


if __name__ == "__main__":
    main()
