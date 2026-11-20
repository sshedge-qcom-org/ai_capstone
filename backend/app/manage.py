"""Operational commands; run migrations before creating the first administrator."""

import argparse
import getpass
import os
import sqlite3
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.engine import make_url

from app.config import settings
from app.database import SessionLocal
from app.models import RefreshSession, User, utcnow
from app.schemas import Register
from app.security import hash_password


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    admin = commands.add_parser(
        "create-admin", help="Create an initial administrator interactively"
    )
    admin.add_argument("--email", required=True)
    admin.add_argument("--full-name", required=True)
    backup = commands.add_parser("backup", help="Create a consistent SQLite backup")
    backup.add_argument("--output", type=Path, required=True)
    commands.add_parser("prune-sessions", help="Remove expired refresh sessions")
    args = parser.parse_args()
    if args.command == "create-admin":
        password = getpass.getpass("Administrator password: ")
        if password != getpass.getpass("Confirm password: "):
            raise SystemExit("Passwords do not match")
        data = Register(full_name=args.full_name, email=args.email, password=password)
        with SessionLocal() as db:
            if db.scalar(select(User.id).where(User.email == data.email)):
                raise SystemExit("Account already exists; use the administration UI")
            db.add(
                User(
                    full_name=data.full_name,
                    email=str(data.email),
                    password_hash=hash_password(data.password),
                    role="admin",
                )
            )
            db.commit()
        print("Administrator created.")
    elif args.command == "backup":
        source = make_url(settings.database_url).database
        if not source or not Path(source).is_file():
            raise SystemExit("Configured SQLite database does not exist")
        target = args.output.resolve()
        if target == Path(source).resolve():
            raise SystemExit("Backup must use a separate path")
        try:
            descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise SystemExit("Backup output already exists; choose a new path") from exc
        os.close(descriptor)
        with sqlite3.connect(f"file:{Path(source).resolve()}?mode=ro", uri=True) as original:
            with sqlite3.connect(target) as copy:
                original.backup(copy)
                if copy.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise SystemExit("Backup failed integrity verification")
        print(f"Verified backup created: {target}")
    else:
        with SessionLocal() as db:
            result = db.execute(delete(RefreshSession).where(RefreshSession.expires_at < utcnow()))
            db.commit()
            print(f"Pruned {result.rowcount} expired sessions.")


if __name__ == "__main__":
    main()
