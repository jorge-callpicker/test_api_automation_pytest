from __future__ import annotations

from collections.abc import Callable
from typing import Any


def step(
    log: list[dict[str, Any]], label: str, check_fn: Callable[..., bool], *args: Any, **kwargs: Any
) -> bool:
    """Ejecuta una aserción de `pytest_check` y registra su resultado en `log`.

    Cada función de `pytest_check` (`check.equal`, `check.is_true`, ...) sigue
    la convención `check_fn(*valores, msg: str = "")` y retorna un bool
    indicando si pasó, sin dejar registro propio de los checks exitosos. Este
    helper llama a `check_fn` (preservando su comportamiento de soft assert),
    captura ese bool, y anota `(label, ok, detail)` en `log` para que el
    reporte documente la aserción sin importar su resultado.
    """
    ok = check_fn(*args, **kwargs)
    detail = kwargs.get("msg")
    if detail is None and args and isinstance(args[-1], str):
        detail = args[-1]
    log.append({"label": label, "ok": bool(ok), "detail": detail or ""})
    return ok
