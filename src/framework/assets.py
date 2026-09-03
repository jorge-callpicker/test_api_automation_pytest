from __future__ import annotations

from framework.config import PROJECT_ROOT

ASSETS_ROOT = PROJECT_ROOT / "assets"


def load_asset(relative_path: str) -> bytes:
    """Lee bytes de un archivo sembrado bajo `assets/`.

    El proyecto nunca genera ni versiona el contenido de estos archivos
    (ver openspec/config.yaml -> "Ruta 2 - Resolucion en runtime"): los
    coloca el QA siguiendo las tareas de siembra del change. Si falta, el
    error debe apuntar a la variable GLB-* correspondiente en vez de
    propagar un FileNotFoundError generico.
    """
    path = ASSETS_ROOT / relative_path
    if not path.is_file():
        raise FileNotFoundError(
            f"Asset requerido no encontrado: {path}. Sembrar el archivo "
            "descrito en variables.yaml -> globals antes de correr este test."
        )
    return path.read_bytes()
