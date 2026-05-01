import json
import re
import time

from openai import OpenAI

from app.config import settings
from app.context.db_schema import full_db_context_helper
from app.logger import get_logger

log = get_logger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def nl_to_sql(question: str) -> tuple[str, float]:
    """Convert a natural-language question to a PostgreSQL query string.
    Returns (sql, elapsed_seconds).

    System message is fully static (only full_db_context_helper) so OpenAI
    caches it after the first call. Date arithmetic uses PostgreSQL's built-in
    CURRENT_DATE / CURRENT_TIMESTAMP rather than injecting a date string.
    """
    messages = [
        {"role": "system", "content": full_db_context_helper},
        {"role": "user", "content": question},
    ]

    log.info("LLM request | model=%s | question=%r", settings.llm_model, question)
    log.debug(
        "LLM request payload | messages=%s",
        json.dumps(messages, ensure_ascii=False),
    )

    t0 = time.perf_counter()
    try:
        response = _get_client().chat.completions.create(
            model=settings.llm_model,
            messages=messages, # type: ignore
            temperature=0,
        )
    except Exception:
        log.exception("LLM call failed | model=%s | question=%r", settings.llm_model, question)
        raise

    elapsed = time.perf_counter() - t0
    usage = response.usage
    raw = response.choices[0].message.content.strip() # type: ignore

    if usage:
        ptd = usage.prompt_tokens_details
        ctd = usage.completion_tokens_details
        log.info(
            "LLM tokens | elapsed=%.3fs | "
            "prompt=%d (cached=%d, audio=%d) | "
            "completion=%d (reasoning=%d, audio=%d) | "
            "total=%d",
            elapsed,
            usage.prompt_tokens,
            (ptd.cached_tokens  if ptd else 0) or 0,
            (ptd.audio_tokens   if ptd else 0) or 0,
            usage.completion_tokens,
            (ctd.reasoning_tokens if ctd else 0) or 0,
            (ctd.audio_tokens     if ctd else 0) or 0,
            usage.total_tokens,
        )
    else:
        log.info("LLM tokens | elapsed=%.3fs | usage=unavailable", elapsed)

    log.debug("LLM raw response | content=%r", raw)
    try:
        log.debug("LLM full response object | %s", response.model_dump_json(indent=2))
    except Exception:
        log.debug("LLM full response object | %s", response)

    raw = re.sub(r"^```(?:sql)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)
    sql = raw.strip()

    log.debug("LLM parsed SQL | sql=%r", sql)
    return sql, elapsed
