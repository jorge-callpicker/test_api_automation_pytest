## Why

Hoy `src/framework/config.py` asume un único token de acceso ya emitido
(`GLB_TOKEN_ADMIN`, literal en `.env`). Las pruebas de `call_details`/
`call_routes` necesitan tokens generados dinámicamente contra
`POST /oauth/token` para múltiples roles del sistema (Tango, Admin,
Supervisor, Asistente, Customer, Extension, Extension Supervisora), cada
uno con su propio `client_id`/`client_secret` y uno o varios `scope`
activados (hoy solo `call_details`). No existe ningún mecanismo en el
framework para emitir estos tokens antes de correr la suite. Por tratarse
de tooling puro de framework (no implementa el contrato observable de
ningún endpoint bajo prueba), no sigue la convención de nombre
`add-test-<endpoint>-tc-<nnn>` ni `add-test-<endpoint>-matriz-<nombre>` —
es un change de infraestructura, igual que `add-test-framework-base`.

Nota de alcance: `GLB_TOKEN_ADMIN` y los `TC-001..TC-003` de `Templates
Gupshup` ya existentes en `variables.yaml` pertenecen a un proyecto y
servidor distintos (contenido previo del repo, no relacionado con
`call_details`/`call_routes`). Este change no los toca ni los migra; solo
dejan de ser el mecanismo recomendado para pruebas nuevas de este API.

## What Changes

- Se agrega `variables.yaml → globals → GLB-oauth_roles`: mapa de roles
  **activos** (allowlist) a su lista de `scopes`. Solo se generan tokens
  para los roles presentes en este mapa; hoy todos con `scopes:
  [call_details]`, preparado para agregar scopes futuros sin tocar
  código:
  ```yaml
  GLB-oauth_roles:
    tango: { scopes: [call_details] }
    admin: { scopes: [call_details] }
    supervisor: { scopes: [call_details] }
    asistente: { scopes: [call_details] }
    customer: { scopes: [call_details] }
    extension: { scopes: [call_details] }
    extension_supervisora: { scopes: [call_details] }
  ```
- Se agregan a `env.example`/`.env`, una pareja por cada rol listado en
  `GLB-oauth_roles`, con placeholders `[REQUIERE RESPUESTA: ...]`:
  `GLB_CLIENT_ID_<ROL>` y `GLB_CLIENT_SECRET_<ROL>` (ej.
  `GLB_CLIENT_ID_TANGO`, `GLB_CLIENT_SECRET_EXTENSION_SUPERVISORA`). Si un
  rol aparece en `GLB-oauth_roles` pero le falta alguna de las dos
  variables, la carga de configuración falla con un error explícito
  (mismo criterio que cualquier `[REQUIERE RESPUESTA: ...]` sin llenar).
- Se extiende `src/framework/config.py` para resolver `client_id`/
  `client_secret` por rol a partir de `GLB-oauth_roles` en vez de campos
  fijos de `Settings` (el detalle de mecanismo queda en `design.md`).
- Se agrega `src/framework/auth.py` con la rutina que, por cada rol
  activo y cada scope de ese rol, hace `POST /oauth/token`
  (`grant_type=client_credentials`, `x-www-form-urlencoded`) y arma un
  mapa `{rol: {scope: access_token}}`.
- Se agrega a `tests/conftest.py` una fixture `access_tokens`
  (`scope="session"`) que ejecuta la rutina una sola vez por corrida de
  pytest y expone el mapa de tokens a cualquier test que la declare como
  parámetro. Si la llamada a `/oauth/token` falla (400/401) para un
  rol/scope ya validado como bien configurado, la fixture aborta toda la
  sesión (`pytest.exit` o excepción no capturada en setup) — no se
  degrada a "rol no disponible".
- **BREAKING (solo para pruebas nuevas de este API)**: las pruebas que se
  escriban de aquí en adelante contra `call_details`/`call_routes` deben
  autenticarse vía la fixture `access_tokens`, no vía `{{GLB-token_admin}}`.

## Capabilities

Este change no introduce ni modifica el contrato observable de ningún
endpoint bajo prueba — es tooling de framework (config, cliente de
autenticación, fixture de sesión). Por eso no declara capabilities y el
change marca `skip_specs: true` en su `.openspec.yaml`, igual que
`add-test-framework-base`. Cuando exista `inputs/oauth/matriz-raiz.csv` y
`casos-prueba.md`, el contrato propio de `POST /oauth/token` (sus
respuestas 200/400/401/403/405/500) se cubrirá en un change
`add-test-oauth-token-tc-<nnn>` / `add-test-oauth-token-matriz-raiz`
aparte, con su propia spec.

### New Capabilities
(ninguna — tooling puro, sin comportamiento de API bajo prueba)

### Modified Capabilities
(ninguna)

## Impact

- **Código nuevo**: `src/framework/auth.py`.
- **Código modificado**: `src/framework/config.py` (resolución de
  credenciales por rol), `tests/conftest.py` (fixture `access_tokens`).
- **Datos versionados**: `variables.yaml → globals → GLB-oauth_roles`
  (nuevo), `env.example` (nuevas variables `GLB_CLIENT_ID_<ROL>` /
  `GLB_CLIENT_SECRET_<ROL>` por rol activo).
- **Secretos locales**: `.env` del QA debe completarse con los
  `client_id`/`client_secret` reales de cada rol activo antes de poder
  correr cualquier test que dependa de `access_tokens`.
- **Sistemas externos**: llama a `POST /oauth/token` del ambiente real
  contra el que corra pytest (una vez por rol/scope activo, al inicio de
  la sesión). No se llama desde este change (Claude no ejecuta pytest).
- **Fuera de alcance**: `GLB_TOKEN_ADMIN`, los `TC-001..TC-003` de
  `Templates Gupshup` y sus tests asociados (no se tocan ni se migran);
  validar el contrato propio de `POST /oauth/token`; el parámetro
  `customer_id` de selección de cuenta (lo maneja cada endpoint, no esta
  rutina).
