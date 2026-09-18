"""
AI Resume -> Profile (spec §14).

Workflow: raw resume text -> AI structures it -> validated against
ResumeStructuredData -> returned as a PREVIEW. The caller (API layer)
is responsible for never auto-saving this to the user's profile —
the user must review and confirm first (spec §49, human-in-the-loop).
"""
from app.schemas.ai import ResumeStructuredData
from app.services.ai_service import ai_service, AIServiceError

_SYSTEM_PROMPT = """You extract structured information from resume text for a career
platform. Extract ONLY information that is actually present in the text — never invent
degrees, companies, or skills that aren't mentioned. If a field isn't present, leave it
empty or use an empty list. Respond ONLY with a JSON object matching this exact shape:
{
  "full_name": "", "email": "", "headline": "", "bio": "",
  "skills": ["..."],
  "education": [{"institution": "", "degree": "", "field_of_study": "", "start_year": null, "end_year": null}],
  "experience": [{"company": "", "title": "", "description": ""}],
  "projects": [{"title": "", "description": ""}],
  "certifications": [{"name": "", "issuer": ""}]
}
"headline" should be a short 1-line professional summary inferred from the resume
(e.g. "Backend Developer with 2 years experience"), not copied verbatim unless the
resume already has one. "bio" can be 2-3 sentences summarizing background, based only
on what's stated."""


async def structure_resume(resume_text: str) -> ResumeStructuredData:
    # Cap input size — resumes shouldn't need more than this, and it keeps
    # the AI call fast/cheap and avoids blowing context on garbage extraction.
    truncated = resume_text[:12000]
    try:
        result = await ai_service.complete_json(_SYSTEM_PROMPT, truncated, temperature=0.1)
    except AIServiceError as exc:
        raise
    return ResumeStructuredData(**result)
