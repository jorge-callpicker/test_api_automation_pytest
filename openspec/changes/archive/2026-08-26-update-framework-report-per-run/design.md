## Context

Ver `proposal.md` § Why. Hoy `--html` y `--json-report-file` son flags fijos
que el QA pasa en la línea de comandos (`reports/report.html`,
`reports/resultados.json`); `tests/conftest.py` ya tiene un hook
`pytest_runtest_makereport` que adjunta cURL solo en `failed`, y
`src/framework/http.py` ya trackea `instance.last_request` vía un event hook
de httpx, pero no existe tracking de la respuesta.

## Goals / Non-Goals

**Goals**
- Cada sesión de pytest escribe su reporte en una carpeta propia, sin
  sobrescribir la de una sesión anterior.
- El comando que se le sugiere al QA no necesita construir el path a mano
  (ni con `date` de bash ni con `Get-Date` de PowerShell).
- El extra de cURL + respuesta aparece en success y en failure por igual.

**Non-Goals**
- No se reescribe `reannotate.py` ni se implementa el contrato de matriz
  para el sidecar (`reports/anotado-<nombre>.csv`) — sigue fuera de alcance,
  documentado como pendiente en `openspec/config.yaml`.
- No se atribuye request/response a nivel de aserción individual dentro de
  un test que hace varias llamadas HTTP: igual que hoy, `last_request` (y
  el nuevo `last_response`) reflejan solo la **última** llamada del cliente
  antes de que termine el test. No se agrega un log de todas las llamadas.
- No se trunca ni resume el body de la respuesta — se confía en que
  `pytest-html --self-contained-html` sigue siendo manejable para los
  tamaños de payload de este proyecto (bodies de API REST, no archivos).
- No se implementa rotación/limpieza automática de carpetas viejas bajo
  `reports/`; la retención sigue siendo manual (ya es git-ignored).

## Decisions

### 1. Carpeta por timestamp calculada en `pytest_configure`, no en el comando del QA

Se agrega a `tests/conftest.py` un hook `pytest_configure(config)` marcado
`@pytest.hookimpl(tryfirst=True)` (para correr antes que el propio
`pytest_configure` de `pytest-html`, que ya lee `config.option.htmlpath` al
inicializarse). El hook:

1. Calcula `run_dir = Path("reports") / datetime.now().strftime("%Y%m%d-%H%M%S")`.
2. Si `config.option.htmlpath` es `None` (el QA no pasó `--html`), lo fija a
   `run_dir / "report.html"` y crea `run_dir` con `mkdir(parents=True)`.
3. `pytest-json-report` no usa `None` como default de `--json-report-file`
   sino el literal `.report.json`. Si `config.option.json_report_file` es
   `None` **o** ese literal (el QA no lo pasó explícito), lo fija a
   `run_dir / "resultados.json"` (misma `run_dir`; si `htmlpath` ya fue
   seteado explícito por el QA, `run_dir` igual se crea a partir del
   timestamp para el JSON). Trade-off aceptado: un QA que pase
   `--json-report-file=.report.json` a propósito (mismo valor que el
   default) también sería redirigido — caso de borde documentado, no
   bloqueante.
4. Si el QA pasó cualquiera de los dos flags explícitamente, ese valor no se
   toca — se respeta como override manual.

**Alternativa descartada**: construir el path en el comando sugerido (ej.
`--html=reports/$(date +%Y%m%d-%H%M%S)/report.html`). Se descarta porque el
comando lo copia el QA entre bash y PowerShell indistintamente (ver
`CLAUDE.md`), y la sintaxis de timestamp difiere entre ambos — es una fuente
de errores de copy-paste que un hook de Python evita por completo.

**Alternativa descartada**: un plugin de pytest separado
(`src/framework/report_plugin.py`) registrado vía `pytest11` entry point.
Se descarta por sobre-ingeniería: el hook cabe en unas pocas líneas dentro
del `conftest.py` que ya existe, y no hay necesidad de distribuirlo fuera de
este repo.

### 2. Tracking de response con un event hook de httpx, simétrico a `last_request`

`src/framework/http.py` agrega `instance.last_response = None` y un segundo
event hook:

```python
def _track_last_response(response: httpx.Response) -> None:
    response.read()
    instance.last_response = response

instance.event_hooks["response"] = [_track_last_response]
```

`response.read()` se llama defensivamente por la misma razón que ya está
comentada para `_track_last_request`: garantizar que el body sea accesible
después, aunque con el uso no-streaming por defecto del cliente ya suele
estar leído.

**Alternativa descartada**: envolver `http_client.request()`/`.send()` con
un wrapper que capture request/response en el punto de la llamada, en vez
de event hooks. Se descarta porque el patrón de event hooks ya existe para
`last_request` — mantener el mismo mecanismo para `last_response` es más
consistente y no requiere tocar cómo los tests invocan el cliente.

### 3. `pytest_runtest_makereport` deja de filtrar por `failed`, agrega bloque de respuesta

Se quita `if report.when != "call" or not report.failed: return` y se
reemplaza por `if report.when != "call": return` (se sigue evaluando una
sola vez por test, en la fase `call`, sin importar el outcome). El bloque de
cURL ya existente se mantiene tal cual. Se agrega un bloque nuevo que, si
`http_client_.last_response` no es `None`, renderiza status code, headers
(como lista `header: valor`) y body (pretty-printed como JSON si
`response.json()` no lanza, si no como texto plano) escapado con
`html.escape`.

El bloque de "Aserciones de pytest-check fallidas" (que depende de
`call.excinfo`) no cambia: solo aparece cuando hay excepción, típico de
`failed`.

## Risks / Trade-offs

- **[Riesgo] Orden de hooks de pytest-html/pytest-json-report**: si alguno
  de esos plugins lee su propio flag de config antes de que nuestro
  `pytest_configure` corra, el override no tendría efecto.
  → **Mitigación**: `@pytest.hookimpl(tryfirst=True)` fuerza a nuestro hook
  a ejecutarse antes en la fase `pytest_configure`; se verifica manualmente
  con una corrida de humo como parte de las tasks (ver `tasks.md`).
- **[Riesgo] Reportes acumulándose sin límite en `reports/`** al no haber
  rotación automática.
  → **Mitigación**: ya es comportamiento git-ignored y de disco local del
  QA, no de CI; se documenta como Non-Goal explícito en vez de resolverlo
  ad hoc en este change.
- **[Riesgo] El body de una respuesta grande infla el HTML autocontenido**.
  → **Mitigación**: aceptado como trade-off (ver Non-Goals); los payloads
  de este proyecto son cuerpos de API REST, no archivos.

## Migration Plan

No hay datos que migrar. Pasos de despliegue:

1. Implementar el tracking de `last_response` en `http.py`.
2. Implementar el hook `pytest_configure` y ampliar
   `pytest_runtest_makereport` en `conftest.py`.
3. Actualizar `.gitignore` para ignorar `reports/*/` en vez de
   `reports/*.html` / `reports/*.json` sueltos en la raíz.
4. Actualizar los comandos de ejemplo en `README.md`, `CLAUDE.md` y
   `openspec/config.yaml` (sección "Reporte y trazabilidad").
5. QA corre una sesión de prueba (`pytest -k "algo trivial"`) y confirma que
   aparece una carpeta nueva bajo `reports/` con `report.html` y
   `resultados.json`, y que un caso exitoso muestra cURL + respuesta en el
   HTML.

Rollback: revertir el commit del change; no hay estado persistente fuera
del repo que limpiar (los reportes viejos en `reports/` no se ven afectados,
siguen siendo archivos sueltos ya generados con el esquema anterior).
