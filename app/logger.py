"""Central logging configuration for fetcherio.

Call setup_logging() once at startup (done in app/main.py).
Every other module just calls get_logger(__name__).

Console  → INFO  (operational summaries, no full LLM prompts) — colourised
File     → DEBUG (full LLM request/response, SQL, etc.)       — plain text
"""
import logging
import logging.handlers
from pathlib import Path

_LOG_DIR = Path(__file__).parent.parent / "logs"

_FMT = "%(asctime)s | %(levelname)-8s | %(name)-35s | %(message)s"
_DATE_FMT = "%Y-%m-%dT%H:%M:%S"

_RESET = "\033[0m"
_LEVEL_COLOURS = {
    logging.DEBUG:    "\033[36m",   # cyan
    logging.INFO:     "\033[32m",   # green
    logging.WARNING:  "\033[33m",   # yellow
    logging.ERROR:    "\033[31m",   # red
    logging.CRITICAL: "\033[1;35m", # bold magenta
}


class _ColourFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        colour = _LEVEL_COLOURS.get(record.levelno, "")
        original = record.levelname
        record.levelname = f"{colour}{original}{_RESET}"
        text = super().format(record)
        record.levelname = original
        return text


def setup_logging() -> None:
    _LOG_DIR.mkdir(exist_ok=True)

    root = logging.getLogger()
    if root.handlers:
        return  # already configured (e.g. re-imported in tests)
    root.setLevel(logging.DEBUG)

    # Console — INFO and above, colourised
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(_ColourFormatter(_FMT, datefmt=_DATE_FMT))
    root.addHandler(ch)

    # Rotating file — DEBUG and above, 5 MB × 3
    fh = logging.handlers.RotatingFileHandler(
        _LOG_DIR / "app.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(_FMT, datefmt=_DATE_FMT))
    root.addHandler(fh)

    # Silence noisy third-party loggers
    for lib in ("httpx", "httpcore", "openai._base_client", "uvicorn.access"):
        logging.getLogger(lib).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
