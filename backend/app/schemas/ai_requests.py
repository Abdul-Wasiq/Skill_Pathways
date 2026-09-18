from pydantic import BaseModel, field_validator

from app.schemas.ai import (
    ResumeEducationItem, ResumeExperienceItem, ResumeProjectItem, ResumeCertificationItem,
)


class CareerAssistantRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question cannot be empty.")
        if len(v) > 2000:
            raise ValueError("Question is too long (max 2000 characters).")
        return v


class JobAnalyzerRequest(BaseModel):
    description: str

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 20:
            raise ValueError("Please paste the full job description (too short to analyze).")
        return v


class PostAssistantRequest(BaseModel):
    content: str
    action: str
    extra_instructions: str = ""

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Draft content cannot be empty.")
        return v


class ResumeConfirmRequest(BaseModel):
    """The user-reviewed/edited version of the AI's resume extraction —
    only what's submitted here actually gets written to the profile."""
    headline: str | None = None
    bio: str | None = None
    skills: list[str] = []
    education: list[ResumeEducationItem] = []
    experience: list[ResumeExperienceItem] = []
    projects: list[ResumeProjectItem] = []
    certifications: list[ResumeCertificationItem] = []
