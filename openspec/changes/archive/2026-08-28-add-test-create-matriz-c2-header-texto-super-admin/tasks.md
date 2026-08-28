## 1. Derivación de ids e inventario de casos

- [x] 1.1 Confirmar que `inputs/Create/create-matriz-c2-header-texto.csv` sigue con hash `e9702f1a9107da4167b0d04c74ecb045860a331c3fc00ef47e17ca4bc41d6fe9` (idéntico al registrado por el change archivado `2026-08-28-add-test-create-matriz-c2-header-texto`). Si difiere, detener el change y revisar contra el CSV nuevo antes de continuar. **Verificado**: hash idéntico.
- [x] 1.2 Confirmar que el CSV está limpio: cero celdas con prefijo de ID de la forma `<campo>.<id> | <valor>`. **Verificado**: cero coincidencias.
- [x] 1.3 Aplicar el prefijo de rol: cada id `X` del rol `Admin` (`V1..V7`, `I1..I11`) pasa a `SA-X` para la variante. A diferencia de `c1-sin-header-super-admin`, **no hay casos omitidos**: ninguna fila rompe la autenticación y las 18 usan el mismo `account_id` (`MTZ-create-account_id-minimo_del_rango` = 65 = `GLB-account_id_valido`), así que no hay caso análogo al cruce de cuentas de `I4` en `c1`. Verificar que el inventario resultante son 18 casos: `SA-V1..SA-V7` y `SA-I1..SA-I11`, sin huecos. **Verificado** por AST + grep sobre el archivo: 7 `V` (V1-V7) + 11 `I` (I1-I11) = 18, sin duplicados.

## 2. Refactor del test existente — sin cambio de comportamiento

- [x] 2.1 En `tests/test_matriz_create_c2_header_texto.py`, extraer el cuerpo de `test_matriz_create_c2_header_texto` a un helper privado (`_ejecutar_caso`) que reciba el rol como primer parámetro, además de `settings`, `http_client`, `case_id`, `expected_status` y `deviations` — mismo patrón que `tests/test_matriz_create_c1_sin_header.py`.
- [x] 2.2 Mover al helper, sin alterar el orden de operaciones: resolución de las `{{...}}` de la fila, `matrix.build_payload(BASE_REQUEST, resolved, FIELD_TYPES)`, apertura de sesión con `auth.obtain_session_tokens(role, ..., account_id=resolved["account_id"])`, construcción de headers, envío como `files=` y asserts.
- [x] 2.3 A diferencia de `c1`, **no hay lógica de fallback de cuenta de sesión que preservar**: las 18 filas ya resuelven `account_id` al mismo valor (`65`), así que el helper abre sesión directo contra `resolved["account_id"]` sin bifurcación adicional.
- [x] 2.4 A diferencia de `c1`, **no hay ramas sin sesión que preservar**: ninguna fila de este CSV omite el header `api-access-token` ni usa un token estático inválido, así que el helper no necesita casos especiales análogos a `I64`/`I65`.
- [x] 2.5 Conservar la jerarquía de aserciones: el status code HTTP es `assert` duro; el resto (respuesta es JSON válido) va con `pytest_check.check(...)`.
- [x] 2.6 Reducir `test_matriz_create_c2_header_texto` a su `parametrize` sobre `CASES` más la llamada al helper con rol `"Admin"`. Verificar que `BASE_REQUEST` y `FIELD_TYPES` siguen definidos una sola vez y compartidos por ambos roles.

## 3. Verificación de no-regresión del rol Admin — bloqueante intermedia

- [x] 3.1 Ejecutar `pytest --stepwise -x -k "test_matriz_create_c2_header_texto and not super_admin" -v` y entregar la salida al QA. **No avanzar a la sección 4 sin retroalimentación positiva**: si las 18 filas de `Admin` no vuelven a quedar en verde, el refactor alteró el request y hay que corregirlo antes de añadir el rol. **Resultado 2026-08-28: `18 passed, 176 deselected` en 52.77s** (`reports/20260828-172116`) — refactor transparente, rol `Admin` sin regresión.

## 4. Construcción del arreglo `CASES_SA`

- [x] 4.1 Reutilizar el `BASE_REQUEST` ya derivado de `inputs/Create/docs.md` para este contexto (`file`, `security` y `expiration` marcados con `OMIT`; `type`, `header` y `header_var` viajan como deviation de cada fila). Cada caso es esa base más la desviación de su fila.
- [x] 4.2 Derivar `CASES_SA` de `CASES` por comprensión de lista, prefijando `SA-` en el `case_id` y en el `id` del `pytest.param` — igual que la decisión 7 de `design.md` de `c1-sin-header-super-admin`. No transcribir los 18 casos como literales: la invariante que este change verifica exige que las desviaciones sean idénticas entre roles, y derivarlas lo garantiza por construcción.
- [x] 4.3 Verificar que la semántica de celdas se hereda intacta de `CASES`: `(ausente)` omite la key del payload vía el centinela `OMIT`; `(vacío)` emite la key con `""`; `apps` y `body_var` están declarados en `FIELD_TYPES` como `String (arreglo JSON)` y viajan serializados como string. `BASE_REQUEST` y `FIELD_TYPES` son compartidos, así que no hay nada que replicar.
- [x] 4.4 Verificar que `CASES_SA` tiene exactamente 18 entradas, que ningún id se repite, y que las desviaciones de cada `SA-X` son el mismo objeto que las de su `X` correspondiente en `CASES`. **Verificado**: `CASES_SA` es una comprensión sin filtro sobre las 18 entradas de `CASES` (`case.values` reusa el mismo objeto `deviations`).

## 5. Función de test del rol SuperAdmin

- [x] 5.1 Añadir `test_matriz_create_c2_header_texto_super_admin` parametrizada sobre `CASES_SA`, delegando en el helper con rol `"SuperAdmin"`.
- [x] 5.2 Verificar que las 18 filas de `CASES_SA` abren sesión real vía `auth.obtain_session_tokens("SuperAdmin", ...)` — no hay ramas sin sesión en este CSV.
- [x] 5.3 **Mirror keys: ninguna.** `inputs/Create/docs.md` → `## Mirror keys en respuesta` declara que no hay campos que validar. No se invoca `framework.mirror.assert_mirror` en ningún caso `SA-V<n>`. Dejar el hecho asentado como comentario en el archivo de test.

## 6. Verificación de variables — cero altas

- [x] 6.1 Verificar que las variables `MTZ-create-type-*` (1), `MTZ-create-header-*` (13) y `MTZ-create-header_var-*` (10), más las reutilizadas de `c1` (`account_id`, `name`, `category`, `lang`, `apps`, `body`, `body_var`, `footer`, `buttons`) que consume `CASES_SA` ya existen en `variables.yaml`, con la indicación original del CSV como comentario en la línea anterior. **Verificado**: las 34 variables `{{...}}` referenciadas en el archivo tienen entrada en `variables.yaml`.
- [x] 6.2 Confirmar que este change **no** da de alta ninguna variable nueva, ningún valor de resolución sembrada con bloque `seed:` y ningún generador en `src/framework/generators.py`. En consecuencia, **no** aplica la tarea de regenerar `docs/generators-catalog.md`. **Confirmado**: `variables.yaml` no se tocó.

## 7. Calidad

- [x] 7.1 Ejecutar `ruff check --fix` y `ruff format` sobre el archivo modificado. **Resultado**: `All checks passed!` / `1 file left unchanged` (vía `.venv/Scripts/ruff.exe`, versión pinneada 0.16.1).

## 8. Ejecución del rol SuperAdmin — bloqueante

- [x] 8.1 Ejecutar `pytest --stepwise -x -k "super_admin" -v` y entregar la salida al QA. La bandera `-x` es obligatoria en matrices: corta al primer fallo del test parametrizado. **Resultado 2026-08-28: `88 passed, 106 deselected` en 217.51s** (`reports/20260828-172221`) — 70 casos de `c1-sin-header` (`SA-V1..SA-V8`, `SA-I1..SA-I63`) + 18 de `c2-header-texto` (`SA-V1..SA-V7`, `SA-I1..SA-I11`), todos en verde.
- [x] 8.2 Ante un fallo, analizar si es bug del test, dato faltante en `variables.yaml`, o discrepancia real del endpoint. Corregir lo mínimo posible y devolver nuevas instrucciones de ejecución. **Aplicó en la corrida conjunta (8.4)**: `SA-V4` falló con `400`/`"All accounts failed"` (`app_id` con `"error":"Unknown error"`). El QA lo verificó con el desarrollador: fue un timeout transitorio de Gupshup, no un bug del test ni del endpoint. No requirió corrección de código ni de `variables.yaml`.
- [x] 8.3 Si una corrida revela que el endpoint se comporta distinto a lo que declara la matriz o `docs.md`, marcar ese caso con `pytest.mark.xfail(strict=True, reason=...)` citando el id y la discrepancia, y registrarlo en `inputs/Create/hallazgos.md` (crear el archivo si es la primera). **Nunca ajustar el valor esperado del test para que pase.** **No aplicó**: la falla de `SA-V4` no fue una discrepancia matriz/endpoint sino un timeout transitorio de Gupshup (infra externa), confirmado por el desarrollador. No se crea `xfail` ni entrada en `hallazgos.md`; `inputs/Create/hallazgos.md` sigue sin existir, que es lo correcto.
- [x] 8.4 Con ambos roles en verde por separado, ejecutar la corrida conjunta `pytest --stepwise -x -k "matriz_create_c2_header_texto" -v` (36 casos) y entregar la salida al QA. **Resultado 2026-08-28**: primera pasada `1 failed, 21 passed` (corte en `SA-V4` por el timeout de Gupshup de 8.2); segunda pasada (`--stepwise` retomó desde el fallo) `15 passed` — `SA-V4` en verde al reintentar, más `SA-V5..SA-V7`, `SA-I1..SA-I11`. **36/36 casos verdes** entre las dos pasadas (18 `Admin` + 18 `SuperAdmin`).

## 9. Cierre

- [x] 9.1 Recoger la retroalimentación explícita del QA sobre la corrida final. El change **no se archiva** sin retroalimentación humana positiva: `18/18` filas verdes para `SuperAdmin` (sección 8.1, dentro de las 88 combinadas con `c1`) y `36/36` en la corrida conjunta (sección 8.4, con el único fallo intermedio atribuido a un timeout de Gupshup y confirmado en verde al reintentar). **Recibida 2026-08-28**: el QA confirmó éxito y que no hace falta volver a ejecutar los tests.
