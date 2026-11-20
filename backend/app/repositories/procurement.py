from sqlalchemy import false, select
from sqlalchemy.orm import Session

from app.models import Order, PurchaseRequest, User


def request_scope(user: User):
    query = select(PurchaseRequest)
    if user.role == "employee":
        return query.where(PurchaseRequest.requested_by == user.id)
    if user.role == "manager":
        return query.join(User, User.id == PurchaseRequest.requested_by).where(
            User.manager_id == user.id
        )
    if user.role == "admin":
        return query
    return query.where(false())


def order_scope(user: User):
    query = select(Order)
    if user.role == "vendor":
        return (
            query.where(Order.supplier_id == user.supplier_id)
            if user.supplier_id
            else query.where(false())
        )
    return query.where(
        Order.request_id.in_(request_scope(user).with_only_columns(PurchaseRequest.id))
    )


class RequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_visible(self, user: User, request_id: int) -> PurchaseRequest | None:
        return self.db.scalar(request_scope(user).where(PurchaseRequest.id == request_id))

    def list(self, user: User, offset: int, limit: int, status: str | None, search: str):
        query = request_scope(user)
        if status:
            query = query.where(PurchaseRequest.status == status)
        if search:
            query = query.where(PurchaseRequest.title.icontains(search, autoescape=True))
        return self.db.scalars(
            query.order_by(PurchaseRequest.created_at.desc(), PurchaseRequest.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()
