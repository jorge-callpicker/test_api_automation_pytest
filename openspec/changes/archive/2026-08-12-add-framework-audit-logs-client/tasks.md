## 1. Configuración (`src/framework/config.py`, `env.example`)

- [x] 1.1 Añadir a `Settings` los campos `GLB_URL_CHATWOOT: str` y
      `GLB_TOKEN_CHATWOOT_ADMIN: str`.
- [x] 1.2 Documentar las dos variables anteriores en `env.example` con
      placeholders `[REQUIERE RESPUESTA: ...]`, en una sección nueva
      (`# --- Variables del ambiente Chatwoot (audit logs) ---`) que deje
      explícito que son distintas de `GLB_URL_BASE`/`GLB_TOKEN_ADMIN`
      (Gupshup/Templates).

## 2. Cliente de audit logs (`src/framework/audit_logs.py`)

- [x] 2.1 Implementar `fetch_audit_logs_page(account_id, page=1, *, settings, http_client) -> dict`:
      `GET` a `f"{settings.GLB_URL_CHATWOOT}/api/v1/accounts/{account_id}/audit_logs"`
      con query param `page` y header `api_access_token: settings.GLB_TOKEN_CHATWOOT_ADMIN`;
      registra `http_client.last_request` para el reporte HTML; retorna
      `response.json()` sin validar el status code (el llamador decide).
- [x] 2.2 Implementar `find_audit_log(account_id, predicate, *, settings, http_client, page=1) -> dict | None`:
      llama a `fetch_audit_logs_page(account_id, page, settings=settings, http_client=http_client)`
      y retorna la primera entrada de `audit_logs[]` donde
      `predicate(entry)` sea `True`, o `None` si no hay coincidencia o la
      key `audit_logs` no está presente en la respuesta.

## 3. Smoke test de verificación (`tests/test_smoke_audit_logs.py`)

- [x] 3.1 Crear `tests/test_smoke_audit_logs.py` con
      `@pytest.mark.tc("SMOKE-003")` que llame a
      `fetch_audit_logs_page` con `{{GLB-account_id_valido}}` y verifique:
      `assert` duro de que la key `audit_logs` está presente en la
      respuesta (`fetch_audit_logs_page` no expone el status code crudo
      por diseño — ver `design.md`; su ausencia es la señal de bloqueo de
      ambiente equivalente a un status distinto de 200, con el body de
      error incluido en el mensaje de assert para diagnóstico), luego
      `pytest_check.check(...)` para `current_page == 1` y que
      `audit_logs` es una lista.

## 4. Validación de aceptación (bloqueante)

- [x] 4.1 **[BLOQUEANTE]** Ejecutar, en este orden:
      `pytest --collect-only`,
      `pytest tests/test_smoke_audit_logs.py -v` (selecciona por archivo,
      no por marcador; requiere que `.env` tenga sembrados
      `GLB_URL_CHATWOOT`/`GLB_TOKEN_CHATWOOT_ADMIN` reales y que el
      ambiente Chatwoot esté disponible con el feature `audit_logs`
      habilitado), y `ruff check .`; entregar la salida completa de los
      tres comandos al QA para retroalimentación. No archivar este change
      sin confirmación explícita de que los tres pasaron. Si
      `test_smoke_audit_logs.py` falla por un código de estado inesperado
      (401/403/404, feature no habilitado), tratarlo como bloqueo de
      ambiente, no como fallo de test.
