"""
PostgreSQL connection management via psycopg2, using a threaded
connection pool so FastAPI's async request handlers don't each open
a brand new connection.

All queries elsewhere in the app MUST use parameterized queries
(the %s placeholder style psycopg2 provides) — never string-format
SQL. See repositories/ for examples.
"""
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from psycopg2 import pool

from app.config import settings

_pool: pool.ThreadedConnectionPool | None = None


def init_pool(minconn: int = 1, maxconn: int | None = None) -> None:
    global _pool
    if _pool is not None:
        return
    _pool = psycopg2.pool.ThreadedConnectionPool(
        minconn,
        maxconn or settings.DATABASE_POOL_MAX,
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        dbname=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD,
        sslmode=settings.DATABASE_SSLMODE,
        # Keep idle connections alive so Neon's proxy doesn't silently drop them.
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5,
    )


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


@contextmanager
def get_connection():
    """Borrow a connection from the pool; commit on success, rollback on error."""
    if _pool is None:
        init_pool()
    conn = _pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)


@contextmanager
def get_cursor(dict_cursor: bool = True):
    """Borrow a connection and yield a cursor. Rows come back as dicts by default."""
    with get_connection() as conn:
        cursor_factory = psycopg2.extras.RealDictCursor if dict_cursor else None
        cur = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cur
        finally:
            cur.close()
