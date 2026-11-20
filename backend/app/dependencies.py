from typing import Annotated

from fastapi import Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_token

DB = Annotated[Session, Depends(get_db)]
bearer = HTTPBearer(auto_error=False)


def current_user(
    db: DB,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    if not credentials:
        raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})
    claims = decode_token(credentials.credentials, "access")
    user = db.get(User, int(claims["sub"]))
    if not user or not user.is_active:
        raise HTTPException(401, "Account is unavailable")
    return user


CurrentUser = Annotated[User, Depends(current_user)]
Offset = Annotated[int, Query(ge=0)]
Limit = Annotated[int, Query(ge=1, le=100)]


def require_roles(*roles: str):
    def check(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(403, "This action is not permitted for your role")
        return user

    return check


Admin = Annotated[User, Depends(require_roles("admin"))]
Staff = Annotated[User, Depends(require_roles("employee", "manager", "admin"))]
Reviewer = Annotated[User, Depends(require_roles("manager", "admin"))]
Employee = Annotated[User, Depends(require_roles("employee"))]
