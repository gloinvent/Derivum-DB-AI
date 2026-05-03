import time
import threading
from collections import defaultdict
from typing import Literal

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.logger import get_logger
from app.services.nl_to_sql import nl_to_sql
from app.services.sql_validator import validate_read_only

router = APIRouter()
log = get_logger(__name__)

_PLAN_ALLOWED_USER_TYPES: dict[str, set[str]] = {
    "free":       {"free"},
    "basic":      {"free", "basic"},
    "pro":        {"free", "basic", "pro"},
    "enterprise": {"free", "basic", "pro", "enterprise"},
}

_RATE_LIMIT = 20
_RATE_WINDOW = 60.0

_rate_store: dict[str, list[float]] = defaultdict(list)
_rate_lock = threading.Lock()


class V1QueryRequest(BaseModel):
    query: str
    user_type: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "Show all PSU AAA bonds maturing in the next 2 years",
                "user_type": "pro",
            }
        }
    }


class V1SuccessResponse(BaseModel):
    status: Literal["success"]
    sql: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "sql": 'SELECT i.isin, e.issuer_name, r.redemption_date FROM "PDB_ebp_records" e JOIN "PDB_isin_records" i ON e.isin_id = i.id JOIN "PDB_redemption" r ON e.isin_id = r.isin_id JOIN "PDB_issuer_organization" io ON e.issuer_name = io.issuer_name WHERE io.issuer_industry = \'PSU\' AND r.redemption_date <= CURRENT_DATE + INTERVAL \'2 YEAR\';',
            }
        }
    }


class V1ErrorResponse(BaseModel):
    status: Literal["error"]
    code: str
    message: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "error",
                "code": "UNAUTHORIZED",
                "message": "API key absent or malformed.",
            }
        }
    }


def _error(status: int, code: str, message: str, headers: dict | None = None) -> JSONResponse:
    log.warning("v1/query | error | status=%d | code=%s | message=%s", status, code, message)
    return JSONResponse(
        status_code=status,
        content={"status": "error", "code": code, "message": message},
        headers=headers,
    )


def _check_rate_limit(key: str) -> JSONResponse | None:
    now = time.time()
    with _rate_lock:
        timestamps = [t for t in _rate_store[key] if now - t < _RATE_WINDOW]
        _rate_store[key] = timestamps
        if len(timestamps) >= _RATE_LIMIT:
            return _error(
                429,
                "RATE_LIMITED",
                "Request volume exceeds the plan's allowed rate.",
                headers={
                    "X-RateLimit-Limit": str(_RATE_LIMIT),
                    "X-RateLimit-Reset": str(int(_RATE_WINDOW)),
                },
            )
        _rate_store[key].append(now)
    return None


@router.post(
    "/v1/query",
    summary="Natural language → SQL",
    description=(
        "Convert a plain-English question about the bond database into a validated "
        "read-only PostgreSQL SELECT query.\n\n"
        "**Auth**: `Authorization: Bearer <V1_API_KEY>`. "
        "Omit entirely when `V1_API_KEY` is not set in `.env` (dev mode).\n\n"
        "**Plan tiers** (`user_type` field): `free` ⊂ `basic` ⊂ `pro` ⊂ `enterprise`. "
        "Omit `user_type` to skip the tier check."
    ),
    tags=["v1"],
    response_model=V1SuccessResponse,
    responses={
        400: {
            "model": V1ErrorResponse,
            "description": "Malformed JSON or missing required field.",
        },
        401: {
            "model": V1ErrorResponse,
            "description": "API key absent, malformed, or revoked.",
        },
        403: {
            "model": V1ErrorResponse,
            "description": "user_type exceeds the plan tier bound to the API key.",
        },
        422: {
            "model": V1ErrorResponse,
            "description": "fetcher.io could not produce valid SQL from the input. Rephrase the query.",
        },
        429: {
            "model": V1ErrorResponse,
            "description": "Request volume exceeds the plan's allowed rate.",
            "headers": {
                "X-RateLimit-Limit": {
                    "description": "Maximum requests allowed per window.",
                    "schema": {"type": "integer", "example": 20},
                },
                "X-RateLimit-Reset": {
                    "description": "Window duration in seconds.",
                    "schema": {"type": "integer", "example": 60},
                },
            },
        },
        500: {
            "model": V1ErrorResponse,
            "description": "Unhandled server-side failure. Retry with exponential backoff.",
        },
    },
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def v1_run_query(
    req: V1QueryRequest,
    authorization: str | None = Header(default=None),
):
    try:
        # 401 — API key
        expected = settings.v1_api_key
        if expected:
            if not authorization or not authorization.startswith("Bearer "):
                return _error(401, "UNAUTHORIZED", "API key absent or malformed.")
            if authorization.removeprefix("Bearer ").strip() != expected:
                return _error(401, "UNAUTHORIZED", "API key absent, malformed, or revoked.")
        token = (authorization or "").removeprefix("Bearer ").strip() or "dev"

        # 429 — rate limit
        if rate_err := _check_rate_limit(token):
            return rate_err

        # 403 — plan tier
        if req.user_type is not None:
            plan = settings.v1_plan_tier
            allowed = _PLAN_ALLOWED_USER_TYPES.get(plan, {"free", "basic"})
            if req.user_type not in allowed:
                return _error(
                    403,
                    "FORBIDDEN",
                    f"user_type '{req.user_type}' exceeds the plan tier bound to the API key.",
                )

        log.info("v1/query | question=%r | user_type=%s", req.query, req.user_type)

        # 422 — NL→SQL conversion
        try:
            sql, _ = nl_to_sql(req.query)
        except Exception as exc:
            log.error("v1/query | LLM error | question=%r | error=%s", req.query, exc)
            return _error(422, "CONVERSION_FAILED", "fetcher.io could not produce valid SQL from the input.")

        try:
            validate_read_only(sql)
        except ValueError:
            log.warning("v1/query | generated non-SELECT SQL | sql=%r", sql)
            return _error(422, "CONVERSION_FAILED", "fetcher.io could not produce valid SQL from the input.")

        log.info("v1/query | success | sql=%r", sql)
        return {"status": "success", "sql": sql}

    except Exception as exc:
        log.exception("v1/query | unhandled error | question=%r | error=%s", req.query, exc)
        return _error(500, "INTERNAL_ERROR", "An unhandled server-side failure occurred.")
