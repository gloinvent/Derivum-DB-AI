from fastapi import APIRouter
from pydantic import BaseModel

from app.logger import get_logger
from app.services.nl_to_sql import nl_to_sql
from app.services.query_executor import execute_query, validate_read_only

router = APIRouter()
log = get_logger(__name__)


class QueryRequest(BaseModel):
    question: str


@router.post("/query", include_in_schema=False)
async def run_query(req: QueryRequest):
    log.info("query | question=%r", req.question)

    result: dict = {
        "sql": None,
        "llm_time": 0.0,
        "db_time": 0.0,
        "rows": [],
        "columns": [],
        "row_count": 0,
        "validated": False,
        "error": None,
    }

    try:
        sql, llm_time = nl_to_sql(req.question)
        result["sql"] = sql
        result["llm_time"] = round(llm_time, 3)
    except Exception as exc:
        log.error("query | LLM error | question=%r | error=%s", req.question, exc)
        result["error"] = f"LLM error: {exc}"
        return result

    try:
        validate_read_only(sql)
        result["validated"] = True
    except ValueError as exc:
        log.warning("query | read-only validation failed | sql=%r | reason=%s", sql, exc)
        result["error"] = str(exc)
        return result

    try:
        rows, db_time = execute_query(sql)
        result["db_time"] = round(db_time, 3)
        result["rows"] = rows
        result["row_count"] = len(rows)
        if rows:
            result["columns"] = list(rows[0].keys())
    except Exception as exc:
        log.error("query | DB error | sql=%r | error=%s", sql, exc)
        result["error"] = f"DB error: {exc}"

    log.info(
        "query | done | rows=%d | llm=%.3fs | db=%.3fs | error=%s",
        result["row_count"],
        result["llm_time"],
        result["db_time"],
        result["error"],
    )
    return result
