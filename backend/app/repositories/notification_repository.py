"""
Data access for notifications.
"""
from app.database import get_cursor

VALID_TYPES = {
    "application_submitted", "application_status_changed", "new_connection_request",
    "connection_accepted", "post_liked", "post_commented", "recommended_opportunity",
    "deadline_approaching", "organization_response", "ai_analysis_completed",
}


def create_notification(user_id: str, notif_type: str, title: str,
                         body: str | None = None, link_url: str | None = None) -> dict:
    if notif_type not in VALID_TYPES:
        raise ValueError(f"Invalid notification type: {notif_type}")
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO notifications (user_id, type, title, body, link_url)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
            """,
            (user_id, notif_type, title, body, link_url),
        )
        return cur.fetchone()


def list_notifications(user_id: str, unread_only: bool = False, limit: int = 50) -> list[dict]:
    query = "SELECT * FROM notifications WHERE user_id = %s"
    params: list = [user_id]
    if unread_only:
        query += " AND is_read = FALSE"
    query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)
    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def mark_read(notification_id: str, user_id: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute(
            "UPDATE notifications SET is_read = TRUE WHERE id = %s AND user_id = %s RETURNING *",
            (notification_id, user_id),
        )
        return cur.fetchone()


def mark_all_read(user_id: str) -> int:
    with get_cursor() as cur:
        cur.execute(
            "UPDATE notifications SET is_read = TRUE WHERE user_id = %s AND is_read = FALSE",
            (user_id,),
        )
        return cur.rowcount


def unread_count(user_id: str) -> int:
    with get_cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS count FROM notifications WHERE user_id = %s AND is_read = FALSE",
            (user_id,),
        )
        return cur.fetchone()["count"]
