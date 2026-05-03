import time

import psycopg2
import psycopg2.extras

from app.config import settings
from app.logger import get_logger
from app.services.sql_validator import validate_read_only  # noqa: F401 — re-exported

log = get_logger(__name__)


def _get_connection():
    return psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        connect_timeout=10,
    )


def execute_query(sql: str) -> tuple[list[dict], float]:
    """Validate and execute sql. Returns (rows, elapsed_seconds)."""
    validate_read_only(sql)

    log.debug("DB execute | sql=%r", sql)

    conn = _get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            t0 = time.perf_counter()
            cur.execute(sql)
            rows = cur.fetchall()
            elapsed = time.perf_counter() - t0

        result = [dict(r) for r in rows]
        log.info("DB result | rows=%d | elapsed=%.3fs", len(result), elapsed)
        return result, elapsed
    except Exception:
        log.exception("DB execute failed | sql=%r", sql[:200])
        raise
    finally:
        conn.close()
