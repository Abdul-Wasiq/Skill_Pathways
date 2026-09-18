"""
Computes the profile completion percentage (spec §8) from real,
measurable fields rather than a hard-coded number.
"""
from app.repositories import profile_repository


def calculate_completion(user_id: str) -> int:
    profile = profile_repository.get_profile_by_user_id(user_id)
    if profile is None:
        return 0

    checks = [
        bool(profile.get("headline")),
        bool(profile.get("bio")),
        bool(profile.get("location")),
        bool(profile.get("university")),
        bool(profile.get("degree")),
        bool(profile.get("career_goals")),
        bool(profile.get("github_url") or profile.get("portfolio_url") or profile.get("website_url")),
        len(profile_repository.get_user_skills(user_id)) >= 3,
        len(profile_repository.list_education(user_id)) >= 1,
        len(profile_repository.list_experience(user_id)) >= 1,
        len(profile_repository.list_projects(user_id)) >= 1,
    ]
    percentage = round(sum(checks) / len(checks) * 100)
    profile_repository.set_profile_completion(user_id, percentage)
    return percentage
