## 1. `src/framework/http.py` — auto-captura de `last_request`

- [x] 1.1 En `client(settings)`, inicializar `instance.last_request = None`
      sobre la instancia de `httpx.Client` antes de retornarla.
- [x] 1.2 Registrar `instance.event_hooks["request"] = [<hook>]`, donde
      `<hook>` es una función/closure que asigna
      `instance.last_request = request` en cada request enviada por el
      cliente (se ejecuta antes de enviar, con el `httpx.Request` crudo
      que `to_curl()` necesita).

## 2. `tests/conftest.py` — extras inline y limpieza

- [x] 2.1 En la fixture `http_client`, eliminar la línea
      `test_client.last_request = None` (ya la cubre `client()` en
      `http.py`).
- [x] 2.2 Importar `escape` de `html` (stdlib) en `conftest.py`.
- [x] 2.3 En `pytest_runtest_makereport`, reemplazar el
      `pytest_html.extras.text(to_curl(last_request), name="cURL (ultima request)")`
      por `pytest_html.extras.html(...)`, con el cURL escapado
      (`escape(to_curl(last_request))`) envuelto en un `<h4>` de título y
      un `<pre>` con el contenido.
- [x] 2.4 Aplicar el mismo tratamiento al extra de
      `"Aserciones de pytest-check fallidas"`: `pytest_html.extras.html(...)`
      con `escape(str(call.excinfo.value))` envuelto en `<h4>` + `<pre>`.
- [x] 2.5 Reemplazar `report.extra = extra` por `report.extras = extra` y
      la lectura `getattr(report, "extra", [])` por
      `getattr(report, "extras", [])` (elimina el `DeprecationWarning` de
      `pytest-html` en cada test fallido).

## 3. Verificación (bloqueante — requiere retroalimentación del QA)

- [x] 3.1 Ejecutar `ruff check --fix .` y `ruff format .` sobre los dos
      archivos modificados.
- [x] 3.2 Agregar temporalmente un test en `tests/` que use `http_client`
      para disparar una request real (contra `{{GLB-url_base}}`, cualquier
      ruta que responda) y una aserción `pytest_check.check(...)` que
      falle a propósito — únicamente para ejercitar el hook de reporte y
      confirmar visualmente el nuevo comportamiento. Documentar en el
      propio test que es temporal y se elimina en la tarea 3.4.
- [ ] 3.3 Ejecutar:
      ```bash
      pytest --html=reports/report.html --self-contained-html \
          --json-report --json-report-file=reports/resultados.json -v
      ```
      Abrir `reports/report.html` en Firefox y en Chrome o Brave. Hacer
      click en la fila del test que falló (no en la columna "Links") y
      confirmar que el cURL y el texto de la aserción fallida aparecen
      **inline** dentro de la fila expandida, en ambos navegadores, sin
      necesidad de refresh y sin ningún link `data:`.
- [ ] 3.4 Eliminar el test temporal agregado en 3.2.
- [ ] 3.5 Entregar al QA la salida de pytest y confirmación de lo
      observado en ambos navegadores. El change no se archiva sin
      retroalimentación explícita y positiva del QA (ver
      `openspec/config.yaml` — "Ciclo humano-en-medio").
