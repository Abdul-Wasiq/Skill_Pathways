from fastapi import APIRouter, Depends, HTTPException, status

from app.repositories import profile_repository
from app.schemas.profile import (
    ProfileUpdateRequest, SkillAddRequest, EducationRequest,
    ExperienceRequest, ProjectRequest, CertificationRequest,
)
from app.services import profile_service
from app.utils.deps import get_current_user, require_roles

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _full_profile(user_id: str) -> dict:
    profile = profile_repository.get_profile_by_user_id(user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    return {
        **profile,
        "skills": profile_repository.get_user_skills(user_id),
        "education": profile_repository.list_education(user_id),
        "experience": profile_repository.list_experience(user_id),
        "projects": profile_repository.list_projects(user_id),
        "certifications": profile_repository.list_certifications(user_id),
    }


@router.get("")
def get_my_profile(current_user: dict = Depends(get_current_user)):
    return _full_profile(current_user["id"])


@router.put("")
def update_my_profile(payload: ProfileUpdateRequest, current_user: dict = Depends(get_current_user)):
    fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    profile_repository.update_profile(current_user["id"], fields)
    profile_service.calculate_completion(current_user["id"])
    return _full_profile(current_user["id"])


@router.post("/skills", status_code=status.HTTP_201_CREATED)
def add_skill(payload: SkillAddRequest, current_user: dict = Depends(get_current_user)):
    skill = profile_repository.get_or_create_skill(payload.name.strip())
    profile_repository.add_user_skill(current_user["id"], skill["id"], payload.proficiency)
    profile_service.calculate_completion(current_user["id"])
    return profile_repository.get_user_skills(current_user["id"])


@router.delete("/skills/{skill_id}")
def remove_skill(skill_id: int, current_user: dict = Depends(get_current_user)):
    profile_repository.remove_user_skill(current_user["id"], skill_id)
    profile_service.calculate_completion(current_user["id"])
    return {"detail": "Skill removed."}


@router.post("/education", status_code=status.HTTP_201_CREATED)
def add_education(payload: EducationRequest, current_user: dict = Depends(get_current_user)):
    entry = profile_repository.add_education(current_user["id"], payload.model_dump())
    profile_service.calculate_completion(current_user["id"])
    return entry


@router.post("/experience", status_code=status.HTTP_201_CREATED)
def add_experience(payload: ExperienceRequest, current_user: dict = Depends(get_current_user)):
    entry = profile_repository.add_experience(current_user["id"], payload.model_dump())
    profile_service.calculate_completion(current_user["id"])
    return entry


@router.post("/projects", status_code=status.HTTP_201_CREATED)
def add_project(payload: ProjectRequest, current_user: dict = Depends(get_current_user)):
    entry = profile_repository.add_project(current_user["id"], payload.model_dump())
    profile_service.calculate_completion(current_user["id"])
    return entry


@router.post("/certifications", status_code=status.HTTP_201_CREATED)
def add_certification(payload: CertificationRequest, current_user: dict = Depends(get_current_user)):
    entry = profile_repository.add_certification(current_user["id"], payload.model_dump())
    return entry
