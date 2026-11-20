from fastapi import APIRouter

from app.dependencies import DB, CurrentUser
from app.schemas import DashboardOut
from app.services.dashboard import dashboard

router = APIRouter(prefix="/api/v1", tags=["Dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
def overview(db: DB, user: CurrentUser):
    return dashboard(db, user)
