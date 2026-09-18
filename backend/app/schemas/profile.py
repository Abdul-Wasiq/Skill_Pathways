from datetime import date

from pydantic import BaseModel, Field


class ProfileUpdateRequest(BaseModel):
    headline: str | None = None
    bio: str | None = None
    profile_picture_url: str | None = None
    location: str | None = None
    university: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    graduation_year: int | None = Field(default=None, ge=1950, le=2100)
    cgpa: float | None = Field(default=None, ge=0, le=4.0)
    career_goals: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    website_url: str | None = None


class SkillAddRequest(BaseModel):
    name: str
    proficiency: str | None = None


class EducationRequest(BaseModel):
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    description: str | None = None


class ExperienceRequest(BaseModel):
    company: str
    title: str
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    description: str | None = None


class ProjectRequest(BaseModel):
    title: str
    description: str | None = None
    url: str | None = None


class CertificationRequest(BaseModel):
    name: str
    issuer: str | None = None
    issue_date: date | None = None
    credential_url: str | None = None
