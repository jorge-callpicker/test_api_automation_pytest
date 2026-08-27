## 1. Derivación de ids e inventario de casos

- [x] 1.1 Derivar los ids desde la columna `Código HTTP Esperado` de `inputs/Create/create-matriz-c1-sin-header.csv`: `< 400` → `V<n>`, `>= 400` → `I<n>`, posicionales dentro de su grupo. Resultado esperado: 8 `V` y 65 `I`, idéntico al del change archivado `2026-08-25-add-test-create-matriz-c1-sin-header` (el CSV no se regeneró — hash `949fbbca…` sin cambios).
- [x] 1.2 Aplicar el prefijo de rol: cada id `X` del rol base pasa a `SA-X` para la variante. La numeración es **alineada**, no contigua: `SA-I<n>` designa el mismo caso del CSV que `I<n>`.
- [x] 1.3 Marcar como omitidos los tres casos declarados en `proposal.md` → *Casos omitidos*: caso 12 (`I4`, por privilegio de rol), caso 72 (`I64`) y caso 73 (`I65`) (por independencia estructural del rol). Verificar que el inventario resultante son 70 casos: `SA-V1..SA-V8` y `SA-I1..SA-I63` con hueco en `SA-I4`.
- [x] 1.4 Confirmar que el CSV está limpio: cero celdas con prefijo de ID de la forma `<campo>.<id> | <valor>`. Si aparece alguna, detener el change y devolver el CSV al proyecto generador.

## 2. Refactor del test existente — sin cambio de comportamiento

- [x] 2.1 En `tests/test_matriz_create_c1_sin_header.py`, extraer el cuerpo de `test_matriz_create_c1_sin_header` a un helper privado que reciba el rol como primer parámetro, además de `settings`, `http_client`, `case_id`, `expected_status` y `deviations`.
- [x] 2.2 Mover al helper, sin alterar el orden de operaciones: resolución de las `{{...}}` de la fila, `matrix.build_payload(BASE_REQUEST, resolved, FIELD_TYPES)`, selección de la cuenta de sesión, construcción de headers, envío como `files=` y asserts.
- [x] 2.3 Conservar íntegra la lógica de selección de cuenta de sesión (decisión 5 de `design.md`): si el `account_id` de la fila coincide con `{{GLB-account_id_valido}}` se usa ese; en cualquier otro caso la sesión se abre contra `{{GLB-account_id_valido}}`.
- [x] 2.4 Conservar el tratamiento especial de los casos sin sesión: `I64` envía headers vacíos, `I65` envía `{{MTZ-create-api_access_token-token_invalido_o_expirado}}`. Estas ramas solo las alcanza el rol base.
- [x] 2.5 Conservar la jerarquía de aserciones: el status code HTTP es `assert` duro; el resto (respuesta es JSON válido) va con `pytest_check.check(...)`.
- [x] 2.6 Reducir `test_matriz_create_c1_sin_header` a su `parametrize` sobre `CASES` más la llamada al helper con rol `"Admin"`. Verificar que `BASE_REQUEST` y `FIELD_TYPES` siguen definidos una sola vez y compartidos por ambos roles.

## 3. Verificación de no-regresión del rol Admin — bloqueante intermedia

- [x] 3.1 Ejecutar `pytest --stepwise -x -k "test_matriz_create_c1_sin_header and not super_admin" -v` y entregar la salida al QA. **No avanzar a la sección 4 sin retroalimentación positiva**: si los 73 casos de `Admin` no vuelven a quedar en verde, el refactor alteró el request y hay que corregirlo antes de añadir el rol. **Resultado 2026-08-27: `73 passed`** — refactor transparente, confirmado por el QA.

## 4. Construcción del arreglo `CASES_SA`

- [x] 4.1 Construir la petición base del contexto `c1-sin-header` reutilizando el `BASE_REQUEST` ya derivado de `inputs/Create/docs.md`: `file`, `header`, `header_var`, `security` y `expiration` marcados con `OMIT`. Cada caso es esa base más la desviación de su fila.
- [x] 4.2 Declarar `_OMITIDOS_SA = {"I4", "I64", "I65"}` con comentario que remita a la decisión 4 de `design.md`, y derivar `CASES_SA` de `CASES` filtrando ese conjunto y prefijando `SA-` en el `case_id` y en el `id` del `pytest.param` (decisión 7 de `design.md`). **Sustituye a la transcripción literal** que planteaba el plan original: las desviaciones de cada fila deben ser idénticas entre roles, y derivarlas lo garantiza por construcción en vez de depender de que la copia fuera perfecta.
- [x] 4.3 Verificar que la semántica de celdas se hereda intacta de `CASES`: `(ausente)` omite la key del payload vía el centinela `OMIT`; `(vacío)` emite la key con `""`; los campos con `Tipo de Dato` `Array` en el CSV están declarados en `FIELD_TYPES` como `String (arreglo JSON)` y viajan serializados como string. `BASE_REQUEST` y `FIELD_TYPES` son compartidos, así que no hay nada que replicar.
- [x] 4.4 Verificar que `CASES_SA` tiene exactamente 70 entradas, que ningún id se repite, que no existe `SA-I4`, y que las desviaciones de cada `SA-X` son el mismo objeto que las de su `X` correspondiente en `CASES`.

## 5. Función de test del rol SuperAdmin

- [x] 5.1 Añadir `test_matriz_create_c1_sin_header_super_admin` parametrizada sobre `CASES_SA`, delegando en el helper con rol `"SuperAdmin"`.
- [x] 5.2 Verificar que ningún caso de `CASES_SA` alcanza las ramas sin sesión del helper: los 70 casos obtienen su token vía `auth.obtain_session_tokens("SuperAdmin", ...)`.
- [x] 5.3 **Mirror keys: ninguna.** `inputs/Create/docs.md` → `## Mirror keys en respuesta` declara que no hay campos que validar. No se invoca `framework.mirror.assert_mirror` en ningún caso `SA-V<n>`. Dejar el hecho asentado como comentario en el archivo de test.

## 6. Verificación de variables — cero altas

- [x] 6.1 Verificar que las 93 variables `MTZ-create-*` y las 7 `GLB-create-*` que consume `CASES_SA` ya existen en `variables.yaml` (`matrix_values:` y `globals:` respectivamente), con la indicación original del CSV como comentario en la línea anterior. Inventario completo en `proposal.md` → *Variables — cero nuevas*.
- [x] 6.2 Confirmar que este change **no** da de alta ninguna variable nueva, ningún valor de resolución sembrada con bloque `seed:` y ningún generador en `src/framework/generators.py`. En consecuencia, **no** aplica la tarea de regenerar `docs/generators-catalog.md`.
- [x] 6.3 Confirmar que `GLB-create-account_id_ajeno` y `MTZ-create-api_access_token-token_invalido_o_expirado` dejan de ser consumidas por la variante de rol pero **siguen en uso** por el rol base: no se eliminan de `variables.yaml`.

## 7. Calidad

- [x] 7.1 Ejecutar `ruff check --fix` sobre el archivo modificado. **`ruff format` se acota deliberadamente**: `HEAD` ya venía sin formatear porque el change archivado commiteó `CASES` como una línea densa por caso, y `ruff format .` produciría un diff de ~1325 líneas reformateando ese bloque preexistente (líneas 41–119), ajeno a este change. Verificado que ese es el **único** hunk que `ruff format` tocaría: el código añadido aquí ya está limpio. Los 73 `E501` que reporta `ruff check` son todos de esas líneas de `CASES` y no son auto-corregibles; reformatearlas es trabajo de un change aparte.

## 8. Ejecución del rol SuperAdmin — bloqueante

- [x] 8.1 Ejecutar `pytest --stepwise -x -k "super_admin" -v` y entregar la salida al QA. La bandera `-x` es obligatoria en matrices: corta al primer fallo del test parametrizado. **Resultado 2026-08-27: `70 passed` en 86.88s** — los 70 casos produjeron el mismo codigo HTTP que su equivalente de `Admin`. Confirmado por el QA.
- [x] 8.2 Ante un fallo, analizar si es bug del test, dato faltante en `variables.yaml`, o discrepancia real del endpoint. Primer lugar donde mirar si se detiene en un caso `SA-V`: `GLB-create-apps_ids_validos` contiene el mismo UUID que `GLB-create-app_id_otra_cuenta` y alimenta `SA-V2`, `SA-V4`, `SA-V6` y `SA-V8` (ver `proposal.md` → *Riesgo abierto*). Corregir lo mínimo posible y devolver nuevas instrucciones de ejecución. **No aplicó**: la corrida de §8.1 no tuvo fallos.
- [x] 8.3 Si una corrida revela que el endpoint se comporta distinto a lo que declara la matriz o `docs.md`, marcar ese caso con `pytest.mark.xfail(strict=True, reason=...)` citando el id y la discrepancia, y registrarlo en `inputs/Create/hallazgos.md` (crear el archivo si es la primera). **Nunca ajustar el valor esperado del test para que pase.** **No aplicó**: ninguna discrepancia entre endpoint y matriz. `inputs/Create/hallazgos.md` sigue sin existir, que es lo correcto.
- [x] 8.4 Con ambos roles en verde por separado, ejecutar la corrida conjunta `pytest --stepwise -x -k "c1_sin_header" -v` (143 casos) y entregar la salida al QA. **Resultado 2026-08-27: `143 passed` en 170.89s** (73 `Admin` + 70 `SuperAdmin`). Confirma que los dos roles no interfieren en una misma sesion: las 16 plantillas creadas por los casos `V` de ambos roles obtuvieron nombres distintos de `unique_lowercase`, y la cache de sesion no cruzo credenciales.

## 9. Registro de resultados

- [x] 9.1 **Omitido deliberadamente**: no se anota el sidecar `reports/anotado-create-matriz-c1-sin-header.csv`. El QA declaró la funcionalidad obsoleta — los reportes por corrida de `2026-08-26-update-framework-report-per-run` registran cURL, status, headers y body de cada caso en todos los outcomes y para ambos roles, bajo `reports/<timestamp>/`. La regla del repo que aún exige el sidecar se retira en un change de framework posterior; la desviación queda declarada en `proposal.md` → *Non-Goals*.
- [x] 9.2 Verificar que el reporte HTML de la corrida final distingue los dos roles: los casos aparecen bajo `test_matriz_create_c1_sin_header` y `test_matriz_create_c1_sin_header_super_admin`, con ids `V<n>`/`I<n>` y `SA-V<n>`/`SA-I<n>` respectivamente. **Verificado** en `reports/20260827-130856/report.html`: 73 casos bajo el rol base y 70 bajo la variante, `SA-I4` ausente, y 143 bloques de cURL + 143 de respuesta (evidencia por caso en todos los outcomes).

## 10. Cierre

- [x] 10.1 Recoger la retroalimentación explícita del QA sobre la corrida final. El change **no se archiva** sin retroalimentación humana positiva: `matriz-c1-sin-header: 73/73 filas verdes` para el rol base y `70/70` para la variante de rol. **Recibida 2026-08-27**: el QA ejecuto y confirmo en verde las tres corridas — §3.1 `73 passed`, §8.1 `70 passed`, §8.4 `143 passed`.
