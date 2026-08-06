from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from framework.config import Settings, load_variables

_PLACEHOLDER_RE = re.compile(r"\{\{([A-Za-z0-9_-]+)\}\}")
_FULL_PLACEHOLDER_RE = re.compile(r"^\{\{([A-Za-z0-9_-]+)\}\}$")


@lru_cache(maxsize=1)
def _default_settings() -> Settings:
    return Settings()


def _braces(name: str) -> str:
    return "{{" + name + "}}"


def _env_attr_name(name: str) -> str:
    return name.upper().replace("-", "_")


def _tc_prefix(name: str) -> str:
    parts = name.split("-")
    return "-".join(parts[:2])


def _resolve_name(name: str, tc_id: str, settings: Settings, variables: dict) -> Any:
    if name.startswith("GLB-"):
        attr = _env_attr_name(name)
        if hasattr(settings, attr):
            return getattr(settings, attr)
        globals_ = variables.get("globals", {})
        if name in globals_:
            return globals_[name]
        raise KeyError(
            f"Variable global '{_braces(name)}' no encontrada en Settings ni en "
            "variables.yaml -> globals"
        )

    if name.startswith("TC-"):
        prefix = _tc_prefix(name)
        if prefix != tc_id:
            raise KeyError(
                f"Variable '{_braces(name)}' pertenece a '{prefix}' pero se intento "
                f"resolver para tc_id='{tc_id}'"
            )
        tc_vars = variables.get("test_cases", {}).get(tc_id, {}).get("variables", {})
        if name not in tc_vars:
            raise KeyError(
                f"Variable '{_braces(name)}' no encontrada en variables.yaml -> "
                f"test_cases.{tc_id}.variables"
            )
        return tc_vars[name]

    raise KeyError(
        f"Variable '{_braces(name)}' no tiene un prefijo reconocido "
        "(se esperaba 'GLB-' o 'TC-XXX-')"
    )


def _interpolate_str(value: str, tc_id: str, settings: Settings, variables: dict) -> Any:
    full_match = _FULL_PLACEHOLDER_RE.match(value)
    if full_match:
        return _resolve_name(full_match.group(1), tc_id, settings, variables)
    return _PLACEHOLDER_RE.sub(
        lambda m: str(_resolve_name(m.group(1), tc_id, settings, variables)),
        value,
    )


def resolve(
    payload: Any,
    tc_id: str,
    *,
    settings: Settings | None = None,
    variables: dict | None = None,
) -> Any:
    settings = settings if settings is not None else _default_settings()
    variables = variables if variables is not None else load_variables()

    if isinstance(payload, str):
        return _interpolate_str(payload, tc_id, settings, variables)
    if isinstance(payload, dict):
        return {
            key: resolve(value, tc_id, settings=settings, variables=variables)
            for key, value in payload.items()
        }
    if isinstance(payload, list):
        return [resolve(item, tc_id, settings=settings, variables=variables) for item in payload]
    return payload
