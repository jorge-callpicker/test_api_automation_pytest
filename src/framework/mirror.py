from __future__ import annotations

from typing import Any


def assert_mirror(
    check: Any,
    request_payload: dict[str, Any],
    response_json: dict[str, Any],
    mirror_keys: list[str],
) -> None:
    """Assert de espejo entrada->respuesta, solo por key JSON exacta (nunca substring).

    Se invoca únicamente para casos de éxito (`status < 400`, incluye `206`) -- el
    caller es responsable de ese filtro, esta función no recibe el status code.
    `mirror_keys` la declara el test (transcrita de `## Mirror keys en respuesta` de
    `docs.md`), no se calcula parseando el markdown en runtime.
    """
    for key in mirror_keys:
        if key not in request_payload or key not in response_json:
            continue
        check.equal(
            response_json[key],
            request_payload[key],
            f"Mirror key '{key}': request={request_payload[key]!r} "
            f"response={response_json[key]!r}",
        )
