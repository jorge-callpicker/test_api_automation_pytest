## ADDED Requirements

### Requirement: Persistencia local de la plantilla creada
El sistema SHALL registrar, por cada app de `apps` en la que la creación fue exitosa, una fila local en la base de datos `oauth`, tabla `templates_gupshup`, asociada a esa `app_id` y al `account_id` de la petición, con `template_code_name` igual al `name` enviado, `languageCode` igual al `lang` enviado, y `category` igual al `category` enviado.

#### Scenario: Fila local creada tras éxito total
- **WHEN** la plantilla se crea exitosamente para una app (`200`)
- **THEN** existe en `oauth.templates_gupshup` una fila con `app_id` igual a la app enviada, `account_id` igual al de la petición, `template_code_name` igual al `name` enviado, `languageCode` igual al `lang` enviado, y `category` igual al `category` enviado

### Requirement: Registro de auditoría en creación exitosa
El sistema SHALL generar, al crear exitosamente una plantilla, una entrada de auditoría visible vía `GET /api/v1/accounts/{account_id}/audit_logs` con `auditable_type` igual a `"Template"`, `source` igual a `"admin_chat"`, `associated_id` igual al `account_id` de la petición, y `comment` que referencia el `name` de la plantilla creada y el `id` del template.

#### Scenario: Entrada de auditoría tras éxito total
- **WHEN** la plantilla se crea exitosamente para una app (`200`)
- **THEN** el API de audit logs de Chatwoot expone, para `account_id`, un registro con `auditable_type = "Template"`, `source = "admin_chat"`, `associated_id` igual al `account_id` de la petición, y `comment` que menciona el `name` de la plantilla creada
