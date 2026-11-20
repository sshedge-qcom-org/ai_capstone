from sqlalchemy.orm import Session

from app.models import Order, User
from app.repositories.procurement import order_scope


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_visible(self, user: User, order_id: int):
        return self.db.scalar(order_scope(user).where(Order.id == order_id))

    def list(self, user: User, offset: int, limit: int, status: str | None):
        query = order_scope(user)
        if status:
            query = query.where(Order.status == status)
        return self.db.scalars(
            query.order_by(Order.order_date.desc(), Order.id.desc()).offset(offset).limit(limit)
        ).all()
