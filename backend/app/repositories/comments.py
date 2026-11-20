from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from app.models import Comment, User


class CommentRepository:
    def __init__(self, db: Session):
        self.db = db

    def query(self):
        child = aliased(Comment)
        count = (
            select(func.count(child.id))
            .where(child.parent_comment_id == Comment.id)
            .correlate(Comment)
            .scalar_subquery()
        )
        return select(Comment, User.full_name, count).join(User, User.id == Comment.user_id)

    @staticmethod
    def serialize(row):
        comment, author, reply_count = row
        return {
            **{column.name: getattr(comment, column.name) for column in comment.__table__.columns},
            "author_name": author,
            "reply_count": reply_count,
        }

    def detail(self, comment_id: int):
        row = self.db.execute(self.query().where(Comment.id == comment_id)).one()
        return self.serialize(row)

    def list(self, request_id: int, parent_id: int | None, offset: int, limit: int):
        rows = self.db.execute(
            self.query()
            .where(
                Comment.request_id == request_id,
                Comment.parent_comment_id == parent_id,
            )
            .order_by(Comment.created_at, Comment.id)
            .offset(offset)
            .limit(limit)
        ).all()
        return [self.serialize(row) for row in rows]
