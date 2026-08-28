## 1. Derivación de casos desde el CSV

- [x] 1.1 Derivar los ids `V1–V7`/`I1–I11` desde la columna `Código HTTP Esperado` de `inputs/Create/create-matriz-c2-header-texto.csv` (18 filas), conservando el número original de `Campo` como metadato — ver inventario en `proposal.md`.
- [x] 1.2 Confirmar que el hash SHA-256 del CSV al momento de implementar sigue siendo `e9702f1a9107da4167b0d04c74ecb045860a331c3fc00ef47e17ca4bc41d6fe9`; si difiere, detener y revisar el change contra el CSV nuevo antes de continuar.

## 2. Variables nuevas en `variables.yaml`

- [x] 2.1 Añadir `MTZ-create-type-text: TEXT` en `matrix_values:`, con comentario de la indicación original.
- [x] 2.2 Añadir las 13 variables `MTZ-create-header-*` listadas en `proposal.md` (Ruta 1 estática), cada una con el comentario de su indicación original de línea anterior.
- [x] 2.3 Añadir las variables `MTZ-create-header_var-*` nuevas (Ruta 1 estática) — corrección sobre `proposal.md`: `MTZ-create-header_var-ausente` ya existía en `variables.yaml` (declarada por `c1-sin-header` pero nunca consumida por su código, que fija `header_var: OMIT` directo); este change la reutiliza para `V1`/`V3` en vez de duplicarla. Las **10** restantes sí son nuevas.
- [x] 2.4 Verificar que los dos valores materializados de longitud máxima con variable (`MTZ-create-header-longitud_maxima_con_variable`, 60 caracteres totales incluyendo el literal `{{1}}`) y su contraparte de `header_var` respetan exactamente el boundary declarado en la celda — verificado programáticamente (60/61 caracteres exactos), no una aproximación.
- [x] 2.5 Confirmar que ninguna variable nueva colisiona con una ya existente de `c1-sin-header` (mismo campo, distinto slug de indicación) — verificado, 0 duplicados en `matrix_values:`.

## 3. Implementación del test parametrizado

- [x] 3.1 Crear `tests/test_matriz_create_c2_header_texto.py` con `BASE_REQUEST` fijando `security` y `expiration` en `OMIT`, y `FIELD_TYPES` para los campos del contexto (igual convención que `test_matriz_create_c1_sin_header.py`). Nota: `file` también queda fijo en `BASE_REQUEST` (nunca varía en este CSV — `type=TEXT` lo prohíbe siempre).
- [x] 3.2 Transcribir las 18 filas como `pytest.mark.parametrize` con ids `V1–V7`/`I1–I11`, cada deviation referenciando únicamente `{{MTZ-create-*}}`/`{{GLB-create-*}}` — cero literales de negocio en el código.
- [x] 3.3 Resolver `api_access_token` invocando `auth.obtain_session_tokens("Admin", settings=..., http_client=..., account_id=<account_id de la fila>)`, igual que en `c1` — ninguna fila de este CSV rompe la autenticación, así que las 18 abren sesión real. Simplificación válida sobre `c1`: como `account_id` es siempre `MTZ-create-account_id-minimo_del_rango` (= `GLB-account_id_valido`), no hace falta la rama condicional de `c1` que decide entre cuenta de la fila y cuenta de sesión por defecto.
- [x] 3.4 Construir el payload con `matrix.build_payload(BASE_REQUEST, resolved, FIELD_TYPES)` y enviarlo como `multipart/form-data` vía `http_client`.
- [x] 3.5 Assert duro sobre el status code HTTP; el resto de aserciones (JSON válido) con `pytest_check.check(...)`.
- [x] 3.6 No invocar `framework.mirror.assert_mirror` — `docs.md` declara `Mirror keys: ninguna` para este endpoint.
- [x] 3.7 No leer `inputs/**/*.csv` en runtime, ni importar un parser de CSV, ni recibir la ruta del CSV como parámetro del test — verificado, el archivo no importa `csv` ni referencia rutas de `inputs/`.

## 4. Verificación y ejecución (QA)

- [x] 4.1 Ejecutar `ruff check --fix .` y `ruff format .` sobre el archivo nuevo antes de entregar — `ruff format` reescribió cada `pytest.param` a formato multilínea (supera el límite de 100 columnas configurado en `pyproject.toml`); `ruff check` reporta "All checks passed!" tras el fix. Nota para el QA: `tests/test_matriz_create_c1_sin_header.py` sigue en formato de una sola línea por caso y hoy falla `ruff check` con `E501` — no se tocó ese archivo (fuera de alcance de este change), pero conviene una pasada de `ruff format` sobre él en un change de limpieza aparte.
- [x] 4.2 **Tarea bloqueante**: entregar al QA el comando `pytest --stepwise -x -k "matriz_create_c2_header_texto" -v` para ejecución manual contra el ambiente real. Corrección sobre el valor original de esta tarea: el `-k` documentado en `openspec/config.yaml` usa guiones, pero los node ids de pytest usan guion bajo (los nombres de función Python no admiten guiones) — quedó pendiente corregir esa plantilla en `config.yaml` como tarea aparte. **Retroalimentación del QA: 18/18 filas `PASSED`** (`V1`–`V7`, `I1`–`I11`), corrida `reports/20260828-124607/`.
- [x] 4.3 No aplica — las 18 filas pasaron en verde, ningún caso reveló discrepancia real del endpoint. Sin entradas nuevas en `inputs/Create/hallazgos.md`.
