from typing import Annotated, Literal

from fastapi import APIRouter, Depends

from app.dependencies import DB, CurrentUser, Limit, Offset, Reviewer, require_roles
from app.models import User
from app.repositories.orders import OrderRepository
from app.schemas import OrderDetail, OrderInput, OrderOut, OrderStatus
from app.services.orders import OrderService

router = APIRouter(prefix="/api/v1", tags=["Orders"])
Fulfiller = Annotated[User, Depends(require_roles("vendor", "admin"))]


@router.get("/orders", response_model=list[OrderOut])
def orders(
    db: DB,
    user: CurrentUser,
    offset: Offset = 0,
    limit: Limit = 50,
    status: Literal["created", "processing", "shipped", "delivered"] | None = None,
):
    return OrderRepository(db).list(user, offset, limit, status)


@router.post("/orders", response_model=OrderOut, status_code=201)
def create(data: OrderInput, db: DB, user: Reviewer):
    return OrderService(db).create(user, data)


@router.get("/orders/{order_id}", response_model=OrderDetail)
def detail(order_id: int, db: DB, user: CurrentUser):
    return OrderService(db).detail(user, order_id)


@router.patch("/orders/{order_id}/status", response_model=OrderOut)
def advance(order_id: int, data: OrderStatus, db: DB, user: Fulfiller):
    return OrderService(db).advance(user, order_id, data.status)
