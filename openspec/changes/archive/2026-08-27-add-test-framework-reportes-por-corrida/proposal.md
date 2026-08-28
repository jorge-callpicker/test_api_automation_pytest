## Why

Hoy `reports/report.html` y `reports/resultados.json` se sobrescriben en
cada corrida porque el QA pasa rutas fijas por CLI, perdiendo la evidencia
de ejecuciones anteriores. Además, el hook de reporte en `tests/conftest.py`
solo adjunta el cURL cuando el caso falla — los casos "Success" (incluidas
las filas `V1..Vn` de una matriz) no dejan rastro de la petición ni de la
respuesta recibida, dificultando auditar qué se envió y qué contestó el
endpoint cuando todo pasó.

Este es un change de infraestructura (`src/framework/` y
`tests/conftest.py`): no sigue el patrón `add-test-<endpoint>-tc-<nnn>` ni
`add-test-<endpoint>-matriz-<nombre>`, ya que no implementa casos de un
endpoint sino que modifica el framework de reportes reutilizado por todos.

## What Changes

- Cada ejecución de pytest crea automáticamente una carpeta nueva
  `reports/<YYYYMMDD_HHMMSS>/` (calculada una sola vez en `pytest_configure`)
  y sobrescribe `config.option.htmlpath` (pytest-html) y la ruta de
  `pytest-json-report` para apuntar dentro de esa carpeta, aunque el QA no
  pase `--html=`/`--json-report-file=` explícitamente. Los comandos
  documentados en `CLAUDE.md`/`README.md` se simplifican para ya no llevar
  esos flags.
- `src/framework/http.py`: se agrega un segundo event hook de `httpx` para
  trackear `last_response` en el cliente, igual que ya existe
  `last_request`.
- `tests/conftest.py`: el hook `pytest_runtest_makereport` deja de
  filtrar solo `report.failed` — corre para cualquier resultado
  (`passed` o `failed`), adjuntando al HTML el cURL de la última request
  (comportamiento ya existente, ahora extendido a éxito) más un bloque
  nuevo con el status y el body de la última respuesta. **El bloque de
  respuesta no distingue por resultado**: aparece tanto en casos
  exitosos como fallidos, verificado y solicitado explícitamente por el
  QA tras probar el change contra un ambiente sustituto.
- **Sin redacción de headers ni truncado de body**: por decisión explícita
  del QA, el cURL se embebe con sus headers tal cual (incluye
  `Authorization` con el token) y el body de la respuesta se embebe
  completo, sin límite de tamaño. Si esto genera un problema operativo
  (reportes pesados, exposición de tokens) se atiende como change
  independiente en el futuro.
- No hay política de retención/limpieza de carpetas `reports/<timestamp>/`
  antiguas; su administración queda a cargo del QA.

## Capabilities

### New Capabilities
- `test-reporting`: comportamiento observable de la generación de reportes
  de ejecución (una carpeta nueva por corrida, evidencia de cURL+response
  en casos exitosos).

### Modified Capabilities
(ninguna — no existen specs previas de esta capability)

## Impact

- `tests/conftest.py`: nuevo `pytest_configure` hook (o extensión del
  existente) + relajación de la condición de `pytest_runtest_makereport`.
- `src/framework/http.py`: nuevo tracking de `last_response` sobre el
  cliente `httpx.Client`.
- `CLAUDE.md` y `README.md`: actualizar los comandos de ejecución
  documentados para reflejar que ya no se pasan `--html=`/
  `--json-report-file=` manualmente.
- Ningún test de endpoint existente se modifica; el cambio es transversal
  y no afecta `variables.yaml`, `inputs/` ni matrices/TCs ya archivados.
- No introduce dependencias nuevas (usa las ya pinneadas: `pytest-html`,
  `pytest-json-report`, `httpx`).
