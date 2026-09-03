## Why

**Tipo de change: matriz** (`add-test-<endpoint>-matriz-<nombre>`), sobre
`inputs/Create/create-matriz-c3-header-documento.csv`. Implementa el
contexto de aplicación `c3-header-documento` (`type=DOCUMENT`, con `file`)
del endpoint `createTemplate` (Gupshup templates, slug corto `create`). Es
el tercer change de matriz de este endpoint: `c1-sin-header` y
`c2-header-texto` (ambos archivados) nunca ejercitan `file` porque en esos
contextos viaja fijo en `OMIT`.

**Alcance de rol: `Admin`**, igual que `c1` y `c2` en su primera
implementación. `SuperAdmin` queda fuera de este change — puede cubrirse
después como change hermano, siguiendo el patrón de
`2026-08-27-add-test-create-matriz-c1-sin-header-super-admin` y
`2026-08-28-add-test-create-matriz-c2-header-texto-super-admin`.

**CSV limpio**: 0 celdas con prefijo de ID de valor (`<campo>.<id> |
<valor>`). Hash SHA-256 del CSV implementado:
`72c87b9c869751c6374f84ea50397200f581e8e809e9adbeafe5e6055d259b31`. No
existe change archivado previo sobre este CSV — es su primera
implementación.

### Arquitectura objetivo — freno duro evaluado, no aplica

`docs.md` declara `Mirror keys: ninguna` → no bloquea por `mirror.py`.
Ninguna celda de este CSV requiere un generador de contenido en runtime:
`name` reutiliza `unique_lowercase` (Ruta 2, ya existente desde `c1`) y
ninguna otra celda dispara Unicidad/Aleatoriedad/Variedad. El campo `file`
sí tiene dos celdas cuyo tamaño (exactamente 100MB, más de 100MB) encajaría
en el disparador semántico de **Volumen** de `config.yaml` — pero **por
decisión explícita de este change, el contenido de un campo `File` nunca
se genera ni se resuelve estáticamente por el modelo**: siempre se resuelve
por la Ruta 3 (sembrada), sin importar si su tamaño activaría Volumen. La
razón: el modelo no puede fabricar un PDF real de 100MB dentro del repo
(inflaría el CSV de conocimiento a un binario versionado o a generación en
memoria en cada corrida), y el equipo de QA ya cuenta con archivos de
prueba reales para este propósito. Esta política se documenta en
`design.md` y se añade como aclaración a `openspec/config.yaml` (tarea de
este change), para que `c4-header-imagen` y `c5-header-video` —que también
usarán `file`— no vuelvan a evaluar la disyuntiva.
`src/framework/matrix.py`, `generators.py`, `mirror.py` y `variables.py`
ya existen (construidos por `c1`/`c2`). Este change **sí genera código de
test**, sin detenerse.

### Piezas nuevas de framework (justifican `design.md`)

Ningún módulo existente sabe construir una parte de archivo real para un
`files=` de multipart (hoy todo campo se envía como `(None, str(valor))`,
ver `tests/test_matriz_create_c2_header_texto.py`). Este change introduce:

1. `src/framework/assets.py` — helper para leer bytes desde `assets/` dado
   un valor `GLB-create-file-*` (una ruta relativa), con error explícito si
   el QA no sembró el archivo.
2. Dispatch por `field_types[campo] == "File"` en el armado de la petición
   del test, para construir `(filename, bytes, content_type)` en vez de
   `(None, str(valor))`.
3. Un ajuste en `src/framework/http.py` (`to_curl`) para que el reporte
   HTML no intente decodificar como UTF-8 el binario de un archivo subido
   (crítico para el caso `I3`, archivo >100MB).

## What Changes

- Añade el test parametrizado `test_matriz_create_c3_header_documento`, que
  cubre las **5 filas** del CSV (`V1–V2`, `I1–I3`) más **1 caso
  suplementario** (`V1-archivo-grande`, ver más abajo) en un único
  `pytest.mark.parametrize` sobre `CASES_TODAS = CASES + CASES_SUPLEMENTARIOS`,
  consumiendo `matrix.build_payload`,
  `auth.obtain_session_tokens`, `variables.resolve` y el nuevo
  `framework.assets.load_asset`. El `BASE_REQUEST` de este contexto fija
  `header`, `header_var`, `security` y `expiration` en `OMIT` (los dos
  primeros prohibidos salvo `type=TEXT`; los otros dos, exclusivos de
  `AUTHENTICATION`) — mismo patrón que `file`/`security`/`expiration` en
  `BASE_REQUEST` de `c2`. `type` y `file` viajan como deviation de cada
  fila.
- Declara **1 variable `MTZ-create-type-*` nueva**: `MTZ-create-type-document`
  = `"DOCUMENT"` (literal ya presente en el paréntesis de la celda).
- Declara **1 variable `MTZ-create-file-*` nueva** de Ruta 1 (estática, no
  sembrada porque no representa contenido de archivo): `MTZ-create-file-ausente_cuando_type_document`
  = `__AUSENTE__`, análoga a `MTZ-create-header-ausente_cuando_type_text`
  de `c2` — mismo valor semántico que `MTZ-create-file-ausente` (de `c1`)
  pero indicación de celda distinta, así que le corresponde su propio
  nombre por la regla de unicidad (campo, texto de celda).
- Declara **4 variables `GLB-create-file-*` nuevas**, Ruta 3 (sembrada) —
  siguiendo la convención de `config.yaml` para esta ruta, el valor inicial
  es un placeholder `[REQUIERE RESPUESTA: ...]` con una ruta sugerida
  dentro de `assets/`; el QA la acepta o la cambia al sembrar, y reemplaza
  el placeholder por la ruta real. El contenido del archivo en esa ruta lo
  coloca el QA, no el proyecto:

  | Variable | Indicación original | Ruta sembrada | Caso |
  |---|---|---|---|
  | `GLB-create-file-pdf_valido_tipico` | (archivo PDF válido, tamaño típico) | `create/file/file-pdf_valido_tipico_7mb.pdf` (~7.9MB) | V1 |
  | `GLB-create-file-pdf_max_100mb` | (archivo PDF de tamaño exactamente 100MB, límite máximo) | `create/file/file-pdf_max_100mb.pdf` (exactamente 104,857,600 bytes) | V2 |
  | `GLB-create-file-tipo_invalido` | (archivo de tipo no permitido para DOCUMENT, ej. imagen) | `create/file/file-tipo_invalido.jpeg` | I2 |
  | `GLB-create-file-pdf_excede_100mb` | (archivo PDF que excede 100MB) | `create/file/file-pdf_excede_100mb.pdf` (~150MB) | I3 |
  | `GLB-create-file-pdf_valido_50mb` | *(no aplica — ver "Caso suplementario" abajo)* | `create/file/file-pdf_valido_tipico.pdf` (~56.9MB) | `V1-archivo-grande` |

  Cada una de las 4 primeras trae una tarea de siembra explícita en
  `tasks.md`. El `content_type` de cada parte se infiere de la extensión de
  la ruta (`mimetypes.guess_type`) — no se declara aparte.

### Caso suplementario (no derivado del CSV)

Durante la ejecución de este change, el QA pidió agregar un sexto caso:
`V1-archivo-grande`, que reenvía la misma petición de `V1` salvo `file`,
con un PDF válido pero de tamaño grande dentro del rango permitido
(~56.9MB, sin llegar al límite de 100MB que ya cubre `V2`). Este caso
**no corresponde a ninguna fila** de
`inputs/Create/create-matriz-c3-header-documento.csv` (que solo tiene las
5 filas del inventario de abajo).

Decisión de trazabilidad: se implementa con un id explícito fuera del
esquema `V<n>`/`I<n>` (que es posicional y se deriva del CSV) — llamarlo
`V3` habría arriesgado una colisión de significado si el CSV real se
regenera después con una fila nueva en esa posición. `CASES_SUPLEMENTARIOS`
en el test queda separado de `CASES` (las 5 filas del CSV) precisamente
para que el inventario de casos derivado del CSV, y su verificación por
hash SHA-256, sigan describiendo únicamente lo que ese CSV contiene.

Origen del archivo sembrado: es el mismo PDF de 56.9MB que originalmente
se sembró (por error, ver hilo de la sesión) como "tamaño típico" de `V1`
antes de corregirlo — se reutiliza aquí en vez de descartarlo, ahora bajo
la variable `GLB-create-file-pdf_valido_50mb` con su propio comentario en
`variables.yaml` explicando que es un caso suplementario, no una
indicación de celda del CSV.
- **Cero generadores nuevos** en `src/framework/generators.py` (ver
  "Arquitectura objetivo" — `file` no usa Ruta 2 en este proyecto).
- **Cero variables `MTZ-*`/`GLB-*` nuevas** para el resto de campos: la fila
  reutiliza sin cambio `MTZ-create-account_id-minimo_del_rango`,
  `MTZ-create-name-nombre_unico_no_usado_antes` (generador
  `unique_lowercase` ya existente), `MTZ-create-category-marketing`,
  `MTZ-create-lang-en_us`, `GLB-create-app_id_valido`,
  `MTZ-create-body-texto_tipico_sin_variables`, `MTZ-create-body_var-ausente`,
  `MTZ-create-footer-ausente`, `MTZ-create-buttons-ausente`,
  `MTZ-create-header-ausente`, `MTZ-create-header_var-ausente`,
  `MTZ-create-security-ausente` y `MTZ-create-expiration-ausente` — todas
  ya declaradas por `c1`/`c2`.
- Mirror keys: **ninguna** — `docs.md` declara explícitamente "No hay
  campos que validar en esta sección".

### Inventario de casos (5 filas → V1–V2, I1–I3)

| ID | # original | HTTP | Prioridad |
|---|---|---|---|
| V1 | 1 | 200 | alto |
| V2 | 2 | 200 | alto |
| I1 | 3 | 400 | alto |
| I2 | 4 | 400 | alto |
| I3 | 5 | 400 | alto |

Las 5 filas son `Prioridad: alto` — no hay orden de prioridad que aplicar
dentro del change; las 5 van en el mismo test parametrizado.

Además, `V1-archivo-grande` (caso suplementario, 200, sin # original ni
Prioridad — no viene del CSV, ver "Caso suplementario" arriba).

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `create`: el requerimiento **Reglas condicionales de encabezado
  (type/file/header)** hoy solo cubre `type` fuera de la lista blanca y el
  caso "sin encabezado" (cubierto por `c1`) y la validación cruzada
  `header`/`header_var` (cubierta por `c2`). Se añaden los escenarios de
  validación de `file` cuando `type` es `DOCUMENT`: tipo de archivo
  permitido (`application/pdf`), tamaño máximo (100MB, límite inclusive),
  y obligatoriedad de `file` cuando `type=DOCUMENT`.

## Impact

- **Código nuevo**: `tests/test_matriz_create_c3_header_documento.py`,
  `src/framework/assets.py`.
- **Código modificado**: `src/framework/http.py` (`to_curl` con guard de
  tamaño para no decodificar bodies grandes como UTF-8).
- `variables.yaml` — 1 entrada nueva en `matrix_values:`
  (`MTZ-create-type-document`), 1 entrada nueva de Ruta 1 en
  `matrix_values:` (`MTZ-create-file-ausente_cuando_type_document`), y 5
  entradas nuevas en `globals:` (`GLB-create-file-*`, todas sembradas con
  la ruta real ya reemplazada — 4 de las 5 filas del CSV, más
  `GLB-create-file-pdf_valido_50mb` del caso suplementario).
- `assets/create/file/` — carpeta nueva versionada (estructura, vía
  `.gitkeep`); su contenido real (los 5 archivos, incluido el del caso
  suplementario) va en `.gitignore` y lo coloca el QA.
- `inputs/Create/create-matriz-c3-header-documento.csv` — fuente de este
  change, sin modificar por parte de este proposal.
- `openspec/specs/create/spec.md` — el requerimiento de reglas
  condicionales de encabezado se extiende con la validación de `file` para
  `type=DOCUMENT` (ver Capabilities).
- `openspec/config.yaml` — se añade una aclaración de que los campos
  `File` se resuelven siempre por Ruta 3 (sembrada), nunca generados
  dinámicamente aunque su tamaño active el disparador de Volumen (ver
  "Arquitectura objetivo" en `Why`).
- **Ambiente**: cada corrida completa crea 3 plantillas nuevas (`V1`, `V2`,
  `V1-archivo-grande`) en la cuenta `65`, con nombres generados por
  `unique_lowercase`, sin colisión con las que ya crean `c1`/`c2`. Requiere
  que el QA haya sembrado los 5 archivos bajo `assets/create/file/` antes
  de ejecutar.
- **Ejecución**: `-x` obligatorio. Los casos `V2`/`I3`/`V1-archivo-grande`
  (archivos de varias decenas de MB o más) requieren un timeout mayor al
  default de 30s del cliente HTTP — se pasa como override por-request, sin
  tocar el cliente compartido.

### Non-Goals

- No se implementa el rol `SuperAdmin` para este contexto.
- No se implementan las matrices restantes de `inputs/Create/`
  (`c4`–`c6`, `cruzada`, `buttons*`), aunque `c4-header-imagen` y
  `c5-header-video` van a reutilizar `framework/assets.py` y la política de
  siembra de `file` documentada aquí.
- No se genera contenido de archivo dinámicamente bajo ninguna
  circunstancia — ver "Arquitectura objetivo".
