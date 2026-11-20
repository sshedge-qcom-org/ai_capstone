import uuid
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.models import RefreshSession, Supplier, User, utcnow
from app.repositories.users import UserRepository
from app.schemas import Register, UserUpdate
from app.security import decode_token, hash_password, issue_token, token_hash, verify_password

DUMMY_HASH = hash_password("timing-protection-not-an-account-19")


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def register(self, data: Register) -> User:
        user = User(
            full_name=data.full_name,
            email=str(data.email).lower(),
            password_hash=hash_password(data.password),
            role="employee",
        )
        self.db.add(user)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(409, "Email is already registered") from exc
        return user

    def login(self, email: str, password: str):
        user = self.users.by_email(email)
        valid = verify_password(password, user.password_hash if user else DUMMY_HASH)
        if not user or not valid or not user.is_active:
            raise HTTPException(401, "Invalid email or password")
        return self.new_session(user)

    def new_session(self, user: User):
        session_id = str(uuid.uuid4())
        duration = timedelta(days=settings.refresh_token_days)
        refresh = issue_token(user.id, "refresh", duration, session_id)
        self.db.add(
            RefreshSession(
                id=session_id,
                user_id=user.id,
                token_hash=token_hash(refresh),
                expires_at=utcnow() + duration,
            )
        )
        self.db.commit()
        return self.access(user), refresh

    def access(self, user: User):
        return {
            "access_token": issue_token(
                user.id, "access", timedelta(minutes=settings.access_token_minutes)
            ),
            "token_type": "bearer",
            "user": user,
        }

    def refresh(self, token: str):
        claims = decode_token(token, "refresh")
        user = self.users.get(int(claims["sub"]))
        if not user or not user.is_active:
            raise HTTPException(401, "Account is unavailable")
        result = self.db.execute(
            update(RefreshSession)
            .where(
                RefreshSession.id == claims["jti"],
                RefreshSession.user_id == user.id,
                RefreshSession.token_hash == token_hash(token),
                RefreshSession.revoked_at.is_(None),
                RefreshSession.expires_at > utcnow(),
            )
            .values(revoked_at=utcnow())
        )
        if result.rowcount != 1:
            self.db.rollback()
            raise HTTPException(401, "Refresh session is revoked or expired")
        return self.new_session(user)

    def logout(self, token: str):
        self.db.execute(
            update(RefreshSession)
            .where(
                RefreshSession.token_hash == token_hash(token),
                RefreshSession.revoked_at.is_(None),
            )
            .values(revoked_at=utcnow())
        )
        self.db.commit()

    def update_user(self, actor: User, user_id: int, data: UserUpdate):
        user = self.users.get(user_id)
        if not user:
            raise HTTPException(404, "User not found")
        if user.id == actor.id and (data.role != "admin" or not data.is_active):
            raise HTTPException(400, "You cannot demote or deactivate your own account")
        if data.supplier_id is not None and (
            data.role != "vendor" or not self.db.get(Supplier, data.supplier_id)
        ):
            raise HTTPException(422, "Only vendors may be linked to an existing supplier")
        if data.role == "vendor" and data.is_active and data.supplier_id is None:
            raise HTTPException(422, "Active vendors require a supplier assignment")
        if data.manager_id is not None:
            manager = self.users.get(data.manager_id)
            if not manager or manager.role != "manager" or not manager.is_active:
                raise HTTPException(422, "Assign an active manager")
            if manager.id == user.id or data.role != "employee":
                raise HTTPException(422, "Only employees can be assigned a separate manager")
        for key, value in data.model_dump().items():
            setattr(user, key, value)
        self.db.commit()
        return user
