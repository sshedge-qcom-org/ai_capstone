import logging
import uuid
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.api.auth import router as auth_router
from app.api.comments import router as comments_router
from app.api.dashboard import router as dashboard_router
from app.api.orders import router as orders_router
from app.api.recommendations import router as recommendations_router
from app.api.reports import router as reports_router
from app.api.requests import router as requests_router
from app.api.suppliers import router as suppliers_router
from app.config import settings
from app.database import get_db
from app.rate_limit import login_limiter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("procurement")
app = FastAPI(title=settings.app_name, version="1.0.0")
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(requests_router)
app.include_router(suppliers_router)
app.include_router(recommendations_router)
app.include_router(orders_router)
app.include_router(comments_router)
app.include_router(reports_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    if (
        request.method == "POST"
        and request.url.path
        in ("/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/refresh")
        and not login_limiter.allow(
            request.client.host if request.client else "unknown", settings.auth_rate_limit
        )
    ):
        response = JSONResponse(
            status_code=429,
            content={"detail": "Too many authentication attempts; retry in one minute"},
            headers={"Retry-After": "60"},
        )
    else:
        response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Frame-Options"] = "DENY"
    logger.info("%s %s %s", request.method, request.url.path, response.status_code)
    return response


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unavailable")
    logger.exception("Unhandled request %s", request_id, exc_info=exc)
    return JSONResponse(
        status_code=500, content={"detail": "Internal server error", "request_id": request_id}
    )


@app.exception_handler(RequestValidationError)
async def invalid_input(_request: Request, exc: RequestValidationError):
    errors = [
        {key: value for key, value in error.items() if key in ("loc", "msg", "type")}
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})


@app.exception_handler(IntegrityError)
async def constraint_conflict(request: Request, _exc: IntegrityError):
    logger.warning("Database conflict in request %s", request.state.request_id)
    return JSONResponse(status_code=409, content={"detail": "Data changed or is still referenced"})


@app.exception_handler(OperationalError)
async def database_unavailable(request: Request, _exc: OperationalError):
    logger.error("Database unavailable in request %s", request.state.request_id)
    return JSONResponse(
        status_code=503,
        content={"detail": "Database temporarily unavailable"},
        headers={"Retry-After": "5"},
    )


@app.get("/api/v1/health", tags=["Health"])
def health(db: Annotated[Session, Depends(get_db)]):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
