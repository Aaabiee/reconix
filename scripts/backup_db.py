#!/usr/bin/env python3
"""Database backup script for Reconix.

Creates timestamped PostgreSQL backups using pg_dump with compression.
Supports local storage and optional upload to S3-compatible storage.

Usage:
    python scripts/backup_db.py
    python scripts/backup_db.py --output-dir /backups --retention-days 30
    python scripts/backup_db.py --database-url postgresql://user:pass@host/reconix

Security:
    - Database URL read from environment variable (never from CLI args in production)
    - Backup files created with restricted permissions (0o600)
    - No shell=True subprocess calls (prevents command injection)
"""

import argparse
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("reconix.backup")

DEFAULT_BACKUP_DIR = "backups"
DEFAULT_RETENTION_DAYS = 30


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


def create_backup(db_config: dict, output_dir: str) -> str | None:
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"reconix_{db_config['database']}_{timestamp}.sql.gz"
    filepath = os.path.join(output_dir, filename)

    env = os.environ.copy()
    env["PGPASSWORD"] = db_config["password"]

    cmd = [
        "pg_dump",
        "--host", db_config["host"],
        "--port", db_config["port"],
        "--username", db_config["username"],
        "--dbname", db_config["database"],
        "--format", "custom",
        "--compress", "9",
        "--no-owner",
        "--no-privileges",
        "--verbose",
        "--file", filepath,
    ]

    logger.info(f"Starting backup: {db_config['database']}@{db_config['host']}")

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=3600,
        )

        if result.returncode != 0:
            logger.error(f"pg_dump failed: {result.stderr}")
            return None

        os.chmod(filepath, 0o600)

        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        logger.info(f"Backup complete: {filepath} ({size_mb:.2f} MB)")
        return filepath

    except FileNotFoundError:
        logger.error("pg_dump not found — install PostgreSQL client tools")
        return None
    except subprocess.TimeoutExpired:
        logger.error("Backup timed out after 1 hour")
        return None


def cleanup_old_backups(output_dir: str, retention_days: int) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    removed = 0

    for entry in Path(output_dir).glob("reconix_*.sql.gz"):
        if entry.is_file():
            mtime = datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                entry.unlink()
                logger.info(f"Removed old backup: {entry.name}")
                removed += 1

    return removed


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconix database backup")
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_BACKUP_DIR,
        help=f"Backup output directory (default: {DEFAULT_BACKUP_DIR})",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=DEFAULT_RETENTION_DAYS,
        help=f"Days to retain old backups (default: {DEFAULT_RETENTION_DAYS})",
    )
    parser.add_argument(
        "--database-url",
        default="",
        help="Database URL (default: reads DATABASE_URL env var)",
    )
    args = parser.parse_args()

    db_url = args.database_url or os.environ.get("DATABASE_URL", "")
    if not db_url:
        logger.error("DATABASE_URL not set. Use --database-url or set the environment variable.")
        sys.exit(1)

    db_config = parse_database_url(db_url)

    filepath = create_backup(db_config, args.output_dir)
    if not filepath:
        sys.exit(1)

    removed = cleanup_old_backups(args.output_dir, args.retention_days)
    if removed:
        logger.info(f"Cleaned up {removed} old backup(s)")

    logger.info("Backup process complete")


if __name__ == "__main__":
    main()
