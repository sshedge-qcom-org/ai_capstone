from datetime import date

from fastapi import APIRouter
from fastapi.responses import Response

from app.dependencies import DB, Reviewer
from app.schemas import ReportsOut
from app.services.reports import ReportName, ReportService

router = APIRouter(prefix="/api/v1", tags=["Reports"])


@router.get("/reports", response_model=ReportsOut)
def reports(db: DB, user: Reviewer, since: date | None = None, until: date | None = None):
    return ReportService(db, user, since, until).all()


@router.get(
    "/reports/export", response_class=Response, responses={200: {"content": {"text/csv": {}}}}
)
def export(
    report: ReportName,
    db: DB,
    user: Reviewer,
    since: date | None = None,
    until: date | None = None,
):
    content = ReportService(db, user, since, until).export(report)
    return Response(
        content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{report}.csv"'},
    )
