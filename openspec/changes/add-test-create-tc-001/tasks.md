## 1. Variables

- [ ] 1.1 Añadir `TC-001-body_var_ejemplo` en `variables.yaml → test_cases.TC-001.variables:` con un valor literal típico (1–1024 caracteres, sin saltos de línea ni 4+ espacios consecutivos).
- [ ] 1.2 Confirmar que `GLB-account_id_valido` y `GLB-create-app_id_valido` (reutilizadas para `{{GLB-account_id_sesion}}` / `{{GLB-app_id_activo_1}}` del TC original) siguen sembradas en `variables.yaml → globals:` sin cambios.
- [ ] 1.3 No declarar `TC-001-nombre_plantilla` en `variables.yaml` — se calcula en el propio archivo de test (ver tarea 2.2 y `proposal.md → Why`).

## 2. Construcción de la petición

- [ ] 2.1 Crear `tests/test_tc_001_creacion_mono_app_sin_encabezado.py` con la petición base del contexto "sin encabezado" derivada de `docs.md`: `account_id`, `name`, `category=MARKETING`, `lang=en_US`, `apps` (un solo elemento), `body` con una variable `{{1}}`, `body_var` con un elemento — sin `type`/`header`/`header_var`/`file`/`security`/`expiration`/`buttons`.
- [ ] 2.2 Calcular `name` en el propio test como `f"tc_1_{unique_lowercase(length=8)}"`, importando `unique_lowercase` directo de `framework.generators` (sin modificar `generators.py`).
- [ ] 2.3 Resolver el resto de campos vía `variables.resolve(..., tc_id="TC-001")` referenciando `{{GLB-account_id_valido}}`, `{{GLB-create-app_id_valido}}`, `{{TC-001-body_var_ejemplo}}`.
- [ ] 2.4 Enviar la petición como `form-data` (`files={campo: (None, valor)}`, mismo patrón que los tests de matriz).

## 3. Ejecución de la petición

- [ ] 3.1 Obtener sesión con `auth.obtain_session_tokens("Admin", account_id=..., settings=settings, http_client=http_client)` (sin usar `GLB_TOKEN_ADMIN`).
- [ ] 3.2 Emitir `POST {{GLB_URL_BASE}}/integrations/gupshup_integrations/templates/create` con header `api-access-token` del token de sesión obtenido.

## 4. Aserciones

- [ ] 4.1 [Assert 1, duro] `assert response.status_code == 200`.
- [ ] 4.2 [Assert 1, soft] `pytest_check.check` sobre `payload[0].app_id == {{GLB-create-app_id_valido}}` y presencia del objeto `template` en la respuesta.
- [ ] 4.3 [Assert 2, soft] Vía fixture `db_conn`, consultar `oauth.templates_gupshup` por `app_id`/`account_id`/`template_code_name` (el `name` generado en 2.2) y verificar con `pytest_check.check` que `languageCode = en_US` y `category = MARKETING`.
- [ ] 4.4 [Assert 3, soft] Vía `framework.audit_logs.find_audit_log(account_id, predicate, settings=settings, http_client=http_client)`, ubicar la entrada cuyo `comment` referencia el `name` generado y verificar con `pytest_check.check` que `auditable_type = "Template"`, `source = "admin_chat"`, `associated_id == account_id`.

## 5. Ejecución bloqueante

- [ ] 5.1 Entregar al QA el comando `pytest --stepwise -k "TC-001" -v` para ejecutar contra el ambiente real.
- [ ] 5.2 Esperar retroalimentación explícita del QA (salida de pytest) antes de dar el change por exitoso. No archivar sin confirmación positiva.
