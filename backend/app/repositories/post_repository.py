"""
Data access for posts and their interactions (likes, comments, shares, saves).
"""
from app.database import get_cursor

POST_FIELDS = """
    p.id, p.author_id, p.organization_id, p.content, p.post_type,
    p.linked_opportunity_id, p.created_at, p.updated_at,
    u.name AS author_name, u.role AS author_role,
    org.name AS organization_name,
    (SELECT COUNT(*) FROM post_likes WHERE post_id = p.id) AS like_count,
    (SELECT COUNT(*) FROM post_comments WHERE post_id = p.id) AS comment_count,
    (SELECT COUNT(*) FROM post_shares WHERE post_id = p.id) AS share_count
"""


def create_post(author_id: str, content: str, post_type: str,
                 organization_id: str | None = None,
                 linked_opportunity_id: str | None = None) -> dict:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO posts (author_id, content, post_type, organization_id, linked_opportunity_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (author_id, content, post_type, organization_id, linked_opportunity_id),
        )
        post_id = cur.fetchone()["id"]
    return get_post_by_id(post_id)


def get_post_by_id(post_id: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT {POST_FIELDS}
            FROM posts p
            JOIN users u ON u.id = p.author_id
            LEFT JOIN organizations org ON org.id = p.organization_id
            WHERE p.id = %s
            """,
            (post_id,),
        )
        return cur.fetchone()


def list_posts(limit: int = 30, offset: int = 0, author_id: str | None = None) -> list[dict]:
    query = f"""
        SELECT {POST_FIELDS}
        FROM posts p
        JOIN users u ON u.id = p.author_id
        LEFT JOIN organizations org ON org.id = p.organization_id
    """
    params: list = []
    if author_id:
        query += " WHERE p.author_id = %s"
        params.append(author_id)
    query += " ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def update_post(post_id: str, content: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute(
            "UPDATE posts SET content = %s WHERE id = %s RETURNING id",
            (content, post_id),
        )
        row = cur.fetchone()
    return get_post_by_id(post_id) if row else None


def delete_post(post_id: str) -> None:
    with get_cursor() as cur:
        cur.execute("DELETE FROM posts WHERE id = %s", (post_id,))


def is_post_author(post_id: str, user_id: str) -> bool:
    with get_cursor() as cur:
        cur.execute("SELECT 1 FROM posts WHERE id = %s AND author_id = %s", (post_id, user_id))
        return cur.fetchone() is not None


# --- Likes ---------------------------------------------------------------

def like_post(post_id: str, user_id: str) -> bool:
    """Returns True if a new like was created (for notification purposes)."""
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO post_likes (post_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING RETURNING post_id",
            (post_id, user_id),
        )
        return cur.fetchone() is not None


def unlike_post(post_id: str, user_id: str) -> None:
    with get_cursor() as cur:
        cur.execute("DELETE FROM post_likes WHERE post_id = %s AND user_id = %s", (post_id, user_id))


def user_has_liked(post_id: str, user_id: str) -> bool:
    with get_cursor() as cur:
        cur.execute("SELECT 1 FROM post_likes WHERE post_id = %s AND user_id = %s", (post_id, user_id))
        return cur.fetchone() is not None


# --- Comments --------------------------------------------------------------

def add_comment(post_id: str, author_id: str, content: str) -> dict:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO post_comments (post_id, author_id, content)
            VALUES (%s, %s, %s)
            RETURNING id, post_id, author_id, content, created_at
            """,
            (post_id, author_id, content),
        )
        comment = cur.fetchone()
        cur.execute("SELECT name FROM users WHERE id = %s", (author_id,))
        comment["author_name"] = cur.fetchone()["name"]
        return comment


def list_comments(post_id: str) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT c.id, c.post_id, c.author_id, c.content, c.created_at, u.name AS author_name
            FROM post_comments c
            JOIN users u ON u.id = c.author_id
            WHERE c.post_id = %s
            ORDER BY c.created_at ASC
            """,
            (post_id,),
        )
        return cur.fetchall()


def get_post_author_id_for_comment(comment_id: str) -> str | None:
    with get_cursor() as cur:
        cur.execute(
            "SELECT p.author_id FROM post_comments c JOIN posts p ON p.id = c.post_id WHERE c.id = %s",
            (comment_id,),
        )
        row = cur.fetchone()
        return row["author_id"] if row else None


# --- Shares / Saves ---------------------------------------------------

def share_post(post_id: str, user_id: str) -> bool:
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO post_shares (post_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING RETURNING id",
            (post_id, user_id),
        )
        return cur.fetchone() is not None


def save_post(post_id: str, user_id: str) -> None:
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO saved_posts (post_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (post_id, user_id),
        )


def unsave_post(post_id: str, user_id: str) -> None:
    with get_cursor() as cur:
        cur.execute("DELETE FROM saved_posts WHERE post_id = %s AND user_id = %s", (post_id, user_id))


def list_saved_posts(user_id: str) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT {POST_FIELDS}
            FROM saved_posts sp
            JOIN posts p ON p.id = sp.post_id
            JOIN users u ON u.id = p.author_id
            LEFT JOIN organizations org ON org.id = p.organization_id
            WHERE sp.user_id = %s
            ORDER BY sp.saved_at DESC
            """,
            (user_id,),
        )
        return cur.fetchall()


# --- Reports -----------------------------------------------------------

def create_report(reporter_id: str, target_type: str, target_id: str, reason: str) -> dict:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO reports (reporter_id, target_type, target_id, reason)
            VALUES (%s, %s, %s, %s)
            RETURNING *
            """,
            (reporter_id, target_type, target_id, reason),
        )
        return cur.fetchone()
