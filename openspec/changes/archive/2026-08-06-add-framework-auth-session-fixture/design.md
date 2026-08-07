## Context

Ver `proposal.md` — Why. `Settings` (`src/framework/config.py`) hoy solo
conoce `GLB_URL_BASE`/`GLB_TOKEN_ADMIN` (config del ambiente Gupshup/
Templates, vía `.env`) y las credenciales de BD. La URL y rutas de Chat
API (`GLB-url_cp_api`, `GLB-path_login`, `GLB-path_select_account`) viven
en `variables.yaml`, no en `.env` — son dominio/rutas del ambiente, no
secretos. El `http_client` de sesión ya existente
(`tests/conftest.py::http_client`) se construye con
`base_url=settings.GLB_URL_BASE`, que **no** es la URL de Chat API — por
lo tanto las requests de login/selectAccount deben usar URLs absolutas,
no rutas relativas al `base_url` configurado del cliente compartido.

## Goals / Non-Goals

**Goals:**
- Fijar la firma pública de la función que encadena login → selectAccount
  y de la fixture que la expone, para que los changes `add-test-*-tc-*`
  futuros la consuman sin reinterpretarla (igual que
  `add-test-framework-base` fijó `resolve()`/`client()`/`engine()`).
- Soportar ambos roles (`SuperAdmin`, `Admin`) sin duplicar la lógica de
  la cadena de requests.
- Evitar reautenticar en cada test: cachear tokens por rol durante la
  sesión de pytest.

**Non-Goals:**
- No se valida el comportamiento propio del endpoint `login` ni
  `selectAccount` (códigos 400/401/403/406/500, mensajes de error) — eso
  es responsabilidad de un `TC-XXX` futuro sobre `casos-prueba.md` de
  login, no de este fixture.
- No se implementa refresh/renovación de token ante expiración a mitad
  de una corrida larga.
- No se toca `GLB-inbox_id_valido` ni el flujo de inboxes/templates.

## Decisions

**1. `auth.py` expone `obtain_session_tokens(role, *, settings, http_client, account_id=None) -> SessionTokens`.**
`SessionTokens` es un `NamedTuple` con dos campos: `api_token` (el JWT
inicial de login) y `api_access_token` (el token definitivo de
`selectAccount`, `payload.api_key`) — nombres tomados literalmente de
`input/login/docs.md` para que el mapeo con la documentación del
endpoint sea directo. `account_id` es keyword-only con default `None`;
si no se pasa, la función resuelve `GLB-account_id_valido` desde
`load_variables()['globals']`. Alternativa descartada: hardcodear
`account_id` dentro de `auth.py` — se descarta porque ambos roles podrían
necesitar cuentas distintas en el futuro, y el parámetro opcional lo
permite sin romper la firma por defecto.

**2. Mapeo rol → credenciales vía diccionario constante en `auth.py`.**
`_ROLE_CREDENTIALS = {"SuperAdmin": ("USR_SADMIN", "PSW_SADMIN"), "Admin": ("USR_ADMIN", "PSW_ADMIN")}`.
La función busca los nombres de atributo en `settings` (instancia de
`Settings`). Un rol no reconocido lanza `ValueError` explícito con el rol
recibido y los roles soportados. Alternativa descartada: aceptar
`username`/`password` directos como parámetros de la función — se
descarta porque el objetivo es que cada TC solo declare el **rol**
(`SuperAdmin`/`Admin`), no credenciales sueltas, manteniendo la regla de
no hardcodear valores de negocio en el código de test.

**3. `GLB-url_cp_api`, `GLB-path_login`, `GLB-path_select_account` y
`GLB-account_id_valido` se leen directo de
`load_variables()['globals']`, no vía `resolve()`.**
`resolve()` (`variables.py`) exige un `tc_id` para resolver nombres
`TC-XXX-*`; estas cuatro variables son `GLB-*` puras sin necesidad de
interpolación dentro de un string mayor, y `auth.py` no tiene ni necesita
un `tc_id` (es infraestructura compartida, no código de un TC concreto).
Alternativa descartada: pasar un `tc_id` sintético (p. ej. `"GLB"`) para
reusar `resolve()` — se descarta por ser un hack que sugiere un acople a
un TC inexistente; una lectura directa del dict de globals es más clara
y no depende del prefijo de un caso.

**4. Requests con URL absoluta sobre el `http_client` de sesión ya
existente, sin crear un segundo `httpx.Client`.**
`obtain_session_tokens` construye `f"{url_cp_api}{path_login}"` y
`f"{url_cp_api}{path_select_account.format(account_id=account_id)}"` y
los pasa directo a `http_client.post()`/`.get()` — httpx usa una URL
absoluta tal cual, ignorando el `base_url` del cliente. Se reusa
`http_client` (y no un cliente nuevo) para conservar el mecanismo de
`last_request`/cURL en el reporte HTML ante fallos. Alternativa
descartada: instanciar un `httpx.Client(base_url=url_cp_api)` aparte —
duplicaría el manejo de cURL para fallos y el ciclo de vida
(open/close) que ya resuelve la fixture `http_client`.

**5. Fixture `session_tokens` (`scope="session"`) como factory,
cacheando por rol.**
```python
@pytest.fixture(scope="session")
def session_tokens(settings, http_client):
    cache: dict[str, SessionTokens] = {}
    def factory(role: str) -> SessionTokens:
        if role not in cache:
            cache[role] = auth.obtain_session_tokens(
                role, settings=settings, http_client=http_client
            )
        return cache[role]
    return factory
```
Un test la consume como `session_tokens("SuperAdmin")`. Se elige
`scope="session"` (igual que `settings`/`http_client`) porque
autenticar es costoso (dos requests HTTP reales) y el token no se
invalida por la ejecución normal de un TC — cachear por rol evita que
cada test dispare su propio login. Alternativa descartada: fixture
`scope="function"` sin caché — reautenticaría en cada test,
multiplicando llamadas reales al ambiente sin beneficio, ya que ningún
TC actual necesita un token "fresco" por test.

## Risks / Trade-offs

- **[Riesgo] Esta fixture golpea el ambiente real en cada corrida donde
  se solicite un rol por primera vez — si el login o selectAccount
  fallan (ambiente caído, credenciales rotadas), todos los TC que
  dependan de ella fallan en el `setup`, no en el `Act` del TC.**
  → Mitigación: el error de `obtain_session_tokens` debe ser legible
  (incluir status code y body de la respuesta que falló) para que el QA
  lo distinga de un fallo de aserción de negocio y lo trate como bloqueo
  de ambiente (regla de `CLAUDE.md` — no corregir el test, desbloquear
  el ambiente).
- **[Riesgo] La caché por rol a nivel de sesión no detecta expiración de
  token en corridas largas.**
  → Mitigación: fuera de alcance (Non-Goals); si aparece, un TC futuro
  que pruebe expiración deberá pedir un token sin pasar por la caché
  (llamando `auth.obtain_session_tokens` directo, no la fixture).
- **[Riesgo] El mapeo rol→variable de entorno está hardcodeado en
  `auth.py`; añadir un tercer rol requiere tocar este archivo.**
  → Mitigación: aceptable por ahora — `docs.md` solo documenta
  Admin/SuperAdmin sin distinción de comportamiento; se documenta como
  punto a extender si el proyecto agrega roles.