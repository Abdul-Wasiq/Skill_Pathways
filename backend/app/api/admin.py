from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator

from app.repositories import admin_repository, post_repository, opportunity_repository
from app.utils.deps import require_roles

router = APIRouter(prefix="/api/admin", tags=["admin"])

_admin_only = Depends(require_roles("admin"))


class ReportStatusUpdateRequest(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"pending", "reviewed", "dismissed", "actioned"}
        if v not in allowed:
            raise ValueError(f"status must be one of {sorted(allowed)}")
        return v


@router.get("/stats")
def get_stats(current_user: dict = _admin_only):
    return admin_repository.get_platform_stats()


@router.get("/users")
def list_users(role: str | None = None, limit: int = 100, offset: int = 0, current_user: dict = _admin_only):
    return admin_repository.list_users(role=role, limit=limit, offset=offset)


@router.put("/users/{user_id}/suspend")
def suspend_user(user_id: str, current_user: dict = _admin_only):
    updated = admin_repository.set_user_active(user_id, False)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return updated


@router.put("/users/{user_id}/reactivate")
def reactivate_user(user_id: str, current_user: dict = _admin_only):
    updated = admin_repository.set_user_active(user_id, True)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return updated


@router.get("/reports")
def list_reports(status: str | None = None, current_user: dict = _admin_only):
    return admin_repository.list_reports(status=status)


@router.put("/reports/{report_id}")
def update_report(report_id: str, payload: ReportStatusUpdateRequest, current_user: dict = _admin_only):
    updated = admin_repository.update_report_status(report_id, payload.status)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return updated


@router.get("/organizations")
def list_organizations(current_user: dict = _admin_only):
    return admin_repository.list_organizations()


@router.put("/organizations/{org_id}/verify")
def verify_organization(org_id: str, current_user: dict = _admin_only):
    updated = admin_repository.verify_organization(org_id)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
    return updated


@router.delete("/posts/{post_id}")
def delete_post(post_id: str, current_user: dict = _admin_only):
    if post_repository.get_post_by_id(post_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    post_repository.delete_post(post_id)
    return {"detail": "Post removed by admin."}


@router.delete("/opportunities/{opportunity_id}")
def delete_opportunity(opportunity_id: str, current_user: dict = _admin_only):
    if opportunity_repository.get_opportunity_by_id(opportunity_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found.")
    opportunity_repository.delete_opportunity(opportunity_id)
    return {"detail": "Opportunity removed by admin."}
