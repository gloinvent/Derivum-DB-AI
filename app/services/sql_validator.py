import re

from app.logger import get_logger

log = get_logger(__name__)

_WRITE_PATTERN = re.compile(
    r"""
    \b(
        INSERT | UPDATE | DELETE | TRUNCATE | DROP   | CREATE  |
        ALTER  | REPLACE | UPSERT | MERGE   | GRANT  | REVOKE  |
        COPY   | VACUUM  | REINDEX | CLUSTER | COMMENT | LOCK
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)


def validate_read_only(sql: str) -> None:
    """Raise ValueError if sql contains any write/DDL operation."""
    stripped = sql.strip()
    match = _WRITE_PATTERN.search(stripped)
    if match:
        log.warning(
            "validate_read_only: rejected write operation '%s' | sql=%r",
            match.group(0).upper(),
            stripped[:200],
        )
        raise ValueError(f"Query contains a disallowed operation: {match.group(0).upper()}")
