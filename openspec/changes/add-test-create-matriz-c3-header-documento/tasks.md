## 1. Derivación de casos desde el CSV

- [ ] 1.1 Derivar los ids `V1–V2`/`I1–I3` desde la columna `Código HTTP Esperado` de `inputs/Create/create-matriz-c3-header-documento.csv` (5 filas), conservando el número original de `Campo` como metadato — ver inventario en `proposal.md`.
- [ ] 1.2 Confirmar que el hash SHA-256 del CSV al momento de implementar sigue siendo `72c87b9c869751c6374f84ea50397200f581e8e809e9adbeafe5e6055d259b31`; si difiere, detener y revisar el change contra el CSV nuevo antes de continuar.

## 2. Piezas nuevas de framework

- [ ] 2.1 Crear `src/framework/assets.py` con `ASSETS_ROOT = PROJECT_ROOT / "assets"` y `load_asset(relative_path: str) -> bytes`, que lee el archivo y lanza `FileNotFoundError` con mensaje explícito (ruta esperada + referencia a `variables.yaml -> globals`) si no fue sembrado — ver `design.md` → Decisión 1.
- [ ] 2.2 Modificar `to_curl` en `src/framework/http.py`: si `len(request.content)` supera 2MB, omitir la decodificación UTF-8 y mostrar `content-type` + tamaño en bytes en su lugar — ver `design.md` → Decisión 3.
- [ ] 2.3 Crear `assets/create/file/` con un `.gitkeep` (carpeta versionada, contenido real ignorado) y añadir la regla correspondiente a `.gitignore` para que los archivos reales bajo `assets/` nunca se commiteen.
- [ ] 2.4 Añadir en `openspec/config.yaml`, sección "Ruta 2 — Resolución en runtime", una aclaración de que los campos de `Tipo de Dato: File` **nunca** se resuelven por Ruta 1 (estática) ni Ruta 2 (runtime) sin importar si su tamaño activa el disparador de Volumen: su contenido siempre se sembra (Ruta 3), a cargo del QA — ver `design.md` → Decisión 4 y `proposal.md` → "Arquitectura objetivo".

## 3. Variables nuevas en `variables.yaml`

- [ ] 3.1 Añadir `MTZ-create-type-document: DOCUMENT` en `matrix_values:`, con comentario de la indicación original.
- [ ] 3.2 Añadir `MTZ-create-file-ausente_cuando_type_document: __AUSENTE__` en `matrix_values:` (Ruta 1 estática — mismo valor semántico que `MTZ-create-file-ausente` de `c1`, pero indicación de celda distinta, así que le corresponde su propio nombre por la regla de unicidad campo/texto-de-celda).
- [ ] 3.3 Añadir las 4 variables `GLB-create-file-*` en `globals:` (Ruta 3 sembrada), cada una con: comentario de la indicación original, bloque de descripción de lo que debe sembrarse, y valor inicial `[REQUIERE RESPUESTA: ruta relativa dentro de assets/ al archivo descrito. Sugerido: <ruta de proposal.md>]`.
- [ ] 3.4 Confirmar que ninguna variable nueva colisiona con una ya existente de `c1`/`c2` (mismo campo, distinto slug de indicación) — 0 duplicados esperados en `matrix_values:`/`globals:`.

## 4. Siembra de assets (QA)

- [ ] 4.1 Colocar en `assets/create/file/pdf_valido_tipico.pdf` (o la ruta que el QA prefiera) un PDF real y válido de tamaño típico (recomendado: unos cientos de KB a pocos MB), y reemplazar el placeholder de `GLB-create-file-pdf_valido_tipico` en `variables.yaml` con la ruta real usada.
- [ ] 4.2 Colocar en `assets/create/file/pdf_max_100mb.pdf` un PDF real de tamaño exactamente 100MB (límite máximo inclusive), y reemplazar el placeholder de `GLB-create-file-pdf_max_100mb`.
- [ ] 4.3 Colocar en `assets/create/file/tipo_invalido.jpg` un archivo real de un tipo no permitido para `DOCUMENT` (ej. una imagen JPEG/PNG), y reemplazar el placeholder de `GLB-create-file-tipo_invalido`. La extensión debe reflejar el tipo real del archivo — `mimetypes.guess_type` infiere el `content_type` de la extensión, no del contenido.
- [ ] 4.4 Colocar en `assets/create/file/pdf_excede_100mb.pdf` un PDF real que supere 100MB, y reemplazar el placeholder de `GLB-create-file-pdf_excede_100mb`.
- [ ] 4.5 Confirmar que los 4 archivos existen en las rutas declaradas antes de ejecutar el test — de lo contrario `framework.assets.load_asset` falla con mensaje explícito en el caso correspondiente.

## 5. Implementación del test parametrizado

- [ ] 5.1 Crear `tests/test_matriz_create_c3_header_documento.py` con `BASE_REQUEST` fijando `header`, `header_var`, `security` y `expiration` en `OMIT` (prohibidos en este contexto), y `FIELD_TYPES` para los campos del contexto (misma convención que `test_matriz_create_c2_header_texto.py`). `type` y `file` viajan como deviation de cada fila, no en `BASE_REQUEST`.
- [ ] 5.2 Transcribir las 5 filas como `pytest.mark.parametrize` con ids `V1`/`V2`/`I1`/`I2`/`I3`, cada deviation referenciando únicamente `{{MTZ-create-*}}`/`{{GLB-create-*}}` — cero literales de negocio en el código.
- [ ] 5.3 Resolver `api_access_token` invocando `auth.obtain_session_tokens("Admin", settings=..., http_client=..., account_id=<account_id de la fila>)`, igual que en `c1`/`c2` — ninguna fila de este CSV rompe la autenticación, así que las 5 abren sesión real.
- [ ] 5.4 Construir el payload con `matrix.build_payload(BASE_REQUEST, resolved, FIELD_TYPES)` y, al armar el `files=` de la petición, aplicar el dispatch de `design.md` → Decisión 2: si `FIELD_TYPES[campo] == "File"` y el valor no es `OMIT`, construir `(Path(value).name, framework.assets.load_asset(value), mimetypes.guess_type(value)[0])`; en cualquier otro caso, mantener `(None, str(value))`.
- [ ] 5.5 Para los casos `V2`/`I3` (archivos de ~100MB), pasar un `timeout` mayor al default por-request en `http_client.post(...)` — sin modificar `framework/http.py` ni la fixture `http_client`.
- [ ] 5.6 Assert duro sobre el status code HTTP; el resto de aserciones (JSON válido) con `pytest_check.check(...)`.
- [ ] 5.7 No invocar `framework.mirror.assert_mirror` — `docs.md` declara `Mirror keys: ninguna` para este endpoint.
- [ ] 5.8 No leer `inputs/**/*.csv` en runtime, ni importar un parser de CSV, ni recibir la ruta del CSV como parámetro del test.

## 6. Verificación y ejecución (QA)

- [ ] 6.1 Ejecutar `ruff check --fix .` y `ruff format .` sobre los archivos nuevos/modificados antes de entregar.
- [ ] 6.2 **Tarea bloqueante**: entregar al QA el comando `pytest --stepwise -x -k "matriz_create_c3_header_documento" -v` para ejecución manual contra el ambiente real, una vez completada la siembra de la sección 4. Esperar retroalimentación explícita antes de continuar.
- [ ] 6.3 Si algún caso revela una discrepancia real entre el endpoint y la matriz o `docs.md` (no un problema de siembra ni del test), marcarlo con `pytest.mark.xfail(strict=True, reason=...)` citando el id y la discrepancia, y registrar una entrada en `inputs/Create/hallazgos.md`. No aplica si las 5 filas pasan en verde.
