"""
Data access for admin operations: user management, moderation,
organization verification, and platform statistics.
"""
from app.database import get_cursor
from app.repositories import user_repository


def list_users(role: str | None = None, limit: int = 100, offset: int = 0) -> list[dict]:
    query = "SELECT id, name, email, role, is_active, created_at FROM users"
    params: list = []
    if role:
        query += " WHERE role = %s"
        params.append(role)
    query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def set_user_active(user_id: str, is_active: bool) -> dict | None:
    with get_cursor() as cur:
        cur.execute(
            "UPDATE users SET is_active = %s WHERE id = %s RETURNING id, name, email, role, is_active",
            (is_active, user_id),
        )
        row = cur.fetchone()
    # Take effect immediately: forget the cached copy so the next request
    # sees the new is_active value instead of waiting for the cache to expire.
    user_repository.invalidate_user_cache(user_id)
    return row


def list_reports(status: str | None = None, limit: int = 100) -> list[dict]:
    query = """
        SELECT r.*, u.name AS reporter_name
        FROM reports r JOIN users u ON u.id = r.reporter_id
    """
    params: list = []
    if status:
        query += " WHERE r.status = %s"
        params.append(status)
    query += " ORDER BY r.created_at DESC LIMIT %s"
    params.append(limit)
    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def update_report_status(report_id: str, status: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute(
            "UPDATE reports SET status = %s WHERE id = %s RETURNING *",
            (status, report_id),
        )
        return cur.fetchone()


def verify_organization(org_id: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute(
            "UPDATE organizations SET is_verified = TRUE WHERE id = %s RETURNING *",
            (org_id,),
        )
        return cur.fetchone()


def list_organizations(limit: int = 100) -> list[dict]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM organizations ORDER BY created_at DESC LIMIT %s", (limit,))
        return cur.fetchall()


def get_platform_stats() -> dict:
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS count FROM users")
        total_users = cur.fetchone()["count"]

        cur.execute("SELECT COUNT(*) AS count FROM organizations")
        total_organizations = cur.fetchone()["count"]

        cur.execute("SELECT COUNT(*) AS count FROM opportunities")
        total_opportunities = cur.fetchone()["count"]

        cur.execute("SELECT COUNT(*) AS count FROM applications")
        total_applications = cur.fetchone()["count"]

        cur.execute("SELECT COUNT(*) AS count FROM posts")
        total_posts = cur.fetchone()["count"]

        cur.execute("SELECT COUNT(*) AS count FROM users WHERE is_active = TRUE")
        active_users = cur.fetchone()["count"]

        cur.execute("SELECT COUNT(*) AS count FROM reports WHERE status = 'pending'")
        pending_reports = cur.fetchone()["count"]

    return {
        "total_users": total_users,
        "total_organizations": total_organizations,
        "total_opportunities": total_opportunities,
        "total_applications": total_applications,
        "total_posts": total_posts,
        "active_users": active_users,
        "pending_reports": pending_reports,
    }
