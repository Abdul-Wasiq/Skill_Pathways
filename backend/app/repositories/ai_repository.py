"""
Data access for cached AI match analyses (ai_analyses table).
Caching avoids re-calling the AI provider every time the same
user/opportunity pair is viewed.
"""
import json

from app.database import get_cursor


def upsert_analysis(user_id: str, opportunity_id: str, result: dict) -> dict:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO ai_analyses
                (user_id, opportunity_id, match_score, eligibility_score, skills_score,
                 education_score, experience_score, matched_skills, missing_skills,
                 explanation, eligibility_notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, opportunity_id) DO UPDATE SET
                match_score = EXCLUDED.match_score,
                eligibility_score = EXCLUDED.eligibility_score,
                skills_score = EXCLUDED.skills_score,
                education_score = EXCLUDED.education_score,
                experience_score = EXCLUDED.experience_score,
                matched_skills = EXCLUDED.matched_skills,
                missing_skills = EXCLUDED.missing_skills,
                explanation = EXCLUDED.explanation,
                eligibility_notes = EXCLUDED.eligibility_notes,
                created_at = now()
            RETURNING *
            """,
            (
                user_id, opportunity_id,
                result["match_score"], result["eligibility_score"], result.get("skills_score"),
                result.get("education_score"), result.get("experience_score"),
                json.dumps(result.get("matched_skills", [])),
                json.dumps(result.get("missing_skills", [])),
                result.get("explanation"), result.get("eligibility_notes"),
            ),
        )
        return cur.fetchone()


def get_analysis(user_id: str, opportunity_id: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM ai_analyses WHERE user_id = %s AND opportunity_id = %s",
            (user_id, opportunity_id),
        )
        return cur.fetchone()
