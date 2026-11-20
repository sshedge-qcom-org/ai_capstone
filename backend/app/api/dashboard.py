from fastapi import APIRouter

from app.dependencies import DB, CurrentUser
from app.services.dashboard import dashboard

router = APIRouter(prefix="/api/v1", tags=["Dashboard"])


@router.get("/dashboard")
def overview(db: DB, user: CurrentUser):
    return dashboard(db, user)
