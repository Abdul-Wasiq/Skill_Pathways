"""
Data access for organizations, opportunities, opportunity_skills,
applications, and saved_opportunities.
"""
from app.database import get_cursor


# --- Organizations ------------------------------------------------------

def create_organization(name: str, description: str | None, industry: str | None,
                         location: str | None, website: str | None,
                         contact_email: str | None, owner_user_id: str) -> dict:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO organizations (name, description, industry, location, website, contact_email)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (name, description, industry, location, website, contact_email),
        )
        org = cur.fetchone()
        cur.execute(
            """
            INSERT INTO organization_members (organization_id, user_id, role)
            VALUES (%s, %s, 'owner')
            """,
            (org["id"], owner_user_id),
        )
        return org


def get_organization_by_id(org_id: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM organizations WHERE id = %s", (org_id,))
        return cur.fetchone()


def user_is_org_member(user_id: str, org_id: str) -> bool:
    with get_cursor() as cur:
        cur.execute(
            "SELECT 1 FROM organization_members WHERE user_id = %s AND organization_id = %s",
            (user_id, org_id),
        )
        return cur.fetchone() is not None


def list_organizations_for_user(user_id: str) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT o.* FROM organizations o
            JOIN organization_members m ON m.organization_id = o.id
            WHERE m.user_id = %s
            """,
            (user_id,),
        )
        return cur.fetchall()


def list_org_member_ids(org_id: str) -> list[str]:
    with get_cursor() as cur:
        cur.execute("SELECT user_id FROM organization_members WHERE organization_id = %s", (org_id,))
        return [row["user_id"] for row in cur.fetchall()]


# --- Opportunities --------------------------------------------------------

def create_opportunity(org_id: str, data: dict) -> dict:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO opportunities
                (organization_id, title, description, type, work_mode, location,
                 salary_or_stipend, deadline, education_requirement, min_experience_years,
                 min_cgpa, eligibility_notes, application_url, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (org_id, data["title"], data["description"], data["type"], data.get("work_mode"),
             data.get("location"), data.get("salary_or_stipend"), data.get("deadline"),
             data.get("education_requirement"), data.get("min_experience_years", 0),
             data.get("min_cgpa"), data.get("eligibility_notes"), data.get("application_url"),
             data.get("status", "open")),
        )
        return cur.fetchone()


def update_opportunity(opportunity_id: str, fields: dict) -> dict | None:
    allowed_columns = {
        "title", "description", "type", "work_mode", "location", "salary_or_stipend",
        "deadline", "education_requirement", "min_experience_years", "min_cgpa",
        "eligibility_notes", "application_url", "status",
    }
    updates = {k: v for k, v in fields.items() if k in allowed_columns}
    if not updates:
        return get_opportunity_by_id(opportunity_id)
    set_clause = ", ".join(f"{col} = %s" for col in updates)
    values = list(updates.values()) + [opportunity_id]
    with get_cursor() as cur:
        cur.execute(
            f"UPDATE opportunities SET {set_clause} WHERE id = %s RETURNING *",
            values,
        )
        return cur.fetchone()


def delete_opportunity(opportunity_id: str) -> None:
    with get_cursor() as cur:
        cur.execute("DELETE FROM opportunities WHERE id = %s", (opportunity_id,))


def get_opportunity_by_id(opportunity_id: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT op.*, o.name AS organization_name, o.logo_url AS organization_logo
            FROM opportunities op
            JOIN organizations o ON o.id = op.organization_id
            WHERE op.id = %s
            """,
            (opportunity_id,),
        )
        return cur.fetchone()


def list_opportunities(opp_type: str | None = None, location: str | None = None,
                        work_mode: str | None = None, search: str | None = None,
                        limit: int = 50, offset: int = 0) -> list[dict]:
    query = """
        SELECT op.*, o.name AS organization_name, o.logo_url AS organization_logo
        FROM opportunities op
        JOIN organizations o ON o.id = op.organization_id
        WHERE op.status = 'open'
    """
    params: list = []
    if opp_type:
        query += " AND op.type = %s"
        params.append(opp_type)
    if location:
        query += " AND op.location ILIKE %s"
        params.append(f"%{location}%")
    if work_mode:
        query += " AND op.work_mode = %s"
        params.append(work_mode)
    if search:
        query += " AND (op.title ILIKE %s OR op.description ILIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY op.created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def list_opportunities_by_org(org_id: str) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM opportunities WHERE organization_id = %s ORDER BY created_at DESC",
            (org_id,),
        )
        return cur.fetchall()


# --- Opportunity skills -----------------------------------------------

def set_opportunity_skills(opportunity_id: str, required: list[int], preferred: list[int]) -> None:
    with get_cursor() as cur:
        cur.execute("DELETE FROM opportunity_skills WHERE opportunity_id = %s", (opportunity_id,))
        for skill_id in required:
            cur.execute(
                "INSERT INTO opportunity_skills (opportunity_id, skill_id, importance) "
                "VALUES (%s, %s, 'required')",
                (opportunity_id, skill_id),
            )
        for skill_id in preferred:
            cur.execute(
                "INSERT INTO opportunity_skills (opportunity_id, skill_id, importance) "
                "VALUES (%s, %s, 'preferred')",
                (opportunity_id, skill_id),
            )


def get_opportunity_skills(opportunity_id: str) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT s.id, s.name, os.importance
            FROM opportunity_skills os
            JOIN skills s ON s.id = os.skill_id
            WHERE os.opportunity_id = %s
            """,
            (opportunity_id,),
        )
        return cur.fetchall()


# --- Applications & saved opportunities --------------------------------

def create_application(user_id: str, opportunity_id: str) -> dict:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO applications (user_id, opportunity_id)
            VALUES (%s, %s)
            RETURNING *
            """,
            (user_id, opportunity_id),
        )
        return cur.fetchone()


def has_applied(user_id: str, opportunity_id: str) -> bool:
    with get_cursor() as cur:
        cur.execute(
            "SELECT 1 FROM applications WHERE user_id = %s AND opportunity_id = %s",
            (user_id, opportunity_id),
        )
        return cur.fetchone() is not None


def list_applications_for_user(user_id: str) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT a.*, op.title AS opportunity_title, org.name AS organization_name
            FROM applications a
            JOIN opportunities op ON op.id = a.opportunity_id
            JOIN organizations org ON org.id = op.organization_id
            WHERE a.user_id = %s
            ORDER BY a.applied_at DESC
            """,
            (user_id,),
        )
        return cur.fetchall()


def list_applications_for_opportunity(opportunity_id: str) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT a.*, u.name AS applicant_name, u.email AS applicant_email
            FROM applications a
            JOIN users u ON u.id = a.user_id
            WHERE a.opportunity_id = %s
            ORDER BY a.applied_at DESC
            """,
            (opportunity_id,),
        )
        return cur.fetchall()


def update_application_status(application_id: str, status: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute(
            "UPDATE applications SET status = %s WHERE id = %s RETURNING *",
            (status, application_id),
        )
        return cur.fetchone()


def save_opportunity(user_id: str, opportunity_id: str) -> None:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO saved_opportunities (user_id, opportunity_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            (user_id, opportunity_id),
        )


def unsave_opportunity(user_id: str, opportunity_id: str) -> None:
    with get_cursor() as cur:
        cur.execute(
            "DELETE FROM saved_opportunities WHERE user_id = %s AND opportunity_id = %s",
            (user_id, opportunity_id),
        )


def list_saved_opportunities(user_id: str) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT op.*, o.name AS organization_name
            FROM saved_opportunities so
            JOIN opportunities op ON op.id = so.opportunity_id
            JOIN organizations o ON o.id = op.organization_id
            WHERE so.user_id = %s
            ORDER BY so.saved_at DESC
            """,
            (user_id,),
        )
        return cur.fetchall()
