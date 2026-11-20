from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def list(self, offset: int, limit: int):
        return self.db.scalars(select(User).order_by(User.id).offset(offset).limit(limit)).all()
