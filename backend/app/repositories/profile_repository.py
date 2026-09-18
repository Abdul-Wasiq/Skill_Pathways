"""
Data access for `profiles`, `user_skills`, and related child tables
(education, experience, projects, certifications).
"""
from app.database import get_cursor


def get_profile_by_user_id(user_id: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM profiles WHERE user_id = %s", (user_id,))
        return cur.fetchone()


def create_profile(user_id: str) -> dict:
    """Creates an empty profile row for a newly registered user."""
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO profiles (user_id) VALUES (%s) RETURNING *",
            (user_id,),
        )
        return cur.fetchone()


def update_profile(user_id: str, fields: dict) -> dict | None:
    """Dynamically builds an UPDATE from a dict of column -> value.
    Column names come only from a fixed whitelist, never from user input directly,
    so this is not vulnerable to SQL injection despite the dynamic assembly."""
    allowed_columns = {
        "headline", "bio", "profile_picture_url", "location", "university",
        "degree", "field_of_study", "graduation_year", "cgpa", "career_goals",
        "github_url", "portfolio_url", "website_url",
    }
    updates = {k: v for k, v in fields.items() if k in allowed_columns}
    if not updates:
        return get_profile_by_user_id(user_id)

    set_clause = ", ".join(f"{col} = %s" for col in updates)
    values = list(updates.values()) + [user_id]

    with get_cursor() as cur:
        cur.execute(
            f"UPDATE profiles SET {set_clause} WHERE user_id = %s RETURNING *",
            values,
        )
        return cur.fetchone()


def set_profile_completion(user_id: str, percentage: int) -> None:
    with get_cursor() as cur:
        cur.execute(
            "UPDATE profiles SET profile_completion = %s WHERE user_id = %s",
            (percentage, user_id),
        )


# --- Skills -----------------------------------------------------------

def get_or_create_skill(name: str) -> dict:
    with get_cursor() as cur:
        cur.execute("SELECT id, name FROM skills WHERE name = %s", (name,))
        existing = cur.fetchone()
        if existing:
            return existing
        cur.execute(
            "INSERT INTO skills (name) VALUES (%s) RETURNING id, name", (name,)
        )
        return cur.fetchone()


def get_user_skills(user_id: str) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT s.id, s.name, us.proficiency
            FROM user_skills us
            JOIN skills s ON s.id = us.skill_id
            WHERE us.user_id = %s
            ORDER BY s.name
            """,
            (user_id,),
        )
        return cur.fetchall()


def add_user_skill(user_id: str, skill_id: int, proficiency: str | None) -> None:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO user_skills (user_id, skill_id, proficiency)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, skill_id) DO UPDATE SET proficiency = EXCLUDED.proficiency
            """,
            (user_id, skill_id, proficiency),
        )


def remove_user_skill(user_id: str, skill_id: int) -> None:
    with get_cursor() as cur:
        cur.execute(
            "DELETE FROM user_skills WHERE user_id = %s AND skill_id = %s",
            (user_id, skill_id),
        )


# --- Education / Experience / Projects / Certifications ---------------

def add_education(user_id: str, data: dict) -> dict:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO education_entries
                (user_id, institution, degree, field_of_study, start_year, end_year, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (user_id, data.get("institution"), data.get("degree"), data.get("field_of_study"),
             data.get("start_year"), data.get("end_year"), data.get("description")),
        )
        return cur.fetchone()


def list_education(user_id: str) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM education_entries WHERE user_id = %s ORDER BY start_year DESC NULLS LAST",
            (user_id,),
        )
        return cur.fetchall()


def add_experience(user_id: str, data: dict) -> dict:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO experience_entries
                (user_id, company, title, start_date, end_date, is_current, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (user_id, data.get("company"), data.get("title"), data.get("start_date"),
             data.get("end_date"), data.get("is_current", False), data.get("description")),
        )
        return cur.fetchone()


def list_experience(user_id: str) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM experience_entries WHERE user_id = %s ORDER BY start_date DESC NULLS LAST",
            (user_id,),
        )
        return cur.fetchall()


def add_project(user_id: str, data: dict) -> dict:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO project_entries (user_id, title, description, url)
            VALUES (%s, %s, %s, %s)
            RETURNING *
            """,
            (user_id, data.get("title"), data.get("description"), data.get("url")),
        )
        return cur.fetchone()


def list_projects(user_id: str) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM project_entries WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,),
        )
        return cur.fetchall()


def add_certification(user_id: str, data: dict) -> dict:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO certification_entries (user_id, name, issuer, issue_date, credential_url)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
            """,
            (user_id, data.get("name"), data.get("issuer"), data.get("issue_date"),
             data.get("credential_url")),
        )
        return cur.fetchone()


def list_certifications(user_id: str) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM certification_entries WHERE user_id = %s ORDER BY issue_date DESC NULLS LAST",
            (user_id,),
        )
        return cur.fetchall()
