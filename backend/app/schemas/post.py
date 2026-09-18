from pydantic import BaseModel, field_validator

POST_TYPES = {"text", "achievement", "project", "question", "opportunity", "learning", "announcement"}


class PostCreateRequest(BaseModel):
    content: str
    post_type: str = "text"
    organization_id: str | None = None
    linked_opportunity_id: str | None = None

    @field_validator("post_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in POST_TYPES:
            raise ValueError(f"post_type must be one of {sorted(POST_TYPES)}")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Post content cannot be empty.")
        if len(v) > 5000:
            raise ValueError("Post content is too long (max 5000 characters).")
        return v


class PostUpdateRequest(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Post content cannot be empty.")
        return v


class CommentCreateRequest(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Comment cannot be empty.")
        if len(v) > 2000:
            raise ValueError("Comment is too long (max 2000 characters).")
        return v


class ReportCreateRequest(BaseModel):
    target_type: str
    target_id: str
    reason: str

    @field_validator("target_type")
    @classmethod
    def validate_target_type(cls, v: str) -> str:
        allowed = {"post", "comment", "user", "opportunity", "organization"}
        if v not in allowed:
            raise ValueError(f"target_type must be one of {sorted(allowed)}")
        return v

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("A reason is required to submit a report.")
        return v
