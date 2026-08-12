## Context

Ver `proposal.md` — Why. `Settings` (`src/framework/config.py`) hoy conoce
dos hosts/tokens del ambiente bajo prueba: `GLB_URL_BASE`/`GLB_TOKEN_ADMIN`
(Gupshup/Templates) y, vía `variables.yaml`, `GLB-url_cp_api` (panel
Callpicker Chat, consumido por `auth.py` para login→selectAccount). La API
de audit logs de Chatwoot (`inputs/audit_logs/docs.md`) es un tercer host
con su propio token, sin relación con ninguno de los dos anteriores. El
`http_client` de sesión (`tests/conftest.py::http_client`) ya se reutiliza
con URLs absolutas para el segundo caso (`auth.py`); este change extiende
el mismo patrón para el tercero.

No existe todavía `inputs/audit_logs/matriz-raiz.csv` ni
`inputs/audit_logs/casos-prueba.md`, por lo que este change no puede ni
debe validar el comportamiento propio del endpoint (paginación real,
errores 401/403, formato de `audited_changes`, etc.) — eso queda para un
`add-test-audit_logs-*` futuro cuando esos artefactos existan.

## Goals / Non-Goals

**Goals:**
- Fijar la firma pública de las funciones de consulta a audit logs para
  que los changes `add-test-*-tc-*`/`add-test-*-matriz-*` futuros de
  plantillas las consuman sin reinterpretarlas (igual que
  `add-test-framework-base` fijó `resolve()`/`client()`/`engine()` y
  `add-framework-auth-session-fixture` fijó `obtain_session_tokens()`).
- Soportar que cada TC consumidor decida su propio criterio de "entrada
  esperada" sin que el framework le imponga una forma de match.
- Reusar la infraestructura HTTP ya existente (cliente de sesión, cURL en
  reporte HTML) en vez de duplicarla.

**Non-Goals:**
- No se valida el comportamiento propio del endpoint `audit_logs`
  (paginación completa, códigos de error, estructura exacta de
  `audited_changes`) — eso es responsabilidad de un `TC-XXX`/matriz
  futuro sobre `inputs/audit_logs/`, no de este cliente.
- No se implementa iteración automática entre páginas ni reintentos con
  espera: el usuario confirmó que la página 1 siempre trae las entradas
  más recientes, que es el único caso de uso actual (assert justo después
  del Act de un TC). Si un caso futuro necesita otra página, la pasa
  explícitamente vía el parámetro `page`.
- No se cachea la respuesta entre llamadas — cada `find_audit_log`
  dispara una request real, igual que `db_conn` no cachea queries.

## Decisions

**1. `audit_logs.py` expone `fetch_audit_logs_page(account_id, page=1, *, settings, http_client) -> dict` y `find_audit_log(account_id, predicate, *, settings, http_client, page=1) -> dict | None`.**
`fetch_audit_logs_page` es la primitiva (una request, un dict crudo);
`find_audit_log` es el helper de conveniencia que la mayoría de los TC
consumirán directamente. Se exponen ambas (no solo `find_audit_log`)
porque un smoke test o un TC futuro que necesite inspeccionar `per_page`/
`total_entries` no debería tener que inventar un `predicate` que siempre
devuelva `True`. Alternativa descartada: una sola función que siempre
filtre — se descarta porque mezclaría la responsabilidad de "traer datos"
con la de "encontrar una entrada", dificultando probar cada una por
separado.

**2. `predicate: Callable[[dict], bool]` en vez de parámetros de filtro fijos (`auditable_type`, `auditable_id`, etc.).**
La doc de Chatwoot no garantiza qué combinación de campos identificará
"la" entrada esperada en cada caso de uso futuro (creación de plantilla,
eliminación, etc.), y anticipar esos campos ahora sería adivinar
requisitos de negocio que no existen todavía. Un `predicate` genérico
deja esa decisión en el TC consumidor, que sí conoce el contexto exacto
(p. ej. `lambda e: e["auditable_type"] == "Template" and e["auditable_id"] == template_id`).
Alternativa descartada: firma con kwargs de filtro fijos
(`auditable_type=None, auditable_id=None, ...`) — se descarta porque
crecería sin control a medida que aparezcan nuevos criterios, y porque
replicaría lógica de filtrado que Python ya resuelve con una lambda.

**3. `page=1` por defecto, sin paginación automática ni `max_pages`.**
El usuario confirmó que la página 1 siempre contiene las entradas más
recientes — el único escenario real hoy es "acabo de crear/eliminar algo,
verifico que su entrada esté ahí". Agregar iteración multi-página o un
límite de seguridad (`max_pages`) sería resolver un problema hipotético
(entradas de otros procesos desplazando la esperada fuera de la página 1)
que nadie ha pedido. Si aparece, se añade en un change posterior con el
caso de uso real que lo motive. Alternativa descartada: iterar hasta
`total_entries` o un `max_pages` fijo — se descarta por regla del
proyecto de no diseñar para escenarios hipotéticos.

**4. Requests con URL absoluta sobre el `http_client` de sesión ya
existente, sin crear un segundo `httpx.Client`.**
Mismo razonamiento que `add-framework-auth-session-fixture` (decisión 4
de su `design.md`): se reusa `http_client` para conservar el mecanismo de
`last_request`/cURL en el reporte HTML ante fallos, evitando duplicar el
ciclo de vida (open/close) de un cliente adicional.

**5. Nuevas variables `GLB_URL_CHATWOOT`/`GLB_TOKEN_CHATWOOT_ADMIN` en
`.env` (vía `Settings`), no en `variables.yaml`.**
Ambas son configuración sensible/específica del ambiente (host y token de
un sistema externo), igual que `GLB_URL_BASE`/`GLB_TOKEN_ADMIN` — no son
datos de negocio versionables. `account_id` sí se resuelve desde
`variables.yaml` (`GLB-account_id_valido`, ya existente) porque el
usuario confirmó que Callpicker Chat comparte el mismo esquema de cuentas
que Chatwoot; no se declara una variable `GLB-*` nueva para eso.

## Risks / Trade-offs

- **[Riesgo] La página 1 podría no contener la entrada esperada si el
  volumen de acciones concurrentes en el ambiente compartido de QA supera
  `per_page` entre el Act del TC y el Assert.**
  → Mitigación: fuera de alcance (Non-Goal); si se observa en ejecución
  real, el siguiente change puede añadir paginación/reintento con el caso
  concreto que lo justifique, en vez de anticiparlo sin evidencia.
- **[Riesgo] `GLB_URL_CHATWOOT`/`GLB_TOKEN_CHATWOOT_ADMIN` quedan como
  `[REQUIERE RESPUESTA: ...]` hasta que el QA los complete — ningún TC
  que dependa de `find_audit_log` puede ejecutarse contra el ambiente
  real hasta entonces.**
  → Mitigación: el smoke test (`test_smoke_audit_logs.py`) es la señal
  temprana de que las credenciales están mal configuradas (falla en
  `setup`, no en un `Assert` de negocio) — regla de `CLAUDE.md` de
  distinguir bloqueo de ambiente de fallo de test.
- **[Riesgo] Un token de audit_logs inválido o sin el feature Enterprise
  habilitado en el ambiente de QA devuelve error, no una lista vacía.**
  → Mitigación: `fetch_audit_logs_page` no oculta el status code — no
  hace `raise_for_status()` ni retorna un dict vacío en error; devuelve
  el JSON tal cual, y es responsabilidad del llamador (smoke test o TC)
  decidir si el status code es aceptable, igual que `auth.py` deja el
  `assert` de status code explícito en cada punto de la cadena.
