from fastapi import APIRouter, Depends, HTTPException, status

from app.repositories import opportunity_repository, profile_repository, notification_repository
from app.schemas.opportunity import (
    OrganizationCreateRequest, OpportunityCreateRequest, OpportunityUpdateRequest,
    ApplicationStatusUpdateRequest,
)
from app.utils.deps import get_current_user, require_roles

router = APIRouter(prefix="/api", tags=["opportunities"])


# --- Organizations --------------------------------------------------------

@router.post("/organizations", status_code=status.HTTP_201_CREATED)
def create_organization(payload: OrganizationCreateRequest,
                         current_user: dict = Depends(require_roles("organization", "admin"))):
    org = opportunity_repository.create_organization(
        payload.name, payload.description, payload.industry, payload.location,
        payload.website, payload.contact_email, current_user["id"],
    )
    return org


@router.get("/organizations/{org_id}")
def get_organization(org_id: str):
    org = opportunity_repository.get_organization_by_id(org_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
    return org


@router.get("/organizations/{org_id}/opportunities")
def list_org_opportunities(org_id: str):
    return opportunity_repository.list_opportunities_by_org(org_id)


def _assert_org_owner(user: dict, org_id: str) -> None:
    if user["role"] == "admin":
        return
    if not opportunity_repository.user_is_org_member(user["id"], org_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                             detail="You do not manage this organization.")


# --- Opportunities ---------------------------------------------------------

@router.post("/organizations/{org_id}/opportunities", status_code=status.HTTP_201_CREATED)
def create_opportunity(org_id: str, payload: OpportunityCreateRequest,
                        current_user: dict = Depends(require_roles("organization", "admin"))):
    _assert_org_owner(current_user, org_id)
    data = payload.model_dump(exclude={"required_skills", "preferred_skills"})
    opportunity = opportunity_repository.create_opportunity(org_id, data)

    required_ids = [profile_repository.get_or_create_skill(s.strip())["id"] for s in payload.required_skills if s.strip()]
    preferred_ids = [profile_repository.get_or_create_skill(s.strip())["id"] for s in payload.preferred_skills if s.strip()]
    opportunity_repository.set_opportunity_skills(opportunity["id"], required_ids, preferred_ids)

    return opportunity_repository.get_opportunity_by_id(opportunity["id"])


@router.get("/opportunities")
def list_opportunities(type: str | None = None, location: str | None = None,
                        work_mode: str | None = None, search: str | None = None,
                        limit: int = 50, offset: int = 0):
    return opportunity_repository.list_opportunities(type, location, work_mode, search, limit, offset)


@router.get("/opportunities/{opportunity_id}")
def get_opportunity(opportunity_id: str):
    opp = opportunity_repository.get_opportunity_by_id(opportunity_id)
    if opp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found.")
    opp["skills"] = opportunity_repository.get_opportunity_skills(opportunity_id)
    return opp


@router.put("/opportunities/{opportunity_id}")
def update_opportunity(opportunity_id: str, payload: OpportunityUpdateRequest,
                        current_user: dict = Depends(require_roles("organization", "admin"))):
    opp = opportunity_repository.get_opportunity_by_id(opportunity_id)
    if opp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found.")
    _assert_org_owner(current_user, opp["organization_id"])
    fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    return opportunity_repository.update_opportunity(opportunity_id, fields)


@router.delete("/opportunities/{opportunity_id}")
def delete_opportunity(opportunity_id: str, current_user: dict = Depends(require_roles("organization", "admin"))):
    opp = opportunity_repository.get_opportunity_by_id(opportunity_id)
    if opp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found.")
    _assert_org_owner(current_user, opp["organization_id"])
    opportunity_repository.delete_opportunity(opportunity_id)
    return {"detail": "Opportunity deleted."}


# --- Applications -----------------------------------------------------

@router.post("/opportunities/{opportunity_id}/apply", status_code=status.HTTP_201_CREATED)
def apply_to_opportunity(opportunity_id: str, current_user: dict = Depends(get_current_user)):
    opp = opportunity_repository.get_opportunity_by_id(opportunity_id)
    if opp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found.")
    if opp["status"] != "open":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This opportunity is no longer accepting applications.")
    if opportunity_repository.has_applied(current_user["id"], opportunity_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already applied to this opportunity.")
    application = opportunity_repository.create_application(current_user["id"], opportunity_id)
    for member_id in opportunity_repository.list_org_member_ids(opp["organization_id"]):
        notification_repository.create_notification(
            user_id=member_id,
            notif_type="application_submitted",
            title=f"New application for {opp['title']}",
            body=f"{current_user['name']} applied.",
            link_url=f"/pages/opportunity-detail.html?id={opportunity_id}",
        )
    return application


@router.post("/opportunities/{opportunity_id}/save", status_code=status.HTTP_201_CREATED)
def save_opportunity(opportunity_id: str, current_user: dict = Depends(get_current_user)):
    opportunity_repository.save_opportunity(current_user["id"], opportunity_id)
    return {"detail": "Opportunity saved."}


@router.delete("/opportunities/{opportunity_id}/save")
def unsave_opportunity(opportunity_id: str, current_user: dict = Depends(get_current_user)):
    opportunity_repository.unsave_opportunity(current_user["id"], opportunity_id)
    return {"detail": "Opportunity unsaved."}


@router.get("/saved-opportunities")
def list_saved(current_user: dict = Depends(get_current_user)):
    return opportunity_repository.list_saved_opportunities(current_user["id"])


@router.get("/applications")
def list_my_applications(current_user: dict = Depends(get_current_user)):
    return opportunity_repository.list_applications_for_user(current_user["id"])


@router.get("/opportunities/{opportunity_id}/applications")
def list_opportunity_applications(opportunity_id: str, current_user: dict = Depends(require_roles("organization", "admin"))):
    opp = opportunity_repository.get_opportunity_by_id(opportunity_id)
    if opp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found.")
    _assert_org_owner(current_user, opp["organization_id"])
    return opportunity_repository.list_applications_for_opportunity(opportunity_id)


@router.put("/applications/{application_id}/status")
def update_application_status(application_id: str, payload: ApplicationStatusUpdateRequest,
                               current_user: dict = Depends(require_roles("organization", "admin"))):
    updated = opportunity_repository.update_application_status(application_id, payload.status)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
    opp = opportunity_repository.get_opportunity_by_id(updated["opportunity_id"])
    notification_repository.create_notification(
        user_id=updated["user_id"],
        notif_type="application_status_changed",
        title=f"Your application status changed for {opp['title'] if opp else 'an opportunity'}",
        body=f"New status: {payload.status.replace('_', ' ')}",
        link_url=f"/pages/opportunity-detail.html?id={updated['opportunity_id']}",
    )
    return updated
