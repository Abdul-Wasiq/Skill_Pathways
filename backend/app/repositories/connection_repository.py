"""
Data access for the connections (networking) system.
"""
from app.database import get_cursor


def send_request(requester_id: str, addressee_id: str) -> dict:
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO connections (requester_id, addressee_id, status)
            VALUES (%s, %s, 'pending')
            RETURNING *
            """,
            (requester_id, addressee_id),
        )
        return cur.fetchone()


def get_connection_between(user_a: str, user_b: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT * FROM connections
            WHERE (requester_id = %s AND addressee_id = %s)
               OR (requester_id = %s AND addressee_id = %s)
            """,
            (user_a, user_b, user_b, user_a),
        )
        return cur.fetchone()


def get_connection_by_id(connection_id: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM connections WHERE id = %s", (connection_id,))
        return cur.fetchone()


def update_status(connection_id: str, status: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute(
            "UPDATE connections SET status = %s WHERE id = %s RETURNING *",
            (status, connection_id),
        )
        return cur.fetchone()


def delete_connection(connection_id: str) -> None:
    with get_cursor() as cur:
        cur.execute("DELETE FROM connections WHERE id = %s", (connection_id,))


def list_connections(user_id: str, status: str = "accepted") -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT c.*, 
                   CASE WHEN c.requester_id = %s THEN c.addressee_id ELSE c.requester_id END AS other_user_id,
                   u.name AS other_user_name, u.role AS other_user_role
            FROM connections c
            JOIN users u ON u.id = (CASE WHEN c.requester_id = %s THEN c.addressee_id ELSE c.requester_id END)
            WHERE (c.requester_id = %s OR c.addressee_id = %s) AND c.status = %s
            ORDER BY c.updated_at DESC
            """,
            (user_id, user_id, user_id, user_id, status),
        )
        return cur.fetchall()


def list_pending_incoming(user_id: str) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT c.*, u.name AS requester_name, u.role AS requester_role
            FROM connections c
            JOIN users u ON u.id = c.requester_id
            WHERE c.addressee_id = %s AND c.status = 'pending'
            ORDER BY c.created_at DESC
            """,
            (user_id,),
        )
        return cur.fetchall()
