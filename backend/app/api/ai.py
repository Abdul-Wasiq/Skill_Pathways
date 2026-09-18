from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from app.repositories import profile_repository, opportunity_repository, ai_repository
from app.services import matching_service, profile_service
from app.services import resume_extraction, resume_ai_service, career_assistant_service
from app.services import job_analyzer_service, post_assistant_service
from app.services.ai_service import AIServiceError
from app.services.resume_extraction import ResumeExtractionError
from app.schemas.ai_requests import (
    CareerAssistantRequest, JobAnalyzerRequest, PostAssistantRequest, ResumeConfirmRequest,
)
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _estimate_years_experience(user_id: str) -> float:
    entries = profile_repository.list_experience(user_id)
    total_days = 0
    today = date.today()
    for e in entries:
        start = e.get("start_date")
        end = e.get("end_date") or today
        if start:
            total_days += max((end - start).days, 0)
    return round(total_days / 365, 1)


@router.post("/opportunity-match/{opportunity_id}")
async def opportunity_match(opportunity_id: str, current_user: dict = Depends(get_current_user)):
    profile = profile_repository.get_profile_by_user_id(current_user["id"])
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete your profile before requesting an AI match score.",
        )

    opportunity = opportunity_repository.get_opportunity_by_id(opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found.")

    user_skills = [s["name"] for s in profile_repository.get_user_skills(current_user["id"])]
    opp_skills = opportunity_repository.get_opportunity_skills(opportunity_id)
    required_skills = [s["name"] for s in opp_skills if s["importance"] == "required"]
    preferred_skills = [s["name"] for s in opp_skills if s["importance"] == "preferred"]
    years_experience = _estimate_years_experience(current_user["id"])

    try:
        analysis = await matching_service.analyze_opportunity_match(
            profile, user_skills, years_experience, opportunity, required_skills, preferred_skills,
        )
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    saved = ai_repository.upsert_analysis(current_user["id"], opportunity_id, analysis.model_dump())
    return saved


@router.get("/opportunity-match/{opportunity_id}")
def get_cached_match(opportunity_id: str, current_user: dict = Depends(get_current_user)):
    analysis = ai_repository.get_analysis(current_user["id"], opportunity_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No match analysis yet — request one via POST /api/ai/opportunity-match/{opportunity_id}.",
        )
    return analysis


# --- AI Resume -> Profile (spec §14) -----------------------------------

@router.post("/resume-to-profile")
async def resume_to_profile(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Extracts + AI-structures a resume. Returns a PREVIEW only — nothing
    is saved until the user calls /resume-to-profile/confirm."""
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided.")

    file_bytes = await file.read()
    max_size = 8 * 1024 * 1024  # 8MB
    if len(file_bytes) > max_size:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is too large (max 8MB).")

    try:
        text = resume_extraction.extract_resume_text(file.filename, file_bytes)
    except ResumeExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    try:
        structured = await resume_ai_service.structure_resume(text)
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    return structured


@router.post("/resume-to-profile/confirm")
def confirm_resume_to_profile(payload: ResumeConfirmRequest, current_user: dict = Depends(get_current_user)):
    """Writes the user-reviewed resume data to their profile. This is the
    only endpoint that actually persists resume data — the extraction
    endpoint above never saves anything by itself (spec §49)."""
    user_id = current_user["id"]

    profile_fields = {}
    if payload.headline:
        profile_fields["headline"] = payload.headline
    if payload.bio:
        profile_fields["bio"] = payload.bio
    if profile_fields:
        profile_repository.update_profile(user_id, profile_fields)

    for skill_name in payload.skills:
        if skill_name.strip():
            skill = profile_repository.get_or_create_skill(skill_name.strip())
            profile_repository.add_user_skill(user_id, skill["id"], None)

    for edu in payload.education:
        if edu.institution.strip():
            profile_repository.add_education(user_id, edu.model_dump())

    for exp in payload.experience:
        if exp.company.strip() or exp.title.strip():
            profile_repository.add_experience(user_id, exp.model_dump())

    for proj in payload.projects:
        if proj.title.strip():
            profile_repository.add_project(user_id, proj.model_dump())

    for cert in payload.certifications:
        if cert.name.strip():
            profile_repository.add_certification(user_id, cert.model_dump())

    profile_service.calculate_completion(user_id)
    return {"detail": "Profile updated from resume."}


# --- AI Career Assistant (spec §17) -------------------------------------

@router.post("/career-assistant")
async def career_assistant(payload: CareerAssistantRequest, current_user: dict = Depends(get_current_user)):
    response = await career_assistant_service.ask_career_assistant(current_user["id"], payload.question)
    return response


# --- AI Job Description Analyzer (spec §18) -----------------------------

def _estimate_years_experience_for(user_id: str) -> float:
    entries = profile_repository.list_experience(user_id)
    total_days = 0
    today = date.today()
    for e in entries:
        start = e.get("start_date")
        end = e.get("end_date") or today
        if start:
            total_days += max((end - start).days, 0)
    return round(total_days / 365, 1)


@router.post("/job-analyzer")
async def job_analyzer(payload: JobAnalyzerRequest, current_user: dict = Depends(get_current_user)):
    profile = profile_repository.get_profile_by_user_id(current_user["id"])
    try:
        if profile is not None:
            user_skills = [s["name"] for s in profile_repository.get_user_skills(current_user["id"])]
            years_experience = _estimate_years_experience_for(current_user["id"])
            result = await job_analyzer_service.analyze_and_match(
                payload.description, profile, user_skills, years_experience
            )
        else:
            analysis = await job_analyzer_service.analyze_job_description(payload.description)
            result = {"analysis": analysis.model_dump(), "match": None}
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    return result


# --- AI Post Assistant (spec §15) ---------------------------------------

@router.post("/post-assistant")
async def post_assistant(payload: PostAssistantRequest, current_user: dict = Depends(get_current_user)):
    try:
        response = await post_assistant_service.assist_post(
            payload.content, payload.action, payload.extra_instructions
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return response
