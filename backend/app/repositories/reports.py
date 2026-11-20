from datetime import date, datetime, time, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import ApprovalEvent, Supplier, User
from app.repositories.procurement import order_scope, request_scope


class ReportRepository:
    def __init__(self, db: Session, user: User, since: date | None, until: date | None):
        self.db = db
        self.requests = request_scope(user).subquery()
        self.orders = order_scope(user).subquery()
        self.since = since
        self.until = until

    def period(self, query, column):
        if self.since:
            query = query.where(column >= datetime.combine(self.since, time.min))
        if self.until:
            query = query.where(column < datetime.combine(self.until + timedelta(days=1), time.min))
        return query

    def rows(self, query):
        return [dict(row) for row in self.db.execute(query).mappings().all()]

    def spending_by_category(self):
        r, o = self.requests.c, self.orders.c
        query = (
            select(
                r.category,
                func.sum(o.amount).label("amount"),
                func.count(o.id).label("orders"),
            )
            .select_from(self.orders)
            .join(self.requests, r.id == o.request_id)
            .where(o.status == "delivered")
        )
        return self.rows(
            self.period(query, o.delivery_date)
            .group_by(r.category)
            .order_by(func.sum(o.amount).desc())
        )

    def supplier_performance(self):
        o = self.orders.c
        delivered = o.status == "delivered"
        query = select(
            Supplier.id.label("supplier_id"),
            Supplier.company_name.label("supplier"),
            Supplier.rating,
            Supplier.reliability_score,
            func.count(o.id).label("total_orders"),
            func.sum(case((delivered, 1), else_=0)).label("delivered_orders"),
            func.sum(case((delivered, o.amount), else_=0)).label("delivered_value"),
            func.avg(
                case(
                    (delivered, func.julianday(o.delivery_date) - func.julianday(o.order_date)),
                    else_=None,
                )
            ).label("average_actual_delivery_days"),
        ).join(self.orders, o.supplier_id == Supplier.id)
        return self.rows(
            self.period(query, o.order_date)
            .group_by(Supplier.id)
            .order_by(func.count(o.id).desc(), Supplier.id)
        )

    def monthly_trends(self):
        r, o = self.requests.c, self.orders.c
        requests = self.rows(
            self.period(
                select(
                    func.strftime("%Y-%m", r.created_at).label("month"),
                    func.count().label("requests"),
                ).select_from(self.requests),
                r.created_at,
            ).group_by("month")
        )
        delivered = self.rows(
            self.period(
                select(
                    func.strftime("%Y-%m", o.delivery_date).label("month"),
                    func.sum(o.amount).label("amount"),
                    func.count().label("delivered_orders"),
                )
                .select_from(self.orders)
                .where(o.status == "delivered"),
                o.delivery_date,
            ).group_by("month")
        )
        months = {
            row["month"]: {
                "month": row["month"],
                "requests": row["requests"],
                "amount": 0,
                "delivered_orders": 0,
            }
            for row in requests
        }
        for row in delivered:
            months.setdefault(row["month"], {"month": row["month"], "requests": 0})
            months[row["month"]].update(row)
        return [months[month] for month in sorted(months)]

    def approval_turnaround(self):
        r = self.requests.c
        final = (
            select(
                ApprovalEvent.request_id,
                func.min(ApprovalEvent.created_at).label("decided_at"),
            )
            .where(ApprovalEvent.decision.in_(("approved", "rejected")))
            .group_by(ApprovalEvent.request_id)
            .subquery()
        )
        query = (
            select(
                r.category,
                func.count().label("decided_requests"),
                func.avg(
                    (func.julianday(final.c.decided_at) - func.julianday(r.created_at)) * 24
                ).label("average_hours"),
            )
            .select_from(self.requests)
            .join(final, final.c.request_id == r.id)
        )
        return self.rows(
            self.period(query, final.c.decided_at).group_by(r.category).order_by(r.category)
        )
