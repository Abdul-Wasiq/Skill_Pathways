"""
AI Career Assistant (spec §17).

Uses the user's actual profile data (skills, education, career goals)
so responses are specific rather than generic ("Learn Docker to
complement your existing Python/FastAPI skills" instead of "Learn
Docker"). Never exposes other users' data — only the current caller's.
"""
from app.repositories import profile_repository
from app.schemas.ai import CareerAssistantResponse
from app.services.ai_service import ai_service, AIServiceError

_SYSTEM_PROMPT = """You are a career assistant for a job/internship/scholarship
platform. You are given a user's real profile data and a question. Answer using
ONLY the profile data provided — do not invent skills, education, or experience
they don't have. Be specific: reference their actual skills/education by name
rather than giving generic advice. Never claim certainty about outcomes you can't
know (e.g. don't say "you will definitely get this job"); use cautious language
like "this may improve your chances". Respond ONLY with a JSON object:
{"answer": "2-5 sentences", "suggested_next_steps": ["short actionable step", "..."]}
suggested_next_steps should have 0-4 items, only include if genuinely useful."""


def _build_profile_context(user_id: str) -> str:
    profile = profile_repository.get_profile_by_user_id(user_id)
    if profile is None:
        return "This user has no profile data yet."

    skills = [s["name"] for s in profile_repository.get_user_skills(user_id)]
    education = profile_repository.list_education(user_id)
    experience = profile_repository.list_experience(user_id)
    projects = profile_repository.list_projects(user_id)

    edu_str = "; ".join(f"{e.get('degree', '')} at {e.get('institution', '')}" for e in education) or "None"
    exp_str = "; ".join(f"{e.get('title', '')} at {e.get('company', '')}" for e in experience) or "None"
    proj_str = "; ".join(p.get("title", "") for p in projects) or "None"

    lines = [
        f"Headline: {profile.get('headline') or 'Not set'}",
        f"University: {profile.get('university') or 'Not set'}",
        f"Degree: {profile.get('degree') or 'Not set'}",
        f"CGPA: {profile.get('cgpa') or 'Not set'}",
        f"Career goals: {profile.get('career_goals') or 'Not set'}",
        f"Skills: {', '.join(skills) if skills else 'None listed'}",
        f"Education history: {edu_str}",
        f"Experience: {exp_str}",
        f"Projects: {proj_str}",
    ]
    return "\n".join(lines)


async def ask_career_assistant(user_id: str, question: str) -> CareerAssistantResponse:
    profile_context = _build_profile_context(user_id)
    user_prompt = f"USER PROFILE:\n{profile_context}\n\nQUESTION: {question}"
    try:
        result = await ai_service.complete_json(_SYSTEM_PROMPT, user_prompt, temperature=0.4)
    except AIServiceError:
        return CareerAssistantResponse(
            answer=(
                "The AI assistant is currently unavailable (no AI provider configured or "
                "the request failed). Please try again later, or check backend/.env for "
                "AI_API_KEY configuration."
            ),
            suggested_next_steps=[],
        )
    return CareerAssistantResponse(**result)
