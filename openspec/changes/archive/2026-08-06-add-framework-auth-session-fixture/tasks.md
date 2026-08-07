## 1. Configuración (`src/framework/config.py`, `.env.example`)

- [x] 1.1 Añadir a `Settings` los campos `USR_SADMIN: str`,
      `PSW_SADMIN: str`, `USR_ADMIN: str`, `PSW_ADMIN: str`.
- [x] 1.2 Documentar las cuatro variables anteriores en `.env.example`
      con placeholders `[REQUIERE RESPUESTA: ...]`, siguiendo el mismo
      formato y comentarios de sección que las entradas existentes.

## 2. Variables de ambiente en `variables.yaml` y `docs.md`

- [x] 2.1 En `variables.yaml -> globals`, renombrar `GBL_URL_CP_API` →
      `GLB-url_cp_api`, `PATH_LOGIN` → `GLB-path_login` y
      `PATH_SELECT_ACCOUNT` → `GLB-path_select_account`, preservando sus
      valores actuales.
- [x] 2.2 En `input/login/docs.md`, actualizar el placeholder
      `{{GBL_URL_CP_API}}` a `{{GLB-url_cp_api}}` en las dos rutas donde
      aparece (Login y Select Account).

## 3. Módulo de autenticación (`src/framework/auth.py`)

- [x] 3.1 Definir `SessionTokens` (`NamedTuple`) con los campos
      `api_token: str` y `api_access_token: str`.
- [x] 3.2 Definir el mapeo constante `_ROLE_CREDENTIALS` (`SuperAdmin` →
      `("USR_SADMIN", "PSW_SADMIN")`, `Admin` → `("USR_ADMIN",
      "PSW_ADMIN")`).
- [x] 3.3 Implementar `obtain_session_tokens(role, *, settings, http_client, account_id=None) -> SessionTokens`:
      resuelve credenciales del rol vía `_ROLE_CREDENTIALS` y `settings`
      (lanza `ValueError` con el rol recibido y los roles soportados si
      el rol no está en el mapeo); si `account_id` es `None`, lo resuelve
      de `load_variables()['globals']['GLB-account_id_valido']`.
- [x] 3.4 Dentro de la función anterior: hacer `POST` a
      `f"{url_cp_api}{path_login}"` con body `{"username": ..., "password": ...}`,
      extraer `payload.api_token` de la respuesta (`assert` duro sobre
      status 200 antes de leer el payload).
- [x] 3.5 Encadenar `GET` a
      `f"{url_cp_api}{path_select_account.format(account_id=account_id)}"`
      con header `api_access_token` igual al `api_token` del paso
      anterior, extraer `payload.api_key` (`assert` duro sobre status
      200 antes de leer el payload).
- [x] 3.6 Retornar `SessionTokens(api_token=..., api_access_token=...)`.

## 4. Fixture en `tests/conftest.py`

- [x] 4.1 Importar `framework.auth` y añadir la fixture
      `session_tokens` (`scope="session"`) que retorna una función
      factory `factory(role: str) -> SessionTokens`, cacheando el
      resultado por `role` en un diccionario local a la fixture para no
      reautenticar en cada solicitud del mismo rol dentro de la misma
      sesión de pytest.

## 5. Smoke test de verificación (`tests/test_smoke_auth.py`)

- [x] 5.1 Crear `tests/test_smoke_auth.py` con
      `@pytest.mark.tc("SMOKE-002")` que, para cada rol
      (`SuperAdmin`, `Admin`), solicite `session_tokens(role)` y
      verifique (soft assertions vía `pytest_check.check(...)`, salvo
      la primera que es `assert` duro) que `api_token` y
      `api_access_token` son strings no vacíos.

## 6. Validación de aceptación (bloqueante)

- [x] 6.1 **[BLOQUEANTE]** Ejecutar, en este orden:
      `pytest --collect-only`,
      `pytest tests/test_smoke_auth.py -v` (selecciona por archivo, no
      por marcador — `-k` no empareja contra el argumento de
      `@pytest.mark.tc(...)`, solo contra el nodeid; requiere que `.env`
      tenga sembrados `USR_SADMIN`/`PSW_SADMIN`/`USR_ADMIN`/`PSW_ADMIN`
      reales y que el ambiente de Chat API esté disponible), y
      `ruff check .`; entregar la salida completa de los tres comandos
      al QA para retroalimentación. No archivar este change sin
      confirmación explícita de que los tres pasaron. Si
      `test_smoke_auth.py` falla por un código de estado inesperado de
      login/selectAccount (no por un error de código), tratarlo como
      bloqueo de ambiente, no como fallo de test.