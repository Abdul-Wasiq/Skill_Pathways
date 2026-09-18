from fastapi import APIRouter, Depends, HTTPException, status

from app.repositories import post_repository, notification_repository
from app.schemas.post import (
    PostCreateRequest, PostUpdateRequest, CommentCreateRequest, ReportCreateRequest,
)
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreateRequest, current_user: dict = Depends(get_current_user)):
    return post_repository.create_post(
        author_id=current_user["id"],
        content=payload.content,
        post_type=payload.post_type,
        organization_id=payload.organization_id,
        linked_opportunity_id=payload.linked_opportunity_id,
    )


@router.get("")
def list_posts(limit: int = 30, offset: int = 0, author_id: str | None = None):
    return post_repository.list_posts(limit=limit, offset=offset, author_id=author_id)


@router.get("/{post_id}")
def get_post(post_id: str):
    post = post_repository.get_post_by_id(post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    post["comments"] = post_repository.list_comments(post_id)
    return post


def _assert_author_or_admin(post_id: str, user: dict) -> None:
    if user["role"] == "admin":
        return
    if not post_repository.is_post_author(post_id, user["id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only modify your own posts.")


@router.put("/{post_id}")
def update_post(post_id: str, payload: PostUpdateRequest, current_user: dict = Depends(get_current_user)):
    if post_repository.get_post_by_id(post_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    _assert_author_or_admin(post_id, current_user)
    return post_repository.update_post(post_id, payload.content)


@router.delete("/{post_id}")
def delete_post(post_id: str, current_user: dict = Depends(get_current_user)):
    if post_repository.get_post_by_id(post_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    _assert_author_or_admin(post_id, current_user)
    post_repository.delete_post(post_id)
    return {"detail": "Post deleted."}


@router.post("/{post_id}/like", status_code=status.HTTP_201_CREATED)
def like_post(post_id: str, current_user: dict = Depends(get_current_user)):
    post = post_repository.get_post_by_id(post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    created = post_repository.like_post(post_id, current_user["id"])
    if created and post["author_id"] != current_user["id"]:
        notification_repository.create_notification(
            user_id=post["author_id"],
            notif_type="post_liked",
            title=f"{current_user['name']} liked your post",
            link_url=f"/pages/post-detail.html?id={post_id}",
        )
    return {"detail": "Post liked."}


@router.delete("/{post_id}/like")
def unlike_post(post_id: str, current_user: dict = Depends(get_current_user)):
    post_repository.unlike_post(post_id, current_user["id"])
    return {"detail": "Like removed."}


@router.post("/{post_id}/comments", status_code=status.HTTP_201_CREATED)
def add_comment(post_id: str, payload: CommentCreateRequest, current_user: dict = Depends(get_current_user)):
    post = post_repository.get_post_by_id(post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    comment = post_repository.add_comment(post_id, current_user["id"], payload.content)
    if post["author_id"] != current_user["id"]:
        notification_repository.create_notification(
            user_id=post["author_id"],
            notif_type="post_commented",
            title=f"{current_user['name']} commented on your post",
            body=payload.content[:200],
            link_url=f"/pages/post-detail.html?id={post_id}",
        )
    return comment


@router.get("/{post_id}/comments")
def list_comments(post_id: str):
    return post_repository.list_comments(post_id)


@router.post("/{post_id}/share", status_code=status.HTTP_201_CREATED)
def share_post(post_id: str, current_user: dict = Depends(get_current_user)):
    if post_repository.get_post_by_id(post_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    post_repository.share_post(post_id, current_user["id"])
    return {"detail": "Post shared."}


@router.post("/{post_id}/save", status_code=status.HTTP_201_CREATED)
def save_post(post_id: str, current_user: dict = Depends(get_current_user)):
    if post_repository.get_post_by_id(post_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    post_repository.save_post(post_id, current_user["id"])
    return {"detail": "Post saved."}


@router.delete("/{post_id}/save")
def unsave_post(post_id: str, current_user: dict = Depends(get_current_user)):
    post_repository.unsave_post(post_id, current_user["id"])
    return {"detail": "Post unsaved."}


@router.get("/saved/me")
def list_my_saved_posts(current_user: dict = Depends(get_current_user)):
    return post_repository.list_saved_posts(current_user["id"])


@router.post("/reports", status_code=status.HTTP_201_CREATED)
def create_report(payload: ReportCreateRequest, current_user: dict = Depends(get_current_user)):
    return post_repository.create_report(
        current_user["id"], payload.target_type, payload.target_id, payload.reason
    )
