from typing import Annotated

from fastapi import APIRouter, Query

from app.dependencies import DB, Admin, Limit, Offset, Staff
from app.repositories.suppliers import SupplierRepository
from app.schemas import CategoryInput, SupplierInput, SupplierOut
from app.services.suppliers import SupplierService

router = APIRouter(prefix="/api/v1", tags=["Suppliers"])


@router.get("/suppliers", response_model=list[SupplierOut])
def suppliers(
    db: DB,
    _user: Staff,
    offset: Offset = 0,
    limit: Limit = 50,
    search: Annotated[str, Query(max_length=120)] = "",
    category: Annotated[str | None, Query(max_length=80)] = None,
):
    return SupplierRepository(db).list(offset, limit, search, category)


@router.get("/suppliers/{supplier_id}", response_model=SupplierOut)
def detail(supplier_id: int, db: DB, _user: Staff):
    return SupplierService(db).get(supplier_id)


@router.post("/suppliers", response_model=SupplierOut, status_code=201)
def create(data: SupplierInput, db: DB, _user: Admin):
    return SupplierService(db).save(data)


@router.patch("/suppliers/{supplier_id}", response_model=SupplierOut)
def edit(supplier_id: int, data: SupplierInput, db: DB, _user: Admin):
    return SupplierService(db).save(data, supplier_id)


@router.delete("/suppliers/{supplier_id}", status_code=204)
def delete(supplier_id: int, db: DB, _user: Admin):
    SupplierService(db).delete(supplier_id)


@router.post("/categories", status_code=201, tags=["Categories"])
def add_category(data: CategoryInput, db: DB, _user: Admin):
    return SupplierService(db).add_category(data.name)


@router.delete("/categories/{name:path}", status_code=204, tags=["Categories"])
def delete_category(name: str, db: DB, _user: Admin):
    SupplierService(db).delete_category(name)
