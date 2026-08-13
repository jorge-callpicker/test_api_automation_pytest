from __future__ import annotations

import httpx

from framework.config import Settings

TIMEOUT_SECONDS = 30.0


def client(settings: Settings) -> httpx.Client:
    instance = httpx.Client(base_url=settings.GLB_URL_BASE, timeout=TIMEOUT_SECONDS)
    instance.last_request = None

    def _track_last_request(request: httpx.Request) -> None:
        instance.last_request = request

    instance.event_hooks["request"] = [_track_last_request]
    return instance


def auth_header(access_token: str) -> dict[str, str]:
    return {"api-access-token": access_token}


def to_curl(request: httpx.Request) -> str:
    parts = ["curl", "-X", request.method, f"'{request.url}'"]
    for key, value in request.headers.items():
        parts.append(f"-H '{key}: {value}'")
    if request.content:
        body = request.content.decode("utf-8", errors="replace")
        parts.append(f"-d '{body}'")
    return " ".join(parts)
