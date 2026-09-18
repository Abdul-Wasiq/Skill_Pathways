"""
AI Job Description Analyzer (spec §18).

Takes pasted job description text, extracts structured requirements via
AI (validated against JobAnalysis schema), then — if the user is logged
in — reuses the SAME deterministic matching_service scoring used for
opportunity matching, so a pasted JD gets the same transparent,
explainable treatment as a posted opportunity rather than a separate
ad-hoc scoring path.
"""
from app.schemas.ai import JobAnalysis
from app.services import matching_service
from app.services.ai_service import ai_service, AIServiceError

_SYSTEM_PROMPT = """You analyze job/internship descriptions for a career platform.
Extract structured requirements from the pasted text. Only include skills/requirements
actually mentioned or clearly implied — do not invent. Respond ONLY with a JSON object:
{
  "required_skills": ["..."], "preferred_skills": ["..."],
  "education_requirement": "short phrase or empty string",
  "experience_requirement": "short phrase or empty string",
  "responsibilities": ["..."], "technical_stack": ["..."], "soft_skills": ["..."],
  "estimated_difficulty": "entry-level|mid-level|senior|unclear",
  "key_notes": "1-2 sentences on anything notable (red flags, unusual requirements, etc.) or empty string"
}"""


async def analyze_job_description(description_text: str) -> JobAnalysis:
    truncated = description_text[:8000]
    try:
        result = await ai_service.complete_json(_SYSTEM_PROMPT, truncated, temperature=0.1)
    except AIServiceError:
        raise
    return JobAnalysis(**result)


def _parse_years_from_text(experience_requirement: str) -> float:
    """Best-effort extraction of a numeric years requirement from free text
    like '1-2 years' or '3+ years experience'. Falls back to 0 (no hard
    requirement detected) rather than guessing wildly."""
    import re
    match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*year", experience_requirement.lower())
    return float(match.group(1)) if match else 0.0


async def analyze_and_match(description_text: str, profile: dict, user_skill_names: list[str],
                             years_experience: float) -> dict:
    analysis = await analyze_job_description(description_text)

    # Build a minimal "opportunity-shaped" dict so we can reuse the exact
    # same transparent scoring function as posted opportunities.
    pseudo_opportunity = {
        "title": "Pasted Job Description",
        "education_requirement": analysis.education_requirement or None,
        "min_experience_years": _parse_years_from_text(analysis.experience_requirement),
        "min_cgpa": None,
    }
    computed = matching_service.compute_match(
        profile, user_skill_names, years_experience, pseudo_opportunity,
        analysis.required_skills, analysis.preferred_skills,
    )

    return {
        "analysis": analysis.model_dump(),
        "match": computed,
    }
