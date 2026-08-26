## Why

Hoy `pytest-html` y `pytest-json-report` escriben siempre a
`reports/report.html` y `reports/resultados.json`, así que cada ejecución
sobrescribe la anterior y el QA pierde el reporte de la corrida previa. Además
el hook de `tests/conftest.py` (`pytest_runtest_makereport`) solo adjunta el
cURL de la última request cuando el test **falla** — en los casos `Success`
no queda registro del cURL ni de la respuesta recibida, lo que dificulta
auditar manualmente el assert de espejo entrada→respuesta o mostrar evidencia
de un caso que pasó.

## What Changes

- `src/framework/http.py`: el cliente httpx trackea también la última
  `Response` (`instance.last_response`), vía un event hook de respuesta
  análogo al que ya existe para `last_request`.
- `tests/conftest.py`:
  - Nuevo hook `pytest_configure` que crea `reports/<YYYYMMDD-HHMMSS>/` al
    iniciar la sesión de pytest (timestamp de inicio del proceso, no por
    test) y redirige ahí `--html` y `--json-report-file` cuando el QA no los
    especifica explícitamente en la línea de comandos.
  - `pytest_runtest_makereport` deja de filtrar `not report.failed`: para
    **todos** los outcomes (`passed`, `failed`, `skipped`) adjunta el cURL de
    la última request. Además, para todos los outcomes que tengan una
    `last_response` disponible, adjunta status code, headers y body de la
    respuesta.
- `.gitignore`: cambia `reports/*.html` / `reports/*.json` por un patrón que
  ignore el contenido de las subcarpetas por timestamp (`reports/*/`),
  preservando el sidecar de matriz si se decide conservarlo fuera de esas
  subcarpetas (ver Impact).
- Documentación (`README.md`, `CLAUDE.md`, `openspec/config.yaml`): se
  actualizan los comandos de ejecución sugeridos al QA para ya no pasar
  `--html=reports/report.html --json-report-file=reports/resultados.json`
  explícitos (el hook los resuelve solo), y los ejemplos de
  `reannotate.py --results ...` pasan a referenciar la carpeta con
  timestamp de la corrida.

## Capabilities

### New Capabilities
- `test-reporting`: comportamiento de generación de reportes de ejecución —
  una carpeta nueva por corrida bajo `reports/`, y contenido de reporte por
  caso (cURL siempre; status/headers/body de la respuesta en éxito y en
  fallo cuando haya una response disponible).

### Modified Capabilities

(ninguna — no existe todavía una capability de reporting en
`openspec/specs/`; `create` no cambia sus requerimientos)

## Impact

- **Código**: `src/framework/http.py`, `tests/conftest.py`.
- **Config**: `.gitignore`.
- **Documentación**: `README.md`, `CLAUDE.md` (sección "Ejecución"),
  `openspec/config.yaml` (sección "Reporte y trazabilidad" del contexto).
- **Sidecar de matriz** (`reports/anotado-<nombre>.csv`, producido por
  `reannotate.py`): sigue siendo responsabilidad del QA generarlo a mano
  (ver "Arquitectura objetivo" en `openspec/config.yaml` —
  `reannotate.py` no implementa el contrato de matriz todavía). Este
  change no toca `reannotate.py`; solo actualiza el ejemplo de comando para
  apuntar a la carpeta con timestamp donde ahora vive `resultados.json`.
- **Compatibilidad**: si el QA sigue pasando `--html`/`--json-report-file`
  explícitos en su comando, esos valores prevalecen sobre el path calculado
  por el hook (no se fuerza sobreescritura de flags explícitos).
- Sin cambios en `variables.yaml`, `inputs/`, ni en la lógica de matriz
  (`matrix.py`, `generators.py`, `mirror.py`).
