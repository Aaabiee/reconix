#!/usr/bin/env python3
"""Database restore script for Reconix.

Restores a PostgreSQL backup created by backup_db.py.

Usage:
    python scripts/restore_db.py --backup-file backups/reconix_reconix_20240301T120000Z.sql.gz
    python scripts/restore_db.py --backup-file backups/latest.sql.gz --database-url postgresql://...

Security:
    - Validates backup file path (no path traversal)
    - Database URL read from environment variable (never from CLI args in production)
    - No shell=True subprocess calls (prevents command injection)
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("reconix.restore")


def parse_database_url(url: str) -> dict:
    parsed = urlparse(url)
    scheme = parsed.scheme.split("+")[0]
    if scheme != "postgresql":
        logger.error(f"Only PostgreSQL is supported, got: {scheme}")
        sys.exit(1)

    return {
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "database": (parsed.path or "/reconix").lstrip("/"),
        "username": parsed.username or "reconix",
        "password": parsed.password or "",
    }


def validate_backup_path(backup_file: str) -> Path:
    path = Path(backup_file).resolve()
    if ".." in backup_file:
        logger.error("Path traversal detected — aborting")
        sys.exit(1)
    if not path.is_file():
        logger.error(f"Backup file not found: {path}")
        sys.exit(1)
    return path


def restore_backup(db_config: dict, backup_path: Path) -> bool:
    env = os.environ.copy()
    env["PGPASSWORD"] = db_config["password"]

    cmd = [
        "pg_restore",
        "--host", db_config["host"],
        "--port", db_config["port"],
        "--username", db_config["username"],
        "--dbname", db_config["database"],
        "--no-owner",
        "--no-privileges",
        "--clean",
        "--if-exists",
        "--verbose",
        str(backup_path),
    ]

    logger.info(f"Starting restore from: {backup_path.name}")
    logger.info(f"Target: {db_config['database']}@{db_config['host']}")

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=3600,
        )

        if result.returncode != 0 and "ERROR" in result.stderr:
            logger.error(f"pg_restore errors: {result.stderr}")
            return False

        if result.returncode != 0:
            logger.warning(f"pg_restore completed with warnings: {result.stderr[:500]}")

        logger.info("Restore complete")
        return True

    except FileNotFoundError:
        logger.error("pg_restore not found — install PostgreSQL client tools")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Restore timed out after 1 hour")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconix database restore")
    parser.add_argument(
        "--backup-file",
        required=True,
        help="Path to backup file created by backup_db.py",
    )
    parser.add_argument(
        "--database-url",
        default="",
        help="Database URL (default: reads DATABASE_URL env var)",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip confirmation prompt",
    )
    args = parser.parse_args()

    db_url = args.database_url or os.environ.get("DATABASE_URL", "")
    if not db_url:
        logger.error("DATABASE_URL not set. Use --database-url or set the environment variable.")
        sys.exit(1)

    db_config = parse_database_url(db_url)
    backup_path = validate_backup_path(args.backup_file)

    if not args.confirm:
        print(f"\nThis will restore {backup_path.name} to {db_config['database']}@{db_config['host']}")
        print("Existing data will be OVERWRITTEN.\n")
        answer = input("Type 'yes' to confirm: ")
        if answer.strip().lower() != "yes":
            logger.info("Restore cancelled by user")
            sys.exit(0)

    success = restore_backup(db_config, backup_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
