## Context

`tests/conftest.py::pytest_runtest_makereport` adjunta dos extras a cada
test fallido usando `pytest_html.extras.text(...)`: el cURL de la última
request (`http_client.last_request`) y el texto de las aserciones de
`pytest-check` fallidas. Con `--self-contained-html` (obligatorio según
`openspec/config.yaml`), `pytest-html` serializa cualquier extra
`text`/`json`/`url` como `<a href="data:...;base64,...">` en la columna
"Links" (`pytest_html/basereport.py::_process_extras` +
`selfcontained_report.py`). Firefox bloquea navegación top-level a URIs
`data:`; Chrome/Brave la permite mal (requiere refresh). Ver proposal.md
- Why para el diagnóstico completo.

`pytest-html` sí soporta un extra `format_type="html"`
(`pytest_html.extras.html(content)`) que se inyecta como `innerHTML`
dentro de la fila expandible del test (`app.js`, `.extraHTML`) — la misma
fila que ya muestra el traceback al hacer click. Ese formato nunca pasa
por `_data_content`/base64: es HTML plano insertado en el DOM del reporte
ya generado.

`src/framework/http.py::client(settings)` construye el `httpx.Client` sin
ningún mecanismo de tracking; hoy cada helper de request debe asignar
`http_client.last_request = response.request` manualmente tras cada
llamada, o el hook de `conftest.py` omite el extra en silencio
(`if last_request is not None`).

## Goals / Non-Goals

**Goals:**
- Los extras de cURL y aserciones fallidas se ven en la misma página del
  reporte, en cualquier navegador, sin URIs `data:`.
- `http_client.last_request` se captura automáticamente para toda request
  enviada por el cliente, sin que cada helper tenga que asignarlo.

**Non-Goals:**
- No se rediseña el layout del reporte HTML ni se añade CSS nuevo — se
  usa el mecanismo de fila expandible que `pytest-html` ya provee.
- No se captura el `response` asociado (solo el `request`) — el cURL
  únicamente necesita el request; si en el futuro se quisiera mostrar
  también el body de la respuesta fallida, es un change aparte.
- No se toca `reannotate.py` ni `resultados.json` — ninguno de los dos
  lee `report.html`.

## Decisions

**1. `pytest_html.extras.html(...)` en vez de `.text(...)` para ambos
extras.**
Es el único formato de `pytest-html` que no pasa por el pipeline de
serialización a `data:` URI en reportes self-contained (confirmado
leyendo `basereport.py::_process_extras`, que solo transforma
`json`/`text`; `html` se deja intacto y se inyecta vía `innerHTML` en
`app.js`). Alternativa descartada: `pytest_html.extras.url(...)`
apuntando a un archivo externo — implicaría reportes no autocontenidos
(contradice el requisito `--self-contained-html` del stack pinneado) y
un archivo por test fallido que gestionar.

Contenido escapado con `html.escape()` y envuelto en `<pre>`: el texto de
`to_curl()` y de `call.excinfo.value` puede contener cualquier caracter
(headers, bodies de respuesta de la API bajo prueba) — sin escapar,
un `<` o `&` en una respuesta rompería el DOM de la fila, y en el peor
caso permitiría HTML/JS arbitrario inyectado en el reporte local.

**2. Efecto colateral aceptado: ya no aparecen en la columna "Links".**
`_process_report` solo agrega a `links` los extras `json`/`text`/`url`
(`basereport.py` línea ~283); un extra `html` nunca entra a esa lista.
Se acepta porque el objetivo explícito es verlos inline al expandir la
fila, no como link — es el comportamiento pedido, no una regresión.

**3. Auto-captura de `last_request` vía `httpx.Client(event_hooks=...)`
en vez de mantener la asignación manual por helper.**
`httpx.Client` soporta `event_hooks={"request": [fn]}`, invocado con el
`Request` antes de enviarlo — exactamente el objeto que `to_curl()`
necesita. Se registra una closure sobre la instancia en
`client(settings)`. Alternativa descartada: envolver `client.send` o
`client.request` con un wrapper manual — más código, y `event_hooks` es
el mecanismo soportado por httpx para este caso exacto (documentado,
estable en 0.28.1, la versión pinneada). Alternativa descartada:
mantener la asignación manual y solo documentar el riesgo — dado que este
change ya toca `http.py`, resolver la causa raíz cuesta lo mismo que
documentarla y evita que se repita en cada helper nuevo (Call
Details/Call Routes incluidos).

**4. `report.extra` → `report.extras` de paso.**
`pytest_html/plugin.py::pytest_runtest_makereport` emite
`DeprecationWarning` cada vez que `report.extra` (singular) tiene
contenido. Como el hook ya se edita para el cambio de formato, se corrige
en la misma pasada — no amerita un change separado por sí solo.

## Risks / Trade-offs

- **[Riesgo] `html.escape()` mal aplicado podría dejar pasar HTML crudo
  si se olvida en un extra futuro** → Mitigación: ambos extras
  (`to_curl`, aserciones) quedan como los únicos dos puntos de
  construcción de extras en el hook; cualquier extra nuevo que se agregue
  a futuro debe seguir el mismo patrón (`html.escape` + `<pre>`), documentado
  aquí como convención del hook.
- **[Riesgo] Un helper futuro podría seguir asignando
  `http_client.last_request` manualmente por costumbre, quedando
  redundante pero inofensivo** → Mitigación: no requiere acción; la
  asignación manual y el `event_hook` no chocan (el último en ejecutar
  gana, y el `event_hook` corre en cada request, así que siempre queda
  actualizado).
- **[Trade-off] Los extras html ya no son "copiables" como texto plano
  con un clic derecho → "Copiar dirección del enlace"** (como sí permite
  un link `data:`) → Aceptado: el QA ve el cURL completo inline y puede
  seleccionarlo/copiarlo directamente del `<pre>`, que es el flujo que
  pidió el QA.

## Migration Plan

No aplica migración de datos ni de ambiente — es un cambio de código en
dos archivos, sin estado persistente. Reportes ya generados
(`reports/report.html` de corridas previas) no se regeneran
retroactivamente; el nuevo comportamiento aplica desde la siguiente
corrida de `pytest`. Rollback: revertir el commit del change, sin pasos
adicionales.
