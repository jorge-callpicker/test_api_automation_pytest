from __future__ import annotations

import email
from email.message import Message

import httpx

from framework.config import Settings

TIMEOUT_SECONDS = 30.0


def client(settings: Settings) -> httpx.Client:
    instance = httpx.Client(base_url=settings.GLB_URL_BASE, timeout=TIMEOUT_SECONDS)
    instance.last_request = None
    instance.last_response = None

    def _track_last_request(request: httpx.Request) -> None:
        # request.content de un body multipart/streaming solo es accesible
        # tras llamar read() -- hay que forzarlo aqui, antes de que el
        # transporte consuma el stream al enviarlo, para que to_curl() pueda
        # leerlo despues (ej. en el reporte de un test fallido).
        request.read()
        instance.last_request = request

    def _track_last_response(response: httpx.Response) -> None:
        # mismo motivo que en _track_last_request: forzar la lectura aqui
        # para que el body siga accesible cuando el reporte lo consuma.
        response.read()
        instance.last_response = response

    instance.event_hooks["request"] = [_track_last_request]
    instance.event_hooks["response"] = [_track_last_response]
    return instance


def _format_multipart(content: bytes, content_type: str) -> list[str]:
    # El multipart de httpx es MIME valido: basta anteponerle su propio
    # Content-Type como si fuera el de un mensaje para que `email` separe
    # las partes por el boundary. Una parte con `filename` es un archivo:
    # nunca se decodifica su contenido (evita tanto un reporte gigante con
    # un archivo de ~100MB como uno ilegible con uno chico -- ver
    # design.md de add-test-create-matriz-c3-header-documento, Decision 3).
    raw = f"Content-Type: {content_type}\r\n\r\n".encode() + content
    message: Message = email.message_from_bytes(raw)
    parts = []
    for part in message.get_payload():
        name = part.get_param("name", header="content-disposition")
        filename = part.get_filename()
        if filename:
            payload = part.get_payload(decode=True) or b""
            parts.append(
                f"--form '{name}=@<archivo omitido del reporte: {filename}, "
                f"{part.get_content_type()}, {len(payload)} bytes>'"
            )
        else:
            value = (part.get_payload(decode=True) or b"").decode("utf-8", errors="replace")
            parts.append(f"--form '{name}=\"{value}\"'")
    return parts


def to_curl(request: httpx.Request) -> str:
    parts = ["curl", "-X", request.method, f"'{request.url}'"]
    for key, value in request.headers.items():
        parts.append(f"-H '{key}: {value}'")
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data") and request.content:
        try:
            parts.extend(_format_multipart(request.content, content_type))
        except Exception:
            parts.append(
                f"-d '<multipart no parseable, {len(request.content)} bytes, "
                f"content-type={content_type}>'"
            )
    elif request.content:
        body = request.content.decode("utf-8", errors="replace")
        parts.append(f"-d '{body}'")
    return " ".join(parts)
