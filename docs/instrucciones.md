# Instrucciones — Tokens OAuth por rol

Este documento asume que ya hiciste el setup general del proyecto
(`venv`, `pip install -e ".[dev]"`, `.env`, `variables.yaml`) descrito en
[`README.md`](../README.md). Aquí solo se cubre lo agregado por el change
`add-test-framework-oauth-tokens` (archivado en
`openspec/changes/archive/2026-08-13-add-test-framework-oauth-tokens/`):
la rutina que emite `access_token` contra `POST /oauth/token` para los
roles del sistema, usada por la fixture de pytest `access_tokens` en vez
del token estático `GLB_TOKEN_ADMIN`.

## 1. Roles y scopes: `GLB-oauth_roles`

La fuente de verdad de "qué roles se autentican en esta corrida" es
`variables.yaml → globals → GLB-oauth_roles`:

```yaml
globals:
  GLB-oauth_roles:
    tango: { scopes: [call_details] }
    admin: { scopes: [call_details] }
    supervisor: { scopes: [call_details] }
    asistente: { scopes: [call_details] }
    customer: { scopes: [call_details] }
    extension: { scopes: [call_details] }
    extension_supervisora: { scopes: [call_details] }
```

Reglas:

- **Un rol ausente (o comentado) de este mapa nunca se procesa** — no se
  valida, no se le pide token, no hace falta llenar sus credenciales.
- **Un rol presente aquí es obligatorio** — si le faltan credenciales en
  `.env`, la sesión de pytest falla al arrancar (ver sección 3).
- `scopes` es una lista: si un rol se habilita para otra API además de
  `call_details`, se agrega el scope en su lista, sin tocar código.

Para probar solo con un rol (como en la validación de este change), comenta
los demás con `#`:

```yaml
  GLB-oauth_roles:
    #tango: { scopes: [call_details] }
    #admin: { scopes: [call_details] }
    customer: { scopes: [call_details] }
```

## 2. Credenciales por rol en `.env`

Por cada rol que dejes activo en `GLB-oauth_roles`, `.env` necesita su
`client_id`/`client_secret` (ver plantilla en `env.example`):

```
GLB_CLIENT_ID_<ROL>=...
GLB_CLIENT_SECRET_<ROL>=...
```

Donde `<ROL>` es el nombre del rol en mayúsculas
(`rol.upper().replace("-", "_")`), por ejemplo:

| Rol en `GLB-oauth_roles` | Variables en `.env`                                              |
|--------------------------|-------------------------------------------------------------------|
| `tango`                   | `GLB_CLIENT_ID_TANGO`, `GLB_CLIENT_SECRET_TANGO`                   |
| `extension_supervisora`   | `GLB_CLIENT_ID_EXTENSION_SUPERVISORA`, `GLB_CLIENT_SECRET_EXTENSION_SUPERVISORA` |

Estas credenciales se obtienen en la sección **API** del menú
**Configuración** del panel de administración de Callpicker, para la
cuenta correspondiente a cada rol.

## 3. Qué pasa si falta una credencial

Al arrancar la sesión de pytest, la fixture `access_tokens` valida cada
rol activo antes de llamar al endpoint. Si falta `client_id` o
`client_secret` de un rol listado en `GLB-oauth_roles`, la sesión aborta
con un error explícito nombrando la variable exacta que falta:

```
RuntimeError: El rol 'customer' esta en GLB-oauth_roles pero falta
'GLB_CLIENT_ID_CUSTOMER' en .env (o quedo con el placeholder sin llenar).
```

Esto es intencional (fail-fast): un rol en la lista es una promesa de que
va a poder autenticarse. Si un rol no tiene credenciales todavía,
coméntalo en `GLB-oauth_roles` en vez de dejarlo fallar.

Si en cambio el servidor rechaza credenciales completas (400/401 de
`/oauth/token`), la excepción trae el cURL equivalente de la request para
diagnóstico.

## 4. Usar `access_tokens` en un test nuevo

Cualquier test de `call_details`/`call_routes` que necesite autenticarse
declara la fixture `access_tokens` como parámetro (igual que
`http_client`/`db_conn`) y arma el header con `framework.http.auth_header`:

```python
from framework.http import auth_header


def test_algo(http_client, access_tokens):
    token = access_tokens["customer"]["call_details"]
    response = http_client.get("/algun-endpoint", headers=auth_header(token))
    assert response.status_code == 200
```

`access_tokens` es `scope="session"`: se emite una sola tanda de tokens
al inicio de la corrida y se reutiliza en todos los tests de esa sesión
de pytest — no hay refresh automático a mitad de corrida. Si una sesión
muy larga expira, el síntoma es un 401 inesperado; la solución es
reiniciar la sesión de pytest.

**No uses `{{GLB-token_admin}}` en pruebas nuevas** de este API — ese
mecanismo sigue existiendo solo por los tests preexistentes de
`Templates Gupshup` (proyecto y servidor distintos), no se migra ni se
retira.

## 5. Fuera de alcance de esta rutina

- **No valida el contrato propio de `POST /oauth/token`** (sus respuestas
  400/401/403/405/500). Eso se cubrirá en un change
  `add-test-oauth-token-tc-<nnn>` / `add-test-oauth-token-matriz-raiz`
  aparte, cuando existan `inputs/oauth/matriz-raiz.csv` y
  `casos-prueba.md`.
- **No maneja `customer_id`** — la selección de cuenta dentro de un
  `client_id`/`client_secret` que cubre varias cuentas la hace cada
  endpoint de negocio, no esta rutina.

## 6. Smoke test de referencia

`tests/test_smoke.py::test_access_tokens_issued_for_every_active_role_and_scope`
(`SMOKE-002`) es el ejemplo mínimo funcionando: itera
`GLB-oauth_roles` y verifica que cada rol/scope activo obtuvo un
`access_token`. Útil para confirmar que `.env` está bien llenado antes de
escribir un test real:

```bash
pytest -k "SMOKE" -v
```
