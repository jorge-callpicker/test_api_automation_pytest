from __future__ import annotations

import httpx

from framework.http import to_curl

TOKEN_PATH = "/oauth/token"


def fetch_tokens(
    client: httpx.Client,
    oauth_roles: dict,
    credentials_by_role: dict[str, tuple[str, str]],
) -> dict[str, dict[str, str]]:
    """Emite un access_token por cada (rol, scope) de oauth_roles.

    Llama POST /oauth/token con grant_type=client_credentials por cada scope
    declarado en oauth_roles[rol]["scopes"], usando las credenciales ya
    resueltas y validadas en credentials_by_role. Cualquier respuesta
    distinta de 200 aborta con una excepcion (fail-fast de sesion) - no hay
    degradacion a "rol no disponible" para roles que ya llegaron con
    credenciales completas.
    """
    tokens: dict[str, dict[str, str]] = {}

    for role, role_config in oauth_roles.items():
        client_id, client_secret = credentials_by_role[role]
        tokens[role] = {}

        for scope in role_config.get("scopes", []):
            response = client.post(
                TOKEN_PATH,
                data={
                    "grant_type": "client_credentials",
                    "scope": scope,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
            )

            if response.status_code != 200:
                curl = to_curl(response.request)
                raise RuntimeError(
                    f"POST {TOKEN_PATH} devolvio {response.status_code} para "
                    f"rol='{role}' scope='{scope}'. Body: {response.text}\n"
                    f"cURL equivalente:\n{curl}"
                )

            tokens[role][scope] = response.json()["access_token"]

    return tokens
