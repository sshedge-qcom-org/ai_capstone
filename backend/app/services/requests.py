from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import ApprovalEvent, Category, PurchaseRequest, User, utcnow
from app.repositories.procurement import RequestRepository
from app.schemas import Decision, RequestDetail, RequestInput


class RequestService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RequestRepository(db)

    def visible(self, user: User, request_id: int) -> PurchaseRequest:
        request = self.repo.get_visible(user, request_id)
        if not request:
            raise HTTPException(404, "Request not found")
        return request

    def detail(self, user: User, request_id: int):
        request = self.visible(user, request_id)
        history = self.db.scalars(
            select(ApprovalEvent)
            .where(ApprovalEvent.request_id == request_id)
            .order_by(ApprovalEvent.created_at, ApprovalEvent.id)
        ).all()
        return RequestDetail(
            **{
                **{
                    column.name: getattr(request, column.name)
                    for column in request.__table__.columns
                },
                "history": history,
            }
        )

    def category_exists(self, name: str):
        if not self.db.get(Category, name):
            raise HTTPException(422, "Choose an existing procurement category")

    def create(self, user: User, data: RequestInput):
        self.category_exists(data.category)
        request = PurchaseRequest(**data.model_dump(), requested_by=user.id, status="pending")
        self.db.add(request)
        self.db.commit()
        return request

    def edit(self, user: User, request_id: int, data: RequestInput):
        request = self.visible(user, request_id)
        if request.requested_by != user.id:
            raise HTTPException(403, "Only the requester may edit this request")
        if request.status not in ("pending", "revision"):
            raise HTTPException(400, "Only pending or revision requests can be edited")
        self.category_exists(data.category)
        result = self.db.execute(
            update(PurchaseRequest)
            .where(
                PurchaseRequest.id == request_id,
                PurchaseRequest.status == request.status,
                PurchaseRequest.updated_at == request.updated_at,
            )
            .values(**data.model_dump(), status="pending", updated_at=utcnow())
        )
        if result.rowcount != 1:
            self.db.rollback()
            raise HTTPException(409, "Request changed; refresh and try again")
        self.db.commit()
        self.db.refresh(request)
        return request

    def decide(self, user: User, request_id: int, data: Decision):
        request = self.visible(user, request_id)
        if request.requested_by == user.id:
            raise HTTPException(403, "You cannot review your own request")
        if request.status != "pending":
            raise HTTPException(400, "Only pending requests can be reviewed")
        if data.decision in ("rejected", "revision") and not data.reason:
            raise HTTPException(422, "A reason is required for rejection or revision")
        result = self.db.execute(
            update(PurchaseRequest)
            .where(
                PurchaseRequest.id == request_id,
                PurchaseRequest.status == "pending",
                PurchaseRequest.updated_at == request.updated_at,
            )
            .values(status=data.decision, updated_at=utcnow())
        )
        if result.rowcount != 1:
            self.db.rollback()
            raise HTTPException(409, "Request changed; refresh and try again")
        self.db.add(
            ApprovalEvent(
                request_id=request_id, actor_id=user.id, decision=data.decision, reason=data.reason
            )
        )
        self.db.commit()
        self.db.refresh(request)
        return request
