from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    GLB_URL_BASE: str
    GLB_TOKEN_ADMIN: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str


@lru_cache(maxsize=1)
def load_variables() -> dict:
    path = PROJECT_ROOT / "variables.yaml"
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {
        "globals": data.get("globals") or {},
        "test_cases": data.get("test_cases") or {},
    }
