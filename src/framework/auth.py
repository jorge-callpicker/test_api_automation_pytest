from __future__ import annotations

from typing import NamedTuple

import httpx

from framework.config import Settings, load_variables

_ROLE_CREDENTIALS: dict[str, tuple[str, str]] = {
    "SuperAdmin": ("USR_SADMIN", "PSW_SADMIN"),
    "Admin": ("USR_ADMIN", "PSW_ADMIN"),
}


class SessionTokens(NamedTuple):
    api_token: str
    api_access_token: str


def _credentials_for_role(role: str, settings: Settings) -> tuple[str, str]:
    try:
        username_attr, password_attr = _ROLE_CREDENTIALS[role]
    except KeyError:
        raise ValueError(
            f"Rol '{role}' no soportado. Roles disponibles: {sorted(_ROLE_CREDENTIALS)}"
        ) from None
    return getattr(settings, username_attr), getattr(settings, password_attr)


def obtain_session_tokens(
    role: str,
    *,
    settings: Settings,
    http_client: httpx.Client,
    account_id: int | None = None,
) -> SessionTokens:
    username, password = _credentials_for_role(role, settings)

    globals_ = load_variables()["globals"]
    url_cp_api = globals_["GLB-url_cp_api"]
    path_login = globals_["GLB-path_login"]
    path_select_account = globals_["GLB-path_select_account"]
    if account_id is None:
        account_id = globals_["GLB-account_id_valido"]

    login_response = http_client.post(
        f"{url_cp_api}{path_login}",
        json={"username": username, "password": password},
    )
    http_client.last_request = login_response.request
    assert login_response.status_code == 200, (
        f"Login falló para rol '{role}': status={login_response.status_code} "
        f"body={login_response.text}"
    )
    api_token = login_response.json()["payload"]["api_token"]

    select_account_response = http_client.get(
        f"{url_cp_api}{path_select_account.format(account_id=account_id)}",
        headers={"api_access_token": api_token},
    )
    http_client.last_request = select_account_response.request
    assert select_account_response.status_code == 200, (
        f"selectAccount falló para rol '{role}' y account_id={account_id}: "
        f"status={select_account_response.status_code} "
        f"body={select_account_response.text}"
    )
    api_access_token = select_account_response.json()["payload"]["api_key"]

    return SessionTokens(api_token=api_token, api_access_token=api_access_token)
