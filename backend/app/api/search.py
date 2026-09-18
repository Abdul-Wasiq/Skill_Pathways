from fastapi import APIRouter

from app.database import get_cursor

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
def global_search(q: str, limit: int = 10):
    """Search across people, organizations, opportunities, posts, and skills.
    Uses ILIKE for simplicity/portability; a production system would use
    full-text search (tsvector) or an external search index for scale."""
    if not q or not q.strip():
        return {"people": [], "organizations": [], "opportunities": [], "posts": [], "skills": []}

    term = f"%{q.strip()}%"

    with get_cursor() as cur:
        cur.execute(
            "SELECT id, name, role FROM users WHERE name ILIKE %s AND role != 'admin' LIMIT %s",
            (term, limit),
        )
        people = cur.fetchall()

        cur.execute(
            "SELECT id, name, industry, location, is_verified FROM organizations WHERE name ILIKE %s LIMIT %s",
            (term, limit),
        )
        organizations = cur.fetchall()

        cur.execute(
            """
            SELECT op.id, op.title, op.type, op.location, o.name AS organization_name
            FROM opportunities op JOIN organizations o ON o.id = op.organization_id
            WHERE op.status = 'open' AND (op.title ILIKE %s OR op.description ILIKE %s)
            LIMIT %s
            """,
            (term, term, limit),
        )
        opportunities = cur.fetchall()

        cur.execute(
            """
            SELECT p.id, p.content, p.post_type, u.name AS author_name
            FROM posts p JOIN users u ON u.id = p.author_id
            WHERE p.content ILIKE %s LIMIT %s
            """,
            (term, limit),
        )
        posts = cur.fetchall()

        cur.execute("SELECT id, name FROM skills WHERE name ILIKE %s LIMIT %s", (term, limit))
        skills = cur.fetchall()

    return {
        "people": people,
        "organizations": organizations,
        "opportunities": opportunities,
        "posts": posts,
        "skills": skills,
    }
