from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Supplier


class SupplierRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, supplier_id: int) -> Supplier | None:
        return self.db.get(Supplier, supplier_id)

    def list(self, offset: int, limit: int, search: str, category: str | None):
        query = select(Supplier)
        if search:
            query = query.where(Supplier.company_name.icontains(search, autoescape=True))
        if category:
            query = query.where(Supplier.category == category)
        return self.db.scalars(
            query.order_by(Supplier.company_name, Supplier.id).offset(offset).limit(limit)
        ).all()
