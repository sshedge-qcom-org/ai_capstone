from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Supplier, User
from app.schemas import SupplierOut
from app.services.requests import RequestService

CENT = Decimal(".01")


def score_supplier(supplier: Supplier) -> dict:
    contributions = {
        "price": Decimal("40") * supplier.average_price_score / 100,
        "rating": Decimal("25") * supplier.rating / 5,
        "delivery": Decimal("20") / (1 + Decimal(supplier.average_delivery_days) / 7),
        "reliability": Decimal("15") * supplier.reliability_score / 100,
    }
    score = sum(contributions.values(), Decimal(0))
    return {
        "supplier": SupplierOut.model_validate(supplier),
        "score": score.quantize(CENT),
        "contributions": {key: value.quantize(CENT) for key, value in contributions.items()},
        "explanation": (
            f"Price value {supplier.average_price_score}/100, rating {supplier.rating}/5, "
            f"delivery {supplier.average_delivery_days} days, reliability "
            f"{supplier.reliability_score}%. Weights: 40% price, 25% rating, "
            "20% delivery, 15% reliability. Higher price value means better affordability."
        ),
    }


def recommendations(db: Session, user: User, request_id: int) -> list[dict]:
    request = RequestService(db).visible(user, request_id)
    if request.status != "approved":
        raise HTTPException(400, "Recommendations require an approved request")
    score = (
        Decimal(".40") * Supplier.average_price_score / 100
        + Decimal(".25") * Supplier.rating / 5
        + Decimal(".20") / (1 + Supplier.average_delivery_days / Decimal(7))
        + Decimal(".15") * Supplier.reliability_score / 100
    )
    suppliers = db.scalars(
        select(Supplier)
        .where(Supplier.category == request.category)
        .order_by(score.desc(), Supplier.id)
        .limit(3)
    ).all()
    return [score_supplier(supplier) for supplier in suppliers]
