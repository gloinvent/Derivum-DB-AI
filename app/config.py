import os
from dotenv import load_dotenv

load_dotenv()


def _get_required_env(key: str) -> str:
    value = os.getenv(key, "")
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


class Settings:
    openai_api_key: str = _get_required_env("OPENAI_API_KEY")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o")
    db_host: str = _get_required_env("HOST")
    db_port: int = int(os.getenv("PORT", 5432))
    db_name: str = _get_required_env("DATABASE")
    db_user: str = _get_required_env("USER")
    db_password: str = _get_required_env("PASSWORD")
    v1_api_key: str = os.getenv("V1_API_KEY", "")
    v1_plan_tier: str = os.getenv("V1_PLAN_TIER", "pro")


settings = Settings()
