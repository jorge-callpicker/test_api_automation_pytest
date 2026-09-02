## Why

Change de infraestructura (`add-test-framework-*`, no es de tipo TC ni matriz):
generaliza tres capacidades del framework de pruebas que hoy limitan cómo se
escriben y auditan los casos `TC-XXX`. (1) El reporte de una corrida solo
documenta las aserciones cuando el test **falla** — un TC que pasa no deja
rastro de qué se verificó en base de datos o en el log de auditoría, lo que
dificulta la auditoría manual de corridas exitosas. (2) Cada `TC-XXX` vive en
su propio archivo (`test_<endpoint>_tc_<nnn>.py`), lo que multiplica archivos
casi idénticos a medida que crecen los casos por endpoint, a diferencia de las
matrices que ya agrupan todos sus casos en un solo archivo. (3) El framework
solo sabe conectarse a una base de datos (`oauth`); los próximos casos de
prueba necesitan validar también contra `callpicker` y `chat`, que viven en el
mismo servidor con las mismas credenciales pero en schemas distintos.

## What Changes

- Nuevo helper de framework que envuelve `pytest_check.check(...)`: captura el
  booleano que ya retorna cada función de `pytest_check`, y acumula
  `(etiqueta, resultado, mensaje)` en una lista por test. El hook
  `pytest_runtest_makereport` de `tests/conftest.py` renderiza esa lista
  completa como tabla en `report.html`, para tests `TC-XXX` **pase o falle**
  el test — no solo cuando falla, como ocurre hoy. No aplica a tests de
  matriz (`test_matriz_*`), que siguen con el comportamiento actual.
- **BREAKING** (convención documentada, no código de producción): los tests
  `TC-XXX` dejan de vivir uno por archivo (`test_<endpoint>_tc_<nnn>.py`) y se
  agrupan en un único archivo por endpoint (`test_<endpoint>.py`), que
  contiene una función `test_<endpoint>_tc_<nnn>` por cada TC implementado —
  mismo patrón que ya usan las matrices. Se migra `tests/test_create_tc_001.py`
  a `tests/test_create.py` sin alterar su contenido. Actualiza la regla
  correspondiente en `openspec/config.yaml` (sección "Ejecución"), que hoy
  exige un archivo por TC. La selección con `-k` no cambia: sigue haciendo
  match por nombre de función, no por archivo.
- `src/framework/db.py::engine()` se generaliza para recibir el nombre del
  schema a conectar, reutilizando el mismo host/usuario/password para los
  tres. Se añaden fixtures `db_conn_callpicker` y `db_conn_chat` en
  `tests/conftest.py`, y las variables `DB_NAME_CALLPICKER`/`DB_NAME_CHAT` en
  `.env.example`. La fixture `db_conn` y la variable `DB_NAME` (schema
  `oauth`) quedan sin cambios, para no romper `tests/test_create_tc_001.py` /
  `tests/test_create.py`.

## Capabilities

### New Capabilities
- `database-access`: el framework SHALL soportar consultas contra múltiples
  bases de datos (`oauth`, `callpicker`, `chat`) mediante fixtures nombradas
  que comparten credenciales de conexión y difieren solo en el schema.

### Modified Capabilities
- `test-reporting`: nuevo requirement — el reporte SHALL documentar cada
  aserción individual de un test `TC-XXX` (su etiqueta, resultado y mensaje),
  independientemente de si el test en conjunto pasó o falló.

## Impact

- `src/framework/db.py` — `engine()` generalizado por schema.
- `src/framework/report.py` (nuevo) — helper de logging de asserts por TC.
- `tests/conftest.py` — fixtures `db_conn_callpicker`/`db_conn_chat`; hook
  `pytest_runtest_makereport` extendido para renderizar el log de asserts.
- `tests/test_create_tc_001.py` → `tests/test_create.py` (rename + adopción
  del helper de log de asserts).
- `.env.example` — nuevas variables `DB_NAME_CALLPICKER`/`DB_NAME_CHAT`; el QA
  debe sembrarlas en su `.env` local.
- `openspec/config.yaml` — actualiza la regla de nombre de archivo/función
  para tests `TC-XXX` en la sección "Ejecución".
