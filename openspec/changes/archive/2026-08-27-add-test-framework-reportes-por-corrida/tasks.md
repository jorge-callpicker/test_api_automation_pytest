## 1. Tracking de la respuesta en el cliente HTTP

- [x] 1.1 En `src/framework/http.py`, agregar un segundo `event_hooks["response"]`
      en `client()` que guarde la última `httpx.Response` en
      `instance.last_response`, forzando la lectura del body (`response.read()`
      o acceso a `.content`) dentro del hook para que quede disponible de forma
      síncrona.
- [x] 1.2 Verificar manualmente (o con un test unitario existente que use
      `http_client`) que `last_response` queda poblado tras una petición real,
      igual que ya ocurre con `last_request`. Verificado contra
      `https://pokeapi.co/api/v2` (sustituto temporal, fuera del proyecto,
      ya que aún no hay endpoint real bajo prueba): el body de la respuesta
      aparece en el reporte, confirmando que `last_response` se pobló.

## 2. Carpeta de reporte nueva por ejecución

- [x] 2.1 En `tests/conftest.py`, agregar un hook `pytest_configure(config)`
      que calcule una sola vez `reports/<YYYYMMDD_HHMMSS>/` para todo el
      proceso de pytest.
- [x] 2.2 Dentro de ese hook, sobrescribir `config.option.htmlpath` solo
      cuando el QA no pasó `--html` explícitamente, apuntando al
      `report.html` dentro de la carpeta nueva. Aplicar el mismo criterio
      para la ruta de `pytest-json-report` (`config.option.json_report_file`)
      apuntando a `resultados.json`.
- [x] 2.3 Crear la carpeta con `Path.mkdir(parents=True, exist_ok=True)`
      antes de que los plugins de reporte escriban en ella.
- [x] 2.4 (Encontrado durante implementación) Actualizar `.gitignore`: los
      patrones `reports/*.html`/`reports/*.json`/`reports/*.xml` solo
      cubrían archivos directos en `reports/`, no las subcarpetas nuevas
      por timestamp. Se reemplazan por `reports/` para seguir sin
      versionar toda la carpeta.

## 3. Evidencia de cURL y respuesta en casos exitosos

- [x] 3.1 En `tests/conftest.py`, relajar la condición de
      `pytest_runtest_makereport` de `if report.when != "call" or not
      report.failed: return` a `if report.when != "call": return`.
- [x] 3.2 Mantener el bloque de cURL existente para cualquier resultado
      (`passed` o `failed`) mientras exista `last_request`.
- [x] 3.3 Agregar un bloque nuevo con el status code y el body completo de
      `last_response`, adjuntado siempre que exista `last_response` —
      sin condicionarlo a `report.passed`/`report.failed`, y sin truncar
      ni redactar su contenido, según decisión explícita del QA.
- [x] 3.4 Conservar sin cambios el bloque de aserciones de
      `pytest-check` fallidas, que solo aplica cuando `call.excinfo is
      not None`.
- [x] 3.5 (Revisión post-verificación) El QA probó el change contra un
      ambiente sustituto y pidió que el bloque de respuesta también
      aparezca en casos `failed`, no solo en `passed`. Se retiró la
      condición `if report.passed:` en `tests/conftest.py` para que el
      bloque de respuesta se adjunte igual en ambos resultados; se
      actualizaron `specs/test-reporting/spec.md`, `design.md` y
      `proposal.md` para reflejar el nuevo alcance.

## 4. Documentación de comandos de ejecución

- [x] 4.1 Actualizar los comandos de ejecución documentados en `CLAUDE.md`
      para quitar `--html=reports/report.html` y
      `--json-report-file=reports/resultados.json`, dado que ahora se
      generan automáticamente por corrida.
- [x] 4.2 Actualizar los comandos equivalentes en `README.md` si existen,
      con la misma simplificación.

## 5. Verificación (bloqueante)

- [x] 5.1 Ejecutar `pytest --self-contained-html --json-report` dos veces
      seguidas y confirmar que quedan dos carpetas `reports/<timestamp>/`
      distintas, cada una con su propio `report.html` y `resultados.json`.
      Verificado con un smoke test desechable contra `https://pokeapi.co/api/v2`
      (fuera del repo, ver mensaje del QA en la sesión): dos corridas
      consecutivas produjeron `reports/20260827_175736/` y
      `reports/20260827_175746/`, ambas con sus dos archivos.
- [x] 5.2 Confirmar en el `report.html` de una corrida con al menos un
      caso `passed` que aparece el bloque de cURL y el bloque de
      status+body de la respuesta para ese caso. Verificado (primera
      versión del change, antes de 3.5): `test_get_pikachu_success` (200)
      mostró ambos bloques; `test_get_unknown_pokemon_fails` (404 vs. 200
      esperado) solo mostró cURL + el assert fallido, sin bloque de
      Response. **Superado por 5.4** tras la revisión 3.5, que ahora exige
      el bloque de respuesta también en fallos.
- [x] 5.3 El QA probó el change (versión con evidencia solo en éxito)
      contra `https://pokeapi.co/api/v2` y confirmó que la carpeta nueva
      por corrida y el bloque de respuesta en éxito funcionan. En esa
      misma retroalimentación pidió extender el bloque de respuesta a
      casos fallidos (ver tarea 3.5) — cambio ya aplicado.
- [x] 5.4 Re-verificar tras 3.5: ejecutar de nuevo el smoke test contra un
      caso `failed` con petición HTTP real y confirmar que el
      `report.html` ahora muestra el bloque de cURL **y** el bloque de
      Response (status + body) para ese caso, además del detalle del
      assert fallido. **Confirmado por el QA** (2026-08-27): corrió
      `pytest -k test_zz --self-contained-html --json-report -v` dos
      veces contra PokeAPI, pegó la salida (`test_zz_pikachu_success`
      PASSED, `test_zz_unknown_pokemon_fails` FAILED con `404 == 200`), y
      confirmó visualmente en el `report.html` que el caso fallido ahora
      muestra cURL + Response, cerrando el requirement.
