## Context

`src/framework/config.py` hoy define `Settings(BaseSettings)` con campos
fijos (`GLB_URL_BASE`, `GLB_TOKEN_ADMIN`, `DB_*`) y `variables.py:
resolve()` que interpola `{{GLB-*}}`/`{{TC-XXX-*}}` leyendo `Settings` y
`variables.yaml` — ambos estáticos, decididos en el change archivado
`add-test-framework-base`. Este change necesita credenciales por **rol**
(7 roles posibles, allowlist dinámica vía `GLB-oauth_roles` en
`variables.yaml`), no un campo fijo por variable. Ver `proposal.md` — Why
para la motivación completa.

Un `client_id`/`client_secret` de rol cubre múltiples cuentas — la
selección de cuenta ocurre vía `customer_id` en cada endpoint de negocio,
no en `/oauth/token` — por lo que el modelo de credenciales es
`rol → (client_id, client_secret, scopes[])`, sin una lista de cuentas.

## Goals / Non-Goals

**Goals:**
- Resolver `client_id`/`client_secret` por rol sin hardcodear los 7
  roles como campos de código — la fuente de verdad de "qué roles están
  activos" es `variables.yaml → GLB-oauth_roles`, no `Settings`.
- Fijar la firma de la rutina de emisión de tokens y de la fixture
  `access_tokens` una sola vez, para que los changes futuros de
  `call_details`/`call_routes` la consuman sin reinterpretarla (mismo
  criterio que `add-test-framework-base` fijó `resolve()`/`client()`).
- Fallar rápido y con mensaje explícito ante configuración incompleta o
  credenciales rechazadas por el servidor, en `setup` de la sesión de
  pytest, antes de que corra cualquier test.

**Non-Goals:**
- No se valida el contrato propio de `POST /oauth/token` (códigos
  400/401/403/405/500, mirror keys) — queda para un change futuro tipo
  `add-test-oauth-token-*` una vez existan `matriz-raiz.csv` y
  `casos-prueba.md` en `inputs/oauth/`.
- No se implementa refresh automático a mitad de sesión ni parsing de
  `expires_in` — la fixture es `session`-scoped y se asume que la
  duración de una corrida de pytest no excede la vigencia del token
  (consistente con la decisión de "una vez por sesión" tomada en
  exploración).
- No se gestiona `customer_id` ni selección de cuenta — responsabilidad
  de cada endpoint de negocio, no de esta rutina.
- No se toca `GLB_TOKEN_ADMIN` ni los `TC-001..TC-003` de `Templates
  Gupshup` existentes (proyecto/servidor distinto, fuera de alcance).

## Decisions

**1. `GLB-oauth_roles` en `variables.yaml → globals` es la única fuente
de verdad de "qué roles están activos", no `Settings`.**
Estructura: `{ <rol>: { scopes: [<scope>, ...] } }`. Un rol ausente del
mapa nunca se procesa (ni se valida, ni se le pide token). Esto separa
"qué roles interesan a esta suite" (dato versionado, cambia con
frecuencia al agregar scopes) de "cuáles son las 7 credenciales
posibles" (dato de negocio, no de código). Alternativa descartada:
hardcodear los 7 roles como constante Python en `auth.py` — obligaría a
tocar código cada vez que un rol se activa/desactiva para una corrida,
contradiciendo el pedido explícito de "un arreglo donde se pueda colocar
esta información".

**2. `Settings` gana `model_config` con `extra="allow"` y
`case_sensitive=True` para capturar `GLB_CLIENT_ID_<ROL>` /
`GLB_CLIENT_SECRET_<ROL>` dinámicos, en vez de un campo fijo por rol.**
Los nombres de estas variables dependen de las claves de
`GLB-oauth_roles` (dato de `variables.yaml`), que `Settings` no conoce en
tiempo de definición de clase — pydantic no soporta campos condicionados
por otro archivo. Con `extra="allow"`, `Settings()` acepta cualquier
`GLB_CLIENT_ID_*`/`GLB_CLIENT_SECRET_*` presente en `.env` y quedan
accesibles vía `getattr(settings, nombre, None)`. `case_sensitive=True`
es obligatorio junto con `extra="allow"`: por defecto
(`case_sensitive=False`), `pydantic-settings` normaliza a minúsculas las
claves de `.env` que no corresponden a un campo declarado antes de
guardarlas como atributos "extra" (los campos declarados como
`GLB_URL_BASE` no sufren esto porque el schema los remapea a su nombre
exacto) — sin `case_sensitive=True`, `getattr(settings,
"GLB_CLIENT_ID_ADMIN", None)` siempre da `None` aunque la variable exista
en `.env`, porque el atributo real quedó como `glb_client_id_admin`. Se
detectó en la validación de aceptación de este change (ver Risks).
Alternativa descartada: leer `os.environ` directo en `auth.py`, sin pasar
por `Settings` — se pierde el punto único de carga de `.env` que
`add-test-framework-base` fijó como decisión (`Settings` vía
`pydantic-settings`), duplicando la lógica de dónde vive la config del
ambiente.

**3. Nueva función `framework.config.role_credentials(settings, rol) ->
tuple[str, str]`** que arma los nombres `GLB_CLIENT_ID_<ROL_UPPER>` /
`GLB_CLIENT_SECRET_<ROL_UPPER>` (`rol.upper().replace("-", "_")`), lee
ambos vía `getattr`, y levanta `RuntimeError` explícito nombrando el rol
y la variable faltante si alguno es `None` o conserva el literal
`[REQUIERE RESPUESTA`. Se usa **solo** para roles que ya están en
`GLB-oauth_roles` — cumple exactamente la regla acordada: "si el rol
aparece en la lista, se valida que tenga credenciales; si no las tiene,
error".

**4. `src/framework/auth.py` expone `fetch_tokens(client, oauth_roles,
credentials_by_role) -> dict[str, dict[str, str]]`.**
Por cada `(rol, scope)` hace `client.post("/oauth/token", data={
"grant_type": "client_credentials", "scope": scope, "client_id": ...,
"client_secret": ...})` (form-urlencoded vía `data=`, sin tocar
`framework/http.py`: `httpx` ya serializa un `dict` pasado a `data=` como
`application/x-www-form-urlencoded`) y guarda
`response.json()["access_token"]`. Reutiliza `framework.http.client(settings)`
— mismo `GLB_URL_BASE` que el resto de la suite, asumiendo que
`/oauth/token` cuelga del mismo host que los endpoints de negocio bajo
prueba (igual que en `docs.md` de `oauth/token`, donde el path es
relativo a la URL base del ambiente). Si el ambiente del QA separara
ambos hosts, se documenta como ajuste de `.env` (`GLB_URL_BASE`), no
como cambio de código.
Cualquier respuesta no-200 levanta excepción con el cURL equivalente
(reusando `framework.http.to_curl`) para diagnóstico — sin captura
silenciosa, por la decisión de fail-fast.

**5. Fixture `access_tokens` (`scope="session"`) en `tests/conftest.py`
orquesta todo, sin exponer `Settings`/`auth.py` directamente a los
tests.**
Orden: `load_variables()["globals"].get("GLB-oauth_roles", {})` →
por cada rol, `role_credentials()` (falla si faltan credenciales) →
`fetch_tokens()` (falla si el servidor rechaza) → devuelve
`dict[rol, dict[scope, access_token]]`. Los tests futuros de
`call_details` la reciben como parámetro de función
(`def test_x(access_tokens): ...`), igual que `http_client`/`db_conn`.

**6. Los tokens NO se resuelven vía `{{...}}`/`resolve()`.**
El mecanismo `{{GLB-*}}` de `variables.py` fue diseñado para datos
estáticos leídos de `Settings`/`variables.yaml` en cualquier momento,
incluso fuera de una sesión de pytest activa. Un `access_token` es un
artefacto efímero que solo existe dentro del `setup` de la fixture de
sesión — forzarlo a través de `resolve()` requeriría inyectar el
resultado de una fixture en un mecanismo pensado para ser stateless, o
mantener un segundo cache global paralelo al de la fixture. Los tests
inyectan `access_tokens` como fixture estándar de pytest y construyen el
header (`{"api-access-token": access_tokens[rol][scope]}`) directamente.
Alternativa descartada: agregar un prefijo nuevo (p. ej. `AUTH-*`) a
`_resolve_name()` — añade una segunda forma de acceder al mismo dato sin
beneficio claro, ya que ningún campo de un body/URL de test necesita el
token interpolado dentro de un string (va siempre completo en un header).

**7. Helper `framework.http.auth_header(access_token: str) -> dict[str, str]`**
centraliza el nombre del header (`api-access-token`, confirmado en
`env.example` para `GLB_TOKEN_ADMIN`) en un solo lugar, evitando que cada
test futuro repita el literal del nombre del header.

## Risks / Trade-offs

- **[Riesgo] `extra="allow"` en `Settings` oculta typos en los nombres
  `GLB_CLIENT_ID_<ROL>`/`GLB_CLIENT_SECRET_<ROL>` (una var mal escrita en
  `.env` no genera error de pydantic, simplemente no se encuentra).**
  → Mitigación: `role_credentials()` valida explícitamente por nombre
  exacto y falla con el nombre de variable esperado en el mensaje — el
  error aparece igual, solo que se genera en la validación de negocio en
  vez de en la validación de schema de pydantic.
- **[Riesgo] Un fallo de un solo rol/scope aborta toda la sesión
  (decisión de fail-fast), incluso si otros roles no relacionados con el
  test que se quiere correr sí están bien configurados.**
  → Mitigación: es la decisión explícita del proyecto (igual criterio que
  el `-x` obligatorio en matrices); si en el futuro se vuelve un problema
  de productividad, es un cambio de framework explícito y documentado,
  no un ajuste silencioso.
- **[Riesgo] Sesiones de pytest muy largas (`--stepwise` interactivo a lo
  largo del día) podrían exceder la vigencia real del token, ya que no
  hay refresh.**
  → Mitigación: fuera de alcance por decisión explícita ("una vez por
  sesión"); si ocurre, el síntoma es un 401 a mitad de corrida — se
  documenta como comportamiento conocido, y el QA reinicia la sesión de
  pytest para forzar nuevos tokens.
- **[Riesgo] Asumir que `/oauth/token` vive bajo el mismo `GLB_URL_BASE`
  que los endpoints de negocio puede ser falso en algún ambiente.**
  → Mitigación: si el smoke test de este change falla con 404 en
  `/oauth/token` pero el resto del ambiente responde, es señal de que el
  QA debe confirmar el host correcto — no requiere cambio de diseño, solo
  de valor de `.env`.

## Migration Plan

Puramente aditivo — no hay datos existentes que migrar:

1. QA llena en `.env` los `GLB_CLIENT_ID_<ROL>`/`GLB_CLIENT_SECRET_<ROL>`
   para cada rol que quiera activar en `variables.yaml → GLB-oauth_roles`.
2. Roles que el QA no vaya a usar se dejan fuera de `GLB-oauth_roles`
   (no requieren credenciales, no producen error).
3. Rollback: revertir el commit del change. `GLB_TOKEN_ADMIN` y los
   tests de `Templates Gupshup` no fueron tocados, siguen funcionando
   igual que antes de este change.
