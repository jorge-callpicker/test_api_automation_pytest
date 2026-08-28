## 1. Derivación de casos desde el CSV

- [ ] 1.1 Derivar los ids `V1–V7`/`I1–I11` desde la columna `Código HTTP Esperado` de `inputs/Create/create-matriz-c2-header-texto.csv` (18 filas), conservando el número original de `Campo` como metadato — ver inventario en `proposal.md`.
- [ ] 1.2 Confirmar que el hash SHA-256 del CSV al momento de implementar sigue siendo `e9702f1a9107da4167b0d04c74ecb045860a331c3fc00ef47e17ca4bc41d6fe9`; si difiere, detener y revisar el change contra el CSV nuevo antes de continuar.

## 2. Variables nuevas en `variables.yaml`

- [ ] 2.1 Añadir `MTZ-create-type-text: TEXT` en `matrix_values:`, con comentario de la indicación original.
- [ ] 2.2 Añadir las 13 variables `MTZ-create-header-*` listadas en `proposal.md` (Ruta 1 estática), cada una con el comentario de su indicación original de línea anterior.
- [ ] 2.3 Añadir las 11 variables `MTZ-create-header_var-*` listadas en `proposal.md` (Ruta 1 estática), con el mismo formato de comentario.
- [ ] 2.4 Verificar que los dos valores materializados de longitud máxima con variable (`MTZ-create-header-longitud_maxima_con_variable`, 60 caracteres totales incluyendo el literal `{{1}}`) y su contraparte de `header_var` respetan exactamente el boundary declarado en la celda — no una aproximación.
- [ ] 2.5 Confirmar que ninguna variable nueva colisiona con una ya existente de `c1-sin-header` (mismo campo, distinto slug de indicación).

## 3. Implementación del test parametrizado

- [ ] 3.1 Crear `tests/test_matriz_create_c2_header_texto.py` con `BASE_REQUEST` fijando `security` y `expiration` en `OMIT`, y `FIELD_TYPES` para los campos del contexto (igual convención que `test_matriz_create_c1_sin_header.py`).
- [ ] 3.2 Transcribir las 18 filas como `pytest.mark.parametrize` con ids `V1–V7`/`I1–I11`, cada deviation referenciando únicamente `{{MTZ-create-*}}`/`{{GLB-create-*}}` — cero literales de negocio en el código.
- [ ] 3.3 Resolver `api_access_token` invocando `auth.obtain_session_tokens("Admin", settings=..., http_client=..., account_id=<account_id de la fila>)`, igual que en `c1` — ninguna fila de este CSV rompe la autenticación, así que las 18 abren sesión real.
- [ ] 3.4 Construir el payload con `matrix.build_payload(BASE_REQUEST, resolved, FIELD_TYPES)` y enviarlo como `multipart/form-data` vía `http_client`.
- [ ] 3.5 Assert duro sobre el status code HTTP; el resto de aserciones (JSON válido) con `pytest_check.check(...)`.
- [ ] 3.6 No invocar `framework.mirror.assert_mirror` — `docs.md` declara `Mirror keys: ninguna` para este endpoint.
- [ ] 3.7 No leer `inputs/**/*.csv` en runtime, ni importar un parser de CSV, ni recibir la ruta del CSV como parámetro del test.

## 4. Verificación y ejecución (QA)

- [ ] 4.1 Ejecutar `ruff check --fix .` y `ruff format .` sobre el archivo nuevo antes de entregar.
- [ ] 4.2 **Tarea bloqueante**: entregar al QA el comando `pytest --stepwise -x -k "matriz-c2-header-texto" -v` para ejecución manual contra el ambiente real. El change no se archiva sin retroalimentación explícita del QA sobre las 18 filas.
- [ ] 4.3 Si algún caso falla por discrepancia real del endpoint (no por bug del test ni dato faltante), marcarlo con `pytest.mark.xfail(strict=True, reason=...)` citando el id (`V<n>`/`I<n>`) y registrar la entrada correspondiente en `inputs/Create/hallazgos.md`.
