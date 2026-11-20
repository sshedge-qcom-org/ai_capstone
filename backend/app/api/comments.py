from typing import Annotated

from fastapi import APIRouter, Query

from app.dependencies import DB, Limit, Offset, Staff
from app.schemas import CommentEdit, CommentInput, CommentOut
from app.services.comments import CommentService

router = APIRouter(prefix="/api/v1", tags=["Discussions"])


@router.get("/requests/{request_id}/comments", response_model=list[CommentOut])
def comments(
    request_id: int,
    db: DB,
    user: Staff,
    parent_id: Annotated[int | None, Query(gt=0)] = None,
    offset: Offset = 0,
    limit: Limit = 20,
):
    return CommentService(db).list(user, request_id, parent_id, offset, limit)


@router.post("/requests/{request_id}/comments", response_model=CommentOut, status_code=201)
def create(request_id: int, data: CommentInput, db: DB, user: Staff):
    return CommentService(db).create(user, request_id, data)


@router.patch("/comments/{comment_id}", response_model=CommentOut)
def edit(comment_id: int, data: CommentEdit, db: DB, user: Staff):
    return CommentService(db).edit(user, comment_id, data.content)


@router.delete("/comments/{comment_id}", status_code=204)
def delete(comment_id: int, db: DB, user: Staff):
    CommentService(db).delete(user, comment_id)
