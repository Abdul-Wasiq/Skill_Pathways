from fastapi import APIRouter, Depends, HTTPException, status

from app.repositories import connection_repository, notification_repository
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/connections", tags=["connections"])


@router.post("/{target_user_id}", status_code=status.HTTP_201_CREATED)
def send_connection_request(target_user_id: str, current_user: dict = Depends(get_current_user)):
    if target_user_id == current_user["id"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot connect with yourself.")
    existing = connection_repository.get_connection_between(current_user["id"], target_user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A connection already exists between you (status: {existing['status']}).",
        )
    connection = connection_repository.send_request(current_user["id"], target_user_id)
    notification_repository.create_notification(
        user_id=target_user_id,
        notif_type="new_connection_request",
        title=f"{current_user['name']} wants to connect",
        link_url="/pages/connections.html",
    )
    return connection


@router.put("/{connection_id}/accept")
def accept_connection(connection_id: str, current_user: dict = Depends(get_current_user)):
    connection = connection_repository.get_connection_by_id(connection_id)
    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection request not found.")
    if connection["addressee_id"] != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This request isn't addressed to you.")
    updated = connection_repository.update_status(connection_id, "accepted")
    notification_repository.create_notification(
        user_id=connection["requester_id"],
        notif_type="connection_accepted",
        title=f"{current_user['name']} accepted your connection request",
        link_url="/pages/connections.html",
    )
    return updated


@router.put("/{connection_id}/reject")
def reject_connection(connection_id: str, current_user: dict = Depends(get_current_user)):
    connection = connection_repository.get_connection_by_id(connection_id)
    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection request not found.")
    if connection["addressee_id"] != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This request isn't addressed to you.")
    return connection_repository.update_status(connection_id, "rejected")


@router.delete("/{connection_id}")
def remove_connection(connection_id: str, current_user: dict = Depends(get_current_user)):
    connection = connection_repository.get_connection_by_id(connection_id)
    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found.")
    if current_user["id"] not in (connection["requester_id"], connection["addressee_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your connection to remove.")
    connection_repository.delete_connection(connection_id)
    return {"detail": "Connection removed."}


@router.get("")
def list_my_connections(current_user: dict = Depends(get_current_user)):
    return connection_repository.list_connections(current_user["id"])


@router.get("/pending")
def list_pending_requests(current_user: dict = Depends(get_current_user)):
    return connection_repository.list_pending_incoming(current_user["id"])
