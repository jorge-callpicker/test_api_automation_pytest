> Este change absorbe la construcción de `src/framework/matrix.py`, `generators.py` y `mirror.py` (ver `Why` en `proposal.md` — excepción declarada a la convención de un tipo por change), además del test de matriz `c1-sin-header`. Firmas fijadas en `design.md`.

## 1. Verificación de estado

- [ ] 1.1 Confirmar que el hash SHA-256 del CSV en disco (`inputs/Create/create-matriz-c1-sin-header.csv`) sigue siendo `81eeefcf5e42edd90e926c7e31d23a45cb0a122ed8483f2e45a80b38a6bfda8b`. Si cambió, el CSV se regeneró y los ids V/I pueden haberse corrido — volver a derivarlos antes de continuar.
- [ ] 1.2 Confirmar que `src/framework/matrix.py`, `generators.py` y `mirror.py` siguen sin existir (si alguno ya existe por otro change en curso, ajustar el alcance de esta sección para no duplicar trabajo).

## 2. `src/framework/matrix.py`

- [ ] 2.1 Implementar `MatrixCase` (`id`, `campo_num`, `http_code`, `priority`, `values: dict[str, str]`) y `parse_matrix(csv_path) -> list[MatrixCase]`: lectura `;` / `utf-8-sig`, salto de las 3 filas de metadata, derivación de ids `V<n>`/`I<n>` posicional por grupo según `Código HTTP Esperado` (`< 400` → V, `>= 400` → I).
- [ ] 2.2 Implementar `mtz_slug(cell_text, *, existing=()) -> str`: minúsculas, sin acentos, `_` entre palabras, catálogo de abreviaturas de `config.yaml` cuando encaje, truncado a las primeras palabras significativas, extendiendo el truncado si colisiona con `existing`.
- [ ] 2.3 Implementar `build_payload(case, base_request, field_types, resolved) -> dict`: `(ausente)` omite la key, `(vacío)` la emite como `""`, campos con `field_types[campo] == "String (arreglo JSON)"` se serializan con `json.dumps(...)` como string.
- [ ] 2.4 Extender `variables.py::resolve()` para reconocer `MTZ-*` resuelto desde `variables.yaml → matrix_values`, delegando en `generators.py::run(name, **params)` cuando el valor almacenado es un dict `{generator, params}` (sin cachear entre filas). No modificar la rama existente de `GLB-*`/`TC-XXX-*`.
- [ ] 2.5 Regenerar el catálogo de 101 nombres `MTZ-create-*` corriendo `mtz_slug` real sobre las 110 celdas únicas del CSV; diffear contra los nombres ya listados en `proposal.md` y corregir `variables.yaml` (nunca `design.md`/`proposal.md` como fuente de verdad tardía) si algo no coincide. Documentar el diff aquí si hubo alguno.
- [ ] 2.6 Unit test de `matrix.py` (fuera de la suite de matriz de negocio) que valide `parse_matrix` sobre `create-matriz-c1-sin-header.csv`: 73 casos, 8 `V`, 65 `I`, y que `mtz_slug` no produzca colisiones dentro de un mismo campo.

## 3. `src/framework/generators.py`

- [ ] 3.1 Implementar el registro `GENERATORS: dict[str, Callable]` y `unique_lowercase(length: int) -> str` (docstring en español, primera línea = descripción corta) para los 3 valores `name-nombre_unico_*` (Ruta 2, disparador de Unicidad).
- [ ] 3.2 Implementar el CLI `--catalog` (`python -m framework.generators --catalog`) que genera la tabla Markdown desde los docstrings.
- [ ] 3.3 Regenerar `docs/generators-catalog.md` con ese CLI. No editarlo a mano.

## 4. `src/framework/mirror.py`

- [ ] 4.1 Implementar `assert_mirror(check, request_payload, response_json, mirror_keys: list[str])`: match exclusivamente por key JSON exacta (nunca substring), una `pytest_check.check(...)` por key declarada.
- [ ] 4.2 No invocarlo desde `test_matriz_create_c1_sin_header` — `docs.md` declara "Mirror keys: ninguna" para este endpoint; la firma queda lista para el próximo endpoint que sí declare mirror keys.

## 5. Validación de aceptación de los módulos de framework (bloqueante)

- [ ] 5.1 **[BLOQUEANTE]** Ejecutar el unit test de `matrix.py` (2.6), `python -m framework.generators --catalog` (3.2/3.3), y `ruff check src/framework/matrix.py src/framework/generators.py src/framework/mirror.py`. Entregar la salida de los tres al QA antes de continuar con la sección 6. No seguir sin confirmación explícita de que los tres pasaron.

## 6. Petición base y semántica de celdas del contexto `c1-sin-header`

- [ ] 6.1 Construir la petición base del contexto a partir de `docs.md`: multipart form-data con `account_id`, `name`, `category`, `lang`, `apps`, `body`, `body_var`, `footer`, `buttons` — sin `type`/`file`/`header`/`header_var`/`security`/`expiration`. Cada caso parametrizado es esta base más la desviación de su fila (vía `build_payload`).

## 7. Variables `MTZ-create-*` (matrix_values)

- [ ] 7.1 Crear las 101 variables `MTZ-create-*` (catálogo regenerado en 2.5) en `variables.yaml → matrix_values:`, cada una con el comentario de la indicación original del CSV.
- [ ] 7.2 Aplicar la corrección de `body_var` documentada en `Why` del proposal: `V1`/`V3`/`V7` usan `MTZ-create-body_var-ausente`; `V5` usa `MTZ-create-body_var-arreglo_con_10_elementos_correspondientes_a`.
- [ ] 7.3 Referenciar `unique_lowercase` desde los 3 `MTZ-create-name-nombre_unico_*` con `generator:`/`params:`.
- [ ] 7.4 `buttons` y `body_var` compuestos se materializan como literal JSON completo en su propia variable `MTZ-create-*` (Opción A) — no requieren composición desde las matrices anidadas de `buttons`.

## 8. Variables `GLB-create-*` sembradas

- [ ] 8.1 Añadir las 8 variables `GLB-create-*` listadas en `proposal.md` a `variables.yaml → globals:`, cada una con placeholder `[REQUIERE RESPUESTA: ...]` y su descripción de siembra.
- [ ] 8.2 (QA) Sembrar en el ambiente: una cuenta existente distinta de 65 (`GLB-create-account_id_ajeno`), un `account_id` que no exista (`GLB-create-account_id_inexistente`), un segundo UUID de app válida (`GLB-create-apps_ids_validos`), un UUID de app inactiva/inexistente (`GLB-create-app_id_inactivo`), un UUID de app de otra cuenta (`GLB-create-app_id_otra_cuenta`), y un `name` de plantilla ya creado (`GLB-create-name_ya_utilizado`).
- [ ] 8.3 (QA) Verificar si `account_id = 1` existe como cuenta válida en el ambiente de pruebas — lo asume la matriz en `V1`/`V3`/`V5`/`V7`, pero el único `account_id` confirmado hasta ahora es 65. Si no existe, reportar como bloqueo de ambiente antes de ejecutar.

## 9. Resolución del header de sesión (`api_access_token`)

- [ ] 9.1 Para los 71 casos que requieren sesión válida, invocar `framework.auth.obtain_session_tokens("Admin", settings=..., http_client=..., account_id=<account_id de la fila>)` directamente desde `matrix.py` por caso parametrizado (decisión 7 de `design.md`) — rol fijo `Admin`, este change no cubre `SuperAdmin`.
- [ ] 9.2 Materializar `I64` (header ausente: no enviar `api-access-token`) e `I65` (`MTZ-create-api_access_token-token_invalido_o_expirado`, un valor estático que no corresponda a ninguna sesión vigente).

## 10. Test parametrizado y aserciones

- [ ] 10.1 Implementar `test_matriz_create_c1_sin_header` con un único `pytest.mark.parametrize` sobre las 73 filas (`V1..V8`, `I1..I65`), usando `parse_matrix`.
- [ ] 10.2 Primera aserción — status code HTTP — como `assert` duro.
- [ ] 10.3 Resto de aserciones de cada caso con `pytest_check.check(...)` (soft assertions).
- [ ] 10.4 No invocar `assert_mirror` (ver 4.2).
- [ ] 10.5 Si alguna fila revela que el endpoint se comporta distinto a lo declarado por la matriz o `docs.md`, marcar ese caso con `pytest.mark.xfail(strict=True, reason=...)` citando el id (`V<n>`/`I<n>`) y la discrepancia, y registrarlo en `inputs/Create/hallazgos.md` (crear el archivo si es el primer hallazgo).
- [ ] 10.6 Anotar resultados en el sidecar `reports/anotado-create-matriz-c1-sin-header.csv` (nunca sobrescribir el CSV de `inputs/`), preservando el BOM `utf-8-sig`. Si `reannotate.py` no soporta aún el contrato de matriz (delimitador/BOM/columna `Campo`/ids `[V<n>]`), anotar manualmente para esta corrida — su reescritura queda fuera de alcance de este change (ver Non-Goals en `design.md`).

## 11. Actualización de `openspec/config.yaml`

- [ ] 11.1 Actualizar § "Arquitectura objetivo — pendiente de implementación": marcar `matrix.py`, `generators.py` y `mirror.py` como existentes, con referencia a este change como el que los introdujo.
- [ ] 11.2 Ajustar la redacción del "Freno duro" y la regla correspondiente en `rules.proposal` (verificación de disponibilidad de los módulos) para que quede como comprobación condicional ("si en el futuro alguno deja de existir o se reescribe") en vez de asumir que nunca existen.

## 12. Ejecución (bloqueante)

- [ ] 12.1 Ejecutar `pytest --stepwise -x -k "matriz-c1-sin-header" -v` y entregar la salida completa al QA. El change no se archiva sin retroalimentación humana explícita y positiva (todas las filas en verde, o discrepancias aceptadas/marcadas como hallazgo).
