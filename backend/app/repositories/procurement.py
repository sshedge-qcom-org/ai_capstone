from sqlalchemy import false, select

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
