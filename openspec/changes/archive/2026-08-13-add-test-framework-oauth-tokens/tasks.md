## 1. Datos de configuración

- [x] 1.1 Agregar a `variables.yaml → globals` la clave
      `GLB-oauth_roles` con los 7 roles del negocio (`tango`, `admin`,
      `supervisor`, `asistente`, `customer`, `extension`,
      `extension_supervisora`), cada uno con `scopes: [call_details]`.
      Comentar en el YAML que un rol ausente de este mapa nunca se
      procesa (allowlist).
- [x] 1.2 Agregar a `env.example` una pareja `GLB_CLIENT_ID_<ROL>` /
      `GLB_CLIENT_SECRET_<ROL>` (placeholder `[REQUIERE RESPUESTA: ...]`)
      por cada rol declarado en el paso 1.1, siguiendo la regla de mapeo
      `rol.upper().replace("-", "_")`. Incluir comentario indicando que
      solo son obligatorias para los roles presentes en
      `GLB-oauth_roles`.

## 2. `src/framework/config.py`

- [x] 2.1 Cambiar `model_config` de `Settings` a
      `SettingsConfigDict(env_file=".env", extra="allow")` para aceptar
      los `GLB_CLIENT_ID_*`/`GLB_CLIENT_SECRET_*` dinámicos sin
      declararlos como campos fijos.
- [x] 2.2 Implementar `role_credentials(settings: Settings, rol: str) ->
      tuple[str, str]` que arme `GLB_CLIENT_ID_<ROL_UPPER>` y
      `GLB_CLIENT_SECRET_<ROL_UPPER>`, los lea vía `getattr(settings,
      nombre, None)`, y levante `RuntimeError` con el nombre exacto de
      la variable faltante si alguno es `None` o conserva el literal
      `[REQUIERE RESPUESTA`.

## 3. `src/framework/auth.py` (nuevo módulo)

- [x] 3.1 Implementar `fetch_tokens(client: httpx.Client, oauth_roles:
      dict, credentials_by_role: dict[str, tuple[str, str]]) ->
      dict[str, dict[str, str]]` que, por cada rol y cada scope de
      `oauth_roles[rol]["scopes"]`, haga
      `client.post("/oauth/token", data={"grant_type":
      "client_credentials", "scope": scope, "client_id": ...,
      "client_secret": ...})` y guarde `response.json()["access_token"]`
      en `resultado[rol][scope]`.
- [x] 3.2 Si la respuesta no es `200`, levantar una excepción que
      incluya el rol, el scope y el cURL equivalente (reusar
      `framework.http.to_curl`) para diagnóstico — sin captura
      silenciosa (fail-fast de sesión).

## 4. `src/framework/http.py`

- [x] 4.1 Agregar `auth_header(access_token: str) -> dict[str, str]`
      que retorne `{"api-access-token": access_token}`.

## 5. Fixture de sesión (`tests/conftest.py`)

- [x] 5.1 Implementar fixture `access_tokens` (`scope="session"`) que:
      lea `load_variables()["globals"].get("GLB-oauth_roles", {})`;
      valide credenciales de cada rol activo con
      `framework.config.role_credentials` (aborta la sesión si falta
      alguna); llame `framework.auth.fetch_tokens` con el
      `http_client` de sesión ya existente; retorne el mapa
      `dict[rol, dict[scope, access_token]]`.

## 6. Smoke test

- [x] 6.1 Agregar a `tests/test_smoke.py` (o archivo nuevo
      `tests/test_smoke_oauth.py`) un caso que, usando la fixture
      `access_tokens`, verifique que cada rol activo en
      `GLB-oauth_roles` tiene un `access_token` no vacío para cada uno
      de sus scopes declarados — sin hardcodear roles ni scopes
      concretos en el assert (iterar sobre `GLB-oauth_roles`).

## 7. Validación de aceptación (bloqueante)

- [x] 7.1 **[BLOQUEANTE]** Antes de ejecutar: completar en `.env` los
      `GLB_CLIENT_ID_<ROL>`/`GLB_CLIENT_SECRET_<ROL>` reales de cada rol
      que quede en `GLB-oauth_roles` (o retirar del mapa los roles sin
      credenciales disponibles todavía).
- [x] 7.2 **[BLOQUEANTE]** Ejecutar `pytest --collect-only`, `pytest -k
      "SMOKE" -v` (o el nombre del test agregado en el paso 6.1) y
      `ruff check .`; entregar la salida completa de los tres comandos
      al QA para retroalimentación. No archivar este change sin
      confirmación explícita de que los tres pasaron y de que los
      `access_token` obtenidos corresponden a los roles/scopes
      esperados.
