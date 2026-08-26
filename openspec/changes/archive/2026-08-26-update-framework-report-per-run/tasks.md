## 1. Tracking de la respuesta HTTP

- [x] 1.1 En `src/framework/http.py`, agregar `instance.last_response = None`
      en `client()`, junto al `last_request` ya existente.
- [x] 1.2 Agregar `_track_last_response(response: httpx.Response) -> None`
      que llama `response.read()` y asigna `instance.last_response = response`,
      registrado en `instance.event_hooks["response"]`.

## 2. Carpeta de reporte por ejecución

- [x] 2.1 En `tests/conftest.py`, agregar `pytest_configure(config)` marcado
      `@pytest.hookimpl(tryfirst=True)` que calcule
      `reports/<YYYYMMDD-HHMMSS>/` a partir de `datetime.now()`.
- [x] 2.2 Si `config.option.htmlpath` es `None`, fijarlo a
      `<run_dir>/report.html` y crear `run_dir` con `mkdir(parents=True, exist_ok=True)`.
      Si ya trae valor (el QA pasó `--html` explícito), no tocarlo.
- [x] 2.3 Si `config.getoption("json_report_file", None)` es `None` **o** el
      literal default de pytest-json-report (`.report.json` — ese plugin no
      usa `None` como default, a diferencia de `--html`), fijarlo a
      `<run_dir>/resultados.json`. Si ya trae otro valor explícito, no
      tocarlo. (Ajuste descubierto durante la implementación: ver
      `design.md` § Decisión 1, actualizado.)

## 3. Extras de cURL y respuesta para todo outcome

- [x] 3.1 En `pytest_runtest_makereport`, cambiar la condición de salida
      temprana de `report.when != "call" or not report.failed` a
      `report.when != "call"`, para que corra en `passed`, `failed` y
      `skipped` por igual.
- [x] 3.2 Agregar bloque que, si `http_client_.last_response` no es `None`,
      renderiza un extra HTML con status code, headers y body de la
      respuesta (pretty-printed como JSON si `response.json()` no lanza,
      si no como texto plano), escapado con `html.escape`.
- [x] 3.3 Verificar que el bloque de "Aserciones de pytest-check fallidas"
      (dependiente de `call.excinfo`) sigue apareciendo solo cuando hay
      excepción — no debe aparecer en casos `passed`.

## 4. Config y documentación

- [x] 4.1 Actualizar `.gitignore`: reemplazar `reports/*.html`,
      `reports/*.json`, `reports/*.xml` por un patrón que ignore el
      contenido de las subcarpetas por timestamp (`reports/*/`),
      preservando el tracking de `reports/anotado-*.csv` si vive fuera de
      esas subcarpetas.
- [x] 4.2 Actualizar los comandos de ejecución sugeridos en `CLAUDE.md`
      (sección "Ejecución") para quitar `--html=reports/report.html
      --json-report-file=reports/resultados.json` explícitos.
- [x] 4.3 Actualizar los mismos comandos en `README.md` (todas las
      ocurrencias listadas: líneas ~696-697, ~809-810, ~980-981, ~993-994)
      y el ejemplo de `reannotate.py --results reports/resultados.json`
      (línea ~852) para apuntar a la carpeta con timestamp de la corrida.
- [x] 4.4 Actualizar `openspec/config.yaml` § "Reporte y trazabilidad" para
      describir la carpeta por timestamp en vez del path fijo
      `reports/report.html` / `reports/resultados.json`.

## 5. Verificación (bloqueante)

- [x] 5.1 QA ejecuta `pytest -k "<algo trivial>" -v` dos veces seguidas sin
      pasar `--html` ni `--json-report-file`, y confirma que aparecen dos
      carpetas distintas bajo `reports/`, cada una con su `report.html` y
      `resultados.json`. Confirmado: `reports/20260826-074611/`,
      `reports/20260826-074742/` (dos corridas de `test_smoke`) y
      `reports/20260826-074847/` (matriz `create-c1-sin-header`, 73 casos).
- [x] 5.2 QA abre el `report.html` de una corrida con al menos un test
      `passed` que haga una petición HTTP, y confirma que el reporte
      muestra el cURL y la respuesta (status/headers/body) de ese caso.
      Confirmado: aparece tanto en peticiones con éxito como con error.
- [x] 5.3 QA entrega la salida de la verificación anterior como
      retroalimentación. El change no se archiva sin esta confirmación
      explícita.
