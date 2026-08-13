## Why

En `reports/report.html`, la columna "Links" ofrece el cURL de la última
request y las aserciones de `pytest-check` fallidas como enlaces a URIs
`data:text/plain;base64,...`. Firefox bloquea la navegación top-level a
URIs `data:` (política de seguridad desde 2019), así que los links no
abren; en Chrome/Brave sí abren pero de forma inconsistente (hay que dar
refresh para ver el contenido). El causante es que `tests/conftest.py`
construye esos extras con `pytest_html.extras.text(...)`, que
`pytest-html` con `--self-contained-html` serializa como URI `data:` en
vez de contenido inline. `pytest-html` sí soporta un formato (`html`) que
inyecta el contenido directamente en la fila expandible del reporte —
sin URIs, sin depender del navegador. Este change es tooling puro sobre
`src/framework/` y `tests/conftest.py` (no sigue la convención
`add-test-<endpoint>-tc-<nnn>` ni `-matriz-<nombre>` porque no implementa
comportamiento de ningún endpoint), análogo a `add-test-framework-base`.

De paso, se aprovecha el cambio en `http.py` para eliminar una fragilidad
ya detectada: hoy cada helper de request debe asignar manualmente
`http_client.last_request = response.request` o el cURL se pierde en
silencio en el reporte (el hook de `conftest.py` simplemente omite el
extra si `last_request` es `None`, sin ningún aviso). Como este change ya
toca `http.py`, se resuelve ahí mismo con un `event_hook` de `httpx` que
captura la última request automáticamente, sin overhead adicional de
otro change.

## What Changes

- `src/framework/http.py`: `client(settings)` inicializa
  `instance.last_request = None` y registra un `event_hooks["request"]`
  que asigna `instance.last_request = request` en cada request enviada
  por el cliente. Elimina la necesidad de que helpers (`auth.py`,
  `audit_logs.py` y los que se agreguen para Call Details/Call Routes)
  asignen `last_request` manualmente tras cada llamada.
- `tests/conftest.py`:
  - Fixture `http_client`: ya no necesita asignar
    `test_client.last_request = None` (queda inicializado en `http.py`).
  - Hook `pytest_runtest_makereport`: reemplaza
    `pytest_html.extras.text(...)` por `pytest_html.extras.html(...)`
    para el cURL de la última request y para las aserciones de
    `pytest-check` fallidas. El contenido se escapa con `html.escape()` y
    se envuelve en `<pre>` (preserva formato, evita romper el DOM del
    reporte con caracteres especiales presentes en respuestas de la API).
  - **BREAKING** (solo para quien lea reportes ya generados): el cURL y
    las aserciones fallidas dejan de aparecer como links en la columna
    "Links" y pasan a mostrarse dentro de la fila expandible del test
    (la misma que hoy muestra el traceback), al hacer click en la fila.
    No afecta reportes ya generados ni el pipeline de reanotación
    (`reannotate.py` lee `resultados.json`, no `report.html`).
  - De paso, corrige `report.extra` (atributo deprecado de `pytest-html`,
    dispara `DeprecationWarning` en cada test fallido) por `report.extras`,
    ya que el hook toca esas mismas líneas.

## Capabilities

Este change no introduce ni modifica ningún contrato observable de un
endpoint bajo prueba — es tooling de framework (reporte HTML y cliente
HTTP interno). Por eso no declara capabilities y el change marca
`skip_specs: true` en su `.openspec.yaml`.

### New Capabilities
(ninguna — tooling puro, sin comportamiento de API)

### Modified Capabilities
(ninguna)

## Impact

- **Código modificado**: `src/framework/http.py`, `tests/conftest.py`.
- **Ningún endpoint, spec, `variables.yaml` o `.env.example` se toca.**
- **Dependencias**: ninguna nueva. Usa `pytest_html.extras.html` y
  `httpx.Client(event_hooks=...)`, ambos ya presentes en el stack
  pinneado (`pytest-html 4.2.0`, `httpx 0.28.1`).
- **Compatibilidad hacia atrás**: los helpers existentes que hoy asignan
  `http_client.last_request` manualmente (si los hubiera) siguen
  funcionando — la asignación explícita simplemente se vuelve redundante,
  no rompe nada.
- **Fuera de alcance**: no se agregan tests de endpoint; no se modifica
  `reannotate.py` ni el mecanismo de `resultados.json`.
