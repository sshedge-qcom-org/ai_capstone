from fastapi import APIRouter

from app.dependencies import DB, Reviewer
from app.schemas import RecommendationOut
from app.services.recommendations import recommendations

router = APIRouter(prefix="/api/v1", tags=["Recommendations"])


@router.get("/requests/{request_id}/recommendations", response_model=list[RecommendationOut])
def recommend(request_id: int, db: DB, user: Reviewer):
    return recommendations(db, user, request_id)
