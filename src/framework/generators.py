from __future__ import annotations

import argparse
import random
import string
import sys
from collections.abc import Callable


def unique_lowercase(length: int) -> str:
    """Nombre unico en minusculas y digitos, de longitud exacta.

    Puramente aleatorio (no se deriva del timestamp): con un componente de reloj
    truncado se corre el riesgo de que dos llamadas en el mismo milisegundo -algo
    común dentro de un mismo loop de parametrizacion- generen el mismo valor sin
    ninguna entropía adicional cuando `length` es menor a la longitud del
    timestamp. No persiste estado entre corridas del proceso de pytest (ver
    "Risks/Trade-offs" en design.md del change que lo introdujo): la colisión
    entre corridas distintas contra el mismo ambiente es un riesgo aceptado, no
    una garantía de repetición dentro de la misma corrida.
    """
    if length < 1:
        raise ValueError("length debe ser >= 1")
    charset = string.ascii_lowercase + string.digits
    return "".join(random.choices(charset, k=length))


GENERATORS: dict[str, Callable[..., str]] = {
    "unique_lowercase": unique_lowercase,
}


def run(name: str, **params) -> str:
    try:
        generator = GENERATORS[name]
    except KeyError:
        raise KeyError(
            f"Generador '{name}' no registrado. Disponibles: {sorted(GENERATORS)}"
        ) from None
    return generator(**params)


def _catalog_markdown() -> str:
    rows = ["| Generador | Descripción |", "|---|---|"]
    for name, func in sorted(GENERATORS.items()):
        doc = (func.__doc__ or "").strip().splitlines()
        summary = doc[0].strip() if doc else ""
        rows.append(f"| `{name}` | {summary} |")
    return "\n".join(rows) + "\n"


def main() -> None:
    # Evita UnicodeEncodeError en consolas Windows sin UTF-8 activo cuando un
    # docstring de generador trae acentos (ver docs/generators-catalog.md).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(prog="python -m framework.generators")
    parser.add_argument(
        "--catalog", action="store_true", help="Imprime el catálogo de generadores en Markdown"
    )
    args = parser.parse_args()
    if args.catalog:
        print(_catalog_markdown(), end="")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
