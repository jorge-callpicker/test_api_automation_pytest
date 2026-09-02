## Context

Ver `proposal.md` → "Why" para la motivación. Estado actual relevante:

- `tests/conftest.py::pytest_runtest_makereport` solo agrega el bloque HTML
  "Aserciones de pytest-check fallidas" cuando `call.excinfo is not None`
  (test fallido). `pytest_check` 2.9.1 (paquete instalado en `.venv`) solo
  lleva un registro interno de fallos (`check_log._failures`); no expone
  ningún registro de los checks que pasaron. Cada función de `pytest_check`
  (`check.equal`, `check.is_true`, etc.) sí **retorna un bool** indicando si
  pasó (vía el decorador `check_func`).
- `src/framework/db.py::engine(settings)` arma una única URL MySQL con
  `settings.DB_HOST/PORT/NAME/USER/PASSWORD`. `tests/conftest.py::_get_engine`
  cachea un solo engine por `id(settings)`.
- La convención de nombre de archivo/función para TC (`tests/test_<endpoint>_tc_<nnn>.py`,
  función `test_<endpoint>_tc_<nnn>`) está documentada como regla dura en
  `openspec/config.yaml` → "Ejecución", justificada porque `-k` hace match
  contra el nodeid (ruta + función + params), no contra el archivo.

## Goals / Non-Goals

**Goals:**
- Documentar en el reporte, para tests `TC-XXX`, cada aserción individual
  (pase o falle el test), sin cambiar el comportamiento de soft-assert de
  `pytest_check`.
- Permitir que un endpoint acumule sus `TC-XXX` en un solo archivo, sin
  romper la selección por `-k` ya documentada.
- Generalizar la conexión a BD para soportar `oauth`, `callpicker` y `chat`
  sin duplicar credenciales.

**Non-Goals:**
- No se toca el comportamiento de reporte de tests de matriz
  (`test_matriz_*`): siguen sin log de aserciones individuales.
- No se introduce un motor de BD distinto a MySQL/MariaDB — las tres BD
  comparten servidor y credenciales, solo cambia el schema.
- No se re-abre ni se vuelve a ejecutar `add-test-framework-base` (archivado
  incompleto); este change es independiente y no depende de sus módulos
  pendientes (`generators.py`, `mirror.py`).

## Decisions

### 1. Log de aserciones: wrapper alrededor de `pytest_check`, no un fork ni un monkeypatch

Se añade `src/framework/assert_log.py` con una función
`step(log: list, label: str, check_fn: Callable[..., bool], *args, **kwargs) -> bool`
que ejecuta `check_fn(*args, **kwargs)` (típicamente `check.equal`,
`check.is_true`, etc.), captura el bool retornado, y hace
`log.append({"label": label, "ok": ok, "detail": ...})`. Los tests `TC-XXX`
reemplazan sus llamadas directas a `check.*` por `step(assert_log, "Assert 2 [BD] ...", check.equal, ...)`.
`tests/conftest.py` gana una fixture `assert_log` (`scope="function"`, lista
vacía) que los tests reciben como parámetro; el hook
`pytest_runtest_makereport` la lee vía `item.funcargs.get("assert_log")` y
renderiza una tabla HTML con todas sus entradas, sin importar el resultado
final del test.

Alternativas consideradas:
- **Monkeypatchear `pytest_check.check_log.log_failure`** para que también
  registre éxitos: se descartó por frágil — depende de internals de una
  librería de terceros que puede cambiar entre versiones sin aviso, y el
  contrato pinneado (`pytest-check==2.9.1`) no lo garantiza.
- **`item.user_properties` / `record_property` nativo de pytest**: más
  "estándar" de pytest, pero no resuelve el problema real (pytest_check
  sigue sin exponer los pases); igual habría que envolver cada `check.*` a
  mano, así que no simplifica nada sobre la fixture propia.

### 2. Un archivo por endpoint para TC-XXX, función como unidad de selección

`tests/test_<endpoint>.py` concentra todas las funciones
`test_<endpoint>_tc_<nnn>` de ese endpoint. La selección por `-k` no cambia:
sigue haciendo match contra el nodeid, que incluye el nombre de función, no
el de archivo — verificable con `pytest --collect-only -k "create_tc_001"`
antes y después de mover el archivo. Cada change de tipo TC pasa de "crear
archivo" a "anexar función a un archivo existente"; como el ciclo de trabajo
es un change a la vez con humano-en-medio, no hay riesgo real de conflicto
concurrente sobre el mismo archivo.

Se migra `tests/test_create_tc_001.py` → `tests/test_create.py` como parte
de este change (ver "Migration Plan"), adoptando también el helper de log de
aserciones del punto 1 para sus tres asserts existentes.

### 3. Un engine por schema, credenciales compartidas

`engine(settings, database: str)` reemplaza el `settings.DB_NAME` fijo por
el parámetro `database`, dejando el resto de la URL (host/puerto/usuario/
password) intacto. `tests/conftest.py::_get_engine` cambia su clave de caché
de `id(settings)` a `(id(settings), database)`, y expone tres fixtures:
`db_conn` (usa `settings.DB_NAME`, sin cambios de comportamiento),
`db_conn_callpicker` (usa `settings.DB_NAME_CALLPICKER`), `db_conn_chat`
(usa `settings.DB_NAME_CHAT`). `Settings` (pydantic) gana los dos campos
nuevos; `DB_HOST/PORT/USER/PASSWORD` no se duplican.

Alternativa considerada: una sola fixture factory `db_conn(alias: str)`.
Se descartó porque cambiaría la firma que ya consume `test_create_tc_001.py`
(`db_conn` como conexión, no como callable) — habría que tocar ese test sin
necesidad, y las fixtures nombradas son igual de explícitas para tres BDs
fijas y conocidas de antemano.

## Risks / Trade-offs

- [Cambiar la firma de `engine()` rompe cualquier otro caller] → Único
  caller hoy es `tests/conftest.py::_get_engine`; se actualiza en el mismo
  change.
- [Los TC ya escritos usan `check.*` directo, no el helper `step(...)`] →
  Solo existe un TC archivado (`TC-001`); se migra explícitamente en este
  change. Los `TC-XXX` futuros nacen ya con el patrón nuevo.
- [El QA no siembra `DB_NAME_CALLPICKER`/`DB_NAME_CHAT` en su `.env` local] →
  `pydantic-settings` falla rápido y explícito al cargar `Settings()` si
  falta una variable requerida; se documenta como tarea de siembra con
  placeholder `[REQUIERE RESPUESTA: ...]` en `.env.example`.
- [Confundir el nuevo `assert_log.py` con el reporte de pytest-html] →
  Nombre del módulo y de la fixture (`assert_log`) distinto de `report.html`/
  `conftest.py` para evitar ambigüedad.

## Migration Plan

1. Añadir `src/framework/assert_log.py` (helper `step(...)`), sin
   consumidores todavía.
2. Generalizar `src/framework/db.py::engine()` por `database`, y actualizar
   `_get_engine` en `tests/conftest.py` para cachear por `(settings, database)`.
3. Añadir fixtures `db_conn_callpicker`/`db_conn_chat` y la fixture
   `assert_log` en `tests/conftest.py`; extender
   `pytest_runtest_makereport` para renderizar la tabla de aserciones cuando
   el test tiene `assert_log` en `funcargs`.
4. Añadir `DB_NAME_CALLPICKER`/`DB_NAME_CHAT` a `.env.example` y a la clase
   `Settings`. Tarea de siembra para el QA en su `.env` local.
5. Migrar `tests/test_create_tc_001.py` → `tests/test_create.py`, adoptando
   `step(...)` en sus tres asserts existentes.
6. Actualizar la regla de "Ejecución" en `openspec/config.yaml` para
   reflejar la convención de archivo agrupado por endpoint.
7. QA ejecuta `pytest --stepwise -k "create_tc_001" -v` y confirma en
   `report.html` la tabla de aserciones individuales, pase o falle.
