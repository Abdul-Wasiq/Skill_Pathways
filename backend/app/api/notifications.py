from fastapi import APIRouter, Depends, HTTPException, status

from app.repositories import notification_repository
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
def list_notifications(unread_only: bool = False, current_user: dict = Depends(get_current_user)):
    return notification_repository.list_notifications(current_user["id"], unread_only=unread_only)


@router.get("/unread-count")
def get_unread_count(current_user: dict = Depends(get_current_user)):
    return {"count": notification_repository.unread_count(current_user["id"])}


@router.put("/{notification_id}/read")
def mark_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    updated = notification_repository.mark_read(notification_id, current_user["id"])
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return updated


@router.put("/read-all")
def mark_all_read(current_user: dict = Depends(get_current_user)):
    count = notification_repository.mark_all_read(current_user["id"])
    return {"marked_read": count}
