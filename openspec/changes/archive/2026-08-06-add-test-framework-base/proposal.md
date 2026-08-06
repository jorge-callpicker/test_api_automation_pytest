## Why

Ningún `TC-XXX` puede implementarse todavía porque no existe el esqueleto
de framework que `openspec/config.yaml` exige: no hay proyecto Python
instalable, ni cliente HTTP, ni engine de BD, ni mecanismo de resolución
de variables `{{...}}`, ni fixtures compartidos. Este change es el
bootstrap previo y único a todos los TC — construye la infraestructura
reutilizable descrita en el stack pinneado, la convención de variables y
la política de soft assertions de `openspec/config.yaml` (secciones
"Stack técnico pinneado", "Convención de variables", "Aserciones AAA y
política de soft assertions", "Aserciones en base de datos" y "Reporte y
trazabilidad"). Por tratarse de tooling puro (no implementa comportamiento
de ningún endpoint), no sigue la convención de nombre `add-test-<endpoint>-tc-<nnn>`
ni referencia un TC de `casos-prueba.md`; en su lugar, cada decisión cita
la sección de `openspec/config.yaml` que la exige.

## What Changes

- Se crea `pyproject.toml` con Python `>=3.11` y las dependencias de
  runtime/dev pinneadas exactas (`==`) definidas en el stack técnico:
  `pytest 9.1.1`, `pytest-html 4.2.0`, `pytest-check 2.9.1`,
  `pytest-json-report 1.5.0`, `httpx 0.28.1`, `sqlalchemy 2.0.51`,
  `pymysql[rsa] 1.2.0`, `pydantic 2.13.4`, `pydantic-settings 2.14.2`,
  `PyYAML` (última menor estable); dev: `ruff 0.16.1`.
- Se configura `[tool.pytest.ini_options]` con `addopts`, `testpaths` y
  los marcadores registrados (`tc`, `prioridad`, `criticidad`, `tipo`,
  `tecnica`, `rol`, `impacto`) para habilitar `--strict-markers`.
- Se configura `[tool.ruff]` (line-length 100, target py311, reglas
  `E,F,I,B,UP,SIM,RUF`).
- Se crea el paquete `src/framework/` con:
  - `config.py`: `Settings(BaseSettings)` que carga `.env` (campos
    `GLB_URL_BASE`, `GLB_TOKEN_ADMIN`, `DB_HOST`, `DB_PORT`, `DB_NAME`,
    `DB_USER`, `DB_PASSWORD`) y `load_variables()` que carga
    `variables.yaml` (`globals` + `test_cases`).
  - `variables.py`: `resolve(payload, tc_id)` — interpolación de
    placeholders `{{...}}` con la regla de precedencia
    `GLB-*` (Settings → `variables.yaml`) y `TC-XXX-*` (aislado por
    `tc_id`), preservando tipo cuando el placeholder ocupa el string
    completo.
  - `http.py`: `client(settings)` (httpx.Client síncrono, timeout 30s) y
    `to_curl(request)` para logging de fallos con el cURL equivalente.
  - `db.py`: `engine(settings)` — engine SQLAlchemy Core sobre
    `pymysql` con `isolation_level="AUTOCOMMIT"`.
  - `reannotate.py`: script CLI que reanota `matriz-raiz.csv` con
    columnas `ultimo_resultado` y `ultima_ejecucion` leyendo
    `resultados.json` (pytest-json-report).
- Se crea `tests/conftest.py` con fixtures `settings` (session),
  `http_client` (session, cierra al final), `db_conn` (function, cierra
  al final) y `resolve_payload` (function, factory por `tc_id`); y el
  hook `pytest_runtest_makereport` que adjunta cURL y detalle de
  `pytest-check` fallidos al reporte HTML.
- Se crea `tests/test_smoke.py` (`@pytest.mark.tc("SMOKE-001")`) que
  valida que `Settings()` y `load_variables()` cargan sin excepción, sin
  tocar red ni BD.
- Ninguna variable `{{GLB-*}}` o `{{TC-XXX-*}}` de negocio se referencia
  en este change: `Settings` y `load_variables()` son el mecanismo de
  resolución, no consumidores de variables de un TC concreto. No se
  requieren altas en `variables.yaml` ni `.env.example`.

## Capabilities

Este change no introduce ni modifica ningún contrato observable de un
endpoint bajo prueba — es tooling de framework (instalación, config,
fixtures, cliente HTTP/DB, script de reanotación). Por eso no declara
capabilities y el change marca `skip_specs: true` en su `.openspec.yaml`.

### New Capabilities
(ninguna — tooling puro, sin comportamiento de API)

### Modified Capabilities
(ninguna)

## Impact

- **Código nuevo**: `pyproject.toml`, `src/framework/__init__.py`,
  `src/framework/config.py`, `src/framework/http.py`,
  `src/framework/db.py`, `src/framework/variables.py`,
  `src/framework/reannotate.py`, `tests/__init__.py`,
  `tests/conftest.py`, `tests/test_smoke.py`.
- **Dependencias**: instala el stack pinneado completo (runtime + dev)
  vía `pip install -e ".[dev]"`.
- **Sistemas externos**: ninguno se llama desde este change (sin
  requests HTTP reales, sin queries a BD real) — solo se define la
  infraestructura para que los changes `add-test-<endpoint>-tc-<nnn>`
  posteriores la consuman.
- **Fuera de alcance**: no se implementa ningún `test_<endpoint>_<tc>.py`;
  no se modifican `variables.yaml`, `.env.example` ni
  `openspec/config.yaml`.
