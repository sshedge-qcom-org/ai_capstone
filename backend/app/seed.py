"""Explicit, idempotent local demo seed; never runs on application startup."""

import os

from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models import Role, User
from app.security import hash_password
from app.services.seed_data import seed_history, seed_procurement

ROLES = ("admin", "manager", "employee", "vendor")


def seed():
    if settings.environment != "development":
        raise SystemExit("Demo seeding is permitted only in development")
    password = os.environ.get("DEMO_PASSWORD", "")
    if len(password) < 10:
        raise SystemExit("Set DEMO_PASSWORD to a strong local-only demo password")
    with SessionLocal() as db:
        for name in ROLES:
            if not db.get(Role, name):
                db.add(Role(name=name))
        db.flush()
        for role in ROLES:
            email = f"{role}@company.com"
            if not db.scalar(select(User).where(User.email == email)):
                db.add(
                    User(
                        full_name=f"Demo {role.title()}",
                        email=email,
                        role=role,
                        password_hash=hash_password(password),
                    )
                )
        db.commit()
        manager = db.scalar(select(User).where(User.email == "manager@company.com"))
        employee = db.scalar(select(User).where(User.email == "employee@company.com"))
        employee.manager_id = manager.id
        seed_procurement(db, employee, manager)
        seed_history(db, manager)
        db.commit()
    print("Demo users seeded (existing passwords preserved).")


if __name__ == "__main__":
    seed()
