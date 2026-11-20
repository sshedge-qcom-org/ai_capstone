from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Category, Order, Supplier
from app.repositories.suppliers import SupplierRepository
from app.schemas import SupplierInput
from app.services.requests import RequestService


class SupplierService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SupplierRepository(db)

    def get(self, supplier_id: int) -> Supplier:
        supplier = self.repo.get(supplier_id)
        if not supplier:
            raise HTTPException(404, "Supplier not found")
        return supplier

    def save(self, data: SupplierInput, supplier_id: int | None = None):
        RequestService(self.db).category_exists(data.category)
        if supplier_id is None:
            supplier = Supplier(**data.model_dump())
            self.db.add(supplier)
        else:
            supplier = self.get(supplier_id)
            if supplier.category != data.category and self.db.scalar(
                select(Order.id).where(Order.supplier_id == supplier.id).limit(1)
            ):
                raise HTTPException(409, "Cannot change category of a supplier with orders")
            for key, value in data.model_dump().items():
                setattr(supplier, key, value)
        self.db.commit()
        return supplier

    def delete(self, supplier_id: int):
        supplier = self.get(supplier_id)
        self.db.delete(supplier)
        self.commit_reference_safe("Supplier is linked to orders or vendor accounts")

    def add_category(self, name: str):
        category = Category(name=name)
        self.db.add(category)
        self.commit_reference_safe("Category already exists")
        return {"name": name}

    def delete_category(self, name: str):
        category = self.db.get(Category, name)
        if not category:
            raise HTTPException(404, "Category not found")
        self.db.delete(category)
        self.commit_reference_safe("Category is used by suppliers or requests")

    def commit_reference_safe(self, message: str):
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(409, message) from exc
