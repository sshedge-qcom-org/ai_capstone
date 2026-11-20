from typing import Annotated, Literal

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.dependencies import DB, Employee, Limit, Offset, Reviewer, Staff
from app.models import Category
from app.repositories.procurement import RequestRepository
from app.schemas import Decision, RequestDetail, RequestInput, RequestOut
from app.services.requests import RequestService

router = APIRouter(prefix="/api/v1", tags=["Purchase Requests"])


@router.get("/categories", response_model=list[str], tags=["Categories"])
def categories(db: DB, _user: Staff):
    return db.scalars(select(Category.name).order_by(Category.name)).all()


@router.get("/requests", response_model=list[RequestOut])
def requests(
    db: DB,
    user: Staff,
    offset: Offset = 0,
    limit: Limit = 50,
    status: Literal["pending", "approved", "rejected", "revision", "ordered"] | None = None,
    search: Annotated[str, Query(max_length=120)] = "",
):
    return RequestRepository(db).list(user, offset, limit, status, search)


@router.post("/requests", response_model=RequestOut, status_code=201)
def create(data: RequestInput, db: DB, user: Employee):
    return RequestService(db).create(user, data)


@router.get("/requests/{request_id}", response_model=RequestDetail)
def detail(request_id: int, db: DB, user: Staff):
    return RequestService(db).detail(user, request_id)


@router.patch("/requests/{request_id}", response_model=RequestOut)
def edit(request_id: int, data: RequestInput, db: DB, user: Employee):
    return RequestService(db).edit(user, request_id, data)


@router.post("/requests/{request_id}/decision", response_model=RequestOut)
def decide(request_id: int, data: Decision, db: DB, user: Reviewer):
    return RequestService(db).decide(user, request_id, data)
