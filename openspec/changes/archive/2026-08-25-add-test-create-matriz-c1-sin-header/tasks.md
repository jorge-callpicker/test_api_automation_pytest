> Este change absorbe la construcción de `src/framework/matrix.py`, `generators.py` y `mirror.py` (ver `Why` en `proposal.md` — excepción declarada a la convención de un tipo por change), además del test de matriz `c1-sin-header`. Firmas fijadas en `design.md`.

## 1. Verificación de estado

- [x] 1.1 Confirmar que el hash SHA-256 del CSV en disco (`inputs/Create/create-matriz-c1-sin-header.csv`) sigue siendo `81eeefcf5e42edd90e926c7e31d23a45cb0a122ed8483f2e45a80b38a6bfda8b`. Si cambió, el CSV se regeneró y los ids V/I pueden haberse corrido — volver a derivarlos antes de continuar.
- [x] 1.2 Confirmar que `src/framework/matrix.py`, `generators.py` y `mirror.py` siguen sin existir (si alguno ya existe por otro change en curso, ajustar el alcance de esta sección para no duplicar trabajo).

## 2. `src/framework/matrix.py`

- [x] 2.1 Implementar `build_payload(base_request: dict, deviations: dict[str, Any], field_types: dict[str, str]) -> dict`: `(ausente)` omite la key, `(vacío)` la emite como `""`, campos con `field_types[campo] == "String (arreglo JSON)"` se serializan con `json.dumps(...)` como string. Función pura, sin lectura de CSV ni de `variables.yaml`.
- [x] 2.2 Extender `variables.py::resolve()` para reconocer `MTZ-*` resuelto desde `variables.yaml → matrix_values`, delegando en `generators.py::run(name, **params)` cuando el valor almacenado es un dict `{generator, params}` (sin cachear entre filas). No modificar la rama existente de `GLB-*`/`TC-XXX-*`.
- [x] 2.3 Unit test de `build_payload` con fixtures literales (sin CSV): casos `(ausente)`/`(vacío)`/serialización `String (arreglo JSON)`, y un caso de regresión para `resolve()` con `MTZ-*` y con `{generator, params}`. Archivo: `tests/test_framework_matrix.py`.

## 3. `src/framework/generators.py`

- [x] 3.1 Implementar el registro `GENERATORS: dict[str, Callable]` y `unique_lowercase(length: int) -> str` (docstring en español, primera línea = descripción corta) para los 3 valores `name-nombre_unico_*` (Ruta 2, disparador de Unicidad).
- [x] 3.2 Implementar el CLI `--catalog` (`python -m framework.generators --catalog`) que genera la tabla Markdown desde los docstrings.
- [x] 3.3 Regenerar `docs/generators-catalog.md` con ese CLI. No editarlo a mano.

## 4. `src/framework/mirror.py`

- [x] 4.1 Implementar `assert_mirror(check, request_payload, response_json, mirror_keys: list[str])`: match exclusivamente por key JSON exacta (nunca substring), una `pytest_check.check(...)` por key declarada.
- [x] 4.2 No invocarlo desde `test_matriz_create_c1_sin_header` — `docs.md` declara "Mirror keys: ninguna" para este endpoint; la firma queda lista para el próximo endpoint que sí declare mirror keys.

## 5. Validación de aceptación de los módulos de framework (bloqueante)

- [x] 5.1 **[BLOQUEANTE]** Ejecutar el unit test de `matrix.py` (2.3), `python -m framework.generators --catalog` (3.2/3.3), y `ruff check src/framework/matrix.py src/framework/generators.py src/framework/mirror.py`. Entregar la salida de los tres al QA antes de continuar con la sección 6. No seguir sin confirmación explícita de que los tres pasaron. **Confirmado por el QA: 10/10 unit tests pasaron; `ruff` encontró `UP035` (import de `Callable`), corregido y re-confirmado limpio.**

## 6. Petición base y semántica de celdas del contexto `c1-sin-header`

- [x] 6.1 Construir la petición base del contexto a partir de `docs.md`: multipart form-data con `account_id`, `name`, `category`, `lang`, `apps`, `body`, `body_var`, `footer`, `buttons` — sin `type`/`file`/`header`/`header_var`/`security`/`expiration`. Cada caso parametrizado es esta base más la desviación de su fila (vía `build_payload`).

## 7. Variables `MTZ-create-*` (matrix_values)

- [x] 7.1 Crear las 101 variables `MTZ-create-*` (catálogo ya fijado en `proposal.md`, sin necesidad de regenerarlo — ver decisión 1 de `design.md`) en `variables.yaml → matrix_values:`, cada una con el comentario de la indicación original del CSV. Generadas y verificadas programáticamente (round-trip YAML) para evitar el riesgo de transcripción manual señalado en `design.md`.
- [x] 7.2 Aplicar la corrección de `body_var` documentada en `Why` del proposal: `V1`/`V3`/`V7` usan `MTZ-create-body_var-ausente`; `V5` usa `MTZ-create-body_var-arreglo_con_10_elementos_correspondientes_a`. El CSV se regeneró durante la implementación y ya trae corregido el mismo problema en I1–I40/I53–I65 (ver nota en `proposal.md` § Why) — `I41`–`I52` se mantienen sin cambio por decisión del QA.
- [x] 7.3 Referenciar `unique_lowercase` desde los 3 `MTZ-create-name-nombre_unico_*` con `generator:`/`params:`.
- [x] 7.4 `buttons` y `body_var` compuestos se materializan como literal JSON completo en su propia variable `MTZ-create-*` (Opción A) — no requieren composición desde las matrices anidadas de `buttons`.

## 8. Variables `GLB-create-*` sembradas

- [x] 8.1 Añadir las 8 variables `GLB-create-*` listadas en `proposal.md` a `variables.yaml → globals:`, cada una con placeholder `[REQUIERE RESPUESTA: ...]` y su descripción de siembra.
- [x] 8.2 (QA) Sembrar en el ambiente: una cuenta existente distinta de 65 (`GLB-create-account_id_ajeno`), un `account_id` que no exista (`GLB-create-account_id_inexistente`), un segundo UUID de app válida (`GLB-create-apps_ids_validos`), un UUID de app inactiva/inexistente (`GLB-create-app_id_inactivo`), un UUID de app de otra cuenta (`GLB-create-app_id_otra_cuenta`), y un `name` de plantilla ya creado (`GLB-create-name_ya_utilizado`). Confirmado por el QA.
- [x] 8.3 (QA) Verificar si `account_id = 1` existe como cuenta válida en el ambiente de pruebas — lo asume la matriz en `V1`/`V3`/`V5`/`V7`, pero el único `account_id` confirmado hasta ahora es 65. Si no existe, reportar como bloqueo de ambiente antes de ejecutar. **Resuelto por el QA**: modificó `MTZ-create-account_id-minimo_del_rango` en `variables.yaml` de `1` a `65` directamente — ya no se asume ninguna cuenta sin confirmar.

## 9. Resolución del header de sesión (`api_access_token`)

- [x] 9.1 Para los 71 casos que requieren sesión válida, invocar `framework.auth.obtain_session_tokens("Admin", settings=..., http_client=..., account_id=<account_id de la fila>)` directamente desde el test por caso parametrizado (decisión 5 de `design.md`) — rol fijo `Admin`, este change no cubre `SuperAdmin`. Cuando el `account_id` de la fila no es un entero positivo utilizable (ausente/vacío/inexistente/ajeno), la sesión se autentica contra `GLB-account_id_valido` (65) para poder llegar a la validación del campo bajo prueba.
- [x] 9.2 Materializar `I64` (header ausente: no enviar `api-access-token`) e `I65` (`MTZ-create-api_access_token-token_invalido_o_expirado`, un valor estático que no corresponda a ninguna sesión vigente).

## 10. Test parametrizado y aserciones

- [x] 10.1 **Leer el CSV una única vez** y transcribir sus 73 filas como tabla Python literal (lista de `pytest.param(id="V1"/"I1", http=..., deviations={campo: "{{MTZ-create-...}}", ...})`) dentro de `tests/test_matriz_create_c1_sin_header.py`. A partir de aquí ningún código vuelve a leer `inputs/Create/create-matriz-c1-sin-header.csv` — es la única tarea de esta sección que toca el archivo de entrada. Generada programáticamente desde el catálogo de variables ya validado, no transcrita a mano.
- [x] 10.2 Implementar `test_matriz_create_c1_sin_header` con un único `pytest.mark.parametrize` sobre esa tabla literal (73 casos: `V1..V8`, `I1..I65`), resolviendo cada `deviation` vía `resolve()` y construyendo el payload con `build_payload`. Envío como `multipart/form-data` real (vía `files={campo: (None, str(valor))}`), consistente con los ejemplos `curl --form` de `docs.md`.
- [x] 10.3 Primera aserción — status code HTTP — como `assert` duro.
- [x] 10.4 Resto de aserciones de cada caso con `pytest_check.check(...)` (soft assertions) — se agregó una verificación de que la respuesta es JSON válido.
- [x] 10.5 No invocar `assert_mirror` (ver 4.2).
- [x] 10.6 Si alguna fila revela que el endpoint se comporta distinto a lo declarado por la matriz o `docs.md`, marcar ese caso con `pytest.mark.xfail(strict=True, reason=...)` citando el id (`V<n>`/`I<n>`) y la discrepancia, y registrarlo en `inputs/Create/hallazgos.md` (crear el archivo si es el primer hallazgo). **Sin hallazgos**: tras la corrección de `I47` en el CSV (§12.1), la corrida real confirmó `400` — no queda ninguna fila con comportamiento distinto al declarado. No existe `inputs/Create/hallazgos.md` ni ningún `xfail` en el test.
- [x] 10.7 Anotar resultados en el sidecar `reports/anotado-create-matriz-c1-sin-header.csv` (nunca sobrescribir el CSV de `inputs/`), preservando el BOM `utf-8-sig`. Si `reannotate.py` no soporta aún el contrato de matriz (delimitador/BOM/columna `Campo`/ids `[V<n>]`), anotar manualmente para esta corrida — su reescritura queda fuera de alcance de este change (ver Non-Goals en `design.md`). Regenerado con el resultado final: 73/73 `PASSED`.

## 11. Actualización de `openspec/config.yaml`

- [x] 11.1 Actualizar § "Arquitectura objetivo — pendiente de implementación": marcar `matrix.py`, `generators.py` y `mirror.py` como existentes, con referencia a este change como el que los introdujo.
- [x] 11.2 Ajustar la redacción del "Freno duro" y la regla correspondiente en `rules.proposal` (verificación de disponibilidad de los módulos) para que quede como comprobación condicional ("si en el futuro alguno deja de existir o se reescribe") en vez de asumir que nunca existen.

## 12. Ejecución (bloqueante)

- [x] 12.1 Ejecutar `pytest --stepwise -x -k "matriz_create_c1_sin_header" -v` y entregar la salida completa al QA. El change no se archiva sin retroalimentación humana explícita y positiva (todas las filas en verde, o discrepancias aceptadas/marcadas como hallazgo).
      **Corrida final (73/73 PASSED, combinando dos ejecuciones)**: `--sw-reset -x` corrió `V1`–`V8`, `I1`–`I33` en verde y se detuvo en `I34` por `httpx.ReadTimeout` (timeout de lectura de 30s durante el login de sesión) — un blip transitorio del ambiente, no un bug de test/dato. Un segundo `--stepwise -x` (retomando desde el cache de stepwise) corrió `I34`–`I65`, todos `PASSED`, incluyendo `I34` sin reintento especial. `I47` confirmó `400` con el `body` corregido (§10.6) — la fila vuelve a probar "`body_var` ausente cuando `body` sí tiene variables" correctamente. Sidecar regenerado en §10.7 con 73/73 `PASSED`. El QA dio por cerrada esta tarea con retroalimentación explícita y positiva.
      **Nota**: el comando de `config.yaml` (`-k "matriz-<nombre>"`, con guiones) es una plantilla genérica — el nombre real de la función es `test_matriz_create_c1_sin_header` (guion bajo, incluye `create`); `-k` hace matching por substring literal del node id, así que el patrón debe coincidir con guiones bajos, no con el sufijo del CSV tal cual.
      **Fix descubierto en ejecución (previo a la primera corrida real)**: `GLB-create-app_id_valido`, `app_id_valido_mutado`, `app_id_inactivo` y `app_id_otra_cuenta` estaban declarados en `variables.yaml` como string plano en vez de lista de un elemento. Como `build_payload` (`matrix.py`) solo serializa a JSON cuando el valor es `list`/`dict`, el campo `apps` viajaba como UUID crudo en vez de `["uuid"]` (arreglo JSON serializado), inconsistente con los ejemplos `curl --form` de `docs.md`. Corregido: los 4 globals ahora son listas de un elemento, igual que `GLB-create-apps_ids_validos`.
      **Fix descubierto en ejecución (`I3` FAILED en la primera corrida real, 10 passed antes)**: la resolución de `session_account_id` en el test comprobaba solo "¿es entero positivo?" para decidir si reutilizar el `account_id` de la fila al abrir sesión. `account_id_inexistente` (100) y `account_id_ajeno` (60) también son enteros positivos pero el token de prueba no tiene acceso a esas cuentas, así que `auth.obtain_session_tokens` fallaba en el paso `selectAccount` antes de llegar al endpoint bajo prueba. Corregido: la comparación ahora es contra `GLB-account_id_valido` (65) en vez de un chequeo genérico de tipo — solo se reutiliza el `account_id` de la fila cuando coincide exactamente con la cuenta válida y accesible.
      **Corrida completa sin `-x` (diagnóstico, 71 passed / 2 failed)**: `I12` (esperado 400, recibido 200 — el endpoint creó la plantilla pese a `name` ya utilizado) e `I47` (esperado 400, recibido 200). Para `I47` el QA confirmó y corrigió el CSV (tercera regeneración, hash `84a8fc11780267ad21f8c34088c0116cec3802a1ec878096460b831b2949307e`): la fila 58 tenía el mismo patrón de inconsistencia `body`/`body_var` ya identificado — `body_var` se corrigió a `(ausente)` en el CSV. Se actualizó `tests/test_matriz_create_c1_sin_header.py` (deviation de `I47` ahora usa `MTZ-create-body_var-ausente`) y se eliminó de `variables.yaml` la variable `MTZ-create-body_var-ausente_cuando_body_contiene_variables`, que quedó sin uso. `I12` queda pendiente como posible hallazgo real (§10.6) — el QA confirmó que el `name` ya existía y va a reconfirmarlo manualmente antes de registrarlo.
      **Cierre (revertido)**: `I12` reconfirmado `PASSED` en la siguiente corrida (`--stepwise -x`, 44 passed / 1 failed hasta detenerse en `I47`). `I47` reveló una segunda inconsistencia: tras corregir `body_var` a `(ausente)`, la fila ya no viola ninguna regla cruzada `body`↔`body_var`, pero `Código HTTP Esperado` seguía en `400` — el `200` del endpoint era correcto dado el dato de ese momento. En esa ocasión el QA lo aceptó como hallazgo (`xfail(strict=True)`, entrada en `hallazgos.md`, sidecar anotado) y marcó esta tarea completa manualmente. **El QA cambió de opinión después**: en vez de dejarlo como hallazgo, corrigió `body` en el CSV (4ª regeneración, hash `949fbbcad7411fda40ea5cc95262d3c9739f551035f2584a00138860bbbe8a22`) para que la fila vuelva a probar "`body_var` ausente cuando `body` sí tiene variables" — preservando la intención original en vez de relajar el resultado. Se revirtieron el `xfail`, `hallazgos.md` y el sidecar (ver §10.6/§10.7); esta tarea vuelve a estar pendiente de una corrida real que confirme `400` en `I47` con el dato corregido.
