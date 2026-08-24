# Metodo create 

## HTTP Creación

| Método HTTP | Ruta de Testing                                                                       | Ruta                                                | Función        | Header de Validación |
| ----------- | ------------------------------------------------------------------------------------- | --------------------------------------------------- | -------------- | -------------------- |
| POST        | https://api.chatdev.callpicker.com/integrations/gupshup_integrations/templates/create | /integrations/gupshup_integrations/templates/create | createTemplate | api-access-token     |
## Posibles Respuestas Creación

| Código HTTP | Cuándo ocurre                                                                                                                       | Estructura de Respuesta                                                         |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| 400         | Cuando falla la validación inicial de campos (campos faltantes, formatos incorrectos, etc.) y no se intenta crear ninguna plantilla | { code: 400, errors: { field: error } }                                         |
| 200         | Cuando la plantilla pudo ser creada para todas las apps de Gupshup enlistadas                                                       | { code: 200, payload: [...] }                                                   |
| 206         | Cuando la plantilla pudo ser creada para algunas apps de Gupshup enlistadas, mientras que otras tuvieron errores                    | { code: 206, success: [...], errors: [...] }                                    |
| 400         | Cuando no fue posible crear ninguna plantilla en ninguna app de Gupshup                                                             | { code: 400, errors: [...], message: 'All accounts failed' }                    |
| 401         | Falla validación de sesión<br>Account_id no coincide con account_id de información de sesión<br>No es una cuenta válida             | { code: 401, message: "Unauthorized" }                                          |
| 500         | No se pudo subir el archivo al servidor de Chat Callpicker                                                                          | { code: 500, message: 'Failed to upload file', errors: { file: upload_error } } |
## Respuesta Exitosa Success Creación

| Campo        | Tipo                      | Descripción                                          |
| ------------ | ------------------------- | ---------------------------------------------------- |
| id           | string                    | ID del template en Gupshup                           |
| name         | string                    | Nombre del template                                  |
| category     | string                    | Categoría (MARKETING, UTILITY, etc.)                 |
| template     | string                    | Contenido del mensaje                                |
| created      | number                    | Timestamp de creación                                |
| language     | string                    | Idioma del template                                  |
| status       | string                    | Estado del template (ej: PENDING)                    |
| cp_id        | string                    | ID interno de Chat                                   |
| active       | boolean                   | Estado interno de Chat                               |
| app_name     | string                    | Identificador del app donde se creó                  |
| metaTemplate | string (JSON serializado) | Información adicional del template (siguiente tabla) |

### Respuesta Exitosa metaTemplate Creación 

| Campo                     | Tipo           | Descripción                                                                          |
| ------------------------- | -------------- | ------------------------------------------------------------------------------------ |
| appId                     | string         | ID del app en Gupshup al que pertenece el template                                   |
| data                      | string         | Contenido principal del template                                                     |
| sampleText                | string         | Texto de ejemplo usado para aprobación del template                                  |
| sampleMedia               | string \| null | Referencia al media de ejemplo (si aplica). Es un identificador generado por Gupshup |
| enableSample              | boolean        | Indica si el template incluye datos de ejemplo                                       |
| editTemplate              | boolean        | Indica si el template fue creado en modo editable                                    |
| addSecurityRecommendation | boolean        | Indica si se agregó recomendación de seguridad (usado en AUTH normalmente)           |
| isCPR                     | boolean        | Información extra de Gupshup                                                         |
| cpr                       | boolean        | Información extra de Gupshup                                                         |

## Respuesta con Errores Creación

| Campo  | Tipo   | Descripción          | Mensaje de Error            | Explicación                                                                               |
| ------ | ------ | -------------------- | --------------------------- | ----------------------------------------------------------------------------------------- |
| app_id | string | ID del app que falló | —                           | Corresponde al app_id enviado en el request que no pudo procesarse                        |
| msg    | string | Motivo del error     | App not found or inactive   | El app no existe en base de datos o está deshabilitado<br>El app no pertenece a la cuenta |
| msg    | string | Motivo del error     | Could not get token         | No se pudo obtener el token necesario para autenticarse con Gupshup Partner               |
| msg    | string | Motivo del error     | Could not upload media file | Falló la subida del archivo multimedia al proveedor (solo aplica a templates con media)   |
| msg    | string | Motivo del error     | Could not create template   | Gupshup rechazó la creación del template o ocurrió un error en su API                     |

## Ejemplos de Respuesta Creación

**Éxito total, estatus 200**
```json
{
    "code": 200,
    "payload": [
        {
            "app_id": "26a51522-cb0b-4293-8d72-cd7d4d578d1d",
            "template": {
                "appId": "26a51522-cb0b-4293-8d72-cd7d4d578d1d",
                "category": "MARKETING",
                "containerMeta": "{\"appId\":\"26a51522-cb0b-4293-8d72-cd7d4d578d1d\",\"data\":\"Hello {{1}}, you have {{2}} points expiring in {{3}} days!\",\"footer\":\"Thanks for shopping with us\",\"sampleText\":\"Hello Elias, you have 500 points expiring in three days!\",\"sampleMedia\":\"4::YXBwbGljYXRpb24vcGRm:ARaI9qkT9Gnqx_ZdR_2SUq2BYKCDVXmZryyjsv9QgL3hdwFWcboaPrJ3zalmfT11MrYCcZug6DKb22BZueGhJIDEtI4a8sNwNHwGICBWRhWTgQ:e:1784673610:2281283925530161:61571973598597:ARaZ3Y-pZZ8APReZtBM\",\"enableSample\":true,\"editTemplate\":false,\"addSecurityRecommendation\":false,\"isCPR\":false,\"cpr\":false,\"mediaUrl\":\"https://chatdev4.callpicker.com/rails/active_storage/blobs/redirect/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaHBBbVN1IiwiZXhwIjpudWxsLCJwdXIiOiJibG9iX2lkIn19--05c54ff0978e8df04f23a0c289ee0d1c744ed641/application_pdf.pdf\"}",
                "createdOn": 1784328010913,
                "data": "Hello {{1}}, you have {{2}} points expiring in {{3}} days!\nThanks for shopping with us",
                "elementName": "rod_test_doc_3",
                "id": "e2de928f-55b6-4d70-a6b3-437fa0a58b73",
                "languageCode": "en",
                "languagePolicy": "deterministic",
                "meta": "{\"example\":\"Hello Elias, you have 500 points expiring in three days!\"}",
                "modifiedOn": 1784328010913,
                "namespace": "1c48e523_489f_4d5d_a7b7_852246afb902",
                "parameterFormat": "POSITIONAL",
                "priority": 1,
                "quality": "UNKNOWN",
                "retry": 0,
                "source": "gupshup",
                "stage": "NONE",
                "state": "ACTIVE",
                "status": "PENDING",
                "templateType": "DOCUMENT",
                "vertical": "Chat_Callpicker",
                "wabaId": "256016737587310"
            }
        },
        {
            "app_id": "4514e6cf-7702-4a83-b3bc-add0347ac54e",
            "template": {
                "appId": "4514e6cf-7702-4a83-b3bc-add0347ac54e",
                "category": "MARKETING",
                "containerMeta": "{\"appId\":\"4514e6cf-7702-4a83-b3bc-add0347ac54e\",\"data\":\"Hello {{1}}, you have {{2}} points expiring in {{3}} days!\",\"footer\":\"Thanks for shopping with us\",\"sampleText\":\"Hello Elias, you have 500 points expiring in three days!\",\"sampleMedia\":\"4::YXBwbGljYXRpb24vcGRm:ARY7VgH2VLfKvz3yqkLWuFK4iM8oS-RuwKZJffFqHh9Dia6LjtZ-NVSuoSJSX9pfHEnAnguQeq7Pg8T_rz-a0xSqxXtAuCJxbMdgX_Ab1KVkeA:e:1784673612:2281283925530161:61571973598597:ARZTJJBv6A0skJS7-rg\",\"enableSample\":true,\"editTemplate\":false,\"addSecurityRecommendation\":false,\"isCPR\":false,\"cpr\":false,\"mediaUrl\":\"https://chatdev4.callpicker.com/rails/active_storage/blobs/redirect/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaHBBbVN1IiwiZXhwIjpudWxsLCJwdXIiOiJibG9iX2lkIn19--05c54ff0978e8df04f23a0c289ee0d1c744ed641/application_pdf.pdf\"}",
                "createdOn": 1784328012541,
                "data": "Hello {{1}}, you have {{2}} points expiring in {{3}} days!\nThanks for shopping with us",
                "elementName": "rod_test_doc_3",
                "id": "15f2c0d6-77ce-4c8c-9091-838a2d742f2f",
                "languageCode": "en",
                "languagePolicy": "deterministic",
                "meta": "{\"example\":\"Hello Elias, you have 500 points expiring in three days!\"}",
                "modifiedOn": 1784328012541,
                "namespace": "314a845d_3252_498b_bd8b_f4a63edadce3",
                "parameterFormat": "POSITIONAL",
                "priority": 1,
                "quality": "UNKNOWN",
                "retry": 0,
                "source": "gupshup",
                "stage": "NONE",
                "state": "ACTIVE",
                "status": "PENDING",
                "templateType": "DOCUMENT",
                "vertical": "Chat_Callpicker",
                "wabaId": "244520078740526"
            }
        }
    ]
}
```
**Éxito parcial, estatus 206**
```json
{
  "code": 206,
  "success": [
    {
            "app_id": "26a51522-cb0b-4293-8d72-cd7d4d578d1d",
            "template": {
                "appId": "26a51522-cb0b-4293-8d72-cd7d4d578d1d",
                "category": "MARKETING",
                "containerMeta": "{\"appId\":\"26a51522-cb0b-4293-8d72-cd7d4d578d1d\",\"data\":\"Hello {{1}}, you have {{2}} points expiring in {{3}} days!\",\"footer\":\"Thanks for shopping with us\",\"sampleText\":\"Hello Elias, you have 500 points expiring in three days!\",\"sampleMedia\":\"4::YXBwbGljYXRpb24vcGRm:ARaI9qkT9Gnqx_ZdR_2SUq2BYKCDVXmZryyjsv9QgL3hdwFWcboaPrJ3zalmfT11MrYCcZug6DKb22BZueGhJIDEtI4a8sNwNHwGICBWRhWTgQ:e:1784673610:2281283925530161:61571973598597:ARaZ3Y-pZZ8APReZtBM\",\"enableSample\":true,\"editTemplate\":false,\"addSecurityRecommendation\":false,\"isCPR\":false,\"cpr\":false,\"mediaUrl\":\"https://chatdev4.callpicker.com/rails/active_storage/blobs/redirect/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaHBBbVN1IiwiZXhwIjpudWxsLCJwdXIiOiJibG9iX2lkIn19--05c54ff0978e8df04f23a0c289ee0d1c744ed641/application_pdf.pdf\"}",
                "createdOn": 1784328010913,
                "data": "Hello {{1}}, you have {{2}} points expiring in {{3}} days!\nThanks for shopping with us",
                "elementName": "rod_test_doc_3",
                "id": "e2de928f-55b6-4d70-a6b3-437fa0a58b73",
                "languageCode": "en",
                "languagePolicy": "deterministic",
                "meta": "{\"example\":\"Hello Elias, you have 500 points expiring in three days!\"}",
                "modifiedOn": 1784328010913,
                "namespace": "1c48e523_489f_4d5d_a7b7_852246afb902",
                "parameterFormat": "POSITIONAL",
                "priority": 1,
                "quality": "UNKNOWN",
                "retry": 0,
                "source": "gupshup",
                "stage": "NONE",
                "state": "ACTIVE",
                "status": "PENDING",
                "templateType": "DOCUMENT",
                "vertical": "Chat_Callpicker",
                "wabaId": "256016737587310"
            }
        }
  ],
  "errors": [
    {
      "app_id": "uuid-2",
      "msg": "Gupshup rejected template creation"
    }
  ]
}
```
**Fallo total, estatus 400**
```json
{
    "code": 400,
    "errors": {
        "footer.value": "Must be at least 1 characters"
    }
}
```

```json
{
    "code": 400,
    "errors": {
        "apps": "App IDs must be valid UUIDs"
    }
}
```

**Error de validación, estatus 400**
```json
{
    "code": 400,
    "errors": {
        "footer.value": "Must be at least 1 characters"
    }
}

{
    "code": 400,
    "errors": {
        "apps": "App IDs must be valid UUIDs"
    }
}
```

**Fallo total**
```json
{
  "code": 400,
  "message": "All accounts failed",
  "errors": [
    {
      "app_id": "uuid-1",
      "msg": "App not found or inactive"
    },
    {
      "app_id": "uuid-2",
      "msg": "Could not get token"
    }
  ]
}
```
## Ejemplos Payload Creación

**Sin header**
```sh
curl --location 'https://api.chatdev.callpicker.com/integrations/gupshup_integrations/templates/create' \
--form 'account_id="58"' \
--form 'name="rod_test_temp_1"' \
--form 'category="MARKETING"' \
--form 'lang="en"' \
--form 'body="Hello {{1}}, you have {{2}} points expiring in {{3}} days!"' \
--form 'body_var="[\"Elias\",\"500\",\"three\"]"' \
--form 'footer="Thanks for shopping with us"' \
--form 'apps="[\"26a51522-cb0b-4293-8d72-cd7d4d578d1d\"]"'
```
**Con header de texto con variable, cuerpo con variables, footer y botones**
```sh
curl --location 'https://api.chatdev.callpicker.com/integrations/gupshup_integrations/templates/create' \
--form 'account_id="58"' \
--form 'name="rod_test_temp_1"' \
--form 'category="MARKETING"' \
--form 'lang="en"' \
--form 'type="TEXT"' \
--form 'header="Hi {{1}}, special offer just for you!"' \
--form 'header_var="John"' \
--form 'body="Hello {{1}}, you have {{2}} points expiring in {{3}} days!"' \
--form 'body_var="[\"Elias\",\"500\",\"three\"]"' \
--form 'footer="Thanks for shopping with us"' \
--form 'apps="[\"26a51522-cb0b-4293-8d72-cd7d4d578d1d\"]"' \
--form 'buttons="[{\"type\":\"QUICK_REPLY\",\"title\":\"Yes\",\"payload\":\"YES_PAYLOAD\"},{\"type\":\"QUICK_REPLY\",\"title\":\"No\",\"payload\":\"NO_PAYLOAD\"},{\"type\":\"URL\",\"title\":\"Visit Site\",\"payload\":\"https://example.com\"},{\"type\":\"URL\",\"title\":\"Shop Now\",\"payload\":\"https://example.com/shop\"},{\"type\":\"PHONE_NUMBER\",\"title\":\"Call Us\",\"payload\":\"5511987654321\"}]"'
```
**Con header de documento**
```sh
curl --location 'https://api.chatdev.callpicker.com/integrations/gupshup_integrations/templates/create' \
--form 'account_id="58"' \
--form 'name="rod_test_doc_2"' \
--form 'category="MARKETING"' \
--form 'lang="en"' \
--form 'type="DOCUMENT"' \
--form 'body="Hello {{1}}, you have {{2}} points expiring in {{3}} days!"' \
--form 'body_var="[\"Elias\",\"500\",\"three\"]"' \
--form 'footer="Thanks for shopping with us"' \
--form 'apps="[\"26a51522-cb0b-4293-8d72-cd7d4d578d1d\",\"4514e6cf-7702-4a83-b3bc-add0347ac54e\"]"' \
--form 'file=@"/ruta/a/tu/archivo.pdf";type=application/pdf'
```
**Autenticación OTP**
```sh
curl --location 'https://api.chatdev.callpicker.com/integrations/gupshup_integrations/templates/create' \
--form 'account_id="58"' \
--form 'name="rod_test_auth_jul_9"' \
--form 'category="AUTHENTICATION"' \
--form 'lang="en"' \
--form 'apps="[\"26a51522-cb0b-4293-8d72-cd7d4d578d1d\"]"' \
--form 'security="true"' \
--form 'expiration="10"'
```
> **Nota:** No utilizar estos valores para generar casos de prueba solo son ejemplos de uso

## Validaciones de Entrada Creación

| Campo                        | ¿Requerido? | Cuándo aplica                                 | Validaciones                                                                                                                                                                                                                                                                                                                                                      | Regex                                                                                                                                                 | Mensajes de Error                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ---------------------------- | ----------- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Campos principales           |             |                                               |                                                                                                                                                                                                                                                                                                                                                                   |                                                                                                                                                       |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| account_id                   | Sí          | Siempre                                       | Número entero entre 1 y 2147483648<br>Debe ser una cuenta existente<br>Debe corresponder a la sesión                                                                                                                                                                                                                                                              | ^[1-9]\\d\*$                                                                                                                                          | Required<br>Must be of type: integer<br>Must be >= 1<br>Must be <= 2147483648                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| name                         | Sí          | Siempre                                       | Solo minúsculas, dígitos y guion bajo.<br>Entre 3 y 179 caracteres                                                                                                                                                                                                                                                                                                | ^[a-z0-9_]{3,179}$                                                                                                                                    | Required<br>Must be of type: string<br>Must match pattern: ^[a-z0-9_]{3,179}$                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| category                     | Sí          | Siempre                                       | Debe ser uno de: MARKETING, UTILITY o AUTHENTICATION                                                                                                                                                                                                                                                                                                              | ^(MARKETING\|UTILITY\|AUTHENTICATION)$                                                                                                                | Required<br>Must be of type: string<br>Must be one of: MARKETING, UTILITY, AUTHENTICATION                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| lang                         | Sí          | Siempre                                       | Debe ser "en_US" o "es_MX"                                                                                                                                                                                                                                                                                                                                        | ^(en_US\|es_MX)$                                                                                                                                      | Required<br>Must be of type: string<br>Must be one of: en_US, es_MX                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| apps                         | Sí          | Siempre                                       | Arreglo no vacío de UUIDs válidos                                                                                                                                                                                                                                                                                                                                 | ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$<br>(case-insensitive)<br>(por elemento)                                                | Required<br>Must be of type: string<br>Must be at least 2 characters<br>Must be a valid JSON array of app IDs<br>At least one app ID is required<br>App IDs must be valid UUIDs                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Header                       |             |                                               |                                                                                                                                                                                                                                                                                                                                                                   |                                                                                                                                                       |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| type                         | No          | Opcional; define reglas de archivo/encabezado | Si está presente, debe ser uno de: TEXT, DOCUMENT, IMAGE o VIDEO                                                                                                                                                                                                                                                                                                  | ^(TEXT\|DOCUMENT\|IMAGE\|VIDEO)$                                                                                                                      | Required<br>Must be of type: string<br>Must be one of: TEXT, DOCUMENT, IMAGE, VIDEO<br>Not allowed for AUTHENTICATION templates                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| file                         | Condicional | type es DOCUMENT, IMAGE o VIDEO               | Prohibido si type es TEXT o está ausente.<br>Requerido si type es DOCUMENT/IMAGE/VIDEO.<br>DOCUMENT → PDF ≤100MB,<br>IMAGE → JPEG/PNG ≤5MB,<br>VIDEO → MP4 ≤16MB                                                                                                                                                                                                  |                                                                                                                                                       | Not allowed for AUTHENTICATION templates<br>File is only allowed when type is IMAGE, VIDEO or DOCUMENT<br>File is required when type is IMAGE, VIDEO or DOCUMENT<br>Invalid file type for DOCUMENT. Allowed: application/pdf<br>Invalid file type for IMAGE. Allowed: image/jpeg, image/png<br>Invalid file type for VIDEO. Allowed: video/mp4<br>File too large for DOCUMENT. Max allowed is 100MB<br>File too large for IMAGE. Max allowed is 5MB<br>File too large for VIDEO. Max allowed is 16MB<br>File too large. Maximum allowed size is 100MB                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| header                       | Condicional | type es TEXT                                  | Requerido cuando type es TEXT (prohibido para otros types).<br>Entre 1 y 60 caracteres.<br>Sin saltos de línea ni 4+ espacios consecutivos.<br>Puede contener como máximo una única variable                                                                                                                                                                      | ^(?=.{1,60}$)(?!.\*\\n)(?!.\* {4}).\*$                                                                                                                | Must be of type: string<br>Must be at least 1 characters<br>Must be at most 60 characters<br>Must match pattern: ^(?!.\*\\\\n)(?!.\*[ ]{4}).\*$<br>Not allowed for AUTHENTICATION templates<br>Header and header_var are only allowed when type is TEXT<br>Header is required when type is TEXT<br>Header can only contain one variable                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| header_var                   | Condicional | header está presente y contiene una variable  | Requerido si header contiene una variable; prohibido si no la contiene.<br>Prohibido si type no es TEXT.<br>Entre 1 y 60 caracteres.<br>Sin saltos de línea ni 4+ espacios consecutivos                                                                                                                                                                           | ^(?=.{1,60}$)(?!.\*\\n)(?!.\* {4}).\*$                                                                                                                | Must be of type: string<br>Must be at least 1 characters<br>Must be at most 60 characters<br>Must match pattern: ^(?!.\*\\\\n)(?!.\*[ ]{4}).\*$<br>Not allowed for AUTHENTICATION templates<br>Header_var is required when header contains a variable<br>Header_var is only allowed if header contains a variable                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Cuerpo                       |             |                                               |                                                                                                                                                                                                                                                                                                                                                                   |                                                                                                                                                       |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| body                         | Condicional | category no es AUTHENTICATION                 | Requerido salvo que category sea AUTHENTICATION.<br>Hasta 1024 caracteres.<br>Hasta 10 variables, deben aparecer en secuencia exacta 1..N sin huecos, repeticiones ni desorden.<br>La cantidad debe coincidir con body_var                                                                                                                                        | ^.{1,1024}$                                                                                                                                           | Must be of type: string<br>Must be at most 1024 characters<br>Not allowed for AUTHENTICATION templates<br>body is required unless category is AUTHENTICATION<br>Body cannot have more than 10 variables<br>Body variables must appear in order starting from {{1}} with no gaps or repeats                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| body_var                     | Condicional | body contiene una o más variables             | Requerido si body contiene variables; prohibido si no.<br>Arreglo cuya longitud debe coincidir exactamente con la cantidad de variables en body.<br>Cada valor: entre 1 y 1024 caracteres, sin saltos de línea ni 4+ espacios consecutivos                                                                                                                        | ^(?=.{1,1024}$)(?!.\*\\n)(?!.\* {4}).\*$<br>(por elemento)                                                                                            | Must be of type: string<br>Must be at least 2 characters<br>Not allowed for AUTHENTICATION templates<br>Body_var is required when body contains variables<br>Body_var is only allowed if body contains variables<br>Body_var must be valid JSON array<br>Body_var must have exactly N item(s) to match body variables<br>Each body_var item must be 1-1024 characters, with no newlines or 4+ consecutive spaces                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Footer                       |             | Footer                                        |                                                                                                                                                                                                                                                                                                                                                                   |                                                                                                                                                       |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| footer                       | No          | category no es AUTHENTICATION                 | Opcional.<br>Debe ser entre 1 y 60 caracteres.<br>No se permiten variables.                                                                                                                                                                                                                                                                                       | ^(?=.{1,60}$)(?!.\*\\{\\{\\d+\\}\\}).\*$                                                                                                              | Must be of type: string<br>Must be at least 1 characters<br>Must be at most 60 characters<br>Not allowed for AUTHENTICATION templates                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| Campos solo de autenticación |             |                                               |                                                                                                                                                                                                                                                                                                                                                                   |                                                                                                                                                       |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| security                     | Condicional | category es AUTHENTICATION                    | Requerido cuando category es AUTHENTICATION; prohibido para otros types.<br>Debe ser true, false, 1 o 0                                                                                                                                                                                                                                                           | ^(true\|false\|1\|0)$                                                                                                                                 | Must be of type: string<br>Must be one of: true, false, 1, 0<br>Security is only allowed for AUTHENTICATION templates<br>Security is required for AUTHENTICATION templates                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| expiration                   | No          | category es AUTHENTICATION                    | Opcional.<br>Entero entre 1 y 90.<br>Prohibido para otros types que no sean AUTHENTICATION                                                                                                                                                                                                                                                                        | ^[1-9]\\d\*$                                                                                                                                          | Must be of type: integer<br>Must be >= 1<br>Must be <= 90<br>Expiration is only allowed for AUTHENTICATION templates                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Botones                      |             |                                               |                                                                                                                                                                                                                                                                                                                                                                   |                                                                                                                                                       |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| buttons                      | No          | category no es AUTHENTICATION                 | Arreglo no vacío.<br>Máximo 10 botones en total (todos los tipos combinados).<br>Botones del mismo tipo deben estar agrupados entre sí.<br>Máximo 10 QUICK_REPLY, 2 URL, 1 PHONE_NUMBER.<br>Prohibido si category es AUTHENTICATION                                                                                                                               |                                                                                                                                                       | Must be of type: string<br>Must be at least 2 characters<br>Not allowed for AUTHENTICATION templates<br>Buttons must be valid JSON array<br>Buttons must be a non-empty array<br>Maximum 10 buttons allowed in total<br>Each button must be an object<br>Each button type must be one of: QUICK_REPLY, URL, PHONE_NUMBER<br>Each button title must be 1-25 characters, non-empty, with no newlines, carriage returns, or tabs<br>Each button payload must be a non-empty string<br>QUICK_REPLY payload must be 1-25 characters, non-empty, with no newlines, carriage returns, or tabs<br>PHONE_NUMBER payload must contain only digits, up to 20 characters<br>URL payload must be at most 2000 characters<br>URL payload must start with http:// or https://, contain no spaces or tabs, and end with a . followed by letters or numbers<br>Maximum 10 QUICK_REPLY buttons allowed<br>Maximum 2 URL buttons allowed<br>Maximum 1 PHONE_NUMBER button allowed<br>Buttons must be grouped by type, not interleaved |
| buttons[].type               | Sí          | Cada objeto botón                             | Debe ser QUICK_REPLY, URL o PHONE_NUMBER                                                                                                                                                                                                                                                                                                                          | ^(QUICK_REPLY\|URL\|PHONE_NUMBER)$                                                                                                                    | Each button type must be one of: QUICK_REPLY, URL, PHONE_NUMBER                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| buttons[].title              | Sí          | Cada objeto botón                             | Entre 1 y 25 caracteres, no vacío ni solo espacios, sin saltos de línea, retornos de carro ni tabulaciones                                                                                                                                                                                                                                                        | ^(?!\\s\*$)(?!.\*[\\n\\r\\t]).{1,25}$                                                                                                                 | Each button title must be 1-25 characters, non-empty, with no newlines, carriage returns, or tabs                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| buttons[].payload            | Sí          | Cada objeto botón                             | Campo único compartido por los 3 tipos.<br>QUICK_REPLY: entre 1 y 25 caracteres, no vacío ni solo espacios, sin saltos de línea/retorno de carro/tabulación.<br>PHONE_NUMBER: solo dígitos, hasta 20 caracteres.<br>URL: debe iniciar con http:// o https://, sin espacios ni tabulaciones, terminar en un punto seguido de letras/números, hasta 2000 caracteres | QUICK_REPLY: ^(?!\\s\*$)(?!.\*[\\n\\r\\t]).{1,25}$<br>URL: ^(?=.{1,2000}$)https?:\\/\\/\\S+\\.[A-Za-z]{2,}(\\/\\S\*)?$<br>PHONE_NUMBER: ^[0-9]{1,20}$ | Each button payload must be a non-empty string<br>QUICK_REPLY payload must be 1-25 characters, non-empty, with no newlines, carriage returns, or tabs<br>PHONE_NUMBER payload must contain only digits, up to 20 characters<br>URL payload must be at most 2000 characters<br>URL payload must start with http:// or https://, contain no spaces or tabs, and end with a . followed by letters or numbers                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |

> **Nota:** Algunos campos cuentan con validación cruzada estructural detectada**: `category` ↔ `type`/`file`/`header`/`header_var`/`body`/`body_var`/`footer`/`security`/`expiration`/`buttons` 
(presencia/ausencia condicionada); `type` ↔ `file`/`header`/`header_var`; `header` ↔ `header_var`; `body` ↔ `body_var`
(coincidencia de conteo); `buttons[].type` ↔ `buttons[].payload` (formato condicionado por tipo de botón).
> **Nota2:** El campo "name" debe ser siempre diferente en cada petición nueva que se haga

## Mirror keys en respuesta
> **Nota:** Solo se muestran los campos que si aparecen en la respuesta

No hay campos que validar en esta sección