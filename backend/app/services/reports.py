import csv
import io
from datetime import date
from typing import Literal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import User
from app.repositories.reports import ReportRepository

ReportName = Literal[
    "spending_by_category", "supplier_performance", "monthly_trends", "approval_turnaround"
]
HEADERS = {
    "spending_by_category": ["category", "amount", "orders"],
    "supplier_performance": [
        "supplier_id",
        "supplier",
        "rating",
        "reliability_score",
        "total_orders",
        "delivered_orders",
        "delivered_value",
        "average_actual_delivery_days",
    ],
    "monthly_trends": ["month", "requests", "amount", "delivered_orders"],
    "approval_turnaround": ["category", "decided_requests", "average_hours"],
}


class ReportService:
    def __init__(self, db: Session, user: User, since: date | None, until: date | None):
        if until == date.max:
            raise HTTPException(422, "End date is outside the supported reporting range")
        if since and until and since > until:
            raise HTTPException(422, "Start date must not follow end date")
        self.repo = ReportRepository(db, user, since, until)

    def report(self, name: ReportName):
        return getattr(self.repo, name)()

    def all(self):
        return {name: self.report(name) for name in HEADERS}

    def export(self, name: ReportName) -> str:
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=HEADERS[name])
        writer.writeheader()
        for row in self.report(name):
            writer.writerow({key: safe_cell(value) for key, value in row.items()})
        return "\ufeff" + output.getvalue()


def safe_cell(value):
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + value
    return value
