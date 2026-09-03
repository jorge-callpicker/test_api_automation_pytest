## 1. Derivación de casos desde el CSV

- [x] 1.1 Derivar los ids `V1–V2`/`I1–I3` desde la columna `Código HTTP Esperado` de `inputs/Create/create-matriz-c3-header-documento.csv` (5 filas), conservando el número original de `Campo` como metadato — ver inventario en `proposal.md`.
- [x] 1.2 Confirmar que el hash SHA-256 del CSV al momento de implementar sigue siendo `72c87b9c869751c6374f84ea50397200f581e8e809e9adbeafe5e6055d259b31`; si difiere, detener y revisar el change contra el CSV nuevo antes de continuar. Reverificado con `certutil -hashfile ... SHA256`: coincide, sin cambios desde el proposal.

## 2. Piezas nuevas de framework

- [x] 2.1 Crear `src/framework/assets.py` con `ASSETS_ROOT = PROJECT_ROOT / "assets"` y `load_asset(relative_path: str) -> bytes`, que lee el archivo y lanza `FileNotFoundError` con mensaje explícito (ruta esperada + referencia a `variables.yaml -> globals`) si no fue sembrado — ver `design.md` → Decisión 1.
- [x] 2.2 Modificar `to_curl` en `src/framework/http.py`: cuando el `content-type` sea `multipart/form-data`, reconstruir cada parte con el módulo estándar `email` en vez de decodificar el body completo — las partes con `filename` (archivo) se muestran como metadato (nombre, content-type, tamaño en bytes), nunca se decodifica su contenido; las demás se decodifican y muestran como `--form 'campo="valor"'`. Con fallback a `-d '<multipart no parseable, N bytes>'` si el parseo falla — ver `design.md` → Decisión 3.
- [x] 2.3 Crear `assets/create/file/` con un `.gitkeep` (carpeta versionada, contenido real ignorado) y añadir la regla correspondiente a `.gitignore` para que los archivos reales bajo `assets/` nunca se commiteen. Verificado con `git add -n`: `.gitkeep` se agregaría, un archivo real de prueba en la misma carpeta quedó ignorado.
- [x] 2.4 Añadir en `openspec/config.yaml`, sección "Ruta 2 — Resolución en runtime", una aclaración de que los campos de `Tipo de Dato: File` **nunca** se resuelven por Ruta 1 (estática) ni Ruta 2 (runtime) sin importar si su tamaño activa el disparador de Volumen: su contenido siempre se sembra (Ruta 3), a cargo del QA — ver `design.md` → Decisión 4 y `proposal.md` → "Arquitectura objetivo". Verificado que `config.yaml` sigue siendo YAML válido tras el cambio.

## 3. Variables nuevas en `variables.yaml`

- [x] 3.1 Añadir `MTZ-create-type-document: DOCUMENT` en `matrix_values:`, con comentario de la indicación original.
- [x] 3.2 Añadir `MTZ-create-file-ausente_cuando_type_document: __AUSENTE__` en `matrix_values:` (Ruta 1 estática — mismo valor semántico que `MTZ-create-file-ausente` de `c1`, pero indicación de celda distinta, así que le corresponde su propio nombre por la regla de unicidad campo/texto-de-celda).
- [x] 3.3 Añadir las 4 variables `GLB-create-file-*` en `globals:` (Ruta 3 sembrada), cada una con: comentario de la indicación original, bloque de descripción de lo que debe sembrarse, y valor inicial `[REQUIERE RESPUESTA: ruta relativa dentro de assets/ al archivo descrito. Sugerido: <ruta de proposal.md>]`.
- [x] 3.4 Confirmar que ninguna variable nueva colisiona con una ya existente de `c1`/`c2` (mismo campo, distinto slug de indicación) — verificado programáticamente con un loader YAML que falla ante keys duplicadas: 0 duplicados en todo `variables.yaml`.

## 4. Siembra de assets (QA)

- [x] 4.1 Colocar en `assets/create/file/file-pdf_valido_tipico_7mb.pdf` un PDF real y válido de tamaño genuinamente típico (~7.9MB), y apuntar `GLB-create-file-pdf_valido_tipico` (`create\file\file-pdf_valido_tipico_7mb.pdf`) a esa ruta. Corrección sobre el valor original de esta tarea: el primer archivo sembrado para `V1` pesaba 56.9MB (mucho más de lo que sugiere "tamaño típico"); se sustituyó por este de ~7.9MB, y el archivo de 56.9MB se reutilizó para el caso suplementario `V1-archivo-grande` (ver sección 7) en vez de descartarse.
- [x] 4.2 Colocar en `assets/create/file/file-pdf_max_100mb.pdf` un PDF real, y apuntar `GLB-create-file-pdf_max_100mb`. Verificado: 104,857,600 bytes exactos (100 MiB), coincide con "límite máximo".
- [x] 4.3 Colocar en `assets/create/file/file-tipo_invalido.jpeg` un archivo real de un tipo no permitido para `DOCUMENT`, y apuntar `GLB-create-file-tipo_invalido`. Verificado: `mimetypes.guess_type` infiere `image/jpeg` de la extensión `.jpeg`.
- [x] 4.4 Colocar en `assets/create/file/file-pdf_excede_100mb.pdf` un PDF real que supere 100MB, y apuntar `GLB-create-file-pdf_excede_100mb`. Verificado: 157,286,400 bytes (150MB), excede el límite.
- [x] 4.5 Confirmar que los archivos existen en las rutas declaradas — verificado programáticamente invocando `framework.variables.resolve` + `framework.assets.load_asset` sobre cada variable: todas leen bytes reales sin `FileNotFoundError` tras corregir un error de siembra inicial (las rutas duplicaban el segmento `assets\`).

## 5. Implementación del test parametrizado

- [x] 5.1 Crear `tests/test_matriz_create_c3_header_documento.py` con `BASE_REQUEST` fijando `header`, `header_var`, `security` y `expiration` en `OMIT` (prohibidos en este contexto), y `FIELD_TYPES` para los campos del contexto (misma convención que `test_matriz_create_c2_header_texto.py`). `type` y `file` viajan como deviation de cada fila, no en `BASE_REQUEST`.
- [x] 5.2 Transcribir las 5 filas como `pytest.mark.parametrize` con ids `V1`/`V2`/`I1`/`I2`/`I3`, cada deviation referenciando únicamente `{{MTZ-create-*}}`/`{{GLB-create-*}}` — cero literales de negocio en el código. Verificado con `pytest --collect-only -k "matriz_create_c3_header_documento"`: 5/5 casos colectados (6/6 tras agregar el caso suplementario, ver sección 7).
- [x] 5.3 Resolver `api_access_token` invocando `auth.obtain_session_tokens("Admin", settings=..., http_client=..., account_id=<account_id de la fila>)`, igual que en `c1`/`c2` — ninguna fila de este CSV rompe la autenticación, así que las 5 abren sesión real.
- [x] 5.4 Construir el payload con `matrix.build_payload(BASE_REQUEST, resolved, FIELD_TYPES)` y, al armar el `files=` de la petición, aplicar el dispatch de `design.md` → Decisión 2 (`_build_files`): si `FIELD_TYPES[campo] == "File"`, construir `(Path(value).name, framework.assets.load_asset(value), mimetypes.guess_type(value)[0])`; en cualquier otro caso, mantener `(None, str(value))`. Verificado con un archivo de humo temporal (no versionado) que `to_curl` reconstruye el `--form` esperado, con la parte de archivo mostrada como metadato.
- [x] 5.5 Para los casos con archivo pesado, pasar un `timeout` mayor al default por-request en `http_client.post(...)` (`LARGE_FILE_TIMEOUT_SECONDS = 300.0`, seleccionado por `case_id in LARGE_FILE_CASE_IDS`) — sin modificar `framework/http.py` ni la fixture `http_client`. Estado final: `LARGE_FILE_CASE_IDS = {"V2", "I3", "V1-archivo-grande"}` — `V1` se sacó del set tras corregir su archivo sembrado a uno genuinamente típico (~7.9MB, ver tarea 4.1); `V1-archivo-grande` se agregó al sumar el caso suplementario (sección 7).
- [x] 5.6 Assert duro sobre el status code HTTP; el resto de aserciones (JSON válido) con `pytest_check.check(...)`.
- [x] 5.7 No invocar `framework.mirror.assert_mirror` — `docs.md` declara `Mirror keys: ninguna` para este endpoint.
- [x] 5.8 No leer `inputs/**/*.csv` en runtime, ni importar un parser de CSV, ni recibir la ruta del CSV como parámetro del test — verificado, el archivo no importa `csv` ni referencia rutas de `inputs/`.

## 6. Verificación y ejecución previa (QA)

- [x] 6.1 Ejecutar `ruff check --fix .` y `ruff format .` sobre los archivos nuevos/modificados antes de entregar — `ruff format` reajustó la firma de `test_matriz_create_c3_header_documento` a multilínea (superaba 100 columnas); `ruff check` reporta "All checks passed!" sobre `src/framework/assets.py`, `src/framework/http.py` y `tests/test_matriz_create_c3_header_documento.py`. Recolección verificada de nuevo tras el formateo: 5/5 casos.
- [x] 6.2 Primera ejecución del QA contra el ambiente real (`pytest --stepwise -x -k "matriz_create_c3_header_documento" -v`, sobre las 5 filas del CSV, antes de agregar el caso suplementario): **5/5 filas `PASSED`**.

## 7. Caso suplementario: V1-archivo-grande (no derivado del CSV)

Ver `proposal.md` → "Caso suplementario (no derivado del CSV)" para el
razonamiento completo. Agregado a pedido del QA tras la primera ejecución
en verde, antes de archivar el change.

- [x] 7.1 Sembrar `assets/create/file/file-pdf_valido_tipico_7mb.pdf` (~7.9MB) como el nuevo contenido de `GLB-create-file-pdf_valido_tipico`, para que `V1` vuelva a usar un archivo genuinamente típico.
- [x] 7.2 Reutilizar el archivo de 56.9MB sembrado originalmente para `V1` (antes de la corrección de 7.1) como contenido del caso nuevo: variable `GLB-create-file-pdf_valido_50mb` en `variables.yaml -> globals`, con comentario explícito de que es un caso suplementario y no una indicación de celda del CSV.
- [x] 7.3 Añadir `CASES_SUPLEMENTARIOS` en `tests/test_matriz_create_c3_header_documento.py`, separado de `CASES` (las 5 filas del CSV), con el caso `V1-archivo-grande` (200) — mismos campos que `V1` salvo `file: {{GLB-create-file-pdf_valido_50mb}}`. El `pytest.mark.parametrize` del test pasa a usar `CASES_TODAS = CASES + CASES_SUPLEMENTARIOS`.
- [x] 7.4 Actualizar `LARGE_FILE_CASE_IDS` a `{"V2", "I3", "V1-archivo-grande"}` (ver tarea 5.5).
- [x] 7.5 Actualizar `proposal.md` (inventario, tabla de variables `GLB-create-file-*`, Impact) y `specs/create/spec.md` (nuevo escenario "Petición válida con documento de tamaño grande dentro del rango") para reflejar el caso suplementario.
- [x] 7.6 Verificar `ruff check`/`ruff format` y recolección (`pytest --collect-only -k "matriz_create_c3_header_documento"`): 6/6 casos, incluido `V1-archivo-grande`.
- [x] 7.7 Verificar programáticamente que `GLB-create-file-pdf_valido_tipico` y `GLB-create-file-pdf_valido_50mb` resuelven y leen bytes reales (`framework.variables.resolve` + `framework.assets.load_asset`).

## 8. Ejecución final y cierre (QA)

- [x] 8.1 **Tarea bloqueante**: entregada al QA. Ejecutada contra el ambiente real: **6/6 `PASSED`** (`V1`, `V2`, `I1`, `I2`, `I3`, `V1-archivo-grande`), corrida `reports/20260903-125014/` (119.64s). Verificado además que `report.html` de esa corrida pesa solo 53KB pese a subir archivos reales de hasta 150MB, y que las partes de archivo aparecen como `archivo omitido del reporte` en el cURL — confirma en producción el fix de `to_curl` (design.md, Decisión 3).
- [x] 8.2 No aplica — las 6 filas pasaron en verde, ningún caso reveló discrepancia real del endpoint. Sin entradas nuevas en `inputs/Create/hallazgos.md`.
