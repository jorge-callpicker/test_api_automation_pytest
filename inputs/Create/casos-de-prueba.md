# Matriz de casos de prueba — Creación de templates de WhatsApp (Gupshup)

Ver artefactos y trazabilidad en `analisis-y-diseno.md`.

Endpoint: `POST {{GLB-url_base}}/integrations/gupshup_integrations/templates/create` (form-data).

Los casos están ordenados por **prioridad descendente**. Toda variable entre `{{ }}` está pendiente de asignación de valor en el catálogo de `analisis-y-diseno.md`.

**Nota de notación:** el formato WhatsApp/Gupshup usa de forma nativa la sintaxis `{{n}}` (doble llave) para las variables **de contenido de la plantilla** (`body`, `header`). Esa sintaxis colisiona visualmente con la convención de variables de este skill (`{{GLB-...}}` / `{{TC-...}}`). Para evitar ambigüedad, en este documento toda variable literal de WhatsApp se representa como `[[n]]` (doble corchete). `[[1]]` significa literalmente `{{1}}` en el payload real y en cualquier mensaje de error citado; al ejecutar el caso, sustituir `[[n]]` por `{{n}}` tal cual. Esto incluye las citas literales de mensajes de error de Gupshup que mencionan `{{1}}` en su texto.

---

## TC-001 - Creación mono-app sin encabezado (Marketing) - Set 1 - Happy paths base

**Tipo:** Positivo
**Técnica:** Happy path base
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Alta
**Prioridad:** Alta
**Criticidad:** Crítica
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** CA01, RN.GEN2, F3.RN1, INT.RN4, AUTH.RN2, F8.RN1 

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-001-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-001-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin autenticada con `{{GLB-token_admin}}`, cuyo `account_id` de sesión coincide con `{{GLB-account_id_sesion}}`; `{{GLB-app_id_activo_1}}` existe, está activa y asociada a la cuenta, con token de partner de Gupshup vigente.

**Act:**
`POST {{GLB-url_base}}/integrations/gupshup_integrations/templates/create` con el `form-data` de Datos de prueba y header `api-access-token: {{GLB-token_admin}}`.

**Assert:**

1. [Respuesta] status `200` con `payload[0].app_id = "{{GLB-app_id_activo_1}}"` y el objeto `template` de la plantilla creada.
2. [Base de datos] existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-001-nombre_plantilla}}`, `languageCode = en_US`, `category = MARKETING`.
3. [API log Chatwot] tras la creación exitosa de la plantilla (status 2XX), el primer registro de los logs asociado a `app_id = {{GLB-app_id_activo_1}}` debe contener `auditable_type = "Template"`, `source = "admin_chat"`, `associated_id = {{GLB-account_id_sesion}}`, `comment = Se creó la plantilla {{TC-001-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).


### Notas de automatización

Sembrar cuenta y app antes de ejecutar. Capturar `template.id` y `app_id` de la respuesta para trazabilidad y limpieza posterior si el entorno lo permite.

**Justificación de Ejecución:** Automática: payload determinístico, sin archivo, con aserciones verificables en la respuesta y en base de datos.

---

## TC-002 - Creación multi-app exitosa con encabezado IMAGE - Set 1 - Happy paths base

**Tipo:** Positivo
**Técnica:** Happy path base
**Rol:** Super admin
**Impacto:** Alto
**Probabilidad:** Alta
**Prioridad:** Alta
**Criticidad:** Crítica
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** CA02, F2.RN5, F7.RN1, F7.RN3, F7.RN4, RN.GEN2

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-002-nombre_plantilla}}
category: UTILITY
lang: en_US
type: IMAGE
file: {{TC-002-file_imagen_valida}} (JPG, 2MB)
apps: ["{{GLB-app_id_activo_1}}", "{{GLB-app_id_activo_2}}"]
body: "Hello [[1]]"
body_var: ["{{TC-002-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
Sesión Super admin con `{{GLB-token_super_admin}}`; ambas apps activas y asociadas a la cuenta, con tokens de partner vigentes.

**Act:**
`POST` con el `form-data` de Datos de prueba, incluyendo el archivo `{{TC-002-file_imagen_valida}}`.

**Assert:**

1. [Respuesta] status `200`, `payload` de longitud 2, ambos elementos con `containerMeta.mediaUrl` apuntando al dominio de Chat (no al dominio temporal de Gupshup).
2. [Base de datos] existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-002-nombre_plantilla}}`, `languageCode = en_US`, `category = UTILITY`, `templateType = IMAGE`.
3. [Base de datos] existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la plantilla asociado a `app_id = {{GLB-app_id_activo_2}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-002-nombre_plantilla}}`, `languageCode = en_US`, `category = UTILITY`, `templateType = IMAGE`.
4. [Base de datos] los registros de la app `{{GLB-app_id_activo_1}}` y de la app `{{GLB-app_id_activo_2}}` en la base de datos `oauth` en la tabla `templates_gupshup` en `mediaUrl` (ubicado dentro del campo `meta`) son idénticos (ambos apuntan al mismo recurso/blob).
5. [API log Chatwot] tras la creación exitosa de la plantilla (status 2XX), el primer registro de los logs asociado a `app_id = {{GLB-app_id_activo_1}}` debe contener `auditable_type = "Template"`, `source = "admin_chat"`, `associated_id = {{GLB-account_id_sesion}}`, `comment = Se creó la plantilla {{TC-002-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).
5. [API log Chatwot] tras la creación exitosa de la plantilla (status 2XX), el primer registro de los logs asociado a `app_id = {{GLB-app_id_activo_2}}` debe contener `auditable_type = "Template"`, `source = "admin_chat"`, `associated_id = {{GLB-account_id_sesion}}`, `comment = Se creó la plantilla {{TC-002-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Verificar mediante logs de red o dobles de prueba que la subida al servidor de Chat ocurrió **una sola vez**, mientras que la subida a Gupshup (obtención de `handle_id`) ocurrió **una vez por cada app**.

**Justificación de Ejecución:** Automática: aserciones observables en la longitud del `payload`, en `mediaUrl` y en el conteo de eventos de auditoría.

---

## TC-003 - Creación AUTHENTICATION con expiration - Set 1 - Happy paths base

**Tipo:** Positivo
**Técnica:** Happy path base
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Alta
**Prioridad:** Alta
**Criticidad:** Crítica
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** CA03, F6.RN2, F6.RN3, RN.GEN2

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-003-nombre_plantilla}}
category: AUTHENTICATION
lang: es_MX
security: "true"
expiration: 15
apps: ["{{GLB-app_id_activo_1}}"]
```

(No se envían `type`, `header`, `header_var`, `footer`, `body`, `body_var`, `file` ni `buttons`.)

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida, `{{GLB-app_id_activo_1}}` activa y asociada a la cuenta.

**Act:**
`POST` con el `form-data` de Datos de prueba.

**Assert:**

1. [Respuesta] status `200`.
2. [Respuesta] el contenido de la plantilla construido para Gupshup (visible en `template.data`/`metaTemplate`) incluye el contenido predefinido para `es_MX`, el mensaje de recomendación de seguridad, el footer con el minuto de expiración `15` y un botón OTP fijo `"Copy Code"`.
3. [Base de datos] existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-003-nombre_plantilla}}`, `languageCode = en_MX`, `category = AUTHENTICATION` `addSecurityRecommendation = true` (ubicado dentro del campo `meta`),`codeExpirationMinutes = 15` (ubicado dentro del campo `meta`).
5. [API log Chatwot] tras la creación exitosa de la plantilla (status 2XX), el primer registro de los logs asociado a `app_id = {{GLB-app_id_activo_1}}` debe contener `auditable_type = "Template"`, `source = "admin_chat"`, `associated_id = {{GLB-account_id_sesion}}`, `comment = Se creó la plantilla {{TC-003-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

El contenido exacto del cuerpo predefinido (`es_MX`) debe compararse contra el literal fijo que Gupshup/Meta usa para plantillas OTP; si el entorno de pruebas no lo documenta, capturarlo del primer run exitoso como snapshot.

**Justificación de Ejecución:** Automática: la validación del contenido predefinido es verificable comparando el cuerpo de la respuesta.

---

## TC-004 - Mismo `name` con `lang` distinto - Set 1 - Happy paths base

**Tipo:** Positivo
**Técnica:** Regla de negocio directa
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** CA17, INT.RN8

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{GLB-template_name_existente}}
category: MARKETING
lang: es_MX
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-004-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
Ya existe una plantilla con `name = {{GLB-template_name_existente}}` y `lang = en_US` en `{{GLB-app_id_activo_1}}` (precondición global).

**Act:**
`POST` enviando el mismo `name` con `lang = es_MX` para la misma app.

**Assert:**

1. [Respuesta] status `200`.
2. [Base de datos] coexisten dos registros locales en la base de datos `oauth` en la tabla `templates_gupshup` de la plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{GLB-template_name_existente}}` y `languageCode = en_MX`, y el otro registro con `template_code_name = {{GLB-template_name_existente}}` y `languageCode = en_US`.
3. [API log Chatwot] tras la creación exitosa de la plantilla (status 2XX), el primer registro de los logs asociado a `app_id = {{GLB-app_id_activo_1}}` debe contener `auditable_type = "Template"`, `source = "admin_chat"`, `associated_id = {{GLB-account_id_sesion}}`, `comment = Se creó la plantilla {{GLB-template_name_existente}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Depende de la precondición global 8 (plantilla `en_US` ya sembrada). Ejecutar después de confirmar que esa siembra existe.

**Justificación de Ejecución:** Automática: verificación directa de coexistencia en BD.

---

## TC-005 - BOLA: `account_id` del body no coincide con el de la sesión - Set 10 - Seguridad

**Tipo:** Seguridad
**Técnica:** Seguridad-BOLA
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Alta
**Prioridad:** Alta
**Criticidad:** Crítica
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** CA04, AUTH.RN2

### Datos de prueba

```
account_id: {{TC-005-account_id_ajeno}}
name: {{TC-005-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-005-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida con `account_id` de sesión `= {{GLB-account_id_sesion}}`.

**Act:**
`POST` con `account_id = {{TC-005-account_id_ajeno}}` (distinto al de la sesión) y header `api-access-token: {{GLB-token_admin}}`.

**Assert:**

1. [Respuesta] status `401`, body `{ code: 401, message: "Unauthorized" }`.
2. [Base de datos] no se crea ningún registro de la plantilla en la base de datos local `oauth` en la tabla `templates_gupshup` con `template_code_name = {{TC-005-nombre_plantilla}}` y `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-005-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).


### Notas de automatización

Caso de seguridad prioritario (BOLA): un usuario legítimo no debe poder operar sobre una cuenta que no es la de su sesión aunque el UUID de `apps` sea válido y pertenezca a esa otra cuenta.

**Justificación de Ejecución:** Automática: la aserción de status y ausencia de efectos secundarios es completamente verificable sin intervención manual.

---

## TC-006 - Degradación de rol Super admin a agente (token vigente) - Set 10 - Seguridad

**Tipo:** Seguridad
**Técnica:** Autorización por rol
**Rol:** Super admin (degradado a agente)
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Alta
**Criticidad:** Crítica
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** CA05, AUTH.RN1, AUTH.RN2

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-006-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-006-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
Usuario que generó `{{GLB-token_degradado_desde_super_admin}}` mientras tenía rol Super admin combinado con agente; posteriormente el rol Super admin fue removido, quedando únicamente como agente. El token sigue vigente (no expiró).

**Act:**
`POST` con el `form-data` válido y header `api-access-token: {{GLB-token_degradado_desde_super_admin}}`.

**Assert:**

1. [Respuesta] status `401`, body `{ code: 401, message: "Unauthorized" }`.
2. [Base de datos] no se crea ningún registro de la plantilla en la base de datos local `oauth` en la tabla `templates_gupshup` con `template_code_name = {{TC-006-nombre_plantilla}}` y `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-006-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Requiere manipular el rol del usuario en base de datos **después** de haber emitido el token (para simular vigencia con rol ya removido). Automatizable si el entorno de pruebas permite alterar roles vía seed/API interna sin regenerar el JWT.

**Justificación de Ejecución:** Automática: siempre que se pueda modificar el rol en BD de forma controlada sin afectar el token ya emitido.

---

## TC-007 - Degradación de rol Admin a agente (token vigente) - Set 10 - Seguridad

**Tipo:** Seguridad
**Técnica:** Autorización por rol
**Rol:** Admin (degradado a agente)
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Alta
**Criticidad:** Crítica
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** CA06, AUTH.RN1, AUTH.RN2

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-007-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-007-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
Usuario que generó `{{GLB-token_degradado_desde_admin}}` con rol Admin; posteriormente fue degradado a rol agente. El token sigue vigente.

**Act:**
`POST` con el `form-data` válido y header `api-access-token: {{GLB-token_degradado_desde_admin}}`.

**Assert:**

1. [Respuesta] status `401`, body `{ code: 401, message: "Unauthorized" }`.
2. [Base de datos] no se crea ningún registro de la plantilla en la base de datos local `oauth` en la tabla `templates_gupshup` con `template_code_name = {{TC-007-nombre_plantilla}}` y `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-007-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Misma consideración de setup que TC-006, aplicada al rol Admin.

**Justificación de Ejecución:** Automática: mismo razonamiento que TC-006.

---

## TC-049 - Admin con `account_id` coincidente en sesión pero sin asociación en BD - Set 10 - Seguridad

**Tipo:** Seguridad
**Técnica:** Seguridad-BOLA
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Alta
**Criticidad:** Crítica
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** RN.GEN1

### Datos de prueba

```
account_id: {{TC-049-account_id_no_asociado}}
name: {{TC-049-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-049-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
Existe una cuenta real `{{TC-049-account_id_no_asociado}}` en el sistema, pero **no** asociada al usuario Admin bajo prueba en base de datos. Se craftea un JWT `{{TC-049-token_admin_account_id_no_asociado}}` cuyo reclamo `account_id` = `{{TC-049-account_id_no_asociado}}` (el mismo valor que se enviará en el body), de forma que la comparación literal `body.account_id == sesión.account_id` (paso 1 de la lógica interna, la misma que aísla TC-005) se cumple.

**Act:**
`POST` con `account_id = {{TC-049-account_id_no_asociado}}` en el body y header `api-access-token: {{TC-049-token_admin_account_id_no_asociado}}`.

**Assert:**

1. [Respuesta] status `401`, body `{ code: 401, message: "Unauthorized" }` — aunque el `account_id` del body coincide con el reclamo `account_id` del token.
2. [Base de datos] no se crea ningún registro de plantilla; no existe relación Admin↔cuenta `{{TC-049-account_id_no_asociado}}` en la tabla de asociación de cuentas.
3. [Log] no se genera ningún evento de auditoría.
4. [Cola/Evento] no se ejecuta ninguna llamada saliente a Gupshup ni al servidor de subida de Chat (verificar ausencia de invocación mediante mocks/spies).

### Notas de automatización

Reutiliza la capacidad de emitir JWT de prueba con reclamos controlados (precondición global 11, ya usada por TC-044) para craftear un token cuyo `account_id` coincide con el enviado en el body pero no tiene asociación real en base de datos. Es la contraparte de TC-005: allí la comparación literal body/sesión falla (RN distinta, `AUTH.RN2`); aquí esa comparación literal se cumple, y lo que se aísla es la validación en base de datos de la asociación cuenta↔Admin (RN.GEN1), confirmada por el negocio tras el cierre de PEND-02.

**Justificación de Ejecución:** Automática: la aserción de status y la ausencia de efectos secundarios en base de datos son completamente verificables sin intervención manual, siempre que el entorno de pruebas permita craftear el JWT y sembrar la falta de asociación en base de datos.

---

## TC-008 - UUIDs duplicados en `apps` - Set 8 - Validaciones de payload: campos requeridos

**Tipo:** Negativo
**Técnica:** Regla de negocio directa
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Alta
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** CA07, INT.RN7

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-008-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}", "{{GLB-app_id_activo_1}}", "{{GLB-app_id_activo_2}}"]
body: "Hello [[1]]"
body_var: ["{{TC-008-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida.

**Act:**
`POST` con `apps` conteniendo `{{GLB-app_id_activo_1}}` duplicado.

**Assert:**

1. [Respuesta] status `400`; el objeto `errors` referencia el campo `apps` y el mensaje `"Duplicate app IDs are not allowed"` (código, campo y mensaje se verifican sin fijar una única forma del objeto `errors` — PEND-01 resuelto: ambas representaciones (`{field,msg}` y diccionario `{campo: mensaje}`) son válidas, ver `analisis-y-diseno.md`).
2. [Base de datos] no se crea ningún registro de la plantilla en la base de datos local `oauth` en la tabla `templates_gupshup` con `template_code_name = {{TC-008-nombre_plantilla}}` y `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-008-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).
4. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_2}}` y `comment = Se creó la plantilla {{TC-008-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Verificar que la detección de duplicados ocurre antes de cualquier llamada externa (mock/spy en cero invocaciones).

**Justificación de Ejecución:** Automática: validación puramente de esquema, sin dependencias externas.

---

## TC-009 - AUTHENTICATION con campo `body` prohibido - Set 5 - Reglas de negocio: Categoría AUTHENTICATION

**Tipo:** Negativo
**Técnica:** Tabla de decisión (DT4)
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** CA10, F6.RN1

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-009-nombre_plantilla}}
category: AUTHENTICATION
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hola"
```

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida.

**Act:**
`POST` con `category = AUTHENTICATION` y `body = "Hola"` incluido.

**Assert:**

1. [Respuesta] status `400`; `msg` indica `"Not allowed for AUTHENTICATION templates"`; el `field` reportado es `body` (primero entre los campos prohibidos presentes, según el orden de la tabla "Validaciones de Entrada Creación").
2. [Base de datos] no se crea ningún registro de la plantilla en la base de datos local `oauth` en la tabla `templates_gupshup` con `template_code_name = {{TC-009-nombre_plantilla}}` y `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-009-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).


### Notas de automatización

No incluir ningún otro campo prohibido en el payload para aislar que el `field` reportado es específicamente `body`.

**Justificación de Ejecución:** Automática: validación de esquema determinística.

---

## TC-010 - AUTHENTICATION sin campo `security` - Set 5 - Reglas de negocio: Categoría AUTHENTICATION

**Tipo:** Negativo
**Técnica:** Tabla de decisión (DT4)
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** F6.RN2

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-010-nombre_plantilla}}
category: AUTHENTICATION
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
```

(Sin `security`.)

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida.

**Act:**
`POST` con `category = AUTHENTICATION` sin enviar `security`.

**Assert:**

1. [Respuesta] status `400`; `msg: "Security is required for AUTHENTICATION templates"`, `field: security`.
2. [Base de datos] no se crea ningún registro de la plantilla en la base de datos local `oauth` en la tabla `templates_gupshup` con `template_code_name = {{TC-010-nombre_plantilla}}` y `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-010-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Ninguna dependencia externa.

**Justificación de Ejecución:** Automática: validación de esquema determinística.

---

## TC-011 - AUTHENTICATION con `expiration` fuera de rango (91) - Set 5 - Reglas de negocio: Categoría AUTHENTICATION

**Tipo:** Negativo
**Técnica:** Tabla de decisión (DT4)
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** F6.RN2

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-011-nombre_plantilla}}
category: AUTHENTICATION
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
security: "true"
expiration: 91
```

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida.

**Act:**
`POST` con `expiration = 91` (borde superior al máximo permitido de 90, valor literal derivado de la regla explícita 1-90).

**Assert:**

1. [Respuesta] status `400`; `msg: "Must be <= 90"`, `field: expiration`.
2. [Base de datos] no se crea ningún registro de la plantilla en la base de datos local `oauth` en la tabla `templates_gupshup` con `template_code_name = {{TC-011-nombre_plantilla}}` y `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-011-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

`security` debe enviarse válido para que la validación llegue a evaluar `expiration` (orden de la tabla de validaciones).

**Justificación de Ejecución:** Automática: validación de esquema determinística.

---

## TC-012 - AUTHENTICATION con `buttons` (prohibido) - Set 5 - Reglas de negocio: Categoría AUTHENTICATION

**Tipo:** Negativo
**Técnica:** Tabla de decisión (DT4)
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** F6.RN1

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-012-nombre_plantilla}}
category: AUTHENTICATION
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
security: "true"
buttons: [{ "type": "QUICK_REPLY", "title": "...", "payload": "..." }]
```

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida. `security` y `expiration` enviados válidos (o `expiration` ausente) para que la validación llegue a evaluar `buttons`, el único campo prohibido presente.

**Act:**
`POST` con `category = AUTHENTICATION` y `buttons` incluido.

**Assert:**

1. [Respuesta] status `400`; `msg` indica `"Not allowed for AUTHENTICATION templates"`, `field: buttons`.
2. [Base de datos] no se crea ningún registro de la plantilla en la base de datos local `oauth` en la tabla `templates_gupshup` con `template_code_name = {{TC-012-nombre_plantilla}}` y `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-012-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Este caso, a diferencia de CA10 (TC-009), aísla específicamente el campo `buttons` como único prohibido presente, verificando que la regla de exclusividad se aplica a cada campo de la lista, no solo a `body`.

**Justificación de Ejecución:** Automática: validación de esquema determinística.

---

## TC-013 - Éxito parcial (206) por app no perteneciente a la cuenta - Set 6 - Transiciones de estado (ciclo de apps)

**Tipo:** Borde
**Técnica:** Transición de estado
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Alta
**Prioridad:** Alta
**Criticidad:** Crítica
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** CA13, F7.RN1, F7.RN3, F7.RN4

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-013-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}", "{{GLB-app_id_no_perteneciente_a_cuenta}}"]
body: "Hello [[1]]"
body_var: ["{{TC-013-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
`{{GLB-app_id_activo_1}}` pertenece a la cuenta; `{{GLB-app_id_no_perteneciente_a_cuenta}}` no pertenece (o no existe).

**Act:**
`POST` con ambas apps en la lista.

**Assert:**

1. [Respuesta] status `206`; `success` contiene el resultado de `{{GLB-app_id_activo_1}}`; `errors` contiene `{ app_id: "{{GLB-app_id_no_perteneciente_a_cuenta}}", msg: "App not found or inactive" }`.
2. [Base de datos] existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-013-nombre_plantilla}}`, `languageCode = en_US`, `category = MARKETING`.
3. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_no_perteneciente_a_cuenta}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-013-nombre_plantilla}}`, `languageCode = en_US`, `category = MARKETING`.
4. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_no_perteneciente_a_cuenta}}` y `comment = Se creó la plantilla {{TC-013-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).
5. [API log Chatwot] tras la creación exitosa de la plantilla (status 2XX), el primer registro de los logs asociado a `app_id = {{GLB-app_id_activo_1}}` debe contener `auditable_type = "Template"`, `source = "admin_chat"`, `associated_id = {{GLB-account_id_sesion}}`, `comment = Se creó la plantilla {{TC-013-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).


### Notas de automatización

Caso central de la máquina de estados del ciclo de apps: valida que el fallo de una app no detiene el procesamiento de las demás.

**Justificación de Ejecución:** Automática: reproducible con datos sembrados reales (una app que no pertenece a la cuenta), sin necesidad de mocks.

---

## TC-014 - Todas las apps fallan: token no obtenible (400 "All accounts failed") - Set 6 - Transiciones de estado (ciclo de apps)

**Tipo:** Borde
**Técnica:** Transición de estado
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Alta
**Criticidad:** Crítica
**Corte-medio-tiempo:** No
**Ejecución:** Manual
**Requerimiento validado:** CA14, TR.RN4, F7.RN3

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-014-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{TC-014-app_id_token_invalido_1}}", "{{TC-014-app_id_token_invalido_2}}"]
body: "Hello [[1]]"
body_var: ["{{TC-014-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
Ambas apps existen y pertenecen a la cuenta, pero sus tokens de partner no pueden obtenerse ni regenerarse (condición de datos/infra especial, no reproducible con las apps activas estándar).

**Act:**
`POST` con ambas apps.

**Assert:**

1. [Respuesta] status `400`; body `{ code: 400, message: "All accounts failed", errors: [{ app_id: "{{TC-014-app_id_token_invalido_1}}", msg: "Could not get token" }, { app_id: "{{TC-014-app_id_token_invalido_2}}", msg: "Could not get token" }] }`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{TC-014-app_id_token_invalido_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-014-nombre_plantilla}}`, `languageCode = en_US`, `category = MARKETING`.
3. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{TC-014-app_id_token_invalido_2}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-014-nombre_plantilla}}`, `languageCode = en_US`, `category = MARKETING`.
4. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{TC-014-app_id_token_invalido_1}}` y `comment = Se creó la plantilla {{TC-014-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).
5. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{TC-014-app_id_token_invalido_2}}` y `comment = Se creó la plantilla {{TC-014-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Requiere sembrar apps con condición de token irrecuperable (por ejemplo, credenciales de partner revocadas en el entorno de pruebas de Gupshup), condición difícil de reproducir de forma determinista solo con datos estándar.

**Justificación de Ejecución:** Manual: depende de una condición de infraestructura externa (token de partner irrecuperable) que requiere preparación específica fuera del control directo del caso de prueba automatizado.

---

## TC-015 - Gupshup rechaza la creación sin mensaje asociado - Set 6 - Transiciones de estado (ciclo de apps)

**Tipo:** Borde
**Técnica:** Transición de estado
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Manual
**Requerimiento validado:** CA15, TR.RN4

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-015-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-015-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
La petición llega hasta el paso 12 (envío a Gupshup); el API de partner de Gupshup está configurado (mock/doble de prueba) para responder con código distinto a 200 sin texto asociado.

**Act:**
`POST` con el `form-data` anterior.

**Assert:**

1. [Respuesta] status `400`, `errors: [{ app_id: "{{GLB-app_id_activo_1}}", msg: "Gupshup rejected template creation" }]`, `message: "All accounts failed"`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-015-nombre_plantilla}}`, `languageCode = en_US`, `category = MARKETING`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-015-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Requiere control directo sobre la respuesta del API de partner de Gupshup (mock/stub); no reproducible únicamente con datos de prueba reales.

**Justificación de Ejecución:** Manual: depende de simular una respuesta específica del sistema externo Gupshup.

---

## TC-016 - `name + lang` ya existente, detección delegada a Gupshup - Set 6 - Transiciones de estado (ciclo de apps)

**Tipo:** Borde
**Técnica:** Transición de estado
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** CA16, INT.RN8

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{GLB-template_name_existente}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-016-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
Ya existe una plantilla con `name = {{GLB-template_name_existente}}` y `lang = en_US` en `{{GLB-app_id_activo_1}}` (precondición global).

**Act:**
`POST` repitiendo exactamente el mismo `name` y `lang` para la misma app.

**Assert:**

1. [Respuesta] el endpoint captura el error que Gupshup retorna por duplicado; la respuesta final es `400` con `message: "All accounts failed"` y el `msg` en `errors[]` es el mensaje devuelto por Gupshup (si viene) o `"Gupshup rejected template creation"` (fallback).
2. [Base de datos] no existe más de un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{GLB-template_name_existente}}`, con el mismo `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{GLB-template_name_existente}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Reproducible con datos reales (sin mocks), reutilizando la plantilla sembrada en la precondición global 8.

**Justificación de Ejecución:** Automática: condición reproducible con datos sembrados reales.

---

## TC-017 - Concurrencia sobre mismo `name + lang` - Set 6 - Transiciones de estado (ciclo de apps)

**Tipo:** Borde
**Técnica:** Transición de estado
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Manual
**Requerimiento validado:** CA18, INT.RN9

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-017-nombre_concurrente}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-017-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
Dos peticiones idénticas preparadas con el mismo `name = {{TC-017-nombre_concurrente}}` y `lang = en_US` para la misma app, listas para dispararse en paralelo.

**Act:**
Disparar ambas peticiones `POST` simultáneamente (sin serialización de por medio).

**Assert:**

1. [Respuesta] la primera petición que alcanza con éxito el paso 13 responde `200` con la plantilla creada.
2. [Respuesta] la segunda petición recibe en `errors[]` el error que Gupshup retorna por duplicado (`"Gupshup rejected template creation"` como fallback).
3. [Base de datos] no existe más de un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-017-nombre_concurrente}}`, con el mismo `languageCode = en_US`.
4. [API log Chatwot] tras la creación exitosa de la plantilla (status 2XX), el primer registro de los logs asociado a `app_id = {{GLB-app_id_activo_1}}` debe contener `auditable_type = "Template"`, `source = "admin_chat"`, `associated_id = {{GLB-account_id_sesion}}`, `comment = Se creó la plantilla {{TC-017-nombre_concurrente}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).
5. [API log Chatwot] no existe más de un registro reciente de logs para `app_id = {{GLB-app_id_activo_1}}` con `comment = Se creó la plantilla {{TC-017-nombre_concurrente}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Requiere un orquestador capaz de disparar ambas peticiones con la menor diferencia de tiempo posible y capturar cuál llega primero a Gupshup; el orden de éxito/fallo puede no ser determinista entre corridas.

**Justificación de Ejecución:** Manual: la naturaleza no determinista de la concurrencia dificulta una aserción automatizada estable sobre cuál petición gana.

---

## TC-018 - Falla la subida del archivo a Chat (500) - Set 6 - Transiciones de estado (ciclo de apps)

**Tipo:** Borde
**Técnica:** Transición de estado
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Manual
**Requerimiento validado:** CA23, F2.RN5

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-018-nombre_plantilla}}
category: MARKETING
lang: en_US
type: DOCUMENT
file: {{TC-018-file_para_subida}}
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-018-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
El sistema de subida interno del servidor de Chat está configurado (mock/doble de prueba) para rechazar el archivo con error 500.

**Act:**
`POST` con un encabezado multimedia (`type = DOCUMENT`) y archivo válido.

**Assert:**

1. [Respuesta] status `500`, body `{ code: 500, message: "Failed to upload file", errors: { file: <upload_error> } }`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-018-nombre_plantilla}}`, `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-018-nombre_concurrente}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).
### Notas de automatización

Requiere forzar el fallo del servicio interno de subida de Chat (mock a nivel de infraestructura), no reproducible solo con datos de prueba.

**Justificación de Ejecución:** Manual: depende de simular un fallo del servicio interno de almacenamiento.

---

## TC-019 - Token de partner expirado se regenera correctamente - Set 6 - Transiciones de estado (ciclo de apps)

**Tipo:** Borde
**Técnica:** Transición de estado
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** CA26, AUTH.RN4, TR.RN1, TR.RN2, TR.RN3

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-019-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{TC-019-app_id_token_expirado}}"]
body: "Hello [[1]]"
body_var: ["{{TC-019-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
`{{TC-019-app_id_token_expirado}}` tiene un token de partner con fecha de expiración pasada en base de datos, pero las credenciales subyacentes siguen siendo válidas para regenerarlo.

**Act:**
`POST` con esa app.

**Assert:**

1. [Respuesta] la regeneración es exitosa y la creación continúa hasta status `200`.
2. [Respuesta] el tiempo total de procesamiento de esa app no supera el peor caso documentado de 120s.
3. [Base de datos] existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{TC-019-app_id_token_expirado}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-015-nombre_plantilla}}`, `languageCode = en_US`, `category = MARKETING`.
4. [API log Chatwot] tras la creación exitosa de la plantilla (status 2XX), el primer registro de los logs asociado a `app_id = {{TC-019-app_id_token_expirado}}` debe contener `auditable_type = "Template"`, `source = "admin_chat"`, `associated_id = {{GLB-account_id_sesion}}`, `comment = Se creó la plantilla {{TC-019-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).


### Notas de automatización

Sembrar la app con `expires_at` en el pasado. Medir el tiempo de respuesta como aserción complementaria (no estricta, solo de sanity).

**Justificación de Ejecución:** Automática: la condición de token expirado es reproducible manipulando directamente la fecha de expiración en base de datos.

---

## TC-020 - Todas las apps fallan con blob multimedia ya subido - Set 6 - Transiciones de estado (ciclo de apps)

**Tipo:** Borde
**Técnica:** Transición de estado
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Manual
**Requerimiento validado:** CA27, F2.RN5

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-020-nombre_plantilla}}
category: MARKETING
lang: en_US
type: IMAGE
file: {{TC-020-file_imagen_3mb}}
apps: ["{{GLB-app_id_activo_1}}", "{{GLB-app_id_activo_2}}"]
body: "Hello [[1]]"
body_var: ["{{TC-020-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
El archivo se subirá con éxito al servidor de Chat (paso 4); ambas apps están configuradas (mock) para fallar al obtener el `handle_id` de Gupshup en el paso 7.

**Act:**
`POST` con el `form-data` anterior.

**Assert:**

1. [Respuesta] status `400`, `message: "All accounts failed"`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-020-nombre_plantilla}}`, `languageCode = en_US`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_2}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-020-nombre_plantilla}}`, `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-020-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).
4. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_2}}` y `comment = Se creó la plantilla {{TC-020-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Documentar que la limpieza del blob es responsabilidad de un cron externo fuera del alcance de este endpoint; no se debe aserir su eliminación en este caso.

**Justificación de Ejecución:** Manual: requiere forzar el fallo de obtención de `handle_id` en Gupshup para ambas apps, condición externa no controlable solo con datos.

---

## TC-021 - Gupshup responde 200 sin información de plantilla - Set 6 - Transiciones de estado (ciclo de apps)

**Tipo:** Borde
**Técnica:** Transición de estado
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Manual
**Requerimiento validado:** F7.RN3 (paso 14 de la lógica interna)

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-021-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-021-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
El API de partner de Gupshup está configurado (mock) para responder `200` en el paso 13 pero sin incluir la información de la plantilla creada.

**Act:**
`POST` con el `form-data` anterior.

**Assert:**

1. [Respuesta] `errors: [{ app_id: "{{GLB-app_id_activo_1}}", msg: "No template returned from Gupshup" }]`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-021-nombre_plantilla}}`, `languageCode = en_US`.
4. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-021-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Transición no cubierta por ningún criterio de aceptación explícito; se agregó por completitud de la máquina de estados (Proceso 3).

**Justificación de Ejecución:** Manual: requiere simular una respuesta 200 vacía del API de partner de Gupshup.

---

## TC-022 - `type = TEXT` sin `header` - Set 2 - Reglas de negocio: Encabezados

**Tipo:** Negativo
**Técnica:** Tabla de decisión (DT1)
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** F1.RN2

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-022-nombre_plantilla}}
category: MARKETING
lang: en_US
type: TEXT
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-022-body_var_ejemplo}}"]
```

(Sin `header`.)

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida.

**Act:**
`POST` con `type = TEXT` sin enviar `header`.

**Assert:**

1. [Respuesta] status `400`; `msg: "Header is required when type is TEXT"`, `field: header`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-022-nombre_plantilla}}`, `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-022-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Ninguna dependencia externa.

**Justificación de Ejecución:** Automática: validación de esquema determinística.

---

## TC-023 - `type = IMAGE` sin `file` - Set 2 - Reglas de negocio: Encabezados

**Tipo:** Negativo
**Técnica:** Tabla de decisión (DT1)
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** F2.RN1

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-023-nombre_plantilla}}
category: MARKETING
lang: en_US
type: IMAGE
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-023-body_var_ejemplo}}"]
```

(Sin `file`.)

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida.

**Act:**
`POST` con `type = IMAGE` sin enviar `file`.

**Assert:**

1. [Respuesta] status `400`; `msg: "File is required when type is IMAGE, VIDEO or DOCUMENT"`, `field: file`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-023-nombre_plantilla}}`, `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-023-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).


### Notas de automatización

Ninguna dependencia externa.

**Justificación de Ejecución:** Automática: validación de esquema determinística.

---

## TC-024 - `file` supera el límite por tipo (IMAGE 6 MB) - Set 2 - Reglas de negocio: Encabezados

**Tipo:** Negativo
**Técnica:** Tabla de decisión (DT1)
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Alta
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** CA08, F2.RN2

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-024-nombre_plantilla}}
category: MARKETING
lang: en_MX
type: IMAGE
file: {{TC-024-file_imagen_6mb}}
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-024-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
Archivo `{{TC-024-file_imagen_6mb}}` es PNG o JPG válido de 6 MB (excede el máximo de 5 MB para IMAGE).

**Act:**
`POST` con dicho archivo bajo `type = IMAGE`.

**Assert:**

1. [Respuesta] status `400`; `msg: "File too large for IMAGE. Max allowed is 5MB"`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-024-nombre_plantilla}}`, `languageCode = en_MX`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-024-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Preparar el binario de 6 MB como fixture reutilizable.

**Justificación de Ejecución:** Automática: validación de tamaño determinística sobre un archivo fijo.

---

## TC-025 - `type = IMAGE` con `file` de MIME `video/mp4` - Set 2 - Reglas de negocio: Encabezados

**Tipo:** Negativo
**Técnica:** Tabla de decisión (DT1)
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Alta
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** CA09, F2.RN2

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-025-nombre_plantilla}}
category: MARKETING
lang: en_US
type: IMAGE
file: {{TC-025-file_imagen_mime_video}}
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-025-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
Archivo `{{TC-025-file_imagen_mime_video}}` cuyo `Content-Type` es `video/mp4`.

**Act:**
`POST` con dicho archivo bajo `type = IMAGE`.

**Assert:**

1. [Respuesta] status `400`; `msg: "Invalid file type for IMAGE. Allowed: image/jpeg, image/png"`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-025-nombre_plantilla}}`, `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-025-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).


### Notas de automatización

Preparar un archivo cuyo MIME declarado sea `video/mp4` independientemente de su contenido real.

**Justificación de Ejecución:** Automática: validación de MIME determinística.

---

## TC-026 - Variables no secuenciales en `body` - Set 3 - Reglas de negocio: Body y variables

**Tipo:** Negativo
**Técnica:** Tabla de decisión (DT2)
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Alta
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** CA19, F3.RN3

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-026-nombre_plantilla}}
category: MARKETING
lang: en_MX
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hola [[1]], tu código es [[3]]"
body_var: ["Ana", "1234"]
```

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida.

**Act:**
`POST` con `body` conteniendo `[[1]]` y `[[3]]` (salto de `[[2]]`).

**Assert:**

1. [Respuesta] status `400`; `msg: "Body variables must appear in order starting from [[1]] with no gaps or repeats"`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-026-nombre_plantilla}}`, `languageCode = en_MX`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-026-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).



### Notas de automatización

Los valores literales de `body`/`body_var` provienen directamente del CA19 del requerimiento.

**Justificación de Ejecución:** Automática: validación de esquema determinística sobre valores literales.

---

## TC-027 - Cantidad de `body_var` no coincide con variables del `body` - Set 3 - Reglas de negocio: Body y variables

**Tipo:** Negativo
**Técnica:** Tabla de decisión (DT2)
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Alta
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** CA20, F3.RN4

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-027-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hola [[1]] y [[2]]"
body_var: ["Ana"]
```

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida.

**Act:**
`POST` con `body` conteniendo 2 variables y `body_var` con 1 solo elemento.

**Assert:**

1. [Respuesta] status `400`; `msg: "Body_var must have exactly 2 item(s) to match body variables"`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-027-nombre_plantilla}}`, `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-027-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).


### Notas de automatización

Valores literales provienen directamente del CA20 del requerimiento.

**Justificación de Ejecución:** Automática: validación de esquema determinística.

---

## TC-028 - `name` con formato inválido (mayúsculas) - Set 8 - Validaciones de payload: campos requeridos

**Tipo:** Negativo
**Técnica:** Regla de negocio directa
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** INT.RN4

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-028-nombre_con_mayusculas}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-028-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
`{{TC-028-nombre_con_mayusculas}}` contiene al menos una letra mayúscula, incumpliendo `^[a-z0-9_]{3,179}$`.

**Act:**
`POST` con ese `name`.

**Assert:**

1. [Respuesta] status `400`; `msg: "Must match pattern: ^[a-z0-9_]{3,179}$"`, `field: name`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-028-nombre_con_mayusculas}}`, `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-028-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).



### Notas de automatización

Ninguna dependencia externa.

**Justificación de Ejecución:** Automática: validación de patrón determinística.

---

## TC-029 - `apps` contiene un elemento con formato de UUID inválido - Set 8 - Validaciones de payload: campos requeridos

**Tipo:** Negativo
**Técnica:** Regla de negocio directa
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Alta
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** INT.RN6

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-029-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{TC-029-uuid_invalido}}"]
body: "Hello [[1]]"
body_var: ["{{TC-029-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
`{{TC-029-uuid_invalido}}` no cumple el patrón `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`.

**Act:**
`POST` con ese valor dentro de `apps`.

**Assert:**

1. [Respuesta] status `400`; `errors: { apps: "App IDs must be valid UUIDs" }` (ejemplo literal tomado de `create_info.md`; PEND-01 resuelto: esta forma de diccionario y la forma `{field,msg}` del requerimiento son ambas válidas — lo que se verifica es código, campo `apps` y mensaje).
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{TC-029-uuid_invalido}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-029-nombre_plantilla}}`, `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{TC-029-uuid_invalido}}` y `comment = Se creó la plantilla {{TC-029-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).


### Notas de automatización

Ninguna dependencia externa.

**Justificación de Ejecución:** Automática: validación de patrón determinística.

---

## TC-030 - `body_var[i]` compuesto solo por espacios en blanco - Set 3 - Reglas de negocio: Body y variables

**Tipo:** Negativo
**Técnica:** Tabla de decisión (DT2)
**Rol:** Admin
**Impacto:** Medio
**Probabilidad:** Media
**Prioridad:** Media
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** CA11, F3.RN5

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-030-nombre_plantilla}}
category: MARKETING
lang: en_MX
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hola [[1]]"
body_var: ["   "]
```

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida.

**Act:**
`POST` con `body_var = ["   "]` (tres espacios en blanco).

**Assert:**

1. [Respuesta] status `400`; `msg` indica incumplimiento de la longitud mínima de 1 carácter.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-030-nombre_plantilla}}`, `languageCode = en_MX`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-030-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).


### Notas de automatización

Valores literales tomados directamente del CA11 del requerimiento.

**Justificación de Ejecución:** Automática: validación de longitud tras `trim()`, determinística.

---

## TC-031 - `body_var[i]` con espacios laterales pero contenido válido - Set 3 - Reglas de negocio: Body y variables

**Tipo:** Positivo
**Técnica:** Tabla de decisión (DT2)
**Rol:** Admin
**Impacto:** Medio
**Probabilidad:** Baja
**Prioridad:** Media
**Criticidad:** Menor
**Corte-medio-tiempo:** Sí
**Ejecución:** Automática
**Requerimiento validado:** CA12, F3.RN5

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-031-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hola [[1]]"
body_var: [" Ana "]
```

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida.

**Act:**
`POST` con `body_var = [" Ana "]`.

**Assert:**

1. [Respuesta] status `200`.
2. [Respuesta] el valor de ejemplo enviado a Gupshup conserva los espacios originales (`" Ana "`), visible en `template.data`/`metaTemplate.sampleText` si el entorno lo expone.
3. [Base de datos] existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-031-nombre_plantilla}}`, `languageCode = en_US`, `data = "Hola [[1]]"` (ubicado dentro del campo `meta`), `sampleText = "Hola [Ana]" ` (ubicado dentro del campo `meta`).
4. [API log Chatwot] tras la creación exitosa de la plantilla (status 2XX), el primer registro de los logs asociado a `app_id = {{GLB-app_id_activo_1}}` debe contener `auditable_type = "Template"`, `source = "admin_chat"`, `associated_id = {{GLB-account_id_sesion}}`, `comment = Se creó la plantilla {{TC-031-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Si el entorno no expone el valor exacto de ejemplo enviado a Gupshup en la respuesta, este caso pasa a requerir inspección adicional (log de la llamada saliente).

**Justificación de Ejecución:** Automática: aserción principal (status 200) verificable en respuesta; la verificación de preservación de espacios puede requerir inspección de logs salientes si no está en la respuesta.

---

## TC-032 - `body` con 11 variables excede el máximo permitido - Set 3 - Reglas de negocio: Body y variables

**Tipo:** Negativo
**Técnica:** Tabla de decisión (DT2)
**Rol:** Admin
**Impacto:** Medio
**Probabilidad:** Media
**Prioridad:** Media
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** F3.RN3

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-032-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "[[1]] [[2]] [[3]] [[4]] [[5]] [[6]] [[7]] [[8]] [[9]] [[10]] [[11]]"
body_var: ["1","2","3","4","5","6","7","8","9","10","11"]
```

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida.

**Act:**
`POST` con `body` conteniendo 11 variables secuenciales.

**Assert:**

1. [Respuesta] status `400`; `msg: "Body cannot have more than 10 variables"`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-032-nombre_plantilla}}`, `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-032-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).


### Notas de automatización

El contenido de `body_var` es literal simple (dígitos como marcador posicional), ya que el valor en sí es irrelevante para esta regla.

**Justificación de Ejecución:** Automática: validación de conteo determinística.

---

## TC-033 - `body` ausente en categoría que lo requiere (MARKETING) - Set 3 - Reglas de negocio: Body y variables

**Tipo:** Negativo
**Técnica:** Regla de negocio directa
**Rol:** Admin
**Impacto:** Alto
**Probabilidad:** Media
**Prioridad:** Media
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** F3.RN1

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-033-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
```

(Sin `body`.)

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida.

**Act:**
`POST` con `category = MARKETING` sin enviar `body`.

**Assert:**

1. [Respuesta] status `400`; `msg: "body is required unless category is AUTHENTICATION"`, `field: body`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-033-nombre_plantilla}}`, `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-033-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Ninguna dependencia externa.

**Justificación de Ejecución:** Automática: validación de campo requerido condicional, determinística.

---

## TC-034 - Botones intercalados (no agrupados por tipo) - Set 4 - Reglas de negocio: Footer y Botones

**Tipo:** Negativo
**Técnica:** Tabla de decisión (DT3)
**Rol:** Admin
**Impacto:** Medio
**Probabilidad:** Media
**Prioridad:** Media
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** CA21, F5.RN3

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-034-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-034-body_var_ejemplo}}"]
buttons: [{{TC-034-boton_quick_reply_valido}}, {{TC-034-boton_url_valido}}, {{TC-034-boton_quick_reply_valido}}]
```

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida.

**Act:**
`POST` con `buttons = [QUICK_REPLY, URL, QUICK_REPLY]` (tipos intercalados, patrón literal del CA21).

**Assert:**

1. [Respuesta] status `400`; `msg: "Buttons must be grouped by type, not interleaved"`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-034-nombre_plantilla}}`, `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-034-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

El contenido de `title`/`payload` de cada botón es irrelevante para esta regla; solo importa la secuencia de `type`.

**Justificación de Ejecución:** Automática: validación de secuencia determinística.

---

## TC-035 - 11 botones `QUICK_REPLY` - Set 4 - Reglas de negocio: Footer y Botones

**Tipo:** Negativo
**Técnica:** Tabla de decisión (DT3)
**Rol:** Admin
**Impacto:** Medio
**Probabilidad:** Media
**Prioridad:** Media
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** CA22, F5.RN4

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-035-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-035-body_var_ejemplo}}"]
buttons: [{{TC-035-boton_quick_reply_valido}} x 11]
```

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida.

**Act:**
`POST` con 11 botones, todos `QUICK_REPLY`.

**Assert:**

1. [Respuesta] status `400`; `msg: "Maximum 10 QUICK_REPLY buttons allowed"`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-035-nombre_plantilla}}`, `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-035-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).


### Notas de automatización

Generar los 11 objetos botón reutilizando la misma plantilla de datos `{{TC-035-boton_quick_reply_valido}}`.

**Justificación de Ejecución:** Automática: validación de conteo determinística.

---

## TC-036 - `footer` contiene una variable (prohibido) - Set 4 - Reglas de negocio: Footer y Botones

**Tipo:** Negativo
**Técnica:** Regla de negocio directa
**Rol:** Admin
**Impacto:** Bajo
**Probabilidad:** Baja
**Prioridad:** Media
**Criticidad:** Menor
**Corte-medio-tiempo:** Sí
**Ejecución:** Automática
**Requerimiento validado:** F4.RN1

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-036-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-036-body_var_ejemplo}}"]
footer: {{TC-036-footer_con_variable}}
```

### Caso de prueba (AAA)

**Arrange:**
`{{TC-036-footer_con_variable}}` contiene el patrón `[[1]]`.

**Act:**
`POST` con ese `footer`.

**Assert:**

1. [Respuesta] status `400`; el error reporta el campo `footer` (representado como `footer` o `footer.value` según la conversión de campos del form-data — ambas formas son válidas, ver PEND-01 resuelto en `analisis-y-diseno.md`) con el mensaje exacto `"Must match pattern: ^(?!.*\{\{\d+\}\}).*$"` (mensaje de incumplimiento de regex — PEND-03 resuelto en `analisis-y-diseno.md`; el fragmento `\{\{\d+\}\}` es un literal de la librería de validación del servidor, distinto de la sintaxis de variable de datos de prueba de este proyecto, con la que no debe confundirse).
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-036-nombre_plantilla}}`, `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-036-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).


### Notas de automatización

La aserción automatizada debe verificar `status 400`, el campo fallido `footer`/`footer.value`, y el texto exacto del mensaje `"Must match pattern: ^(?!.*\{\{\d+\}\}).*$"`.

**Justificación de Ejecución:** Automática: código, campo y mensaje son ahora completamente determinísticos (PEND-03 resuelto).

---

## TC-037 - Pairwise: UTILITY + DOCUMENT + 1 app + botón URL - Set 7 - Pairwise

**Tipo:** Positivo
**Técnica:** Pairwise
**Rol:** Admin
**Impacto:** Medio
**Probabilidad:** Media
**Prioridad:** Media
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** F2.RN4, F5.RN2

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-037-nombre_plantilla}}
category: UTILITY
lang: en_US
type: DOCUMENT
file: {{TC-037-file_documento_pdf}}
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-037-body_var_ejemplo}}"]
buttons: [{{TC-037-boton_url_valido}}]
```

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida; `{{TC-037-file_documento_pdf}}` es un PDF válido.

**Act:**
`POST` con la combinación anterior.

**Assert:**

1. [Respuesta] status `200`, plantilla creada con encabezado tipo documento y un botón `URL`.
2. [Base de datos] existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-037-nombre_plantilla}}`, `languageCode = en_US`, `category = UTILITY`, `templateType = DOCUMENT`, `data = "Hello [[1]]"` (ubicado dentro del campo `meta`), `sampleText = Hello [{{TC-037-body_var_ejemplo}}]` (ubicado dentro del campo `meta`), `buttons = [{{TC-037-boton_url_valido}}]` (ubicado dentro del campo `meta`), y `mediaUrl` (ubicado dentro del campo `meta`). 
3. [API log Chatwot] tras la creación exitosa de la plantilla (status 2XX), el primer registro de los logs asociado a `app_id = {{GLB-app_id_activo_1}}` debe contener `auditable_type = "Template"`, `source = "admin_chat"`, `associated_id = {{GLB-account_id_sesion}}`, `comment = Se creó la plantilla {{TC-037-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Cubre la combinación `category=UTILITY` × `header=DOCUMENT`, no ejercitada por ningún criterio de aceptación explícito.

**Justificación de Ejecución:** Automática: payload determinístico con archivo fijo.

---

## TC-038 - Pairwise: UTILITY + VIDEO + multi-app + botón QUICK_REPLY - Set 7 - Pairwise

**Tipo:** Positivo
**Técnica:** Pairwise
**Rol:** Admin
**Impacto:** Medio
**Probabilidad:** Media
**Prioridad:** Media
**Criticidad:** Mayor
**Corte-medio-tiempo:** No
**Ejecución:** Automática
**Requerimiento validado:** F2.RN4, F5.RN2

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-038-nombre_plantilla}}
category: UTILITY
lang: en_US
type: VIDEO
file: {{TC-038-file_video_mp4}}
apps: ["{{GLB-app_id_activo_1}}", "{{GLB-app_id_activo_2}}"]
body: "Hello [[1]]"
body_var: ["{{TC-038-body_var_ejemplo}}"]
buttons: [{{TC-038-boton_quick_reply_valido}}]
```

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida; `{{TC-038-file_video_mp4}}` es un MP4 válido; ambas apps activas.

**Act:**
`POST` con la combinación anterior.

**Assert:**

1. [Respuesta] status `200`, `payload` de longitud 2, ambas con encabezado tipo video y un botón `QUICK_REPLY`.
2. [Base de datos] existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-038-nombre_plantilla}}`, `languageCode = en_US`, `category = UTILITY`, `templateType = VIDEO`, `data = "Hello [[1]]"` (ubicado dentro del campo `meta`), `sampleText = Hello [{{TC-038-body_var_ejemplo}}]` (ubicado dentro del campo `meta`), `buttons = [{{TC-038-boton_quick_reply_valido}}]` (ubicado dentro del campo `meta`), y `mediaUrl` (ubicado dentro del campo `meta`).
2. [Base de datos] existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_2}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-038-nombre_plantilla}}`, `languageCode = en_US`, `category = UTILITY`, `templateType = VIDEO`, `data = "Hello [[1]]"` (ubicado dentro del campo `meta`), `sampleText = Hello [{{TC-038-body_var_ejemplo}}]` (ubicado dentro del campo `meta`), `buttons = [{{TC-038-boton_quick_reply_valido}}]` (ubicado dentro del campo `meta`).
3. [Base de datos] los registros de la app `{{GLB-app_id_activo_1}}` y de la app `{{GLB-app_id_activo_2}}` en la base de datos `oauth` en la tabla `templates_gupshup` en `mediaUrl` (ubicado dentro del campo `meta`) son idénticos (ambos apuntan al mismo recurso/blob).
4. [API log Chatwot] tras la creación exitosa de la plantilla (status 2XX), el primer registro de los logs asociado a `app_id = {{GLB-app_id_activo_1}}` debe contener `auditable_type = "Template"`, `source = "admin_chat"`, `associated_id = {{GLB-account_id_sesion}}`, `comment = Se creó la plantilla {{TC-038-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).
5. [API log Chatwot] tras la creación exitosa de la plantilla (status 2XX), el primer registro de los logs asociado a `app_id = {{GLB-app_id_activo_2}}` debe contener `auditable_type = "Template"`, `source = "admin_chat"`, `associated_id = {{GLB-account_id_sesion}}`, `comment = Se creó la plantilla {{TC-038-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Cubre `header=VIDEO` (no ejercitado por ningún CA explícito) combinado con multi-app y botones `QUICK_REPLY`.

**Justificación de Ejecución:** Automática: payload determinístico con archivo fijo.

---

## TC-039 - Pairwise: UTILITY + header TEXT + 1 app + botón PHONE_NUMBER - Set 7 - Pairwise

**Tipo:** Positivo
**Técnica:** Pairwise
**Rol:** Admin
**Impacto:** Medio
**Probabilidad:** Media
**Prioridad:** Media
**Criticidad:** Mayor
**Corte-medio-tiempo:** Sí
**Ejecución:** Automática
**Requerimiento validado:** F1.RN2, F5.RN2

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-039-nombre_plantilla}}
category: UTILITY
lang: en_MX
type: TEXT
header: {{TC-039-header_texto_valido}}
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-039-body_var_ejemplo}}"]
buttons: [{{TC-039-boton_phone_valido}}]
```

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida; `{{TC-039-header_texto_valido}}` no contiene variables (por lo que no se envía `header_var`).

**Act:**
`POST` con la combinación anterior.

**Assert:**

1. [Respuesta] status `200`, plantilla creada con encabezado de texto y un botón `PHONE_NUMBER`.
2. [Base de datos] existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-039-nombre_plantilla}}`, `languageCode = en_MX`, `category = UTILITY`, `templateType = TEXT`, `data = "Hello [[1]]"` (ubicado dentro del campo `meta`), `sampleText = Hello [{{TC-039-body_var_ejemplo}}]` (ubicado dentro del campo `meta`), `buttons = [{TC-039-boton_phone_valido}}]` (ubicado dentro del campo `meta`), `header = "{{TC-039-header_texto_valido}}"` (ubicado dentro del campo `meta`), `sampleHeader = "{{TC-039-header_texto_valido}}"` (ubicado dentro del campo `meta`).
3. [API log Chatwot] tras la creación exitosa de la plantilla (status 2XX), el primer registro de los logs asociado a `app_id = {{GLB-app_id_activo_1}}` debe contener `auditable_type = "Template"`, `source = "admin_chat"`, `associated_id = {{GLB-account_id_sesion}}`, `comment = Se creó la plantilla {{TC-039-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Es el único happy path de la matriz que ejercita un encabezado `TEXT` válido; complementa los negativos de Set 2 (que solo cubren fallos de esta regla).

**Justificación de Ejecución:** Automática: payload determinístico sin archivo.

---

## TC-040 - Pairwise: AUTHENTICATION multi-app - Set 7 - Pairwise

**Tipo:** Positivo
**Técnica:** Pairwise
**Rol:** Super admin
**Impacto:** Medio
**Probabilidad:** Media
**Prioridad:** Media
**Criticidad:** Mayor
**Corte-medio-tiempo:** Sí
**Ejecución:** Automática
**Requerimiento validado:** F6.RN2, F7.RN1

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-040-nombre_plantilla}}
category: AUTHENTICATION
lang: en_US
security: "false"
apps: ["{{GLB-app_id_activo_1}}", "{{GLB-app_id_activo_2}}"]
```

### Caso de prueba (AAA)

**Arrange:**
Sesión Super admin válida; ambas apps activas.

**Act:**
`POST` con `category = AUTHENTICATION`, `security = "false"` (sin `expiration`), para 2 apps.

**Assert:**

1. [Respuesta] status `200`, `payload` de longitud 2, ninguna incluye el mensaje de recomendación de seguridad (por `security = false`).
2. [Base de datos] existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-040-nombre_plantilla}}`, `languageCode = en_US`, `category = AUTHENTICATION`, `addSecurityRecommendation = false`(ubicado dentro del campo `meta`).
3. [Base de datos] existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_2}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-040-nombre_plantilla}}`, `languageCode = en_US`, `category = AUTHENTICATION`, `addSecurityRecommendation = false`(ubicado dentro del campo `meta`).
4. [API log Chatwot] tras la creación exitosa de la plantilla (status 2XX), el primer registro de los logs asociado a `app_id = {{GLB-app_id_activo_1}}` debe contener `auditable_type = "Template"`, `source = "admin_chat"`, `associated_id = {{GLB-account_id_sesion}}`, `comment = Se creó la plantilla {{TC-040-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).
5. [API log Chatwot] tras la creación exitosa de la plantilla (status 2XX), el primer registro de los logs asociado a `app_id = {{GLB-app_id_activo_2}}` debe contener `auditable_type = "Template"`, `source = "admin_chat"`, `associated_id = {{GLB-account_id_sesion}}`, `comment = Se creó la plantilla {{TC-040-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Complementa CA03 (que usa `security = true` y 1 sola app) verificando la combinación `security = false` sin `expiration`, en escenario multi-app.

**Justificación de Ejecución:** Automática: payload determinístico sin archivo.

---

## TC-041 - Borde: `name` de 180 caracteres (excede el máximo) - Set 9 - Casos de borde y valores límite

**Tipo:** Borde
**Técnica:** Borde
**Rol:** Admin
**Impacto:** Medio
**Probabilidad:** Media
**Prioridad:** Media
**Criticidad:** Mayor
**Corte-medio-tiempo:** Sí
**Ejecución:** Automática
**Requerimiento validado:** INT.RN4

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-041-nombre_180_caracteres}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-041-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
`{{TC-041-nombre_180_caracteres}}` mide exactamente 180 caracteres válidos (`[a-z0-9_]`), uno por encima del máximo de 179 definido por la regla `^[a-z0-9_]{3,179}$`.

**Act:**
`POST` con ese `name`.

**Assert:**

1. [Respuesta] status `400`; `msg: "Must match pattern: ^[a-z0-9_]{3,179}$"`, `field: name`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-041-nombre_180_caracteres}}`, `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-041-nombre_180_caracteres}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

El valor de 180 caracteres es un borde literal derivado de la regla explícita (3-179); solo el contenido exacto de la cadena es variable.

**Justificación de Ejecución:** Automática: validación de longitud determinística.

---

## TC-042 - Borde: `header` con dos variables (excede el máximo de una) - Set 9 - Casos de borde y valores límite

**Tipo:** Borde
**Técnica:** Borde
**Rol:** Admin
**Impacto:** Medio
**Probabilidad:** Media
**Prioridad:** Media
**Criticidad:** Mayor
**Corte-medio-tiempo:** Sí
**Ejecución:** Automática
**Requerimiento validado:** F1.RN2

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-042-nombre_plantilla}}
category: MARKETING
lang: en_MX
type: TEXT
header: {{TC-042-header_dos_variables}}
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-042-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
`{{TC-042-header_dos_variables}}` contiene dos ocurrencias de variable (ej. `[[1]]` y `[[2]]`), por encima del máximo de una permitida.

**Act:**
`POST` con ese `header`, sin `header_var` (para aislar el error de conteo de variables).

**Assert:**

1. [Respuesta] status `400`; `msg: "Header can only contain one variable"`, `field: header`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-042-nombre_plantilla}}`, `languageCode = en_MX`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-042-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).


### Notas de automatización

El número de variables (2, borde sobre el máximo de 1) es literal; el texto exacto del header es variable.

**Justificación de Ejecución:** Automática: validación de conteo determinística.

---

## TC-043 - Borde: `footer` de 61 caracteres (excede el máximo) - Set 9 - Casos de borde y valores límite

**Tipo:** Borde
**Técnica:** Borde
**Rol:** Admin
**Impacto:** Medio
**Probabilidad:** Media
**Prioridad:** Media
**Criticidad:** Mayor
**Corte-medio-tiempo:** Sí
**Ejecución:** Automática
**Requerimiento validado:** F4.RN1

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-043-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-043-body_var_ejemplo}}"]
footer: {{TC-043-footer_61_caracteres}}
```

### Caso de prueba (AAA)

**Arrange:**
`{{TC-043-footer_61_caracteres}}` mide exactamente 61 caracteres, uno por encima del máximo de 60.

**Act:**
`POST` con ese `footer`.

**Assert:**

1. [Respuesta] status `400`; `msg: "Must be at most 60 characters"`, `field: footer`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-043-nombre_plantilla}}`, `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-043-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

El largo de 61 caracteres es un borde literal derivado de la regla explícita (1-60); el contenido exacto es variable.

**Justificación de Ejecución:** Automática: validación de longitud determinística.

---

## TC-044 - Borde: `account_id` sobre el máximo permitido (2147483649) - Set 9 - Casos de borde y valores límite

**Tipo:** Borde
**Técnica:** Borde
**Rol:** Admin
**Impacto:** Medio
**Probabilidad:** Media
**Prioridad:** Media
**Criticidad:** Mayor
**Corte-medio-tiempo:** Sí
**Ejecución:** Manual
**Requerimiento validado:** INT.RN4

### Datos de prueba

```
account_id: 2147483649
name: {{TC-044-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-044-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
Se dispone de `{{TC-044-token_account_id_limite}}`, un JWT de prueba crafteado cuyo `account_id` de sesión también es `2147483649` (mismo valor que el body), para que el chequeo de coincidencia de sesión (paso 1) no interfiera y la petición llegue a la validación de esquema.

**Act:**
`POST` con `account_id = 2147483649` y header `api-access-token: {{TC-044-token_account_id_limite}}`.

**Assert:**

1. [Respuesta] status `400`; `msg: "Must be <= 2147483648"`, `field: account_id`.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = 2147483649` con `template_code_name = {{TC-044-nombre_plantilla}}`, `languageCode = en_US`.
3. [API log Chatwot] no se genera un registro reciente en el log de la creación del template asociado a `app_id = {{GLB-app_id_activo_1}}` y `comment = Se creó la plantilla {{TC-044-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).


### Notas de automatización

`2147483649` es un valor de borde literal derivado de la regla explícita (máximo 2147483648). Requiere capacidad de emitir un JWT de prueba con `account_id` arbitrario en sus claims, lo cual normalmente excede las herramientas estándar de un framework de automatización de API y requiere colaboración del equipo de backend/QA para generar el token de prueba.

**Justificación de Ejecución:** Manual: depende de la emisión de un JWT de prueba con un claim de `account_id` fuera de rango, una capacidad de setup no estándar.

---

## TC-045 - Campo adicional no contemplado es ignorado (Mass Assignment) - Set 10 - Seguridad

**Tipo:** Seguridad
**Técnica:** Seguridad-OWASP (Mass Assignment / API3:2023 Broken Object Property Level Authorization)
**Rol:** Admin
**Impacto:** Medio
**Probabilidad:** Baja
**Prioridad:** Media
**Criticidad:** Menor
**Corte-medio-tiempo:** Sí
**Ejecución:** Automática
**Requerimiento validado:** INT.RN10

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-045-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-045-body_var_ejemplo}}"]
{{TC-045-campo_no_contemplado}}: "{{TC-045-valor_no_contemplado}}"
```

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida.

**Act:**
`POST` con un campo adicional (`{{TC-045-campo_no_contemplado}}`) que no forma parte del esquema documentado.

**Assert:**

1. [Respuesta] status `200`, idéntico a un happy path estándar, sin importar el campo extra.
2. [Base de datos] no existe un registro local en la base de datos `oauth` en la tabla `templates_gupshup` de la nueva plantilla asociado a `app_id = {{GLB-app_id_activo_1}}` y a `account_id = {{GLB-account_id_sesion}}` con `template_code_name = {{TC-045-nombre_plantilla}}`, `languageCode = en_US`.
3. [Base de datos] el campo extra no `{{TC-045-campo_no_contemplado}} = {{TC-045-valor_no_contemplado}}` persiste en ningún atributo de la plantilla creada.
4. [API log Chatwot] tras la creación exitosa de la plantilla (status 2XX), el primer registro de los logs asociado a `app_id = {{GLB-app_id_activo_1}}` debe contener `auditable_type = "Template"`, `source = "admin_chat"`, `associated_id = {{GLB-account_id_sesion}}`, `comment = Se creó la plantilla {{TC-045-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Probar con un nombre de campo que, de ser procesado indebidamente, representaría un riesgo (por ejemplo, un campo que sugiera escalar privilegios o alterar `account_id`), para verificar que el filtrado de campos desconocidos es real y no una omisión accidental de la documentación.

**Justificación de Ejecución:** Automática: comparación de respuesta y estado en BD, sin intervención manual.

---

## TC-046 - Creación exitosa pero falla el fetch del inbox - Set 11 - Log de auditoría

**Tipo:** Borde
**Técnica:** Prueba sugerida (obligatoria por CA)
**Rol:** Admin
**Impacto:** Medio
**Probabilidad:** Baja
**Prioridad:** Baja
**Criticidad:** Menor
**Corte-medio-tiempo:** Sí
**Ejecución:** Manual
**Requerimiento validado:** CA24, LOG.RN13, LOG.RN15

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-046-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-046-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
La plantilla se crea exitosamente en Gupshup (HTTP 2xx del endpoint principal). La petición interna de información del inbox está configurada (mock) para retornar timeout.

**Act:**
`POST` con el `form-data` anterior.

**Assert:**

1. [Log] al fallar el log de la creación del template se escribe en `pino` el literal `"failed to fetch inbox info, won't send audit log"` seguido del detalle del fallo.
2. [Respuesta] la respuesta HTTP 200/206 al cliente se preserva sin alteración. 

### Notas de automatización

Requiere mockear la consulta interna de información del inbox para forzar timeout, e inspeccionar el archivo `pino` (o un sink equivalente en el entorno de pruebas) para confirmar el literal exacto.

**Justificación de Ejecución:** Manual: requiere inspección del archivo de log interno `pino`, no expuesto en la respuesta de la API.

---

## TC-047 - Creación exitosa pero falla el `POST` al endpoint de logs - Set 11 - Log de auditoría

**Tipo:** Borde
**Técnica:** Prueba sugerida (obligatoria por CA)
**Rol:** Admin
**Impacto:** Medio
**Probabilidad:** Baja
**Prioridad:** Baja
**Criticidad:** Menor
**Corte-medio-tiempo:** Sí
**Ejecución:** Manual
**Requerimiento validado:** CA25, LOG.RN14, LOG.RN15

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-047-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-047-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
La plantilla se crea exitosamente y el fetch del inbox retorna `200` con el nombre. El `POST` al endpoint de logs de Chat está configurado (mock) para retornar HTTP 500.

**Act:**
`POST` con el `form-data` anterior.

**Assert:**

1. [Log] al fallar el log de la creación del template se escribe en `pino` el literal `"failed to create audit log"` seguido del detalle del fallo.
2. [Respuesta] la respuesta HTTP 200/206 al cliente se preserva sin alteración.

### Notas de automatización

Requiere mockear el endpoint de creación de logs de Chat para forzar un 500, e inspeccionar `pino`.

**Justificación de Ejecución:** Manual: requiere inspección del archivo `pino` y control del endpoint interno de logs.

---

## TC-048 - Verificación de campos y formato del log de auditoría en creación exitosa - Set 11 - Log de auditoría

**Tipo:** Positivo
**Técnica:** Prueba sugerida (obligatoria, complementaria a TC-001)
**Rol:** Admin
**Impacto:** Bajo
**Probabilidad:** Baja
**Prioridad:** Baja
**Criticidad:** Menor
**Corte-medio-tiempo:** Sí
**Ejecución:** Manual
**Requerimiento validado:** LOG.RN1, LOG.RN2, LOG.RN3, LOG.RN4, LOG.RN6, LOG.RN7, LOG.RN8, LOG.RN9, LOG.RN10, LOG.RN11, LOG.RN12

### Datos de prueba

```
account_id: {{GLB-account_id_sesion}}
name: {{TC-048-nombre_plantilla}}
category: MARKETING
lang: en_US
apps: ["{{GLB-app_id_activo_1}}"]
body: "Hello [[1]]"
body_var: ["{{TC-048-body_var_ejemplo}}"]
```

### Caso de prueba (AAA)

**Arrange:**
Sesión Admin válida con `{{GLB-token_admin}}`; `{{GLB-token_chat}}` disponible desde la sesión decodificada.

**Act:**
`POST` con el `form-data` anterior, resultando en creación exitosa.

**Assert:**

1. 1. [Respuesta] status `200`.
2. [API log Chatwot] tras la creación exitosa de la plantilla (status 2XX), el primer registro de los logs asociado a `app_id = {{GLB-app_id_activo_1}}` debe contener `auditable_type = "Template"`, `source = "admin_chat"`, `associated_id = {{GLB-account_id_sesion}}`, `comment = Se creó la plantilla {{TC-048-nombre_plantilla}} (#{template_id}) del inbox {inbox_name} (#{inbox_id})`(con los valores reales sustituidos).

### Notas de automatización

Requiere acceso al panel de auditoría de Chat o consulta directa a la tabla `Audits`, y capacidad de inspeccionar las cabeceras de las llamadas salientes internas (inbox info y creación de log) para confirmar qué token se usó en cada una.

**Justificación de Ejecución:** Manual: la verificación de qué token se usó en cada llamada interna y el formato exacto del `comment` requieren inspección fuera de la respuesta pública de la API.
