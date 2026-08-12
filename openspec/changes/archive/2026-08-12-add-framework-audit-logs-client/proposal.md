## Why

Los próximos `TC-XXX`/matrices sobre plantillas (crear, eliminar) necesitan
verificar que la acción quedó registrada en el audit log de Chatwoot
(`GET /api/v1/accounts/{account_id}/audit_logs`), además de la sesión ya
resuelta por `session_tokens`. Hoy el framework no tiene forma de
consultar esa API — es un tercer host/token, distinto tanto de
`GLB-url_cp_api` (panel Callpicker Chat) como de `GLB_URL_BASE`/
`GLB_TOKEN_ADMIN` (ambiente Gupshup/Templates). Sin este cliente, cada
TC futuro que necesite el assert de audit log tendría que reimplementar a
mano la request y su autenticación. Este change añade ese mecanismo una
sola vez, como infraestructura reutilizable del framework — igual que
`add-test-framework-base` fijó `resolve()`/`client()`/`engine()` y
`add-framework-auth-session-fixture` fijó `session_tokens`. Por tratarse
de tooling puro (no valida el comportamiento propio del endpoint
`audit_logs`, solo lo consume para leer entradas), no sigue la
convención `add-test-<endpoint>-tc-<nnn>` ni referencia un TC de
`casos-prueba.md` — `inputs/audit_logs/casos-prueba.md` no existe aún;
cuando se genere, los TC propios de `audit_logs` se implementarán como
changes independientes.

## What Changes

- Se añade `src/framework/audit_logs.py` con dos funciones:
  - `fetch_audit_logs_page(account_id, page=1, *, settings, http_client) -> dict`:
    hace `GET {{GLB_URL_CHATWOOT}}/api/v1/accounts/{account_id}/audit_logs?page={page}`
    con header `api_access_token: {{GLB_TOKEN_CHATWOOT_ADMIN}}` y devuelve
    el JSON crudo de la página (`per_page`, `total_entries`,
    `current_page`, `audit_logs`).
  - `find_audit_log(account_id, predicate, *, settings, http_client, page=1) -> dict | None`:
    obtiene la página indicada (por defecto la 1, que siempre contiene
    las entradas más recientes) y devuelve la primera entrada de
    `audit_logs[]` donde `predicate(entry)` sea `True`, o `None` si
    ninguna coincide. No pagina automáticamente ni reintenta — el
    llamador decide el criterio de match y, si lo necesita, una página
    distinta.
- Se añaden a `Settings` (`src/framework/config.py`) los campos
  `GLB_URL_CHATWOOT` y `GLB_TOKEN_CHATWOOT_ADMIN`, documentados en
  `env.example` con placeholders `[REQUIERE RESPUESTA: ...]` (host y
  token del ambiente Chatwoot, distintos de `GLB_URL_BASE`/
  `GLB_TOKEN_ADMIN`).
- Reutiliza el `http_client` de sesión ya existente (`tests/conftest.py`)
  con URL absoluta, igual que `auth.py` hace para login/selectAccount —
  no se abre un segundo `httpx.Client`, para conservar el mecanismo de
  `last_request`/cURL en el reporte HTML ante fallos.
- El path parameter `account_id` reutiliza `GLB-account_id_valido`
  (ya existente en `variables.yaml`) — no se declara ninguna variable
  nueva ahí; Callpicker Chat comparte el mismo esquema de cuentas que
  Chatwoot.
- Se añade un smoke test (`tests/test_smoke_audit_logs.py`) que ejercita
  `fetch_audit_logs_page` contra el ambiente real con `GLB-account_id_valido`
  y verifica que la respuesta trae la forma esperada (`audit_logs` es
  lista, `current_page == 1`). Esto no es un `TC-XXX` de negocio — valida
  que la infraestructura en sí funciona, igual que `test_smoke_auth.py`
  hace con `session_tokens`.

## Capabilities

Este change no introduce ni modifica ningún contrato observable de un
endpoint bajo prueba — es tooling de framework (un cliente reutilizable
para consultar audit logs). Por eso no declara capabilities y marca
`skip_specs: true` en su `.openspec.yaml`.

### New Capabilities
(ninguna — tooling puro, sin comportamiento de API bajo prueba)

### Modified Capabilities
(ninguna)

## Impact

- **Código nuevo**: `src/framework/audit_logs.py`,
  `tests/test_smoke_audit_logs.py`.
- **Código modificado**: `src/framework/config.py` (nuevos campos en
  `Settings`), `env.example` (nuevas entradas `GLB_URL_CHATWOOT`,
  `GLB_TOKEN_CHATWOOT_ADMIN`).
- **Sistemas externos**: consume realmente
  `GET .../api/v1/accounts/{account_id}/audit_logs` contra el ambiente
  Chatwoot del QA al ejecutarse (no es un mock) — requiere que
  `GLB_URL_CHATWOOT`/`GLB_TOKEN_CHATWOOT_ADMIN` sean válidos en el
  ambiente donde el QA corra `pytest`.
- **Fuera de alcance**: no se implementa ningún `test_<endpoint>_<tc>.py`
  que use `find_audit_log` como assert (eso lo hará el primer change
  `add-test-*-tc-*`/`add-test-*-matriz-*` de plantillas que lo consuma);
  no se implementa paginación automática, reintentos, ni tests propios
  del endpoint `audit_logs` (bloqueado hasta que existan
  `inputs/audit_logs/matriz-raiz.csv`/`casos-prueba.md`).
