from fastapi import APIRouter, Depends

from app.services import feed_service
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/feed", tags=["feed"])


@router.get("")
def get_feed(limit: int = 20, current_user: dict = Depends(get_current_user)):
    return feed_service.get_personalized_feed(current_user["id"], limit=limit)
