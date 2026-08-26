from __future__ import annotations

import json
from typing import Any

OMIT = "__AUSENTE__"
"""Sentinel para una `deviation` de matriz: la key correspondiente no se emite en el payload."""

_JSON_ARRAY_TYPE = "String (arreglo JSON)"


def build_payload(
    base_request: dict[str, Any],
    deviations: dict[str, Any],
    field_types: dict[str, str],
) -> dict[str, Any]:
    """Construye el payload de un caso de matriz: `base_request` + `deviations` ya resueltas.

    Semántica por campo (ver `openspec/config.yaml` -> "Construcción de la petición"):
    - Un valor igual a `OMIT` omite la key del payload (no se emite, no es `null`).
    - Cualquier otro valor se emite tal cual, salvo que `field_types[campo]` sea
      `"String (arreglo JSON)"` y el valor sea una lista/dict nativo, en cuyo caso se
      serializa con `json.dumps(...)` antes de insertarse (viaja como string, no como
      arreglo JSON nativo). Un valor que ya es `str` para ese mismo campo se inserta
      sin volver a serializar -- es el caso de una celda deliberadamente inválida
      (ej. "no es un arreglo JSON válido"), que no debe convertirse en JSON válido.
    """
    merged = {**base_request, **deviations}

    payload: dict[str, Any] = {}
    for field, value in merged.items():
        if value is OMIT or value == OMIT:
            continue
        if field_types.get(field) == _JSON_ARRAY_TYPE and isinstance(value, (list, dict)):
            payload[field] = json.dumps(value)
        else:
            payload[field] = value
    return payload
