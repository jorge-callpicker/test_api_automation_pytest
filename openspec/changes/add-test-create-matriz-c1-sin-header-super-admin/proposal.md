## Why

**Tipo de change: matriz** (`add-test-<endpoint>-matriz-<nombre>`), sobre
`inputs/Create/create-matriz-c1-sin-header.csv`.

El change archivado `2026-08-25-add-test-create-matriz-c1-sin-header` implementó
esta matriz **únicamente para el rol `Admin`** y declaró explícitamente en su
`Why` que `SuperAdmin` quedaba fuera de alcance. Ese hueco sigue abierto: hoy
ninguna prueba del endpoint `createTemplate` se ejecuta con credenciales de
`SuperAdmin`, pese a que `framework.auth` soporta el rol desde
`2026-08-06-add-framework-auth-session-fixture` y el smoke `SMOKE-002` lo
ejercita en verde.

Lo que este change verifica es una **invariante de seguridad**: que un rol
elevado no relaje ninguna validación de campo del endpoint. Las 70 filas
aplicables de la matriz deben producir exactamente el mismo código HTTP con
`SuperAdmin` que con `Admin`.

### Desviación de cardinalidad — declarada y aceptada

La regla del repo dice *"hay exactamente un change por archivo CSV del
endpoint"*. Este change es el **segundo** sobre el mismo CSV, diferenciado por
rol y no por archivo. Es una decisión explícita del QA durante la exploración
previa: la alternativa (un CSV por rol generado desde el proyecto de
refinamiento) duplicaría 73 filas idénticas cuyo único delta es la credencial de
sesión, y desalinearía los dos artefactos ante cualquier regeneración futura.

Consecuencia práctica: el código vive en **el mismo archivo de test** que el rol
`Admin`, con un segundo arreglo `CASES_SA` y una segunda función de test. No se
crea `tests/test_matriz_create_c1_sin_header_super_admin.py`.

### CSV no regenerado

Hash SHA-256 actual: `949fbbcad7411fda40ea5cc95262d3c9739f551035f2584a00138860bbbe8a22`.
Es **idéntico** al registrado por el change archivado. El CSV no se regeneró
desde entonces; los ids `V<n>`/`I<n>` y los códigos esperados de `Admin` siguen
siendo válidos y sirven de referencia directa para los de `SuperAdmin`.

Verificación de limpieza: 0 celdas con prefijo de ID (`<campo>.<id> | <valor>`).
El CSV pasó la fase de limpieza del proyecto generador.

### Arquitectura objetivo — disponible

`src/framework/matrix.py` (`OMIT`, `build_payload`), `generators.py`
(`unique_lowercase`) y `mirror.py` existen y son los que ya usa el test de
`Admin` en verde. **No hay dependencia faltante**, así que este change no aplica
el freno de "escribir el proposal y detenerse": puede generar código de test.

## What Changes

### Alcance de rol

- Se añade cobertura del rol `SuperAdmin` (credenciales `USR_SADMIN`/`PSW_SADMIN`
  de `.env`, confirmadas sembradas por el QA y verificadas por `SMOKE-002` en
  `PASSED`).
- El rol `Admin` conserva su comportamiento actual. El único cambio en su ruta es
  estructural: el cuerpo del test se extrae a un helper compartido.

### Estructura del archivo de test

`tests/test_matriz_create_c1_sin_header.py` pasa de una a dos funciones de test,
ambas delegando en un helper privado con el cuerpo real (request, assert de
status, assert de JSON válido):

| Función | Arreglo | Rol | Casos |
|---|---|---|---|
| `test_matriz_create_c1_sin_header` | `CASES` | `Admin` | 73 |
| `test_matriz_create_c1_sin_header_super_admin` | `CASES_SA` | `SuperAdmin` | 70 |

### Convención de ids y numeración alineada

Los ids de `SuperAdmin` llevan prefijo `SA-`: `SA-V1..SA-V8` y `SA-I1..SA-I63`,
**con hueco en `SA-I4`**.

`SA-I<n>` apunta siempre al mismo caso del CSV que `I<n>`, de modo que comparar
ambos roles en el reporte es directo. Esto se aparta de la regla *"los ids son
posicionales dentro de su grupo"*: la numeración contigua habría desplazado todos
los ids a partir del cuarto (`SA-I30` sería el caso 31), rompiendo la
trazabilidad entre roles y contra el CSV. La desviación es deliberada y se
registra aquí.

### Casos omitidos — tres, con razón registrada

| Caso CSV | id `Admin` | HTTP esperado | Razón de la omisión |
|---|---|---|---|
| 12 | `I4` | 401 | `account_id` = `GLB-create-account_id_ajeno` (cuenta 60, ajena a la sesión). `SuperAdmin` **sí alcanza** cuentas ajenas, por lo que el endpoint respondería `200` y no el `401` que declara la matriz. El cruce legítimo de cuentas es funcionalidad preexistente que el QA asume correcta y declara fuera del alcance de prueba. |
| 72 | `I64` | 401 | Petición sin header `api-access-token`. No invoca `obtain_session_tokens`; el request es **byte-idéntico** en ambos roles. Duplicarlo no aporta información. |
| 73 | `I65` | 401 | Header con token estático inválido (`MTZ-create-api_access_token-token_invalido_o_expirado`). Tampoco abre sesión: mismo request en ambos roles. |

**Supuesto explícito, no verificado**: el `200` esperado en el caso 12 para
`SuperAdmin` implica que el endpoint omite la comprobación `payload.account_id`↔
`sesión` cuando el token pertenece a ese rol. El test actual abre la sesión
contra `GLB-account_id_valido` (65) aunque la fila declare 60, así que este
change **no ejercita** esa ruta ni la confirma. Se registra como supuesto del QA.

### Variables — cero nuevas

Este change **no extrae ninguna variable `MTZ-*` nueva del CSV** ni añade
`GLB-*`, y no introduce generadores en `src/framework/generators.py`. Los 70
casos de `SuperAdmin` consumen exactamente el subconjunto ya registrado en
`variables.yaml` por el change archivado, con las indicaciones originales del CSV
ya documentadas allí como comentario en la línea anterior a cada entrada.

**93 variables `MTZ-create-*` consumidas**, agrupadas por campo:

- `account_id` (4): `65`, `ausente`, `minimo_del_rango`, `vacio`
- `name` (12): `ausente`, `contiene_caracteres_especiales_no_permitidos`, `contiene_espacios`, `contiene_mayusculas`, `contiene_punto_decimal`, `contiene_signo_negativo`, `longitud_180`, `longitud_2`, `nombre_unico_de_longitud_maxima`, `nombre_unico_de_longitud_minima`, `nombre_unico_no_usado_antes`, `vacio`
- `category` (8): `ausente`, `caracteres_especiales`, `marketing`, `tipo_de_dato_incorrecto`, `utility`, `vacio`, `valor_de_la_lista_blanca_en`, `valor_fuera_de_la_lista_blanca`
- `lang` (6): `ausente`, `en_us`, `es_mx`, `vacio`, `valor_de_la_lista_blanca_en`, `valor_fuera_de_la_lista_blanca`
- `apps` (8): `arreglo_con_elemento_con_caracteres_especiales`, `arreglo_con_un_elemento_que_no`, `arreglo_json_vacio`, `arreglo_solo_letras`, `arreglo_solo_numeros`, `ausente`, `no_es_un_arreglo_json_valido`, `vacio`
- `type` (6): `ausente`, `caracteres_especiales`, `tipo_de_dato_incorrecto`, `vacio`, `valor_de_la_lista_blanca_en`, `valor_fuera_de_la_lista_blanca`
- `body` (12): `ausente_cuando_category_authentication`, `longitud_1025`, `longitud_maxima`, `longitud_minima`, `mas_de_10_variables`, `texto_compuesto_unicamente_por_variables`, `texto_con_el_maximo_de_10`, `texto_con_el_minimo_de_variables`, `texto_tipico_con_variables_secuenciales_1`, `texto_tipico_sin_variables`, `vacio`, `variables_fuera_de_secuencia`
- `body_var` (11): `arreglo_con_10_elementos_correspondientes_a`, `arreglo_con_exactamente_1_elemento`, `arreglo_con_tres_elementos`, `arreglo_con_un_elemento_correspondiente_a`, `ausente`, `cantidad_de_elementos_distinta_a_la`, `elemento_con_4_o_mas_espacios`, `elemento_con_salto_de_linea`, `elemento_de_longitud_maxima`, `no_es_un_arreglo_json_valido`, `vacio`
- `footer` (11): `ausente`, `cadena_de_caracteres_especiales`, `cadena_de_solo_numeros`, `cadena_que_alterna_entre_letras`, `cadena_que_alterna_entre_mayusculas_y`, `contiene_una_variable_1`, `longitud_61`, `longitud_maxima`, `longitud_minima`, `texto_tipico_sin_variables`, `vacio`
- `buttons` (15): `arreglo_con_botones_agrupados_por_tipo`, `arreglo_con_botones_quick_reply`, `arreglo_con_botones_quick_reply_y`, `arreglo_con_botones_url_y_phone`, `arreglo_con_el_maximo_de_10`, `arreglo_con_un_boton_quick_reply`, `arreglo_json_vacio`, `ausente`, `botones_del_mismo_tipo_no_agrupados`, `mas_de_10_botones_en_total`, `mas_de_10_botones_quick_reply`, `mas_de_1_boton_phone_number`, `mas_de_2_botones_url`, `no_es_un_arreglo_json_valido`, `vacio`

**7 variables `GLB-create-*` consumidas** (resolución sembrada, ya con su bloque
`seed:` en `variables.yaml`): `account_id_inexistente`, `app_id_inactivo`,
`app_id_otra_cuenta`, `app_id_valido`, `app_id_valido_mutado`,
`apps_ids_validos`, `name_ya_utilizado`.

Más `GLB-account_id_valido` (65), consumida por el helper para decidir la cuenta
de sesión.

**Dejan de consumirse** por las omisiones: `GLB-create-account_id_ajeno` (solo
`I4`) y `MTZ-create-api_access_token-token_invalido_o_expirado` (solo `I65`).
Ambas siguen en uso por el rol `Admin`; no se eliminan.

### Mirror keys

**Mirror keys: ninguna.** La sección `## Mirror keys en respuesta` de
`inputs/Create/docs.md` dice *"No hay campos que validar en esta sección"*. No se
invoca `framework.mirror.assert_mirror` en ningún caso `SA-V<n>`.

### Inventario de casos

70 casos. Prioridad: 51 `alto`, 19 `medio` — metadato de orden de
implementación y revisión, no se traduce a markers ni filtros de ejecución.

| id | caso CSV | HTTP | Prioridad | id | caso CSV | HTTP | Prioridad |
|---|---|---|---|---|---|---|---|
| `SA-V1` | 1 | 200 | alto | `SA-I31` | 39 | 400 | alto |
| `SA-V2` | 2 | 200 | alto | `SA-I32` | 40 | 400 | medio |
| `SA-V3` | 3 | 200 | alto | `SA-I33` | 41 | 400 | medio |
| `SA-V4` | 4 | 200 | alto | `SA-I34` | 42 | 400 | medio |
| `SA-V5` | 5 | 200 | alto | `SA-I35` | 43 | 400 | medio |
| `SA-V6` | 6 | 200 | alto | `SA-I36` | 44 | 400 | alto |
| `SA-V7` | 7 | 200 | alto | `SA-I37` | 45 | 400 | alto |
| `SA-V8` | 8 | 200 | alto | `SA-I38` | 46 | 400 | alto |
| `SA-I1` | 9 | 400 | alto | `SA-I39` | 47 | 400 | medio |
| `SA-I2` | 10 | 400 | alto | `SA-I40` | 48 | 400 | alto |
| `SA-I3` | 11 | 401 | alto | `SA-I41` | 49 | 400 | alto |
| *(omitido)* | *12* | *401* | *alto* | `SA-I42` | 50 | 400 | medio |
| `SA-I5` | 13 | 400 | alto | `SA-I43` | 51 | 400 | alto |
| `SA-I6` | 14 | 400 | alto | `SA-I44` | 52 | 400 | alto |
| `SA-I7` | 15 | 400 | medio | `SA-I45` | 53 | 400 | alto |
| `SA-I8` | 16 | 400 | medio | `SA-I46` | 54 | 400 | medio |
| `SA-I9` | 17 | 400 | medio | `SA-I47` | 55 | 400 | alto |
| `SA-I10` | 18 | 400 | alto | `SA-I48` | 56 | 400 | medio |
| `SA-I11` | 19 | 400 | medio | `SA-I49` | 57 | 400 | alto |
| `SA-I12` | 20 | 400 | alto | `SA-I50` | 58 | 400 | alto |
| `SA-I13` | 21 | 400 | medio | `SA-I51` | 59 | 400 | medio |
| `SA-I14` | 22 | 400 | medio | `SA-I52` | 60 | 400 | medio |
| `SA-I15` | 23 | 400 | alto | `SA-I53` | 61 | 400 | medio |
| `SA-I16` | 24 | 400 | alto | `SA-I54` | 62 | 400 | alto |
| `SA-I17` | 25 | 400 | alto | `SA-I55` | 63 | 400 | alto |
| `SA-I18` | 26 | 400 | alto | `SA-I56` | 64 | 400 | alto |
| `SA-I19` | 27 | 400 | medio | `SA-I57` | 65 | 400 | alto |
| `SA-I20` | 28 | 400 | alto | `SA-I58` | 66 | 400 | alto |
| `SA-I21` | 29 | 400 | alto | `SA-I59` | 67 | 400 | alto |
| `SA-I22` | 30 | 400 | alto | `SA-I60` | 68 | 400 | alto |
| `SA-I23` | 31 | 400 | medio | `SA-I61` | 69 | 400 | alto |
| `SA-I24` | 32 | 400 | alto | `SA-I62` | 70 | 400 | alto |
| `SA-I25` | 33 | 400 | alto | `SA-I63` | 71 | 400 | alto |
| `SA-I26` | 34 | 400 | alto | *(omitido)* | *72* | *401* | *alto* |
| `SA-I27` | 35 | 400 | alto | *(omitido)* | *73* | *401* | *alto* |
| `SA-I28` | 36 | 400 | alto | | | | |
| `SA-I29` | 37 | 400 | alto | | | | |
| `SA-I30` | 38 | 400 | alto | | | | |

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `create`: el requerimiento **Autenticación de sesión** afirma hoy, sin
  calificar por rol, que el sistema responde `401` cuando `account_id` es una
  cuenta existente distinta de la de la sesión. La exploración estableció que esa
  afirmación no es universal: `SuperAdmin` alcanza cuentas ajenas. El escenario
  se acota al alcance realmente verificado, y se añade un requerimiento de
  **invariancia de validación por rol** — las reglas de validación de campo
  producen el mismo resultado con `Admin` y con `SuperAdmin`, que es justo lo que
  los 70 casos nuevos ejercitan.

## Impact

- **Código**: `tests/test_matriz_create_c1_sin_header.py` — se extrae el cuerpo
  actual a un helper compartido y se añaden `CASES_SA` (70 entradas) más la
  función `test_matriz_create_c1_sin_header_super_admin`. El archivo pasa de 73 a
  143 casos parametrizados.
- **Framework**: sin cambios. `auth.py`, `matrix.py`, `generators.py`,
  `http.py` y `variables.py` se consumen tal como están.
- **Datos**: sin cambios en `variables.yaml`, `.env` ni `env.example`.
- **Inputs**: sin cambios. El CSV de `inputs/` no se toca.
- **Ambiente**: cada corrida completa crea 8 plantillas adicionales en la cuenta
  65 (las de `SA-V1..SA-V8`), con nombres generados por `unique_lowercase`, así
  que no colisionan con las que ya crea el rol `Admin`.
- **Ejecución**: con `-x` obligatorio y ambos roles en el mismo archivo, un fallo
  de `Admin` corta antes de llegar a `SuperAdmin`. Los comandos que se entreguen
  al QA filtran por función para poder correr un rol sin el otro.

### Non-Goals

- **No se anota el sidecar** `reports/anotado-create-matriz-c1-sin-header.csv`.
  El QA declaró la funcionalidad obsoleta: los reportes por corrida introducidos
  en `2026-08-26-update-framework-report-per-run` ya registran cURL, status,
  headers y body de cada caso en todos los outcomes, para ambos roles, bajo
  `reports/<timestamp>/`.
- **No se elimina** `src/framework/reannotate.py` ni las reglas de
  `openspec/config.yaml` que exigen el sidecar, ni sus menciones en `CLAUDE.md`
  y `README.md`. Esa limpieza es un change de framework aparte, posterior a este.
  **Consecuencia registrada**: mientras tanto, este proposal se desvía de una
  regla vigente del repo.
- **No se prueba el cruce legítimo de cuentas** (sesión de `SuperAdmin` abierta
  sobre una cuenta que `Admin` no alcanza). Funcionalidad preexistente que se
  asume correcta.
- **No se recupera el caso límite `account_id = 1`**. La cuenta 1 no opera
  correctamente en el ambiente; `MTZ-create-account_id-minimo_del_rango` conserva
  el valor 65, igual que para `Admin`.
- **No se implementan** las nueve matrices restantes de `inputs/Create/`.

### Riesgo abierto

`variables.yaml` tiene cambios sin commitear que no se han vuelto a ejecutar:
`GLB-create-apps_ids_validos` incluye ahora el mismo UUID declarado en
`GLB-create-app_id_otra_cuenta`. Esa variable alimenta los casos `V2`, `V4`, `V6`
y `V8` — con este change, también `SA-V2`, `SA-V4`, `SA-V6` y `SA-V8`, es decir 8
casos en vez de 4. Si el endpoint valida pertenencia de app a la cuenta, esos
casos fallarían con `400` en lugar de `200`. No bloquea la implementación, pero
es el primer lugar donde mirar si la corrida se detiene en un caso `V`.
