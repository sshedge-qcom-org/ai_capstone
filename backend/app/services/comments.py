from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Comment, User
from app.repositories.comments import CommentRepository
from app.schemas import CommentInput
from app.services.requests import RequestService

MAX_REPLY_DEPTH = 8


class CommentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CommentRepository(db)

    def visible(self, user: User, comment_id: int) -> Comment:
        comment = self.db.get(Comment, comment_id)
        if not comment:
            raise HTTPException(404, "Comment not found")
        RequestService(self.db).visible(user, comment.request_id)
        return comment

    def list(self, user: User, request_id: int, parent_id: int | None, offset: int, limit: int):
        RequestService(self.db).visible(user, request_id)
        if parent_id is not None:
            parent = self.visible(user, parent_id)
            if parent.request_id != request_id:
                raise HTTPException(422, "Parent comment belongs to another request")
        return self.repo.list(request_id, parent_id, offset, limit)

    def create(self, user: User, request_id: int, data: CommentInput):
        RequestService(self.db).visible(user, request_id)
        if data.parent_comment_id is not None:
            parent = self.visible(user, data.parent_comment_id)
            if parent.request_id != request_id:
                raise HTTPException(422, "Reply must belong to the same request")
            depth = 1
            while parent.parent_comment_id is not None:
                depth += 1
                parent = self.db.get(Comment, parent.parent_comment_id)
            if depth > MAX_REPLY_DEPTH:
                raise HTTPException(422, f"Replies are limited to {MAX_REPLY_DEPTH} levels")
        comment = Comment(request_id=request_id, user_id=user.id, **data.model_dump())
        self.db.add(comment)
        self.db.commit()
        return self.repo.detail(comment.id)

    def edit(self, user: User, comment_id: int, content: str):
        comment = self.visible(user, comment_id)
        if comment.user_id != user.id:
            raise HTTPException(403, "Only the author may edit a comment")
        if comment.is_deleted:
            raise HTTPException(400, "Deleted comments cannot be edited")
        result = self.db.execute(
            update(Comment)
            .where(
                Comment.id == comment_id,
                Comment.is_deleted.is_(False),
                Comment.updated_at == comment.updated_at,
            )
            .values(content=content)
        )
        if result.rowcount != 1:
            self.db.rollback()
            raise HTTPException(409, "Comment changed; refresh and try again")
        self.db.commit()
        return self.repo.detail(comment.id)

    def delete(self, user: User, comment_id: int):
        comment = self.visible(user, comment_id)
        if user.id != comment.user_id and user.role != "admin":
            raise HTTPException(403, "Only the author or an admin may delete a comment")
        comment.content = "[deleted]"
        comment.is_deleted = True
        self.db.commit()
