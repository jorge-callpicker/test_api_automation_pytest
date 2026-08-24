## Context

`src/framework/` ya resuelve la ruta `TC-XXX` (`config.py`, `variables.py::resolve()`, `http.py`, `db.py`, fixtures de `conftest.py` — todo de `2026-08-06-add-test-framework-base`) y la sesión de autenticación (`auth.py::obtain_session_tokens`, de `add-framework-auth-session-fixture`). Ninguno de esos módulos parsea CSV de matriz, deriva ids `V/I`, ni ejecuta el assert de espejo. Este documento fija la forma/API de `matrix.py`, `generators.py` y `mirror.py` — las decisiones aquí las va a consumir todo change de matriz futuro sobre cualquier endpoint, no solo `create`. Ver `proposal.md` — Why para la motivación de por qué esto se construye dentro de un change de matriz en vez de un change de infraestructura separado.

## Goals / Non-Goals

**Goals:**
- Fijar la firma pública de `matrix.py` (parseo, derivación de ids, slug de indicación, construcción de payload) para que la consuman los changes de matriz de cualquier endpoint.
- Fijar el registro de generadores de `generators.py` y su CLI `--catalog`.
- Fijar la firma de `mirror.py` y su alcance (qué valida, qué no).
- Resolver, en la implementación, el riesgo de que el slug derivado en runtime no coincida con los 101 nombres `MTZ-create-*` ya escritos a mano en este proposal.

**Non-Goals:**
- `matrix.py` no parsea `docs.md`. La petición base del contexto y la lista de mirror keys se derivan de `docs.md` en tiempo de autoría (por el modelo, al escribir el test), no en tiempo de ejecución — igual que hoy ningún test `TC-XXX` parsea `casos-prueba.md` en runtime.
- No se implementa Ruta 2 (runtime) más allá de un único generador (`unique_lowercase`) — el registro queda abierto para que futuros changes de matriz añadan generadores sin tocar la firma.
- No se implementa la anotación del sidecar (`reports/anotado-<nombre>.csv`) en este change — `reannotate.py` existe pero no cumple el contrato de matriz (delimitador, BOM, columna `Campo`, ids `[V<n>]`/`[I<n>]`); su reescritura queda fuera de alcance aquí porque no bloquea que el test de esta matriz corra ni pase.

## Decisions

**1. `matrix.py` expone `parse_matrix(csv_path) -> list[MatrixCase]`, un `NamedTuple` con `id` (`"V1"`/`"I1"`), `campo_num` (el número original de la columna `Campo`), `http_code`, `priority`, y `values: dict[str, str]` (campo → texto crudo de la celda, sin resolver).**
Separa el parseo (estructura del CSV) de la resolución (qué literal/generador/seed corresponde a cada celda) — la resolución vive en `variables.yaml`, no en el CSV. Alternativa descartada: que `parse_matrix` devuelva ya los valores resueltos — acoplaría el parser a la convención de nombres `MTZ-*`, que puede evolucionar independientemente del formato del CSV.

**2. `matrix.py` expone `mtz_slug(cell_text: str, *, existing: set[str] = ()) -> str`, determinista y libre de colisión, siguiendo el algoritmo ya descrito en `openspec/config.yaml` § "Convención de variables MTZ" (minúsculas, sin acentos, `_` entre palabras, catálogo de abreviaturas preferente, truncado a las primeras palabras significativas) — y si el slug resultante ya está en `existing`, extiende el truncado palabra por palabra hasta desambiguar.**
Esta es la pieza que hoy no existe como función compartida: el catálogo de 101 variables de `proposal.md` se derivó con un script ad hoc de exploración, no con esta función. Al implementar, `mtz_slug` es la única fuente de verdad — se debe regenerar el catálogo corriendo `mtz_slug` sobre las 110 celdas únicas del CSV y diffear contra los nombres ya declarados en `proposal.md`; si algún nombre difiere (por ejemplo, si el truncado a 6 palabras de este documento no coincide con el de la función real), se corrige `variables.yaml` para que coincida con lo que `matrix.py` calcula en runtime, nunca al revés. Alternativa descartada: un archivo sidecar que mapee `(fila, campo) → nombre de variable` escrito a mano — evita el riesgo de desincronización pero reintroduce exactamente el tipo de artefacto generado-a-mano que el proyecto intenta evitar (como el sidecar de anotación, pero para nombres en vez de resultados).

**3. `matrix.py` expone `build_payload(case: MatrixCase, base_request: dict, field_types: dict[str, str], resolved: dict[str, Any]) -> dict`.**
`resolved` ya viene calculado por el caller (test) a partir de `variables.yaml` (vía `resolve()` extendido, decisión 4) — `build_payload` solo aplica la semántica estructural: `(ausente)` omite la key, `(vacío)` la emite como `""`, y los campos cuyo `field_types[campo] == "String (arreglo JSON)"` (`apps`, `body_var`, `buttons` en este CSV) se serializan con `json.dumps(...)` antes de insertarse como string, nunca como arreglo nativo. Alternativa descartada: que `build_payload` también resuelva `variables.yaml` — mezclaría dos responsabilidades (estructura del payload vs. origen del dato) y obligaría a pasarle `settings`/`http_client` sin necesitarlos para lo estructural.

**4. `variables.py::resolve()` se extiende para reconocer el prefijo `MTZ-*` (además de `GLB-*`/`TC-XXX-*`), resuelto desde `variables.yaml → matrix_values`. Si el valor almacenado es un dict con `generator`/`params`, `resolve()` delega en `generators.py::run(name, **params)` en cada llamada (no cachea entre filas).**
Reutiliza el mecanismo de interpolación `{{...}}` ya construido y probado en `add-test-framework-base` en vez de crear un segundo resolutor paralelo solo para matrices. Alternativa descartada: que `matrix.py` resuelva `MTZ-*` por su cuenta, sin pasar por `resolve()` — duplicaría la lógica de precedencia/interpolación que `variables.py` ya tiene, con el riesgo de que ambas diverjan.

**5. `generators.py` expone un registro `GENERATORS: dict[str, Callable]`, la función `unique_lowercase(length: int) -> str` (docstring en español, primera línea = descripción corta para el catálogo), y un CLI `--catalog` que imprime una tabla Markdown a partir de esos docstrings.**
`unique_lowercase` cubre los 3 valores `name-nombre_unico_*` de esta matriz (disparador de Unicidad). El registro es un dict plano, no una clase/plugin system — no hay evidencia todavía de necesitar más que "nombre → función callable con kwargs".

**6. `mirror.py` expone `assert_mirror(check, request_payload: dict, response_json: dict, mirror_keys: list[str]) -> None`. `mirror_keys` lo declara el test (una lista literal, transcrita a mano de la sección `## Mirror keys en respuesta` de `docs.md`), no lo calcula `mirror.py` parseando el markdown.**
Igual que la decisión de Non-Goals: parsear `docs.md` en runtime introduciría una dependencia frágil (el markdown puede reformatearse sin que cambie el contrato) para un dato que ya es responsabilidad de autoría, igual que la petición base. Para este endpoint, `docs.md` declara "Mirror keys: ninguna", así que el test de esta matriz llama a `test_matriz_create_c1_sin_header` sin invocar `assert_mirror` en absoluto — pero la firma queda fija para el próximo endpoint que sí declare mirror keys. `assert_mirror` solo se invoca para casos con `status < 400` (incluye `206`); el caller es responsable de ese filtro, `assert_mirror` no recibe el status code.

**7. `matrix.py` no invoca al fixture `session_tokens` de `conftest.py` para el header de sesión — llama `auth.obtain_session_tokens(role, settings=settings, http_client=http_client, account_id=case.values["account_id"] ya resuelto)` directamente por caso.**
El fixture cachea un solo token por rol usando siempre `GLB-account_id_valido`; esta matriz varía `account_id` fila por fila (1 y 65), así que cachear por rol devolvería el token equivocado en la mitad de las filas. Alternativa descartada: extender el fixture `session_tokens` para aceptar `account_id` como parámetro de fábrica — se descarta aquí porque cambiaría la firma que ya consumen los tests `TC-XXX` existentes; queda como posible mejora de un change de framework futuro, no de este.

## Risks / Trade-offs

- **[Riesgo] El catálogo de 101 nombres `MTZ-create-*` en `proposal.md` se derivó con un script de exploración, no con `mtz_slug()` real.** → Mitigación: decisión 2 ya lo declara — regenerar y diffear contra `proposal.md` al implementar; ajustar `variables.yaml` si hay diferencias, documentar el diff en `tasks.md` al marcarla completa.
- **[Riesgo] Extender `resolve()` para `MTZ-*` (decisión 4) puede introducir una regresión en la resolución `GLB-*`/`TC-XXX-*` ya usada por los tests `TC-XXX` existentes.** → Mitigación: `MTZ-*` es un prefijo nuevo y mutuamente exclusivo — la rama de código para `GLB-*`/`TC-XXX-*` no se modifica, solo se añade una rama adicional. Añadir un test de regresión que corra la suite `TC-XXX` existente sin cambios de resultado.
- **[Riesgo] `unique_lowercase` sin memoria entre corridas puede repetir un nombre ya usado en una ejecución anterior contra el mismo ambiente (colisión real en Gupshup, no solo en el CSV).** → Mitigación: fuera de alcance resolverlo con estado persistido en este change — se documenta como limitación conocida; si ocurre, es indistinguible de un hallazgo y se trata como tal (`xfail` + entrada en `hallazgos.md`) hasta que un change de framework futuro decida sembrar un contador o sufijo temporal.

## Migration Plan

No aplica — módulos nuevos, sin código previo que migrar. `reannotate.py` no se toca ni se reescribe en este change (Non-Goals).

## Open Questions

(ninguna — las decisiones de firma quedan fijas arriba; cualquier ajuste futuro de firma es un change de framework explícito, no una re-discusión por endpoint, igual que el precedente de `add-test-framework-base`)
