"""
Data access for the `users` table. All queries are parameterized —
never build SQL via string formatting/concatenation.
"""
import threading
import time

from app.database import get_cursor

# --- Short-lived in-memory cache for get_user_by_id -----------------------
# get_current_user runs on nearly every request, and each lookup is a full
# round trip to the database. Caching the row for a few seconds removes that
# trip from most requests. The cache is cleared immediately whenever a user
# is changed through this app (see invalidate_user_cache), so a suspended
# account is blocked right away on this server, not after the cache expires.
_USER_CACHE_TTL_SECONDS = 30.0
_USER_CACHE_MAX_ENTRIES = 1000
_user_cache: dict[str, tuple[float, dict | None]] = {}
_user_cache_lock = threading.Lock()


def invalidate_user_cache(user_id: str | None = None) -> None:
    """Drop one user (or everyone) from the cache."""
    with _user_cache_lock:
        if user_id is None:
            _user_cache.clear()
        else:
            _user_cache.pop(str(user_id), None)


def get_user_by_email(email: str) -> dict | None:
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, name, email, password_hash, role, is_active, created_at "
            "FROM users WHERE email = %s",
            (email,),
        )
        return cur.fetchone()


def get_user_by_id(user_id: str) -> dict | None:
    key = str(user_id)
    now = time.monotonic()
    with _user_cache_lock:
        hit = _user_cache.get(key)
        if hit is not None and now - hit[0] < _USER_CACHE_TTL_SECONDS:
            # Return a copy so callers cannot modify the cached row.
            return dict(hit[1]) if hit[1] is not None else None

    with get_cursor() as cur:
        cur.execute(
            "SELECT id, name, email, password_hash, role, is_active, created_at "
            "FROM users WHERE id = %s",
            (user_id,),
        )
        row = cur.fetchone()

    with _user_cache_lock:
        if len(_user_cache) >= _USER_CACHE_MAX_ENTRIES:
            _user_cache.clear()          # simple bound so memory cannot grow forever
        _user_cache[key] = (now, dict(row) if row is not None else None)
    return row


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
