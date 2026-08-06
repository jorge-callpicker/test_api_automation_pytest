from __future__ import annotations

import httpx

from framework.config import Settings

TIMEOUT_SECONDS = 30.0


def client(settings: Settings) -> httpx.Client:
    return httpx.Client(base_url=settings.GLB_URL_BASE, timeout=TIMEOUT_SECONDS)


def to_curl(request: httpx.Request) -> str:
    parts = ["curl", "-X", request.method, f"'{request.url}'"]
    for key, value in request.headers.items():
        parts.append(f"-H '{key}: {value}'")
    if request.content:
        body = request.content.decode("utf-8", errors="replace")
        parts.append(f"-d '{body}'")
    return " ".join(parts)
