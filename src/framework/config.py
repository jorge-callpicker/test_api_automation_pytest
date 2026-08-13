from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow", case_sensitive=True)

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


def _role_env_slug(role: str) -> str:
    return role.upper().replace("-", "_")


def role_credentials(settings: Settings, role: str) -> tuple[str, str]:
    """Resuelve (client_id, client_secret) para un rol de GLB-oauth_roles.

    Solo se llama para roles ya presentes en `GLB-oauth_roles` — un rol
    listado ahi es obligatorio, asi que falta de credenciales es un error de
    configuracion, no un caso a tolerar en silencio.
    """
    slug = _role_env_slug(role)
    client_id_name = f"GLB_CLIENT_ID_{slug}"
    client_secret_name = f"GLB_CLIENT_SECRET_{slug}"

    client_id = getattr(settings, client_id_name, None)
    client_secret = getattr(settings, client_secret_name, None)

    for name, value in ((client_id_name, client_id), (client_secret_name, client_secret)):
        if not value or str(value).startswith("[REQUIERE RESPUESTA"):
            raise RuntimeError(
                f"El rol '{role}' esta en GLB-oauth_roles pero falta "
                f"'{name}' en .env (o quedo con el placeholder sin llenar)."
            )

    return client_id, client_secret
