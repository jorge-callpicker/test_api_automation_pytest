## Why

Ningún `TC-XXX` de un endpoint que requiera sesión autenticada (todos,
salvo `login` mismo) puede implementarse todavía porque el framework no
tiene forma de obtener el `api-access-token` definitivo. Hoy cada test
tendría que reimplementar a mano la cadena `POST /panel_chat/login` →
`GET /panel_chat/selectAccount/{account_id}`, duplicando lógica y
credenciales por rol en cada change futuro. Este change añade ese
mecanismo una sola vez, como infraestructura reutilizable del framework
— igual que `add-test-framework-base` fijó `resolve()`, `client()` y
`engine()`. Por tratarse de tooling puro (no valida el comportamiento del
endpoint `login` en sí, solo lo consume para obtener un token), no sigue
la convención `add-test-<endpoint>-tc-<nnn>` ni referencia un TC de
`casos-prueba.md` — `input/login/casos-prueba.md` no existe aún; cuando
se genere, el TC de login se implementará como un change independiente
que sí valide sus propias aserciones.

## What Changes

- Se añade `src/framework/auth.py` con una función que encadena
  `POST {{GLB-url_cp_api}}{{GLB-path_login}}` (body `username`/`password`)
  seguido de `GET {{GLB-url_cp_api}}{{GLB-path_select_account}}` (path
  `account_id`, header `api_access_token` con el token del paso previo),
  devolviendo ambos tokens: el `api_token` inicial (login) y el
  `api-access-token` definitivo (`payload.api_key` de selectAccount).
- La función acepta el **rol** (`SuperAdmin` / `Admin`) como parámetro y
  resuelve las credenciales correspondientes desde `Settings`
  (`USR_SADMIN`/`PSW_SADMIN` o `USR_ADMIN`/`PSW_ADMIN`).
- Se añaden a `Settings` (`src/framework/config.py`) los campos
  `USR_SADMIN`, `PSW_SADMIN`, `USR_ADMIN`, `PSW_ADMIN` — ya presentes en
  el `.env` del QA — y se documentan en `.env.example` con placeholders
  `[REQUIERE RESPUESTA: ...]`.
- Se añade a `tests/conftest.py` una fixture factory (`scope="function"`)
  que, dado un rol, retorna ambos tokens usando la función de
  `auth.py` y el `http_client` existente.
- En `variables.yaml`, se renombran los globals ya presentes para seguir
  la convención `GLB-*` (guion) que reconoce el resolver actual:
  - `GBL_URL_CP_API` → `GLB-url_cp_api`
  - `PATH_LOGIN` → `GLB-path_login`
  - `PATH_SELECT_ACCOUNT` → `GLB-path_select_account`
  Estas tres siguen viviendo en `variables.yaml` (no son secretas, son el
  dominio/rutas del ambiente de Chat API), a diferencia de
  `GLB_URL_BASE`/`GLB_TOKEN_ADMIN` que sí viven en `.env`.
- Se actualizan los placeholders correspondientes en
  `input/login/docs.md` (`{{GBL_URL_CP_API}}` → `{{GLB-url_cp_api}}`)
  para que la documentación de entrada no quede inconsistente con el
  nuevo nombre.
- Se añade un smoke test (`tests/test_smoke_auth.py`) que ejercita la
  fixture `session_tokens` para ambos roles contra el ambiente real,
  verificando que ambos tokens resueltos sean strings no vacíos. Esto
  no es un `TC-XXX` de negocio — es la validación de que la
  infraestructura en sí funciona, igual que `test_smoke.py` valida
  `Settings`/`load_variables()`.
- `GLB-inbox_id_valido` (aún con placeholder `[REQUIERE RESPUESTA: ...]`
  en `variables.yaml`) queda **fuera de alcance**: no lo consume esta
  rutina de autenticación.

## Capabilities

Este change no introduce ni modifica ningún contrato observable de un
endpoint bajo prueba — es tooling de framework (un fixture de
autenticación reutilizable). Por eso no declara capabilities y marca
`skip_specs: true` en su `.openspec.yaml`.

### New Capabilities
(ninguna — tooling puro, sin comportamiento de API bajo prueba)

### Modified Capabilities
(ninguna)

## Impact

- **Código nuevo**: `src/framework/auth.py`, `tests/test_smoke_auth.py`.
- **Código modificado**: `src/framework/config.py` (nuevos campos en
  `Settings`), `tests/conftest.py` (nueva fixture factory),
  `variables.yaml` (renombre de tres globals), `.env.example` (nuevas
  entradas de credenciales), `input/login/docs.md` (placeholder
  renombrado).
- **Sistemas externos**: consume realmente `POST .../panel_chat/login` y
  `GET .../panel_chat/selectAccount/{account_id}` contra el ambiente del
  QA al ejecutarse (no es un mock) — requiere que esas credenciales y esa
  URL sean válidas en el ambiente donde el QA corra `pytest`.
- **Fuera de alcance**: no se implementa ningún `test_<endpoint>_<tc>.py`
  que use esta fixture (eso lo hará el primer change `add-test-*-tc-*`
  que la consuma); no se toca `GLB-inbox_id_valido` ni el flujo de
  inboxes/templates; no se genera `input/login/casos-prueba.md` ni
  `matriz-raiz.csv` (ese es un paso previo distinto, de refinamiento de
  casos, no de este change de framework).
