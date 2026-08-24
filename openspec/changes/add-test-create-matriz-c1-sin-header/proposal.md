## Why

Tipo de change: `add-test-create-matriz-c1-sin-header` — matriz CSV completa (una fila = un caso), no un `TC-XXX` individual. Implementa el contexto de aplicación `c1-sin-header` (sin `type`/`file`/`header`/`header_var`) del endpoint `createTemplate` (Gupshup templates, slug corto `create`), a partir de `inputs/Create/create-matriz-c1-sin-header.csv`.

**Excepción declarada a la convención de un tipo por change**: `src/framework/matrix.py`, `generators.py` y `mirror.py` no existen. `2026-08-06-add-test-framework-base` (archivado, todas sus tareas completas) nunca construyó estos tres módulos — solo cubrió la ruta `TC-XXX` (config, cliente HTTP, engine BD, `resolve()`, fixtures). No hay change de infraestructura previo del que depender: por decisión explícita del QA, **este change absorbe también la construcción de esos tres módulos**, en vez de abrir un change de infraestructura separado (el patrón que sí siguieron `add-framework-auth-session-fixture` y `add-framework-audit-logs-client`). Es una excepción puntual a la regla de `config.yaml` de que cada change declara un único tipo — ver `design.md` para las decisiones de forma/API de los tres módulos, y la tarea de actualizar `openspec/config.yaml` § "Arquitectura objetivo" una vez implementados (deja de haber freno duro para los changes de matriz futuros).

**Inconsistencia interna detectada en el CSV (no se modifica el archivo)**: en 4 filas, `body_var` no coincide con la cantidad de variables `{{n}}` de `body` en la misma fila, violando la regla cruzada que el propio `docs.md` documenta (`body` ↔ `body_var`, coincidencia de conteo):

| Caso | `body` (variables) | `body_var` en el CSV | `body_var` corregido |
|---|---|---|---|
| V1 | 0 variables | espera 1 elemento | `(ausente)` |
| V3 | 0 variables | espera 1 elemento | `(ausente)` |
| V7 | 0 variables | espera 1 elemento | `(ausente)` |
| V5 | 10 variables | `(ausente)` | `(arreglo con 10 elementos correspondientes a las variables de body)` |

Se resuelve con el valor corregido (coherente con la regla cruzada de `docs.md`), documentado aquí; el CSV de `inputs/` permanece sin tocar.

**Riesgo de ambiente a verificar por el QA** (no bloquea el proposal): las filas V1/V3/V5/V7 usan `account_id = 1` ("mínimo del rango") como cuenta válida existente para un caso de éxito. El único `account_id` de prueba confirmado hasta ahora en el proyecto es `65` (`GLB-account_id_valido`). Si la cuenta `1` no existe en el ambiente, estas 4 filas fallarán por causa ambiental, no por el test — se deja como tarea de verificación, no se asume.

## What Changes

- Construye `src/framework/matrix.py`: una única función pura `build_payload(base_request, deviations, field_types)` que aplica la semántica `(ausente)`/`(vacío)`/serialización `String (arreglo JSON)` sobre valores ya resueltos — **sin parsear el CSV en runtime**. El CSV se lee una sola vez, en tiempo de autoría: sus 73 filas quedan transcritas como tabla Python literal dentro del test (ver decisión 1 de `design.md`).
- Construye `src/framework/generators.py`: registro de generadores (Ruta 2) con el primero, `unique_lowercase(length)`, y el CLI `--catalog` que regenera `docs/generators-catalog.md` desde los docstrings.
- Construye `src/framework/mirror.py`: assert de espejo entrada→respuesta por key JSON exacta, ejecutado solo en casos de éxito (`status < 400`, incluye `206`).
- Añade el test parametrizado `test_matriz_create_c1_sin_header` — ya no bloqueado — que cubre las **73 filas** del CSV como un único `pytest.mark.parametrize`, consumiendo los tres módulos anteriores.
- Declara **101 variables `MTZ-create-*`** derivadas de las celdas de la matriz (ver catálogo completo abajo). Los nombres quedan fijos tal como están listados aquí — no se recalculan en runtime (ver decisión 1 de `design.md`).
- Declara **8 variables `GLB-create-*` de resolución sembrada** (Ruta 3), con placeholder `[REQUIERE RESPUESTA: ...]` y tarea de siembra.
- Declara **1 excepción**: el campo `api_access_token` en su valor `(token válido correspondiente a la sesión)` **no** se materializa en `matrix_values:` — se resuelve llamando a `auth.obtain_session_tokens("Admin", account_id=<account_id de la fila>, ...)`, el helper ya existente del change archivado `add-framework-auth-session-fixture` (2026-08-06). Solo los 2 casos que rompen deliberadamente el header (`I64` ausente, `I65` inválido/expirado) necesitan valor propio.
- **Alcance de rol**: este change cubre únicamente el rol `Admin` (credenciales `USR_ADMIN`/`PSW_ADMIN` de `.env`). El rol `SuperAdmin` no se implementa en este change.
- `buttons` y `body_var` se materializan como literales JSON completos dentro de su propia variable `MTZ-create-*` (Opción A, acordada): no se abre `design.md` para un patrón de composición reutilizable.
- Mirror keys: **ninguna** — `docs.md` declara explícitamente "No hay campos que validar en esta sección".
- Hash SHA-256 del CSV implementado: `81eeefcf5e42edd90e926c7e31d23a45cb0a122ed8483f2e45a80b38a6bfda8b`. No existe change archivado previo sobre este CSV con el que comparar.

### Inventario de casos (73 filas → V1–V8, I1–I65)

| ID | # original | HTTP | Prioridad |
|---|---|---|---|
| V1 | 1 | 200 | alto |
| V2 | 2 | 200 | alto |
| V3 | 3 | 200 | alto |
| V4 | 4 | 200 | alto |
| V5 | 5 | 200 | alto |
| V6 | 6 | 200 | alto |
| V7 | 7 | 200 | alto |
| V8 | 8 | 200 | alto |
| I1 | 9 | 400 | alto |
| I2 | 10 | 400 | alto |
| I3 | 11 | 401 | alto |
| I4 | 12 | 401 | alto |
| I5 | 13 | 400 | alto |
| I6 | 14 | 400 | alto |
| I7 | 15 | 400 | medio |
| I8 | 16 | 400 | medio |
| I9 | 17 | 400 | medio |
| I10 | 18 | 400 | alto |
| I11 | 19 | 400 | medio |
| I12 | 20 | 400 | alto |
| I13 | 21 | 400 | medio |
| I14 | 22 | 400 | medio |
| I15 | 23 | 400 | alto |
| I16 | 24 | 400 | alto |
| I17 | 25 | 400 | alto |
| I18 | 26 | 400 | alto |
| I19 | 27 | 400 | medio |
| I20 | 28 | 400 | alto |
| I21 | 29 | 400 | alto |
| I22 | 30 | 400 | alto |
| I23 | 31 | 400 | medio |
| I24 | 32 | 400 | alto |
| I25 | 33 | 400 | alto |
| I26 | 34 | 400 | alto |
| I27 | 35 | 400 | alto |
| I28 | 36 | 400 | alto |
| I29 | 37 | 400 | alto |
| I30 | 38 | 400 | alto |
| I31 | 39 | 400 | alto |
| I32 | 40 | 400 | medio |
| I33 | 41 | 400 | medio |
| I34 | 42 | 400 | medio |
| I35 | 43 | 400 | medio |
| I36 | 44 | 400 | alto |
| I37 | 45 | 400 | alto |
| I38 | 46 | 400 | alto |
| I39 | 47 | 400 | medio |
| I40 | 48 | 400 | alto |
| I41 | 49 | 400 | alto |
| I42 | 50 | 400 | medio |
| I43 | 51 | 400 | alto |
| I44 | 52 | 400 | alto |
| I45 | 53 | 400 | alto |
| I46 | 54 | 400 | medio |
| I47 | 55 | 400 | alto |
| I48 | 56 | 400 | medio |
| I49 | 57 | 400 | alto |
| I50 | 58 | 400 | alto |
| I51 | 59 | 400 | medio |
| I52 | 60 | 400 | medio |
| I53 | 61 | 400 | medio |
| I54 | 62 | 400 | alto |
| I55 | 63 | 400 | alto |
| I56 | 64 | 400 | alto |
| I57 | 65 | 400 | alto |
| I58 | 66 | 400 | alto |
| I59 | 67 | 400 | alto |
| I60 | 68 | 400 | alto |
| I61 | 69 | 400 | alto |
| I62 | 70 | 400 | alto |
| I63 | 71 | 400 | alto |
| I64 | 72 | 401 | alto |
| I65 | 73 | 401 | alto |

Orden de escritura/revisión sugerido: primero todas las filas `Prioridad: alto` (V1–V8 y la mayoría de I1–I65), luego `medio`. Ninguna fila de este CSV es `bajo`. La prioridad no filtra qué se implementa — las 73 filas van en el mismo test parametrizado.

### Catálogo de variables `MTZ-create-*` (101, Ruta 1 estática salvo lo indicado)

| Variable | Indicación original | Casos |
|---|---|---|
| MTZ-create-account_id-ausente | (ausente) | I1 |
| MTZ-create-account_id-minimo_del_rango | (mínimo del rango, 1) | V1,V3,V5,V7,I5–I65 (correlativos) |
| MTZ-create-account_id-vacio | (vacío) | I2 |
| MTZ-create-account_id-65 | 65 | V2,V4,V6,V8 |
| MTZ-create-api_access_token-ausente | (ausente) — no se envía el header | I64 |
| MTZ-create-api_access_token-token_invalido_o_expirado | (token inválido o expirado) | I65 |
| MTZ-create-apps-arreglo_json_vacio | (arreglo JSON vacío, sin elementos) | I27 |
| MTZ-create-apps-arreglo_solo_letras | (arreglo con elemento compuesto solo de letras, no es un UUID) | I32 |
| MTZ-create-apps-arreglo_solo_numeros | (arreglo con elemento compuesto solo de números, no es un UUID) | I33 |
| MTZ-create-apps-arreglo_con_elemento_con_caracteres_especiales | (arreglo con elemento con caracteres especiales, no es un UUID) | I34 |
| MTZ-create-apps-arreglo_con_un_elemento_que_no | (arreglo con un elemento que no es un UUID válido) | I28 |
| MTZ-create-apps-ausente | (ausente) | I25 |
| MTZ-create-apps-no_es_un_arreglo_json_valido | (no es un arreglo JSON válido) | I29 |
| MTZ-create-apps-vacio | (vacío) | I26 |
| MTZ-create-body-ausente_cuando_category_authentication | (ausente cuando category≠AUTHENTICATION) | I41 |
| MTZ-create-body-longitud_1025 | (longitud 1025, por encima del máximo) | I43 |
| MTZ-create-body-longitud_maxima | (longitud máxima, 1024 caracteres) | V4 |
| MTZ-create-body-longitud_minima | (longitud mínima, 1 carácter) | V3 |
| MTZ-create-body-mas_de_10_variables | (más de 10 variables) | I44 |
| MTZ-create-body-texto_compuesto_unicamente_por_variables | (texto compuesto únicamente por variables, sin texto fijo alrededor) | I46 |
| MTZ-create-body-texto_con_el_maximo_de_10 | (texto con el máximo de 10 variables secuenciales) | V5 |
| MTZ-create-body-texto_con_el_minimo_de_variables | (texto con el mínimo de variables, 1 variable {{1}}) | V6 |
| MTZ-create-body-texto_tipico_con_variables_secuenciales_1 | (texto típico con variables secuenciales {{1}} a {{3}}) | V2,V8 |
| MTZ-create-body-texto_tipico_sin_variables | (texto típico sin variables, longitud media) | V1,V7,I1–I40,I47–I65 (correlativos) |
| MTZ-create-body-vacio | (vacío) | I42 |
| MTZ-create-body-variables_fuera_de_secuencia | (variables fuera de secuencia, con huecos o repeticiones) | I45 |
| MTZ-create-body_var-arreglo_con_10_elementos_correspondientes_a | **[corregido]** (arreglo con 10 elementos correspondientes a las variables de body) | V5 |
| MTZ-create-body_var-arreglo_con_exactamente_1_elemento | (arreglo con exactamente 1 elemento, límite mínimo de variables) | V6 |
| MTZ-create-body_var-arreglo_con_tres_elementos | (arreglo con tres elementos, valores típicos) | V2,V8 |
| MTZ-create-body_var-arreglo_con_un_elemento_correspondiente_a | (arreglo con un elemento correspondiente a una variable de body) | I1–I46,I53–I65 (correlativos, sin V1/V3/V7) |
| MTZ-create-body_var-ausente_cuando_body_contiene_variables | (ausente cuando body contiene variables) | I47 |
| MTZ-create-body_var-ausente | **[corregido]** (ausente) | V1,V3,V7 |
| MTZ-create-body_var-cantidad_de_elementos_distinta_a_la | (cantidad de elementos distinta a la cantidad de variables en body) | I50 |
| MTZ-create-body_var-elemento_con_4_o_mas_espacios | (elemento con 4 o más espacios consecutivos) | I52 |
| MTZ-create-body_var-elemento_con_salto_de_linea | (elemento con salto de línea) | I51 |
| MTZ-create-body_var-elemento_de_longitud_maxima | (elemento de longitud máxima, 1024 caracteres) | V4 |
| MTZ-create-body_var-no_es_un_arreglo_json_valido | (no es un arreglo JSON válido) | I49 |
| MTZ-create-body_var-vacio | (vacío) | I48 |
| MTZ-create-buttons-arreglo_json_vacio | (arreglo JSON vacío, sin elementos) | I57 |
| MTZ-create-buttons-arreglo_con_botones_quick_reply_y | (arreglo con botones QUICK_REPLY y PHONE_NUMBER agrupados por tipo, dentro de límites) | V6 |
| MTZ-create-buttons-arreglo_con_botones_quick_reply | (arreglo con botones QUICK_REPLY, URL y PHONE_NUMBER agrupados por tipo, dentro de límites) | V5 |
| MTZ-create-buttons-arreglo_con_botones_url_y_phone | (arreglo con botones URL y PHONE_NUMBER agrupados por tipo, dentro de límites) | V7 |
| MTZ-create-buttons-arreglo_con_botones_agrupados_por_tipo | (arreglo con botones agrupados por tipo, cantidad típica) | V3 |
| MTZ-create-buttons-arreglo_con_el_maximo_de_10 | (arreglo con el máximo de 10 botones en total) | V4 |
| MTZ-create-buttons-arreglo_con_un_boton_quick_reply | (arreglo con un botón QUICK_REPLY válido) | V2 |
| MTZ-create-buttons-ausente | (ausente) | V1,V8,I1–I55,I64,I65 (correlativos) |
| MTZ-create-buttons-botones_del_mismo_tipo_no_agrupados | (botones del mismo tipo no agrupados, intercalados) | I63 |
| MTZ-create-buttons-mas_de_1_boton_phone_number | (más de 1 botón PHONE_NUMBER) | I62 |
| MTZ-create-buttons-mas_de_10_botones_quick_reply | (más de 10 botones QUICK_REPLY) — disparador Volumen, resuelto en Ruta 1 estática en este change (ver nota abajo) | I60 |
| MTZ-create-buttons-mas_de_10_botones_en_total | (más de 10 botones en total) | I59 |
| MTZ-create-buttons-mas_de_2_botones_url | (más de 2 botones URL) | I61 |
| MTZ-create-buttons-no_es_un_arreglo_json_valido | (no es un arreglo JSON válido) | I58 |
| MTZ-create-buttons-vacio | (vacío) | I56 |
| MTZ-create-category-ausente | (ausente) | I16 |
| MTZ-create-category-caracteres_especiales | (caracteres especiales) | I19 |
| MTZ-create-category-tipo_de_dato_incorrecto | (tipo de dato incorrecto, numérico) | I18 |
| MTZ-create-category-vacio | (vacío) | I17 |
| MTZ-create-category-valor_de_la_lista_blanca_en | (valor de la lista blanca en minúsculas, ej. marketing) | I20 |
| MTZ-create-category-valor_fuera_de_la_lista_blanca | (valor fuera de la lista blanca) | I15 |
| MTZ-create-category-marketing | MARKETING | V1,V3,V5,V7,I1–I14,I21–I65 (correlativos) |
| MTZ-create-category-utility | UTILITY | V2,V4,V6,V8 |
| MTZ-create-expiration-ausente | (ausente) | V1–V8,I1–I65 (todos) |
| MTZ-create-file-ausente | (ausente) | V1–V8,I1–I65 (todos) |
| MTZ-create-footer-ausente | (ausente) | V4 |
| MTZ-create-footer-cadena_de_caracteres_especiales | (cadena de caracteres especiales) | V7 |
| MTZ-create-footer-cadena_de_solo_numeros | (cadena de solo números) | V6 |
| MTZ-create-footer-cadena_que_alterna_entre_letras | (cadena que alterna entre letras, números y caracteres especiales) | V8 |
| MTZ-create-footer-cadena_que_alterna_entre_mayusculas_y | (cadena que alterna entre mayúsculas y minúsculas) | V5 |
| MTZ-create-footer-contiene_una_variable_1 | (contiene una variable {{1}}, prohibido) | I55 |
| MTZ-create-footer-longitud_61 | (longitud 61, por encima del máximo) | I54 |
| MTZ-create-footer-longitud_maxima | (longitud máxima, 60 caracteres) | V3 |
| MTZ-create-footer-longitud_minima | (longitud mínima, 1 carácter) | V2 |
| MTZ-create-footer-texto_tipico_sin_variables | (texto típico sin variables, longitud media) | V1,I1–I52,I56–I65 (correlativos) |
| MTZ-create-footer-vacio | (vacío) | I53 |
| MTZ-create-header-ausente | (ausente) | V1–V8,I1–I65 (todos) |
| MTZ-create-header_var-ausente | (ausente) | V1–V8,I1–I65 (todos) |
| MTZ-create-lang-ausente | (ausente) | I22 |
| MTZ-create-lang-vacio | (vacío) | I23 |
| MTZ-create-lang-valor_de_la_lista_blanca_en | (valor de la lista blanca en minúsculas, ej. en_us) | I24 |
| MTZ-create-lang-valor_fuera_de_la_lista_blanca | (valor fuera de la lista blanca) | I21 |
| MTZ-create-lang-en_us | en_US | V1,V3,V5,V7,I1–I20,I25–I65 (correlativos) |
| MTZ-create-lang-es_mx | es_MX | V2,V4,V6,V8 |
| MTZ-create-name-ausente | (ausente) | I10 |
| MTZ-create-name-contiene_caracteres_especiales_no_permitidos | (contiene caracteres especiales no permitidos) | I8 |
| MTZ-create-name-contiene_espacios | (contiene espacios) | I9 |
| MTZ-create-name-contiene_mayusculas | (contiene mayúsculas, viola el patrón) | I7 |
| MTZ-create-name-contiene_punto_decimal | (contiene punto decimal, ej. 12.5) | I14 |
| MTZ-create-name-contiene_signo_negativo | (contiene signo negativo, ej. -123) | I13 |
| MTZ-create-name-longitud_180 | (longitud 180, por encima del máximo) | I6 |
| MTZ-create-name-longitud_2 | (longitud 2, por debajo del mínimo) | I5 |
| MTZ-create-name-nombre_unico_de_longitud_maxima | (nombre único de longitud máxima, 179 caracteres) — Ruta 2, disparador Unicidad | V3,V6 |
| MTZ-create-name-nombre_unico_de_longitud_minima | (nombre único de longitud mínima, 3 caracteres) — Ruta 2, disparador Unicidad | V2,V5,V8 |
| MTZ-create-name-nombre_unico_no_usado_antes | (nombre único no usado antes, longitud típica, minúsculas/dígitos/guion bajo) — Ruta 2, disparador Unicidad | V1,V4,V7,I1–I4,I15–I65 (correlativos) |
| MTZ-create-name-vacio | (vacío) | I11 |
| MTZ-create-security-ausente | (ausente) | V1–V8,I1–I65 (todos) |
| MTZ-create-type-ausente | (ausente) | V1–V8,I1–I35,I41–I65 (correlativos) |
| MTZ-create-type-caracteres_especiales | (caracteres especiales) | I39 |
| MTZ-create-type-tipo_de_dato_incorrecto | (tipo de dato incorrecto, numérico) | I38 |
| MTZ-create-type-vacio | (vacío) | I37 |
| MTZ-create-type-valor_de_la_lista_blanca_en | (valor de la lista blanca en minúsculas, ej. text) | I40 |
| MTZ-create-type-valor_fuera_de_la_lista_blanca | (valor fuera de la lista blanca) | I36 |

Las tres entradas `name-nombre_unico_*` son Ruta 2 (runtime): disparador de Unicidad ("no usado antes"). El generador `unique_lowercase(length)` que las resuelve **sí se implementa en este change** — ver `design.md` (decisión 5) y `tasks.md` § 3. `MTZ-create-buttons-mas_de_10_botones_quick_reply` (11 botones, contenido indiferente) es candidato a Ruta 2 por disparador de Volumen, pero `design.md` (Non-Goals) limita explícitamente el alcance de generadores de este change a `unique_lowercase` — por la regla de oro ("si dudas, estática") queda en Ruta 1: se materializa como un literal de 11 botones `QUICK_REPLY` escrito a mano en `MTZ-create-buttons-mas_de_10_botones_quick_reply`. Construir un generador genérico de "N botones" queda fuera de alcance, no bloquea este change.

### Variables `GLB-create-*` de resolución sembrada (Ruta 3, 8 variables)

| Variable | Origen (indicación) | Casos | Seed |
|---|---|---|---|
| GLB-create-account_id_ajeno | account_id: (cuenta existente, ajena a la sesión) | I4 | Un `account_id` entero, existente en el ambiente, distinto de `GLB-account_id_valido` (65). |
| GLB-create-account_id_inexistente | account_id: (cuenta inexistente) | I3 | Un `account_id` entero dentro del rango válido (1–2147483648) que no corresponda a ninguna cuenta real en el ambiente. |
| GLB-create-app_id_valido | apps: (arreglo con un único/múltiples UUID válido de una app existente de la cuenta) | V1,V3,V5,V7 y la mayoría de I1–I65 | Un UUID de app de Gupshup existente y habilitada, asociada a `GLB-account_id_valido`. |
| GLB-create-apps_ids_validos | apps: (arreglo con múltiples UUID válidos de apps existentes de la cuenta) | V2,V4,V6,V8 | Un segundo UUID de app existente y habilitada, asociada a la misma cuenta, distinto de `GLB-create-app_id_valido`. |
| GLB-create-app_id_inactivo | apps: (arreglo con UUID inexistente o inactivo) | I30 | Un UUID de app deshabilitada, o un UUID con formato válido que no exista en el ambiente. |
| GLB-create-app_id_otra_cuenta | apps: (arreglo con UUID que no pertenece a la cuenta) | I31 | Un UUID de app real, pero asociada a una cuenta distinta de `GLB-account_id_valido`. |
| GLB-create-app_id_valido_mutado | apps: (arreglo con un UUID existente modificando o agregando un carácter del string original) | I35 | No requiere siembra propia — se deriva mutando 1 carácter de `GLB-create-app_id_valido` una vez sembrado. Se documenta aquí porque depende de un valor sembrado, no porque necesite su propio dato de ambiente. |
| GLB-create-name_ya_utilizado | name: (nombre ya utilizado en una petición anterior) | I12 | Un `name` de plantilla que ya exista en Gupshup para alguna de las apps sembradas arriba (crear una plantilla previa con ese nombre, o reutilizar una existente). |

### Excepción: `api_access_token` no es un valor de matriz

| Campo/valor | Casos | Motivo |
|---|---|---|
| api_access_token: (token válido correspondiente a la sesión) | V1–V8, I1–I63 | Se resuelve invocando `framework.auth.obtain_session_tokens("Admin", settings=..., http_client=..., account_id=<account_id de la fila>)` — helper existente desde `add-framework-auth-session-fixture` (2026-08-06). Rol fijo `Admin` (ver "Alcance de rol" en What Changes); `SuperAdmin` queda fuera de este change. El fixture `session_tokens` de `tests/conftest.py` cachea por rol usando siempre `GLB-account_id_valido`, así que `matrix.py` invoca `obtain_session_tokens` directamente con el `account_id` de cada caso en vez de depender de ese fixture cacheado — ver `design.md`. |

## Capabilities

### New Capabilities
- `create`: contrato observable del endpoint `POST /integrations/gupshup_integrations/templates/create` (`createTemplate`) — validaciones de entrada, códigos HTTP de respuesta (200/206/400/401/500) y ausencia de mirror keys.

### Modified Capabilities
(ninguna — no existe spec previa para este endpoint)

## Impact

- **Código nuevo**: `src/framework/matrix.py`, `src/framework/generators.py`, `src/framework/mirror.py` (firmas en `design.md`), y `tests/test_matriz_create_c1_sin_header.py`.
- `inputs/Create/create-matriz-c1-sin-header.csv` — fuente de este change, sin modificar.
- `variables.yaml` — 101 entradas nuevas en `matrix_values:` y 8 en `globals:`.
- `openspec/config.yaml` — actualizar § "Arquitectura objetivo — pendiente de implementación": los tres módulos dejan de estar pendientes; ajustar la tabla de estado y la redacción del "Freno duro" (pasa de "no existen" a condicional, ya no aplica a este ni a futuros changes de matriz). Ver tarea dedicada en `tasks.md`.
- `docs/generators-catalog.md` — se regenera con `python -m framework.generators --catalog` tras añadir `unique_lowercase`.
- `tests/conftest.py` no se modifica: `matrix.py` invoca `auth.obtain_session_tokens` directamente con el `account_id` de cada caso en vez de depender del fixture `session_tokens` cacheado (ver `design.md`).
- **Precedente roto conscientemente**: este change ya no es puramente "un tipo por change" (`config.yaml` § Dos tipos de change proposal) — construye infraestructura de framework además de la matriz. Se documenta como excepción explícita en `Why`, no como nuevo patrón por defecto.
