## 1. Proyecto Python y dependencias

- [x] 1.1 Crear `pyproject.toml` con `requires-python = ">=3.11"` y las
      dependencias de runtime pinneadas exactas (`==`): `pytest==9.1.1`,
      `pytest-html==4.2.0`, `pytest-check==2.9.1`,
      `pytest-json-report==1.5.0`, `httpx==0.28.1`, `sqlalchemy==2.0.51`,
      `pymysql[rsa]==1.2.0`, `pydantic==2.13.4`,
      `pydantic-settings==2.14.2`, `PyYAML` (última menor estable, sin
      pin de patch).
- [x] 1.2 Declarar el extra `dev` en `pyproject.toml` con
      `ruff==0.16.1`.
- [x] 1.3 Configurar `[tool.pytest.ini_options]`: `addopts =
      "--strict-markers -ra --tb=short"`, `testpaths = ["tests"]`, y
      registrar los marcadores `tc(id)`, `prioridad(nivel)`,
      `criticidad(nivel)`, `tipo(clase)`, `tecnica(nombre)`,
      `rol(nombre)`, `impacto(nivel)`.
- [x] 1.4 Configurar `[tool.ruff]`: `line-length = 100`,
      `target-version = "py311"`, `lint.select = ["E", "F", "I", "B",
      "UP", "SIM", "RUF"]`.
- [x] 1.5 Configurar el mapeo de paquete (`[tool.setuptools]` o
      equivalente) para que `framework` sea importable desde `src/`.

## 2. Estructura de carpetas

- [x] 2.1 Crear `src/framework/__init__.py`.
- [x] 2.2 Crear `tests/__init__.py`.

## 3. Módulo de configuración (`src/framework/config.py`)

- [x] 3.1 Implementar `Settings(BaseSettings)` con `model_config =
      SettingsConfigDict(env_file=".env", extra="ignore")` y los campos
      requeridos `GLB_URL_BASE: str`, `GLB_TOKEN_ADMIN: str`,
      `DB_HOST: str`, `DB_PORT: int`, `DB_NAME: str`, `DB_USER: str`,
      `DB_PASSWORD: str`.
- [x] 3.2 Implementar `load_variables() -> dict` que lee
      `variables.yaml` desde la raíz del proyecto y retorna un dict con
      las claves `globals` y `test_cases` (vacías si el archivo no
      define alguna).

## 4. Resolución de variables `{{...}}` (`src/framework/variables.py`)

- [x] 4.1 Implementar el detector de placeholders con regex
      `\{\{([A-Za-z0-9_-]+)\}\}`.
- [x] 4.2 Implementar la resolución de nombres `GLB-*`: mapear
      guion→underscore y mayúsculas, buscar primero en la instancia de
      `Settings`; si el atributo no existe, buscar en
      `variables.yaml → globals`.
- [x] 4.3 Implementar la resolución de nombres `TC-XXX-*`: aceptar solo
      si el prefijo `TC-XXX` coincide con el `tc_id` recibido;
      lanzar `KeyError` con mensaje que incluya el nombre de la
      variable y el `tc_id` esperado vs. el del payload en caso
      contrario.
- [x] 4.4 Implementar `resolve(payload, tc_id)` recursivo sobre
      dict/list/str, preservando el tipo nativo del valor resuelto
      cuando el placeholder ocupa el string completo, e interpolando
      como texto cuando está embebido en un string más largo.

## 5. Cliente HTTP (`src/framework/http.py`)

- [x] 5.1 Implementar `client(settings) -> httpx.Client` con
      `base_url=settings.GLB_URL_BASE` y `timeout=30`.
- [x] 5.2 Implementar `to_curl(request: httpx.Request) -> str` que
      construya el comando cURL equivalente incluyendo método, URL,
      headers y body (si existe).

## 6. Engine de base de datos (`src/framework/db.py`)

- [x] 6.1 Implementar `engine(settings) -> sqlalchemy.Engine` que
      construya la URL de conexión MySQL vía `pymysql` a partir de
      `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, con
      `isolation_level="AUTOCOMMIT"`.

## 7. Fixtures compartidos (`tests/conftest.py`)

- [x] 7.1 Implementar fixture `settings` (`scope="session"`) que
      instancie `Settings()`.
- [x] 7.2 Implementar fixture `http_client` (`scope="session"`) que
      haga `yield` del cliente de `framework.http.client(settings)` y
      llame `.close()` al finalizar; inicializar el atributo que
      almacenará la última request (para el hook de reporte).
- [x] 7.3 Implementar fixture `db_conn` (`scope="function"`) que haga
      `yield` de una conexión de `framework.db.engine(settings)` y
      llame `.close()` al finalizar.
- [x] 7.4 Implementar fixture `resolve_payload` (`scope="function"`)
      como factory: dado un `tc_id`, retorna
      `functools.partial(resolve, tc_id=tc_id)`.
- [x] 7.5 Implementar el hook `pytest_runtest_makereport` que, en caso
      de fallo (`report.outcome == "failed"`), adjunte al reporte HTML
      (vía `pytest-html`'s `extra`) el cURL de la última request
      almacenada en `http_client` y el detalle de las aserciones de
      `pytest-check` que fallaron.

## 8. Script de reanotación (`src/framework/reannotate.py`)

- [x] 8.1 Implementar el CLI con argumentos `--matrix <ruta>` y
      `--results <ruta>` (usando `argparse`), invocable como
      `python -m framework.reannotate`.
- [x] 8.2 Implementar la lectura de `resultados.json`
      (pytest-json-report) y la extracción, por test, del `TC-XXX`
      (desde el nodeid o metadata del marcador `tc`) y su outcome
      (`PASSED`/`FAILED`/`SKIPPED`).
- [x] 8.3 Implementar la actualización del CSV: matchear por columna
      `TC` o `id` contra el `TC-XXX` extraído, y añadir/actualizar las
      columnas `ultimo_resultado` y `ultima_ejecucion` (ISO 8601),
      preservando el resto de columnas y filas sin match.

## 9. Smoke test

- [x] 9.1 Crear `tests/test_smoke.py` marcado con
      `@pytest.mark.tc("SMOKE-001")` que verifique que `Settings()`
      instancia sin excepción (usa la fixture `settings`).
- [x] 9.2 En el mismo archivo, verificar que `load_variables()` retorna
      un dict con las claves `globals` y `test_cases`, sin hacer
      requests HTTP ni consultas a BD.

## 10. Validación de aceptación (bloqueante)

- [x] 10.1 **[BLOQUEANTE]** Ejecutar `pip install -e ".[dev]"`,
      `pytest --collect-only`, `pytest tests/test_smoke.py -v`,
      `ruff check .` y `python -c "from framework.config import
      Settings, load_variables; from framework.variables import
      resolve; print('ok')"`, y entregar la salida completa de los
      cinco comandos al QA para retroalimentación. No archivar este
      change sin confirmación explícita de que los cinco pasaron.
