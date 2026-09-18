from datetime import datetime

from pydantic import BaseModel, Field, field_validator

OPPORTUNITY_TYPES = {"job", "internship", "scholarship", "fellowship",
                      "competition", "event", "training", "other"}
WORK_MODES = {"remote", "hybrid", "on_site"}
APPLICATION_STATUSES = {"applied", "under_review", "shortlisted", "rejected", "accepted", "withdrawn"}


class OrganizationCreateRequest(BaseModel):
    name: str
    description: str | None = None
    industry: str | None = None
    location: str | None = None
    website: str | None = None
    contact_email: str | None = None


class OpportunityCreateRequest(BaseModel):
    title: str
    description: str
    type: str
    work_mode: str | None = None
    location: str | None = None
    salary_or_stipend: str | None = None
    deadline: datetime | None = None
    education_requirement: str | None = None
    min_experience_years: float = 0
    min_cgpa: float | None = Field(default=None, ge=0, le=4.0)
    eligibility_notes: str | None = None
    application_url: str | None = None
    required_skills: list[str] = []
    preferred_skills: list[str] = []

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in OPPORTUNITY_TYPES:
            raise ValueError(f"type must be one of {sorted(OPPORTUNITY_TYPES)}")
        return v

    @field_validator("work_mode")
    @classmethod
    def validate_work_mode(cls, v: str | None) -> str | None:
        if v is not None and v not in WORK_MODES:
            raise ValueError(f"work_mode must be one of {sorted(WORK_MODES)}")
        return v


class OpportunityUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    work_mode: str | None = None
    location: str | None = None
    salary_or_stipend: str | None = None
    deadline: datetime | None = None
    education_requirement: str | None = None
    min_experience_years: float | None = None
    min_cgpa: float | None = None
    eligibility_notes: str | None = None
    application_url: str | None = None
    status: str | None = None


class ApplicationStatusUpdateRequest(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in APPLICATION_STATUSES:
            raise ValueError(f"status must be one of {sorted(APPLICATION_STATUSES)}")
        return v
