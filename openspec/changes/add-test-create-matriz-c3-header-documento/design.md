## Context

Ver `proposal.md` → "Why" para la motivación. Resumen técnico del estado
actual: `tests/test_matriz_create_c2_header_texto.py` construye el
multipart de cada caso con `files = {field: (None, str(value)) for field,
value in payload.items()}` — toda key viaja como parte de texto, sin
filename. Este change es el primero que necesita una parte real de
archivo (`file` con `type=DOCUMENT`), y ese `(None, str(value))` no sirve
para eso: la parte de archivo necesita `(filename, bytes, content_type)`.

`src/framework/matrix.build_payload` no distingue el campo `File` de
cualquier otro — hoy lo deja pasar tal cual (rama `else` de su `for`).
`src/framework/http.to_curl` decodifica `request.content` completo como
UTF-8 para el reporte HTML, sin límite de tamaño.

## Goals / Non-Goals

**Goals:**
- Que un test de matriz pueda enviar una parte de archivo real dentro de
  un `files=` de httpx, con su contenido leído desde disco.
- Que el contenido de esos archivos lo aporte el QA (assets sembrados),
  nunca el proyecto — ver "Arquitectura objetivo" en `proposal.md`.
- Que el reporte HTML no se degrade (ilegible o desproporcionadamente
  grande) cuando el body de una petición incluye un archivo binario.
- Que lo construido aquí sea reutilizable sin cambios por
  `c4-header-imagen` y `c5-header-video` (mismo patrón `file` +
  `type` condicional, solo cambia el tipo de contenido esperado).

**Non-Goals:**
- No se resuelve el timeout de 30s del cliente HTTP compartido a nivel de
  framework — se usa el override por-request de httpx en los dos casos que
  lo necesitan (`V2`, `I3`), sin tocar `http.client()`.
- No se implementa un parser real de multipart para el reporte — el fix de
  `to_curl` es un guard genérico por tamaño, no una reconstrucción fiel del
  cuerpo.
- No se cubre `c4`/`c5`/`c6`/`buttons*`/`cruzada` — quedan como changes
  hermanos futuros que reutilizarán estas piezas.

## Decisions

### 1. Nuevo módulo `src/framework/assets.py`, no ampliar `matrix.py`

`matrix.build_payload` es puro (dict + dict → dict, sin I/O). Leer bytes de
disco es una responsabilidad distinta (I/O, puede fallar por archivo
faltante). Separar evita que `matrix.py` — usado por autoría/análisis
offline del CSV, ver `openspec/config.yaml` — dependa de que el
filesystem de `assets/` exista.

```python
# src/framework/assets.py
from pathlib import Path
from framework.config import PROJECT_ROOT

ASSETS_ROOT = PROJECT_ROOT / "assets"

def load_asset(relative_path: str) -> bytes:
    path = ASSETS_ROOT / relative_path
    if not path.is_file():
        raise FileNotFoundError(
            f"Asset requerido no encontrado: {path}. Sembrar el archivo "
            "descrito en variables.yaml -> globals antes de correr este test."
        )
    return path.read_bytes()
```

Alternativa descartada: meter la lectura de disco dentro de
`variables.resolve()` cuando el nombre de variable empieza con
`GLB-create-file-`. Se descarta porque `resolve()` es agnóstico del tipo
de dato de la variable (hoy solo interpola/pasa el valor tal cual) y
mezclar I/O ahí acoplaría el resolutor genérico a una convención de un
solo endpoint.

### 2. Dispatch por `File` vive en el test, no en `matrix.build_payload`

`build_payload` sigue devolviendo el valor crudo del campo `file` (la ruta
relativa, ya resuelta desde `{{GLB-create-file-*}}`). La conversión a
tupla `(filename, bytes, content_type)` ocurre al armar el `files=` del
`http_client.post(...)`, igual que hoy la conversión `(None, str(value))`
ocurre ahí y no dentro de `build_payload`:

```python
import mimetypes
from pathlib import Path
from framework.assets import load_asset

def _build_files(payload: dict, field_types: dict) -> dict:
    files = {}
    for field, value in payload.items():
        if field_types.get(field) == "File":
            content_type, _ = mimetypes.guess_type(value)
            files[field] = (
                Path(value).name,
                load_asset(value),
                content_type or "application/octet-stream",
            )
        else:
            files[field] = (None, str(value))
    return files
```

`mimetypes.guess_type` infiere el `content_type` de la extensión del
archivo sembrado — resuelve también `I2` (tipo no permitido) sin
declaración aparte: si el QA nombra ese asset `tipo_invalido.jpg`,
`mimetypes` ya infiere `image/jpeg`.

Alternativa descartada: declarar `content_type` explícito por variable
(`GLB-create-file-*` como dict `{path, content_type}` en vez de string).
Se descarta por innecesaria — ningún caso de este CSV requiere un
`content_type` que contradiga la extensión real del archivo.

### 3. Guard de tamaño en `to_curl`, no parser de multipart

```python
_MAX_CURL_BODY_BYTES = 2 * 1024 * 1024  # 2MB

def to_curl(request: httpx.Request) -> str:
    parts = ["curl", "-X", request.method, f"'{request.url}'"]
    for key, value in request.headers.items():
        parts.append(f"-H '{key}: {value}'")
    if request.content:
        if len(request.content) > _MAX_CURL_BODY_BYTES:
            parts.append(
                f"-d '<body omitido en reporte: {len(request.content)} bytes, "
                f"content-type={request.headers.get('content-type', '?')}>'"
            )
        else:
            body = request.content.decode("utf-8", errors="replace")
            parts.append(f"-d '{body}'")
    return " ".join(parts)
```

Genérico: protege cualquier body futuro que exceda el umbral, no solo
archivos. Alternativa descartada: parsear el multipart para mostrar cada
parte de texto real y solo omitir la parte de archivo. Se descarta por
complejidad — `httpx` no expone las partes ya separadas post-envío, habría
que re-parsear el `Content-Type: multipart/form-data; boundary=...` a
mano, y el valor para el QA de ver el cURL exacto de un caso con archivo
de 100MB es marginal frente al costo de mantenimiento.

### 4. Política: campos `File` siempre por Ruta 3 (sembrada)

Documentado en `proposal.md` → "Why". Se añade como aclaración textual en
`openspec/config.yaml`, sección "Ruta 2 — Resolución en runtime", para que
quede explícito que el disparador de Volumen no aplica a campos `File`:
el contenido de un archivo nunca lo genera el modelo ni en frío
(estática) ni en caliente (runtime), siempre lo aporta el QA.

## Risks / Trade-offs

- **QA olvida sembrar uno de los 4 archivos** → `load_asset` falla con
  `FileNotFoundError` y mensaje explícito señalando la ruta y la variable
  `GLB-*` correspondiente, en vez de un error genérico de `httpx` o un
  `400` inesperado que se confundiría con hallazgo del endpoint.
- **Archivo de ~100MB (`V2`, `I3`) excede el timeout de 30s del cliente
  compartido** → override de `timeout=` por-request en esos dos casos
  únicamente; no se cambia `http.client()`.
- **`_track_last_request`/`_track_last_response` en `http.py` fuerzan
  `.read()` sobre el request/response completo** (para que `to_curl` y el
  reporte tengan el body disponible después) → con un archivo de 100MB
  esto ya implica tenerlo completo en memoria durante la corrida de ese
  caso puntual; aceptado como costo de una corrida manual y local, no de
  CI.
- **`assets/` vacío en un checkout nuevo** → la carpeta se versiona con
  `.gitkeep` para que la ruta exista; el contenido real depende de que el
  QA la siembre siguiendo `tasks.md`. Sin eso, `V1`/`V2`/`I2`/`I3` fallan
  con el mensaje explícito del Decision 1, no con un error ambiguo.
