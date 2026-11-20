from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Supplier, User
from app.repositories.procurement import order_scope, request_scope


def dashboard(db: Session, user: User) -> dict:
    requests = request_scope(user).subquery()
    orders = order_scope(user).subquery()
    delivered = select(orders).where(orders.c.status == "delivered").subquery()
    monthly = (
        db.execute(
            select(
                func.strftime("%Y-%m", delivered.c.delivery_date).label("month"),
                func.sum(delivered.c.amount).label("amount"),
            )
            .group_by("month")
            .order_by("month")
        )
        .mappings()
        .all()
    )
    statuses = (
        db.execute(
            select(requests.c.status, func.count().label("count")).group_by(requests.c.status)
        )
        .mappings()
        .all()
    )
    top = (
        db.execute(
            select(
                Supplier.company_name.label("supplier"),
                func.sum(delivered.c.amount).label("amount"),
            )
            .join(delivered, delivered.c.supplier_id == Supplier.id)
            .group_by(Supplier.id)
            .order_by(func.sum(delivered.c.amount).desc())
            .limit(5)
        )
        .mappings()
        .all()
    )
    return {
        "total_requests": db.scalar(select(func.count()).select_from(requests)),
        "total_suppliers": db.scalar(select(func.count(Supplier.id)))
        if user.role != "vendor"
        else 0,
        "approved_orders": db.scalar(select(func.count()).select_from(orders)),
        "pending_approvals": db.scalar(
            select(func.count()).select_from(requests).where(requests.c.status == "pending")
        ),
        "procurement_spend": db.scalar(select(func.coalesce(func.sum(delivered.c.amount), 0))),
        "monthly_spending": [dict(row) for row in monthly],
        "approval_status": [dict(row) for row in statuses],
        "top_suppliers": [dict(row) for row in top],
    }
