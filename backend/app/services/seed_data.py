from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    ApprovalEvent,
    Category,
    Order,
    OrderEvent,
    PurchaseRequest,
    Supplier,
    User,
    utcnow,
)

CATEGORIES = ("IT Equipment", "Office Supplies", "Furniture", "Services", "Facilities")
COMPANIES = (
    "Northstar",
    "Evergreen",
    "Summit",
    "Meridian",
    "Atlas",
    "Horizon",
)


def seed_procurement(db: Session, employee: User, manager: User):
    for category in CATEGORIES:
        if not db.get(Category, category):
            db.add(Category(name=category))
    db.flush()
    if not db.scalar(select(Supplier.id).limit(1)):
        for i, category in enumerate(CATEGORIES):
            for j, company in enumerate(COMPANIES):
                db.add(
                    Supplier(
                        company_name=f"{company} {category}",
                        category=category,
                        rating=Decimal("3.7") + Decimal(j) / 5,
                        average_price_score=65 + ((i * 7 + j * 9) % 35),
                        average_delivery_days=2 + ((i + j * 3) % 16),
                        reliability_score=80 + ((i + j * 4) % 20),
                        contact_person=f"{company} Account Team",
                        email=f"sales{i}{j}@example.com",
                    )
                )
        db.flush()
    vendor = db.scalar(select(User).where(User.email == "vendor@company.com"))
    vendor.supplier_id = db.scalar(select(Supplier.id).order_by(Supplier.id).limit(1))
    if db.scalar(select(PurchaseRequest.id).limit(1)):
        return
    items = (
        "Laptop refresh",
        "Stationery restock",
        "Ergonomic chairs",
        "Security assessment",
        "Building maintenance",
    )
    for i in range(30):
        created = utcnow() - timedelta(days=(29 - i) * 6)
        category = CATEGORIES[i % 5]
        status = "ordered" if i < 20 else ("pending", "approved", "revision", "rejected")[i % 4]
        request = PurchaseRequest(
            title=f"{items[i % 5]} - batch {i + 1}",
            description="Scheduled departmental procurement to support operational capacity.",
            category=category,
            estimated_budget=Decimal(300 + i * 175),
            quantity=1 + i % 8,
            target_delivery_date=date.today() + timedelta(days=14),
            status=status,
            requested_by=employee.id,
            created_at=created,
            updated_at=created,
        )
        db.add(request)
        db.flush()
        if status == "ordered":
            supplier_id = db.scalar(
                select(Supplier.id)
                .where(Supplier.category == category)
                .order_by(Supplier.id)
                .offset(i % 6)
                .limit(1)
            )
            delivered = i < 17
            db.add(
                Order(
                    request_id=request.id,
                    supplier_id=supplier_id,
                    approved_by=manager.id,
                    status="delivered" if delivered else "processing",
                    amount=request.estimated_budget,
                    order_date=created + timedelta(days=2),
                    delivery_date=created + timedelta(days=9) if delivered else None,
                    updated_at=created + timedelta(days=9 if delivered else 3),
                )
            )


def seed_history(db: Session, manager: User):
    for request in db.scalars(select(PurchaseRequest)).all():
        if db.scalar(select(ApprovalEvent.id).where(ApprovalEvent.request_id == request.id)):
            continue
        if request.status in ("approved", "ordered", "rejected", "revision"):
            db.add(
                ApprovalEvent(
                    request_id=request.id,
                    actor_id=manager.id,
                    decision="approved" if request.status == "ordered" else request.status,
                    reason="Reviewed during the scheduled procurement cycle.",
                    created_at=request.created_at + timedelta(hours=24 + request.id % 24),
                )
            )
    for order in db.scalars(select(Order)).all():
        if db.scalar(select(OrderEvent.id).where(OrderEvent.order_id == order.id)):
            continue
        steps = ("created", "processing", "shipped", "delivered")
        for i, status in enumerate(steps[: steps.index(order.status) + 1]):
            db.add(
                OrderEvent(
                    order_id=order.id,
                    actor_id=manager.id,
                    status=status,
                    created_at=(
                        order.delivery_date
                        if status == "delivered"
                        else order.order_date + timedelta(hours=12 * i)
                    ),
                )
            )
