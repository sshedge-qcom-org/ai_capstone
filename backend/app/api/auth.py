from fastapi import APIRouter, HTTPException, Request, Response

from app.config import settings
from app.dependencies import DB, Admin, CurrentUser, Limit, Offset
from app.repositories.users import UserRepository
from app.schemas import Login, Register, TokenOut, UserOut, UserUpdate
from app.services.auth import AuthService

router = APIRouter(prefix="/api/v1", tags=["Authentication"])
COOKIE = "procureai_refresh"
COOKIE_PATH = "/api/v1/auth"


def validate_origin(request: Request):
    origin = request.headers.get("origin")
    if origin and origin not in settings.cors_origins:
        raise HTTPException(403, "Untrusted request origin")


def set_refresh(response: Response, token: str):
    response.set_cookie(
        COOKIE,
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path=COOKIE_PATH,
        max_age=settings.refresh_token_days * 86400,
    )


@router.post("/auth/register", response_model=UserOut, status_code=201)
def register(data: Register, db: DB, request: Request):
    validate_origin(request)
    return AuthService(db).register(data)


@router.post("/auth/login", response_model=TokenOut)
def login(data: Login, db: DB, request: Request, response: Response):
    validate_origin(request)
    result, refresh = AuthService(db).login(str(data.email), data.password)
    set_refresh(response, refresh)
    return result


@router.post("/auth/refresh", response_model=TokenOut)
def refresh(db: DB, request: Request, response: Response):
    validate_origin(request)
    token = request.cookies.get(COOKIE)
    if not token:
        raise HTTPException(401, "Refresh cookie required")
    result, rotated = AuthService(db).refresh(token)
    set_refresh(response, rotated)
    return result


@router.post("/auth/logout", status_code=204)
def logout(db: DB, request: Request, response: Response):
    validate_origin(request)
    token = request.cookies.get(COOKIE)
    if token:
        AuthService(db).logout(token)
    response.delete_cookie(
        COOKIE, path=COOKIE_PATH, secure=settings.cookie_secure, httponly=True, samesite="strict"
    )


@router.get("/auth/me", response_model=UserOut)
def me(user: CurrentUser):
    return user


@router.get("/users", response_model=list[UserOut], tags=["Administration"])
def users(db: DB, _admin: Admin, offset: Offset = 0, limit: Limit = 50):
    return UserRepository(db).list(offset, limit)


@router.patch("/users/{user_id}", response_model=UserOut, tags=["Administration"])
def update_user(user_id: int, data: UserUpdate, db: DB, admin: Admin):
    return AuthService(db).update_user(admin, user_id, data)
