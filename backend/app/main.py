import logging
import uuid
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.requests import router as requests_router
from app.config import settings
from app.database import get_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("procurement")
app = FastAPI(title=settings.app_name, version="1.0.0")
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(requests_router)
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
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    logger.info("%s %s %s", request.method, request.url.path, response.status_code)
    return response


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unavailable")
    logger.exception("Unhandled request %s", request_id, exc_info=exc)
    return JSONResponse(
        status_code=500, content={"detail": "Internal server error", "request_id": request_id}
    )


@app.get("/api/v1/health", tags=["Health"])
def health(db: Annotated[Session, Depends(get_db)]):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
