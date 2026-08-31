## 1. Variables

- [x] 1.1 Añadir `TC-001-body_var_ejemplo` en `variables.yaml → test_cases.TC-001.variables:` con un valor literal típico (1–1024 caracteres, sin saltos de línea ni 4+ espacios consecutivos). Se añadió también `TC-001-body_texto` ("Hello {{1}}"), descubierta como necesaria durante la implementación: el `{{1}}` nativo de WhatsApp colisiona con la sintaxis `{{...}}` de `variables.resolve()` si se escribe mezclado con texto directo en el payload — solo es seguro como variable de referencia completa (mismo patrón que `MTZ-create-body-*` en las matrices).
- [x] 1.2 Confirmar que `GLB-account_id_valido` y `GLB-create-app_id_valido` (reutilizadas para `{{GLB-account_id_sesion}}` / `{{GLB-app_id_activo_1}}` del TC original) siguen sembradas en `variables.yaml → globals:` sin cambios.
- [x] 1.3 No declarar `TC-001-nombre_plantilla` en `variables.yaml` — se calcula en el propio archivo de test (ver tarea 2.2 y `proposal.md → Why`).

## 2. Construcción de la petición

- [x] 2.1 Crear `tests/test_create_tc_001.py` (función `test_create_tc_001`, marcada `@pytest.mark.tc("TC-001")`) con la petición base del contexto "sin encabezado" derivada de `docs.md`: `account_id`, `name`, `category=MARKETING`, `lang=en_US`, `apps` (un solo elemento), `body` con una variable `{{1}}`, `body_var` con un elemento — sin `type`/`header`/`header_var`/`file`/`security`/`expiration`/`buttons`.
- [x] 2.2 Calcular `name` en el propio test como `f"tc_1_{unique_lowercase(length=8)}"`, importando `unique_lowercase` directo de `framework.generators` (sin modificar `generators.py`).
- [x] 2.3 Resolver el resto de campos vía `variables.resolve(..., tc_id="TC-001")` referenciando `{{GLB-account_id_valido}}`, `{{GLB-create-app_id_valido}}`, `{{TC-001-body_texto}}`, `{{TC-001-body_var_ejemplo}}`.
- [x] 2.4 Enviar la petición como `form-data` (`files={campo: (None, valor)}`, mismo patrón que los tests de matriz), reutilizando `framework.matrix.build_payload` para la serialización de `apps`/`body_var` como string JSON.

## 3. Ejecución de la petición

- [x] 3.1 Obtener sesión con `auth.obtain_session_tokens("Admin", account_id=..., settings=settings, http_client=http_client)` (sin usar `GLB_TOKEN_ADMIN`).
- [x] 3.2 Emitir `POST` a `/integrations/gupshup_integrations/templates/create` (relativo a `GLB_URL_BASE`, ya configurado como `base_url` del `http_client`) con header `api-access-token` del token de sesión obtenido.

## 4. Aserciones

- [x] 4.1 [Assert 1, duro] `assert response.status_code == 200`.
- [x] 4.2 [Assert 1, soft] `pytest_check.check` sobre `payload[0].app_id == {{GLB-create-app_id_valido}}` y presencia del objeto `template` en la respuesta.
- [x] 4.3 [Assert 2, soft] Vía fixture `db_conn`, consultar `oauth.templates_gupshup` por `app_id`/`account_id`/`template_code_name` (el `name` generado en 2.2) y verificar con `pytest_check.check` que `languageCode = en_US` y `category = MARKETING`.
- [x] 4.4 [Assert 3, soft] Instanciar un `httpx.Client()` propio (sin los event hooks de `framework.http.client()`) solo para esta llamada, y usarlo en `framework.audit_logs.find_audit_log(account_id, predicate, settings=settings, http_client=<cliente propio>)` para ubicar la entrada cuyo `comment` referencia el `name` generado; verificar con `pytest_check.check` que `auditable_type = "Template"`, `source = "admin_chat"`, `associated_id == account_id`. No reutilizar el `http_client` de la fixture — evita que el reporte registre la petición de auditoría en vez de la petición al endpoint bajo prueba (ver `proposal.md`, decisión 7).

## 5. Corrección de convención

- [x] 5.1 Corregir en `openspec/config.yaml` (sección "Ejecución") el ejemplo de comando para TC individual: de `pytest --stepwise -k "TC-001" -v` (selecciona 0 tests, verificado empíricamente — ver `proposal.md`, decisión 8) a la forma con guion bajo (`pytest --stepwise -k "create_tc_001" -v`), extendiendo la nota existente sobre `-k` para que cubra también TC individual, no solo matriz.

## 6. Ejecución bloqueante

- [x] 6.1 Entregar al QA el comando `pytest --stepwise -k "create_tc_001" -v` para ejecutar contra el ambiente real.
- [x] 6.2 Esperar retroalimentación explícita del QA (salida de pytest) antes de dar el change por exitoso. No archivar sin confirmación positiva. Confirmado: `test_create_tc_001 PASSED` (1 passed, 194 deselected), tras corregir `DB_NAME` en `.env`.
