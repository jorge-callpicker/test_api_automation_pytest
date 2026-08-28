## Why

**Tipo de change: matriz** (`add-test-<endpoint>-matriz-<nombre>`), sobre
`inputs/Create/create-matriz-c2-header-texto.csv`. Es el segundo change
sobre este CSV: el archivado `2026-08-28-add-test-create-matriz-c2-header-texto`
implementó sus 18 filas únicamente para el rol `Admin` y declaró
explícitamente en su `Why` que `SuperAdmin` quedaba fuera de alcance,
"puede cubrirse después como change hermano, siguiendo el mismo patrón
que `2026-08-27-add-test-create-matriz-c1-sin-header-super-admin`". Este
change cierra ese hueco.

Lo que verifica es la misma invariante de seguridad que `c1-sin-header`
extendió a `SuperAdmin`: que un rol elevado no relaje ninguna validación
de campo. Aquí, específicamente, la validación cruzada `header`↔`header_var`
que `c2-header-texto` (Admin) fue la primera en ejercitar.

### Desviación de cardinalidad — declarada y aceptada, mismo precedente que c1

La regla del repo pide un change por CSV. Este es el **segundo** sobre
`create-matriz-c2-header-texto.csv`, diferenciado por rol y no por archivo
— la misma desviación que ya aceptó y documentó
`2026-08-27-add-test-create-matriz-c1-sin-header-super-admin` (ver su
`proposal.md` → *Desviación de cardinalidad* y su `design.md` → *Decisión
1*). El código vive en el mismo archivo de test que el rol `Admin`
(`tests/test_matriz_create_c2_header_texto.py`), con un segundo arreglo
`CASES_SA` y una segunda función de test — no se crea
`tests/test_matriz_create_c2_header_texto_super_admin.py`.

### CSV no regenerado

Hash SHA-256 verificado en esta exploración:
`e9702f1a9107da4167b0d04c74ecb045860a331c3fc00ef47e17ca4bc41d6fe9`.
Idéntico al registrado por el change archivado de `Admin`. El CSV no se
regeneró; los ids `V1–V7`/`I1–I11` y los códigos esperados de `Admin`
siguen siendo válidos y sirven de referencia directa para los de
`SuperAdmin`.

### Cero omisiones — a diferencia de c1

`c1-sin-header` tuvo que excluir 3 de sus 73 filas para `SuperAdmin`: una
por privilegio de rol (`I4`, cruce de cuentas — el endpoint le permite a
`SuperAdmin` acceder a cuentas ajenas) y dos por independencia estructural
(`I64`/`I65`, piden sin sesión o con token estático inválido — nunca
invocan `obtain_session_tokens`, así que su request es idéntico en
cualquier rol).

Ninguno de los dos criterios aplica a `c2-header-texto`:

- **Ninguna de las 18 filas rompe la autenticación** — ya lo declaró el
  `Why` del change archivado de `Admin`: "a diferencia de c1, que sí tenía
  casos I64/I65". Las 18 abren sesión real.
- **Las 18 filas usan el mismo `account_id`**:
  `MTZ-create-account_id-minimo_del_rango`, que vale `65` en
  `variables.yaml` — idéntico a `GLB-account_id_valido`. Ninguna fila usa
  una cuenta ajena o inexistente, así que no hay caso análogo a `I4`.

Consecuencia: las **18 filas transfieren sin excepción** a `SuperAdmin`,
con numeración alineada y **sin huecos** (a diferencia del hueco en
`SA-I4` que sí tuvo `c1`).

### Arquitectura objetivo — disponible, no aplica freno duro

Mismas condiciones que el change archivado de `Admin`: ninguna celda cae
en ruta de resolución runtime salvo `name` (generador `unique_lowercase`,
ya existente), y `docs.md` declara `Mirror keys: ninguna`.
`src/framework/matrix.py`, `generators.py` y `mirror.py` ya existen. Este
change **sí genera código de test**, sin detenerse.

### Sin delta de spec

El change archivado de `c1-sin-header-super-admin` agregó a
`specs/create/spec.md` el requerimiento **"Invariancia de la validación de
campos respecto al rol"**, redactado a nivel de endpoint —no acotado a los
campos de `c1`— y con escenarios cuyos ejemplos ("por ejemplo body_var/body,
botones") son ilustrativos, no exhaustivos. La validación cruzada
`header`↔`header_var` que este change ejercita con `SuperAdmin` ya cae bajo
ese requerimiento genérico: no se descubre ninguna excepción por rol (a
diferencia de `c1-SA`, que sí encontró que `SuperAdmin` cruza cuentas y
tuvo que calificar el requerimiento de *Autenticación de sesión*). Por lo
tanto este change no declara ninguna capability nueva ni modificada, y
`.openspec.yaml` fija `skip_specs: true`.

## What Changes

- Refactoriza `tests/test_matriz_create_c2_header_texto.py`: el cuerpo
  actual de `test_matriz_create_c2_header_texto` se extrae a un helper
  privado parametrizado por `role`, siguiendo el mismo patrón que
  `_ejecutar_caso` en `tests/test_matriz_create_c1_sin_header.py`. El rol
  `Admin` conserva su comportamiento actual — mismo request, mismos
  asserts.
- Añade `test_matriz_create_c2_header_texto_super_admin`, con `CASES_SA`
  **derivado** de `CASES` por comprensión de lista (no transcrito), igual
  que la decisión 7 del `design.md` de `c1-SA`.
- **Cero filas omitidas**: las 18 filas del CSV transfieren completas.
  Ids alineados y sin huecos: `SA-V1..SA-V7` (7), `SA-I1..SA-I11` (11).
- **Cero variables `MTZ-*`/`GLB-*` nuevas** y **cero generadores nuevos**:
  las 18 filas de `SuperAdmin` consumen exactamente el mismo subconjunto
  de `variables.yaml` que ya registró el change archivado de `Admin` (24
  entradas `MTZ-create-type-*`/`header-*`/`header_var-*`, más las
  reutilizadas de `c1`: `account_id`, `name`, `category`, `lang`, `apps`,
  `body`, `body_var`, `footer`, `buttons`).
- Mirror keys: **ninguna** — `docs.md` declara explícitamente "No hay
  campos que validar en esta sección".
- Sin cambios en `src/framework/` — reutiliza `matrix.py`, `auth.py`
  (`_ROLE_CREDENTIALS` ya soporta `SuperAdmin` desde
  `2026-08-06-add-framework-auth-session-fixture`), `generators.py`,
  `http.py` y `variables.py` tal como están.

### Inventario de casos — 18 filas → SA-V1–SA-V7, SA-I1–SA-I11

| id `SuperAdmin` | id `Admin` (referencia) | # original | HTTP | Prioridad |
|---|---|---|---|---|
| SA-V1 | V1 | 1 | 200 | alto |
| SA-V2 | V2 | 2 | 200 | alto |
| SA-V3 | V3 | 3 | 200 | alto |
| SA-V4 | V4 | 4 | 200 | alto |
| SA-V5 | V5 | 5 | 200 | alto |
| SA-V6 | V6 | 6 | 200 | alto |
| SA-V7 | V7 | 7 | 200 | alto |
| SA-I1 | I1 | 8 | 400 | alto |
| SA-I2 | I2 | 9 | 400 | medio |
| SA-I3 | I3 | 10 | 400 | alto |
| SA-I4 | I4 | 11 | 400 | medio |
| SA-I5 | I5 | 12 | 400 | medio |
| SA-I6 | I6 | 13 | 400 | alto |
| SA-I7 | I7 | 14 | 400 | alto |
| SA-I8 | I8 | 15 | 400 | medio |
| SA-I9 | I9 | 16 | 400 | alto |
| SA-I10 | I10 | 17 | 400 | medio |
| SA-I11 | I11 | 18 | 400 | medio |

Orden de escritura/revisión sugerido: primero `Prioridad: alto`
(SA-V1–SA-V7, SA-I1, SA-I3, SA-I6, SA-I7, SA-I9), luego `medio` (SA-I2,
SA-I4, SA-I5, SA-I8, SA-I10, SA-I11). La prioridad no filtra ejecución.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

(ninguna) — ver `Why` → *Sin delta de spec*. `.openspec.yaml` declara
`skip_specs: true`.

## Impact

- **Código**: `tests/test_matriz_create_c2_header_texto.py` — se extrae
  el cuerpo actual a un helper compartido y se añaden `CASES_SA` (18
  entradas) más la función `test_matriz_create_c2_header_texto_super_admin`.
  El archivo pasa de 18 a 36 casos parametrizados.
- **Framework**: sin cambios. `auth.py`, `matrix.py`, `generators.py`,
  `http.py` y `variables.py` se consumen tal como están.
- **Datos**: sin cambios en `variables.yaml`, `.env` ni `.env.example`.
- **Inputs**: sin cambios. El CSV de `inputs/` no se toca.
- **Specs**: sin cambios — ver `Why` → *Sin delta de spec*.
- **Ambiente**: cada corrida completa crea 7 plantillas adicionales en la
  cuenta `65` (las de `SA-V1..SA-V7`), con nombres generados por
  `unique_lowercase`, sin colisión con las que ya crean `Admin` de este
  contexto ni con las de `c1` (`Admin`/`SuperAdmin`).
- **Ejecución**: `-x` obligatorio; con ambos roles en el mismo archivo, un
  fallo de `Admin` corta antes de llegar a `SuperAdmin`. Las instrucciones
  al QA filtran por nombre de función para poder correr un rol sin el
  otro.

### Non-Goals

- No se implementan las matrices restantes de `inputs/Create/`
  (`c1` ya cubre ambos roles; quedan `c3`–`c6`, `cruzada`, `buttons*`).
- No se prueba el cruce legítimo de cuentas para este contexto — no
  aplica, porque ninguna fila de `c2-header-texto` usa una cuenta ajena
  (ver `Why` → *Cero omisiones*).
