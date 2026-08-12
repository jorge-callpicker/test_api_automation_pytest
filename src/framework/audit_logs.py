from __future__ import annotations

from collections.abc import Callable

import httpx

from framework.config import Settings


def fetch_audit_logs_page(
    account_id: int,
    page: int = 1,
    *,
    settings: Settings,
    http_client: httpx.Client,
) -> dict:
    response = http_client.get(
        f"{settings.GLB_URL_CHATWOOT}/api/v1/accounts/{account_id}/audit_logs",
        params={"page": page},
        headers={"api_access_token": settings.GLB_TOKEN_CHATWOOT_ADMIN},
    )
    http_client.last_request = response.request
    return response.json()


def find_audit_log(
    account_id: int,
    predicate: Callable[[dict], bool],
    *,
    settings: Settings,
    http_client: httpx.Client,
    page: int = 1,
) -> dict | None:
    body = fetch_audit_logs_page(account_id, page, settings=settings, http_client=http_client)
    for entry in body.get("audit_logs", []):
        if predicate(entry):
            return entry
    return None
