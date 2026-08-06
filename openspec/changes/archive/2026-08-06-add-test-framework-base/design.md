## Context

Ningún artefacto de framework existe aún en el repo. Este documento fija
las decisiones de forma/API de los módulos que todos los `TC-XXX`
posteriores consumirán (`resolve()`, fixtures de `conftest.py`, cliente
HTTP, engine de BD) — decisiones que, una vez tomadas aquí, no deberían
volver a discutirse por TC individual. Ver `proposal.md` — Why para la
motivación.

## Goals / Non-Goals

**Goals:**
- Fijar la firma pública de `resolve()`, `client()`, `engine()` y las
  fixtures de `conftest.py` para que los changes `add-test-<endpoint>-tc-<nnn>`
  las consuman sin reinterpretarlas.
- Fijar la regla de precedencia y aislamiento de `{{...}}` una sola vez
  (no por TC).
- Fijar cómo se captura el cURL de la última request para adjuntarlo al
  reporte HTML en fallos, sin acoplar cada test a ese mecanismo.

**Non-Goals:**
- No se definen los `pytest.mark` de negocio por endpoint (eso lo
  declara cada TC).
- No se implementa retry/backoff en el cliente HTTP ni pooling
  avanzado de conexiones BD — se usa lo que httpx/SQLAlchemy ofrecen por
  defecto.
- No se valida el *contenido* de `variables.yaml`/`.env` (esquema,
  tipos por variable) más allá de los campos requeridos en `Settings`.

## Decisions

**1. `Settings` vía `pydantic-settings`, un solo objeto para todo el proyecto.**
`Settings(BaseSettings)` con `model_config = SettingsConfigDict(env_file=".env", extra="ignore")`
carga `.env` una vez por sesión (fixture `settings`, scope=session).
Alternativa descartada: leer `os.environ` a mano — se pierde validación
de tipos (`DB_PORT` como `int`) y el error temprano si falta una env var
requerida.

**2. `resolve(payload, tc_id, *, settings=None, variables=None)` — firma
de 2 argumentos lógicos, carga perezosa y cacheada de `Settings`/`variables.yaml` cuando no se inyectan.**
El caller de producción (`resolve_payload` en `conftest.py`) usa
`functools.partial(resolve, tc_id=tc_id)`, sin bindear `settings` ni
`variables` — por lo tanto `resolve()` debe poder resolver ambos por sí
mismo en la llamada real. Para no repetir I/O en cada placeholder,
`variables.py` mantiene un loader de `Settings` y uno de
`load_variables()` cacheados a nivel de módulo (`functools.lru_cache`),
invocados solo si el caller no pasó `settings=`/`variables=`
explícitamente. Los parámetros con keyword-only por defecto `None`
existen para permitir inyección en pruebas unitarias del propio
framework (pasar un `Settings`/dict de prueba sin tocar `.env` ni
`variables.yaml` reales) sin cambiar la firma que consume
`resolve_payload`. Alternativa descartada: exigir que el caller siempre
inyecte `settings`/`variables` — rompe la firma de 2 argumentos pedida
explícitamente y obligaría a que `resolve_payload` bindeara 3 valores
en el `partial`, no solo `tc_id`.

**3. Precedencia `GLB-*`: `Settings` antes que `variables.yaml → globals`.**
Motivo: `Settings` cubre secretos y config sensible (`.env`, no
versionado); si una clave `GLB-*` existe en ambos, la fuente no
versionada gana porque representa el valor real del ambiente del QA en
ejecución. Alternativa descartada: `variables.yaml` gana — permitiría
que un valor versionado (compartido en git) sobrescriba silenciosamente
un secreto de ambiente.

**4. `TC-XXX-*` se resuelve solo si el prefijo coincide con `tc_id` — `KeyError` explícito en caso contrario.**
Motivo (`openspec/config.yaml` — Convención de variables): los datos
sembrados de un TC pueden dejar la BD en un estado inválido para otros
casos, por lo que reusar una variable `TC-XXX-*` fuera de su TC es un
error de autor, no un caso a tolerar silenciosamente. El `KeyError` debe
incluir el nombre de la variable y el `tc_id` esperado vs. recibido para
que el mensaje sea autoexplicativo en el reporte de pytest.

**5. Preservación de tipo solo cuando el placeholder ocupa el string completo.**
`"{{GLB-account_id_valido}}"` (string completo) devuelve el tipo nativo
del valor resuelto (int, bool, etc.); `"id: {{GLB-account_id_valido}}"`
(placeholder embebido) siempre devuelve `str` vía interpolación de
texto. Esto evita ambigüedad: no hay forma de "preservar tipo" dentro de
un string parcial.

**6. Captura de cURL para el reporte HTML vía atributo en el cliente, no vía hook de httpx.**
`http_client` (fixture session) es un `httpx.Client` estándar; el
`to_curl()` se invoca en el hook `pytest_runtest_makereport` leyendo
`http_client.last_request` (atributo simple asignado tras cada
`.request()`/`.get()`/etc. que el propio test dispare). Alternativa
descartada: un *event hook* de httpx (`httpx.Client(event_hooks=...)`)
— es más "idiomático" pero dispersa el estado fuera del objeto cliente y
complica leerlo desde el hook de pytest sin una fixture intermedia.
Se documenta como convención: los tests que quieran cURL en el reporte
deben usar `http_client` directamente (no crear clientes httpx propios).

**7. `db_conn` es `scope=function`, nunca `session`.**
Motivo (`openspec/config.yaml` — Aserciones en base de datos): no se
abren transacciones desde los tests y cada función de test debe obtener
su propia conexión AUTOCOMMIT, evitando estado de conexión colgado entre
tests si uno falla a mitad de una query.

**8. `reannotate.py` matchea por columna `TC`/`id` contra nodeids que *contengan* `TC-XXX`, no por igualdad exacta de nodeid.**
Motivo: el nodeid real depende del nombre de archivo/función
(`test_templates_delete_tc_001.py::test_...`), que no se fija en este
change; solo el marcador `@pytest.mark.tc("TC-XXX")` — visible en
`resultados.json` vía `pytest-json-report`— es estable. El matching es
por substring `TC-XXX` extraído del nodeid o de los metadatos del ítem
en `resultados.json`, no por comparación exacta de string.

## Risks / Trade-offs

- **[Riesgo] Cambiar la firma de `resolve()`/fixtures después de que
  existan TC implementados rompe todos los tests ya generados.**
  → Mitigación: estas firmas quedan fijadas en este change precisamente
  para evitarlo; cualquier cambio futuro de firma requiere un change de
  framework explícito (no un TC), con impacto documentado.
- **[Riesgo] `extra="ignore"` en `Settings` oculta typos en nombres de
  env vars (una var mal escrita en `.env` no genera error, solo se
  ignora).**
  → Mitigación: los 7 campos requeridos (`GLB_URL_BASE`,
  `GLB_TOKEN_ADMIN`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`,
  `DB_PASSWORD`) sin default hacen que pydantic falle igual si falta
  alguno; el smoke test (`SMOKE-001`) detecta esto en cada corrida.
- **[Riesgo] El atributo `last_request` en `http_client` es mutable y
  compartido (fixture de sesión) — si pytest-xdist se habilitara a
  futuro, dos tests en paralelo podrían pisarse el cURL mostrado en el
  reporte.**
  → Mitigación: fuera de alcance por ahora (`openspec/config.yaml` no
  menciona ejecución paralela); documentar como no soportado si se
  adopta xdist más adelante.
