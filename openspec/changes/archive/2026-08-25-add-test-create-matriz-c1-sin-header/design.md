## Context

`src/framework/` ya resuelve la ruta `TC-XXX` (`config.py`, `variables.py::resolve()`, `http.py`, `db.py`, fixtures de `conftest.py` — todo de `2026-08-06-add-test-framework-base`) y la sesión de autenticación (`auth.py::obtain_session_tokens`, de `add-framework-auth-session-fixture`). Ninguno de esos módulos aplica la semántica de payload de una matriz ni ejecuta el assert de espejo. Este documento fija la forma/API de `matrix.py`, `generators.py` y `mirror.py` — las decisiones aquí las va a consumir todo change de matriz futuro sobre cualquier endpoint, no solo `create`. Ver `proposal.md` — Why para la motivación de por qué esto se construye dentro de un change de matriz en vez de un change de infraestructura separado.

**Decisión de arquitectura tomada durante la exploración de este change**: el CSV de matriz se lee **una sola vez, en tiempo de autoría** (por el modelo, al aplicar este change), no en cada corrida de `pytest`. El test generado no abre ni parsea el CSV — las 73 filas quedan transcritas como una tabla Python literal dentro del propio archivo de test. Esto es exactamente el mismo patrón que ya usan los tests `TC-XXX` con `casos-prueba.md` (nunca lo parsean en runtime), y evita que la identidad de las variables `MTZ-*` dependa de una función de slugificación reproducible en runtime. `matrix.py` no incluye, por tanto, ningún parser de CSV.

## Goals / Non-Goals

**Goals:**
- Fijar la firma pública de `matrix.py` (una única función pura de construcción de payload) para que la consuman los changes de matriz de cualquier endpoint, sin acoplarla al formato del CSV.
- Fijar el registro de generadores de `generators.py` y su CLI `--catalog`.
- Fijar la firma de `mirror.py` y su alcance (qué valida, qué no).
- Eliminar la dependencia de runtime del CSV de entrada: el test no debe leer `inputs/<endpoint>/matriz-*.csv` para poder correr.

**Non-Goals:**
- `matrix.py` no parsea el CSV de matriz ni `docs.md`. La derivación de ids `V/I`, la petición base del contexto y la lista de mirror keys se derivan en tiempo de autoría (por el modelo, al escribir el test) — igual que hoy ningún test `TC-XXX` parsea `casos-prueba.md` en runtime.
- No se implementa Ruta 2 (runtime) más allá de un único generador (`unique_lowercase`) — el registro queda abierto para que futuros changes de matriz añadan generadores sin tocar la firma.
- No se implementa la anotación del sidecar (`reports/anotado-<nombre>.csv`) en este change — `reannotate.py` existe pero no cumple el contrato de matriz (delimitador, BOM, columna `Campo`, ids `[V<n>]`/`[I<n>]`); su reescritura queda fuera de alcance aquí porque no bloquea que el test de esta matriz corra ni pase.

## Decisions

**1. `matrix.py` expone una única función pública, `build_payload(base_request: dict, deviations: dict[str, Any], field_types: dict[str, str]) -> dict`, sin conocimiento del CSV ni de `variables.yaml`.**
`deviations` ya viene resuelto por el caller (test) a partir de `variables.yaml` (vía `resolve()` extendido, decisión 2) — `build_payload` solo aplica la semántica estructural sobre valores ya concretos: `(ausente)` omite la key (una `deviation` con valor sentinela, p. ej. `OMIT`, o simplemente ausente del dict), `(vacío)` la emite como `""`, y los campos cuyo `field_types[campo] == "String (arreglo JSON)"` (`apps`, `body_var`, `buttons` en este CSV) se serializan con `json.dumps(...)` antes de insertarse como string, nunca como arreglo nativo. Es una función pura, sin I/O, testeable con fixtures literales de un par de líneas.
Alternativa descartada (la explorada primero): que `matrix.py` parseara el CSV en runtime (`parse_matrix`/`MatrixCase`) y derivara el nombre de cada variable con una función de slug (`mtz_slug`) reproducida en cada corrida. Se descarta porque introduce dos riesgos que no aportan nada a cambio: (a) el test deja de poder correr si el CSV no está en la ruta esperada, y (b) el nombre de variable calculado en runtime debe coincidir byte a byte con el que quedó escrito a mano en `variables.yaml` — cualquier diferencia en el truncado del slug rompe la resolución en silencio. El proyecto ya asume (`config.yaml` § "Ingesta de artefactos", hash SHA-256 del CSV) que un CSV regenerado siempre exige un change nuevo, nunca una relectura automática — así que el "beneficio" de parsear en runtime (adaptarse a un CSV que cambió) no es algo que el proyecto quiera. En su lugar, el CSV se lee **una sola vez, en tiempo de autoría**: el modelo transcribe las 73 filas como una tabla Python literal (lista de `pytest.param(id=..., http=..., deviations={...})`) directamente en `test_matriz_create_c1_sin_header.py`, con los nombres `MTZ-create-*` ya fijos (los del catálogo de `proposal.md`, sin necesidad de regenerarlos ni diffearlos contra nada).

**2. `variables.py::resolve()` se extiende para reconocer el prefijo `MTZ-*` (además de `GLB-*`/`TC-XXX-*`), resuelto desde `variables.yaml → matrix_values`. Si el valor almacenado es un dict con `generator`/`params`, `resolve()` delega en `generators.py::run(name, **params)` en cada llamada (no cachea entre filas).**
Reutiliza el mecanismo de interpolación `{{...}}` ya construido y probado en `add-test-framework-base` en vez de crear un segundo resolutor paralelo solo para matrices. Alternativa descartada: que `matrix.py` resuelva `MTZ-*` por su cuenta, sin pasar por `resolve()` — duplicaría la lógica de precedencia/interpolación que `variables.py` ya tiene, con el riesgo de que ambas diverjan.

**3. `generators.py` expone un registro `GENERATORS: dict[str, Callable]`, la función `unique_lowercase(length: int) -> str` (docstring en español, primera línea = descripción corta para el catálogo), y un CLI `--catalog` que imprime una tabla Markdown a partir de esos docstrings.**
`unique_lowercase` cubre los 3 valores `name-nombre_unico_*` de esta matriz (disparador de Unicidad). El registro es un dict plano, no una clase/plugin system — no hay evidencia todavía de necesitar más que "nombre → función callable con kwargs".

**4. `mirror.py` expone `assert_mirror(check, request_payload: dict, response_json: dict, mirror_keys: list[str]) -> None`. `mirror_keys` lo declara el test (una lista literal, transcrita a mano de la sección `## Mirror keys en respuesta` de `docs.md`), no lo calcula `mirror.py` parseando el markdown.**
Igual que la decisión de Non-Goals: parsear `docs.md` en runtime introduciría una dependencia frágil (el markdown puede reformatearse sin que cambie el contrato) para un dato que ya es responsabilidad de autoría, igual que la petición base. Para este endpoint, `docs.md` declara "Mirror keys: ninguna", así que el test de esta matriz llama a `test_matriz_create_c1_sin_header` sin invocar `assert_mirror` en absoluto — pero la firma queda fija para el próximo endpoint que sí declare mirror keys. `assert_mirror` solo se invoca para casos con `status < 400` (incluye `206`); el caller es responsable de ese filtro, `assert_mirror` no recibe el status code.

**5. El test no usa el fixture `session_tokens` de `conftest.py` para el header de sesión — llama `auth.obtain_session_tokens("Admin", settings=settings, http_client=http_client, account_id=<account_id ya resuelto de la fila>)` directamente por caso parametrizado.**
El fixture cachea un solo token por rol usando siempre `GLB-account_id_valido`; esta matriz varía `account_id` fila por fila (1 y 65), así que cachear por rol devolvería el token equivocado en la mitad de las filas. Alternativa descartada: extender el fixture `session_tokens` para aceptar `account_id` como parámetro de fábrica — se descarta aquí porque cambiaría la firma que ya consumen los tests `TC-XXX` existentes; queda como posible mejora de un change de framework futuro, no de este.

## Risks / Trade-offs

- **[Riesgo] Transcribir 73 filas a mano (tabla Python literal) tiene más superficie de error humano/del modelo que un parser automático — un valor mal copiado no lo detecta ninguna herramienta.** → Mitigación: la transcripción usa como fuente única el catálogo de 101 variables `MTZ-create-*` ya validado en `proposal.md` (no se vuelve a leer el CSV celda por celda "a ojo"); el unit test de `build_payload` cubre la semántica estructural, y la corrida bloqueante final (`tasks.md` §12) es la que expone cualquier caso mal transcrito.
- **[Riesgo] Extender `resolve()` para `MTZ-*` (decisión 2) puede introducir una regresión en la resolución `GLB-*`/`TC-XXX-*` ya usada por los tests `TC-XXX` existentes.** → Mitigación: `MTZ-*` es un prefijo nuevo y mutuamente exclusivo — la rama de código para `GLB-*`/`TC-XXX-*` no se modifica, solo se añade una rama adicional. Añadir un test de regresión que corra la suite `TC-XXX` existente sin cambios de resultado.
- **[Riesgo] `unique_lowercase` sin memoria entre corridas puede repetir un nombre ya usado en una ejecución anterior contra el mismo ambiente (colisión real en Gupshup, no solo en el CSV).** → Mitigación: fuera de alcance resolverlo con estado persistido en este change — se documenta como limitación conocida; si ocurre, es indistinguible de un hallazgo y se trata como tal (`xfail` + entrada en `hallazgos.md`) hasta que un change de framework futuro decida sembrar un contador o sufijo temporal.

## Migration Plan

No aplica — módulos nuevos, sin código previo que migrar. `reannotate.py` no se toca ni se reescribe en este change (Non-Goals).

## Open Questions

(ninguna — las decisiones de firma quedan fijas arriba; cualquier ajuste futuro de firma es un change de framework explícito, no una re-discusión por endpoint, igual que el precedente de `add-test-framework-base`)
