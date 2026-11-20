from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Order, OrderEvent, PurchaseRequest, Supplier, User, utcnow
from app.repositories.orders import OrderRepository
from app.schemas import OrderDetail, OrderInput
from app.services.requests import RequestService
from app.services.suppliers import SupplierService

TRANSITIONS = {"created": "processing", "processing": "shipped", "shipped": "delivered"}


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = OrderRepository(db)

    def visible(self, user: User, order_id: int):
        order = self.repo.get_visible(user, order_id)
        if not order:
            raise HTTPException(404, "Order not found")
        return order

    def detail(self, user: User, order_id: int):
        order = self.visible(user, order_id)
        history = self.db.scalars(
            select(OrderEvent)
            .where(OrderEvent.order_id == order_id)
            .order_by(OrderEvent.created_at, OrderEvent.id)
        ).all()
        return OrderDetail(
            **{column.name: getattr(order, column.name) for column in order.__table__.columns},
            request_title=self.db.get(PurchaseRequest, order.request_id).title,
            supplier_name=self.db.get(Supplier, order.supplier_id).company_name,
            history=history,
        )

    def create(self, user: User, data: OrderInput):
        request = RequestService(self.db).visible(user, data.request_id)
        if request.requested_by == user.id:
            raise HTTPException(403, "You cannot order your own request")
        if request.status != "approved":
            raise HTTPException(400, "Order creation requires an approved, unordered request")
        supplier = SupplierService(self.db).get(data.supplier_id)
        if supplier.category != request.category:
            raise HTTPException(422, "Supplier must match the request category")
        result = self.db.execute(
            update(PurchaseRequest)
            .where(
                PurchaseRequest.id == request.id,
                PurchaseRequest.status == "approved",
                PurchaseRequest.updated_at == request.updated_at,
            )
            .values(status="ordered", updated_at=utcnow())
        )
        if result.rowcount != 1:
            self.db.rollback()
            raise HTTPException(409, "Request changed; refresh and try again")
        order = Order(
            request_id=request.id,
            supplier_id=supplier.id,
            approved_by=user.id,
            status="created",
            amount=request.estimated_budget,
        )
        self.db.add(order)
        try:
            self.db.flush()
            self.db.add(OrderEvent(order_id=order.id, actor_id=user.id, status="created"))
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(409, "An order already exists for this request") from exc
        return order

    def advance(self, user: User, order_id: int, status: str):
        order = self.visible(user, order_id)
        if TRANSITIONS.get(order.status) != status:
            raise HTTPException(400, "Advance exactly one fulfilment step; delivery is final")
        now = utcnow()
        values = {"status": status, "updated_at": now}
        if status == "delivered":
            values["delivery_date"] = now
        result = self.db.execute(
            update(Order)
            .where(
                Order.id == order.id,
                Order.status == order.status,
            )
            .values(**values)
        )
        if result.rowcount != 1:
            self.db.rollback()
            raise HTTPException(409, "Order changed; refresh and try again")
        self.db.add(OrderEvent(order_id=order.id, actor_id=user.id, status=status))
        self.db.commit()
        self.db.refresh(order)
        return order
