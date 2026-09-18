"""
Data access for the `users` table. All queries are parameterized —
never build SQL via string formatting/concatenation.
"""
from app.database import get_cursor


def get_user_by_email(email: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, name, email, password_hash, role, is_active, created_at "
            "FROM users WHERE email = %s",
            (email,),
        )
        return cur.fetchone()


def get_user_by_id(user_id: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, name, email, password_hash, role, is_active, created_at "
            "FROM users WHERE id = %s",
            (user_id,),
        )
        return cur.fetchone()


def create_user(name: str, email: str, password_hash: str, role: str) -> dict:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (name, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
            RETURNING id, name, email, role, is_active, created_at
            """,
            (name, email, password_hash, role),
        )
        return cur.fetchone()


def email_exists(email: str) -> bool:
    with get_cursor() as cur:
        cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
        return cur.fetchone() is not None
