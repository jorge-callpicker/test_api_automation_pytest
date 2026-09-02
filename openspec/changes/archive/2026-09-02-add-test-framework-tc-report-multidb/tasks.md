## 1. Helper de log de aserciones

- [x] 1.1 Crear `src/framework/assert_log.py` con `step(log: list, label: str, check_fn: Callable[..., bool], *args, **kwargs) -> bool`: ejecuta `check_fn(*args, **kwargs)`, captura el bool retornado y hace `log.append({"label": label, "ok": ok, "detail": ...})`.
- [x] 1.2 Añadir fixture `assert_log` (`scope="function"`, retorna lista vacía) en `tests/conftest.py`.

## 2. Reporte — render del log de aserciones (solo TC-XXX)

- [x] 2.1 Extender `pytest_runtest_makereport` en `tests/conftest.py` para leer `item.funcargs.get("assert_log")` y, si existe y no está vacía, agregar un bloque HTML con una tabla (etiqueta, resultado, mensaje) por cada entrada — independientemente de si `report.outcome` es `passed` o `failed`.
- [x] 2.2 Verificar que el bloque no aparece para tests que no reciben la fixture `assert_log` (tests de matriz, smoke tests) — comportamiento de reporte sin cambios para ellos.

## 3. Multi-BD — oauth, callpicker, chat

- [x] 3.1 Añadir `DB_NAME_CALLPICKER` y `DB_NAME_CHAT` a la clase `Settings` en `src/framework/config.py`.
- [x] 3.2 Añadir `DB_NAME_CALLPICKER=[REQUIERE RESPUESTA: nombre del schema callpicker en el mismo servidor de DB_HOST]` y `DB_NAME_CHAT=[REQUIERE RESPUESTA: nombre del schema chat en el mismo servidor de DB_HOST]` a `.env.example`, junto a un comentario que aclare que comparten host/usuario/password con `DB_NAME`.
- [x] 3.3 Generalizar `src/framework/db.py::engine(settings, database)` para construir la `URL` con el parámetro `database` en vez de `settings.DB_NAME` fijo.
- [x] 3.4 Actualizar `_get_engine` en `tests/conftest.py` para cachear por `(id(settings), database)` en vez de `id(settings)`.
- [x] 3.5 Añadir fixtures `db_conn_callpicker` y `db_conn_chat` (`scope="function"`) en `tests/conftest.py`, análogas a `db_conn` mas usando `settings.DB_NAME_CALLPICKER`/`settings.DB_NAME_CHAT`. `db_conn` sigue usando `settings.DB_NAME` (oauth) sin cambios.

## 4. Migración de TC-001 al archivo agrupado por endpoint

- [x] 4.1 Crear `tests/test_create.py` con el contenido actual de `tests/test_create_tc_001.py` (imports, `ENDPOINT_PATH`, `FIELD_TYPES`, función `test_create_tc_001`), adoptando `step(assert_log, ...)` del punto 1 en sus tres bloques de assert (`[Respuesta]`, `[Base de datos]`, `[API log Chatwoot]`) y agregando el parámetro `assert_log` a la firma de la función.
- [x] 4.2 Eliminar `tests/test_create_tc_001.py` una vez migrado su contenido.
- [x] 4.3 Verificar que `pytest --collect-only -k "create_tc_001"` sigue seleccionando exactamente un test tras la migración.

## 5. Actualizar la convención documentada

- [x] 5.1 Actualizar `openspec/config.yaml` → sección "Ejecución": reemplazar la regla de un archivo por TC (`tests/test_<endpoint>_tc_<nnn>.py`) por la convención de archivo agrupado (`tests/test_<endpoint>.py` con función `test_<endpoint>_tc_<nnn>` por cada TC), aclarando que la selección por `-k` sigue dependiendo del nombre de función, no de archivo.

## 6. Ejecución — bloqueante

- [x] 6.1 Ejecutar `pytest --stepwise -k "create_tc_001" -v` y entregar la salida al QA para retroalimentación. Confirmar en `report.html` que la tabla de aserciones individuales aparece para este test, pase o falle. El change no se archiva sin retroalimentación humana positiva.
