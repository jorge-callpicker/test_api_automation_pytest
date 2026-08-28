## Why

**Tipo de change: matriz** (`add-test-<endpoint>-matriz-<nombre>`), sobre
`inputs/Create/create-matriz-c2-header-texto.csv`. Implementa el contexto de
aplicación `c2-header-texto` (`type=TEXT`, con `header`/`header_var`) del
endpoint `createTemplate` (Gupshup templates, slug corto `create`). Es el
segundo change de matriz de este endpoint — el primero, `c1-sin-header`
(archivado), nunca ejercita `header`/`header_var` porque en ese contexto
ambos van fijos en `OMIT`.

**Alcance de rol: `Admin`**, igual que el primer change archivado sobre
`c1-sin-header`. Ninguna de las 18 filas rompe deliberadamente la
autenticación (a diferencia de `c1`, que sí tenía casos `I64`/`I65`), así
que las 18 abren sesión real contra `GLB-account_id_valido` vía
`auth.obtain_session_tokens("Admin", ...)`. `SuperAdmin` queda fuera de este
change — puede cubrirse después como change hermano, siguiendo el mismo
patrón que `2026-08-27-add-test-create-matriz-c1-sin-header-super-admin`.

**Inconsistencia del CSV detectada y corregida durante la exploración (no
por este change)**: la matriz original traía filas donde `header` no
mencionaba ninguna variable pero `header_var` sí traía un valor, esperando
`200` — lo cual viola la regla cruzada que el propio `docs.md` documenta
(`header_var` requerido únicamente cuando `header` contiene una variable).
El QA corrigió el CSV en dos pasadas durante la exploración previa a este
proposal:

1. Separó el caso ambiguo original en dos casos limpios: uno donde `header`
   prueba un boundary de longitud **sin** variable (pareado con
   `header_var: (ausente)`), y varios donde el boundary/contenido de
   `header` declara explícitamente `con una única variable {{1}}` (pareados
   con un `header_var` real).
2. Corrigió la redacción contradictoria del caso 14 (`header`:
   *"texto típico **sin variables**... con una única variable {{1}}"* →
   *"texto típico **de longitud media**, con una única variable {{1}}"*),
   dejando claro que ese caso sí declara una variable y prueba la ausencia
   prohibida de `header_var`.

Verificado con `awk` sobre las 18 filas finales: ningún par
`header`/`header_var`/HTTP esperado se contradice entre sí. 0 celdas con
prefijo de ID de valor (`<campo>.<id> | <valor>`) — el CSV pasó la fase de
limpieza del proyecto generador.

### Arquitectura objetivo — disponible, no aplica freno duro

Ninguna celda de este CSV cae en un disparador de resolución runtime
(unicidad/aleatoriedad/variedad/volumen) salvo `name`, que ya usa el
generador `unique_lowercase` existente desde `c1`. `docs.md` declara
`Mirror keys: ninguna`. `src/framework/matrix.py`, `generators.py` y
`mirror.py` ya existen (construidos por el change de `c1`). Este change
**sí genera código de test**, sin detenerse.

### CSV no regenerado desde el corte de esta exploración

Hash SHA-256 del CSV implementado:
`e9702f1a9107da4167b0d04c74ecb045860a331c3fc00ef47e17ca4bc41d6fe9`. No
existe change archivado previo sobre este CSV con el que comparar — es su
primera implementación.

## What Changes

- Añade el test parametrizado `test_matriz_create_c2_header_texto`, que
  cubre las **18 filas** del CSV (`V1–V7`, `I1–I11`) como un único
  `pytest.mark.parametrize`, consumiendo `matrix.build_payload`,
  `auth.obtain_session_tokens` y `variables.resolve` — los mismos módulos
  que ya usa `c1`. El `BASE_REQUEST` de este contexto fija `security` y
  `expiration` en `OMIT` (campos exclusivos de `AUTHENTICATION`, ausentes en
  todo `MARKETING`); `type`, `header` y `header_var` viajan como deviation
  de cada fila en vez de fijos en `OMIT`, a diferencia de `c1`.
- Declara **1 variable `MTZ-create-type-*` nueva**: `MTZ-create-type-text`
  = `"TEXT"` (literal ya presente en el paréntesis de la celda).
- Declara **13 variables `MTZ-create-header-*` nuevas** (Ruta 1 estática,
  todas con el literal a elegir por el change salvo donde el paréntesis ya
  lo trae):

  | Variable | Indicación original | Casos |
  |---|---|---|
  | `MTZ-create-header-texto_tipico_sin_variables` | (texto típico sin variables, longitud media) | V1, I8–I11 |
  | `MTZ-create-header-texto_tipico_con_una_unica_variable` | (texto típico con una única variable {{1}}) | V2, V4 |
  | `MTZ-create-header-longitud_minima` | (longitud mínima, 1 carácter) | V3 |
  | `MTZ-create-header-longitud_maxima_con_variable` | (longitud máxima, con una única variable {{1}}, 60 caracteres) | V5 |
  | `MTZ-create-header-cadena_que_alterna_con_variable` | (cadena que alterna entre mayúsculas y minúsculas, con una única variable {{1}}) | V6 |
  | `MTZ-create-header-caracteres_especiales_con_variable` | (caracteres especiales, con una única variable {{1}}) | V7 |
  | `MTZ-create-header-ausente_cuando_type_text` | (ausente cuando type=TEXT) | I1 |
  | `MTZ-create-header-vacio` | (vacío) | I2 |
  | `MTZ-create-header-longitud_61` | (longitud 61, por encima del máximo) | I3 |
  | `MTZ-create-header-contiene_salto_de_linea` | (contiene salto de línea) | I4 |
  | `MTZ-create-header-contiene_4_o_mas_espacios` | (contiene 4 o más espacios consecutivos) | I5 |
  | `MTZ-create-header-contiene_dos_o_mas_variables` | (contiene dos o más variables) | I6 |
  | `MTZ-create-header-texto_tipico_con_variable` | (texto típico de longitud media, con una única variable {{1}}) | I7 |

- Declara **11 variables `MTZ-create-header_var-*` nuevas**:

  | Variable | Indicación original | Casos |
  |---|---|---|
  | `MTZ-create-header_var-ausente` | (ausente) | V1, V3 |
  | `MTZ-create-header_var-longitud_minima` | (longitud mínima, 1 carácter) | V2 |
  | `MTZ-create-header_var-longitud_maxima` | (longitud máxima, 60 caracteres) | V4 |
  | `MTZ-create-header_var-cadena_que_alterna_entre_mayusculas_y` | (cadena que alterna entre mayúsculas y minúsculas) | V5 |
  | `MTZ-create-header_var-caracteres_especiales` | (caracteres especiales) | V6 |
  | `MTZ-create-header_var-valor_tipico_correspondiente_a_la_variable` | (valor típico correspondiente a la variable del header) | V7, I1–I6 |
  | `MTZ-create-header_var-ausente_cuando_header_contiene_variable` | (ausente cuando header contiene variable) | I7 |
  | `MTZ-create-header_var-vacio` | (vacío) | I8 |
  | `MTZ-create-header_var-longitud_61` | (longitud 61, por encima del máximo) | I9 |
  | `MTZ-create-header_var-contiene_salto_de_linea` | (contiene salto de línea) | I10 |
  | `MTZ-create-header_var-contiene_4_o_mas_espacios` | (contiene 4 o más espacios consecutivos) | I11 |

- **Cero variables `GLB-create-*` nuevas** y **cero generadores nuevos**:
  las 18 filas reutilizan sin cambio `MTZ-create-account_id-minimo_del_rango`,
  `MTZ-create-name-nombre_unico_no_usado_antes` (Ruta 2, generador
  `unique_lowercase` ya existente), `MTZ-create-category-marketing`,
  `MTZ-create-lang-en_us`, `GLB-create-app_id_valido`,
  `MTZ-create-file-ausente`, `MTZ-create-body-texto_tipico_sin_variables`,
  `MTZ-create-body_var-ausente`, `MTZ-create-footer-texto_tipico_sin_variables`,
  `MTZ-create-buttons-ausente` y el mecanismo de sesión
  `auth.obtain_session_tokens("Admin", ...)` ya usado por `c1` para
  `api_access_token: (token válido correspondiente a la sesión)`.
- Mirror keys: **ninguna** — `docs.md` declara explícitamente "No hay campos
  que validar en esta sección".

### Inventario de casos (18 filas → V1–V7, I1–I11)

| ID | # original | HTTP | Prioridad |
|---|---|---|---|
| V1 | 1 | 200 | alto |
| V2 | 2 | 200 | alto |
| V3 | 3 | 200 | alto |
| V4 | 4 | 200 | alto |
| V5 | 5 | 200 | alto |
| V6 | 6 | 200 | alto |
| V7 | 7 | 200 | alto |
| I1 | 8 | 400 | alto |
| I2 | 9 | 400 | medio |
| I3 | 10 | 400 | alto |
| I4 | 11 | 400 | medio |
| I5 | 12 | 400 | medio |
| I6 | 13 | 400 | alto |
| I7 | 14 | 400 | alto |
| I8 | 15 | 400 | medio |
| I9 | 16 | 400 | alto |
| I10 | 17 | 400 | medio |
| I11 | 18 | 400 | medio |

Orden de escritura/revisión sugerido: primero las filas `Prioridad: alto`
(V1–V7, I1, I3, I6, I7, I9), luego `medio` (I2, I4, I5, I8, I10, I11).
Ninguna fila de este CSV es `bajo`. La prioridad no filtra qué se
implementa — las 18 filas van en el mismo test parametrizado.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `create`: el requerimiento **Reglas condicionales de encabezado
  (type/file/header)** hoy solo cubre `type` fuera de la lista blanca y el
  caso "sin encabezado" (cubierto por `c1`). Se añade la validación cruzada
  `header` ↔ `header_var` cuando `type=TEXT`: `header` requerido y entre
  1–60 caracteres, con a lo sumo una variable `{{1}}`, sin saltos de línea
  ni 4+ espacios consecutivos; `header_var` requerido si y solo si `header`
  contiene esa variable.

## Impact

- **Código nuevo**: `tests/test_matriz_create_c2_header_texto.py`. Sin
  cambios en `src/framework/` — reutiliza `matrix.py`, `auth.py`,
  `generators.py`, `http.py` y `variables.py` tal como están.
- `variables.yaml` — 25 entradas nuevas en `matrix_values:` (1 de `type`,
  13 de `header`, 11 de `header_var`). Cero entradas nuevas en `globals:`.
- `inputs/Create/create-matriz-c2-header-texto.csv` — fuente de este
  change, sin modificar por parte de este proposal (ya llegó corregido por
  el QA antes de proponer).
- `openspec/specs/create/spec.md` — el requerimiento de reglas
  condicionales de encabezado se extiende con la validación cruzada
  `header`/`header_var` (ver Capabilities).
- **Ambiente**: cada corrida completa crea 7 plantillas nuevas en la cuenta
  `65` (las de `V1`–`V7`), con nombres generados por `unique_lowercase`, sin
  colisión con las que ya crean `c1` (`Admin`/`SuperAdmin`).
- **Ejecución**: `-x` obligatorio; con las 18 filas en un solo archivo, un
  fallo temprano corta antes de llegar a los casos posteriores.

### Non-Goals

- No se implementa el rol `SuperAdmin` para este contexto (ver "Alcance de
  rol" en `Why`).
- No se implementan las matrices restantes de `inputs/Create/`
  (`c3`–`c6`, `cruzada`, `buttons*`).
