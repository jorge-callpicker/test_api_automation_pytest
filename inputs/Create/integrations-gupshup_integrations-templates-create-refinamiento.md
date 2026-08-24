---
endpoint: /integrations/gupshup_integrations/templates/create
metodo: POST
estado: aprobado
version: 4
documentacion: docs/input/Create/create_info.md, docs/input/contexto_base.md
salida: docs/output/Create/
matriz_generada_en_version: 4
---

# Refinamiento: POST /integrations/gupshup_integrations/templates/create

## 1. Contextos de aplicación

El body es `multipart/form-data`. `category` y `type` determinan qué campos aplican. `buttons[].type` determina, dentro del objeto anidado `buttons`, qué reglas aplican a `buttons[].payload`. Todos los contextos son mutuamente excluyentes.

**Regla de diseño declarada y confirmada por el usuario (v2):** los campos que no varían según el sub-contexto de `type` (`account_id`, `name`, `category`, `lang`, `apps`, `body`, `body_var`, `footer`, `buttons`, header `api-access-token`) se prueban exhaustivamente (válidos e inválidos) únicamente en el contexto `c1`. En `c2`-`c6` aparecen fijos en una única combinación válida (no generan filas de error propias).

| Slug | Contexto | Condición de activación | Campos aplicables (varían) | Campos prohibidos |
|---|---|---|---|---|
| c1-sin-header | `category` ∈ {MARKETING, UTILITY} ∧ `type` ausente | `type` ausente | account_id, name, category, lang, apps, type, body, body_var, footer, buttons, api_access_token | file, header, header_var, security, expiration |
| c2-header-texto | `category` ∈ {MARKETING, UTILITY} ∧ `type` = TEXT | `type`=TEXT | type (fijo=TEXT), header, header_var | file, security, expiration |
| c3-header-documento | `category` ∈ {MARKETING, UTILITY} ∧ `type` = DOCUMENT | `type`=DOCUMENT | type (fijo=DOCUMENT), file | header, header_var, security, expiration |
| c4-header-imagen | `category` ∈ {MARKETING, UTILITY} ∧ `type` = IMAGE | `type`=IMAGE | type (fijo=IMAGE), file | header, header_var, security, expiration |
| c5-header-video | `category` ∈ {MARKETING, UTILITY} ∧ `type` = VIDEO | `type`=VIDEO | type (fijo=VIDEO), file | header, header_var, security, expiration |
| c6-autenticacion | `category` = AUTHENTICATION | `category`=AUTHENTICATION | category (fijo=AUTHENTICATION), security, expiration | type, file, header, header_var, body, body_var, footer, buttons |
| c7-boton-quick-reply | dentro de `buttons`, `buttons[].type` = QUICK_REPLY | tipo de botón = QUICK_REPLY | buttons[].type (fijo), buttons[].title, buttons[].payload | (n/a — objeto anidado) |
| c8-boton-url | dentro de `buttons`, `buttons[].type` = URL | tipo de botón = URL | buttons[].type (fijo), buttons[].title, buttons[].payload | (n/a — objeto anidado) |
| c9-boton-phone-number | dentro de `buttons`, `buttons[].type` = PHONE_NUMBER | tipo de botón = PHONE_NUMBER | buttons[].type (fijo), buttons[].title, buttons[].payload | (n/a — objeto anidado) |

## 2. Refinamiento de campos

| Campo | Ubicación | Tipo | Min/Max o lista blanca | Regex | Requerido | Validación | Criticidad negocio |
|---|---|---|---|---|---|---|---|
| api-access-token | Header | String | (fuera de alcance: formato/expiración) | (no documentado) | Sí (implícito por "Header de Validación") | Cruzada (con sesión); solo se valida que sea JWT y que la sesión exista en BD | normal |
| account_id | Body (form) | Integer | min 1 / max 2147483648 | `^[1-9]\d*$` | Sí | Cruzada (debe existir y corresponder a la sesión) | **alta** (feedback) |
| name | Body (form) | String | 3-179 caracteres | `^[a-z0-9_]{3,179}$` | Sí | Independiente + cruzada temporal (debe ser distinto en cada petición; duplicado → 400, mensaje Gupshup dentro de `errors`) | normal |
| category | Body (form) | String | Lista blanca: MARKETING, UTILITY, AUTHENTICATION | `^(MARKETING\|UTILITY\|AUTHENTICATION)$` | Sí | Cruzada (determina reglas de otros campos) | **alta** (feedback) |
| lang | Body (form) | String | Lista blanca: en_US, es_MX | `^(en_US\|es_MX)$` | Sí | Independiente | normal |
| apps | Body (form) | Array\<String UUID\> | No vacío | UUID por elemento (case-insensitive) | Sí | Cruzada (existencia y pertenencia a la cuenta) | **alta** (feedback) |
| type | Body (form) | String | Lista blanca: TEXT, DOCUMENT, IMAGE, VIDEO | `^(TEXT\|DOCUMENT\|IMAGE\|VIDEO)$` | No (opcional; prohibido si `category`=AUTHENTICATION) | Cruzada | **alta** (feedback) |
| file | Body (form, archivo) | File | Reglas por sub-tipo (ver campo `type`) | (sin regex único; validación por tipo MIME/tamaño) | Condicional (requerido si `type`∈{DOCUMENT,IMAGE,VIDEO}; prohibido si `type`=TEXT/ausente o `category`=AUTHENTICATION) | Cruzada | normal |
| header | Body (form) | String | 1-60 caracteres, máx. 1 variable | `^(?=.{1,60}$)(?!.*\n)(?!.* {4}).*$` | Condicional (requerido si `type`=TEXT; prohibido en otro caso) | Cruzada | normal |
| header_var | Body (form) | String | 1-60 caracteres | `^(?=.{1,60}$)(?!.*\n)(?!.* {4}).*$` | Condicional (requerido si `header` contiene variable; prohibido si no, o si `type`≠TEXT) | Cruzada | normal |
| body | Body (form) | String | Máx. 1024 caracteres, hasta 10 variables secuenciales | `^.{1,1024}$` | Condicional (requerido salvo `category`=AUTHENTICATION) | Cruzada (secuencia de variables, coincidencia con `body_var`) | normal |
| body_var | Body (form) | Array\<String\> | Longitud = variables en `body`; c/u 1-1024 caracteres | `^(?=.{1,1024}$)(?!.*\n)(?!.* {4}).*$` (por elemento) | Condicional (requerido si `body` tiene variables; prohibido si no) | Cruzada | normal |
| footer | Body (form) | String | 1-60 caracteres, sin variables | `^(?=.{1,60}$)(?!.*\{\{\d+\}\}).*$` | No (opcional; prohibido si `category`=AUTHENTICATION) | Independiente + cruzada (prohibición en AUTHENTICATION) | normal |
| security | Body (form) | String (booleano) | Lista blanca: true, false, 1, 0 | `^(true\|false\|1\|0)$` | Condicional (requerido si `category`=AUTHENTICATION; prohibido si no) | Cruzada | normal |
| expiration | Body (form) | Integer | 1-90 | `^[1-9]\d*$` | No (opcional; solo aplica si `category`=AUTHENTICATION; prohibido si no) | Cruzada | normal |
| buttons | Body (form) | Array\<Object\> | No vacío; máx. 10 total; máx. 10 QUICK_REPLY, 2 URL, 1 PHONE_NUMBER; agrupados por tipo | (sin regex único a nivel arreglo) | No (opcional; prohibido si `category`=AUTHENTICATION) | Cruzada | **alta** (feedback) |
| buttons[].type | Body (form, anidado) | String | Lista blanca: QUICK_REPLY, URL, PHONE_NUMBER | `^(QUICK_REPLY\|URL\|PHONE_NUMBER)$` | Sí (dentro del objeto) | Cruzada (determina reglas de `payload`) | normal |
| buttons[].title | Body (form, anidado) | String | 1-25 caracteres, no vacío/solo espacios | `^(?!\s*$)(?!.*[\n\r\t]).{1,25}$` | Sí | Independiente | normal |
| buttons[].payload | Body (form, anidado) | String | Reglas por `buttons[].type` (ver sección 3) | QUICK_REPLY: `^(?!\s*$)(?!.*[\n\r\t]).{1,25}$` · URL: `^(?=.{1,2000}$)https?:\/\/\S+\.[A-Za-z]{2,}(\/\S*)?$` · PHONE_NUMBER: `^[0-9]{1,20}$` | Sí | Cruzada (depende de `buttons[].type`) | normal |

## 3. Valores válidos e inválidos por campo

| ID | Campo | Clase | Valor | Contexto | Prioridad | Origen |
|---|---|---|---|---|---|---|
| api_access_token.V1 | api_access_token | válido | (token válido correspondiente a la sesión) | c1 | alto | documentacion |
| api_access_token.I1 | api_access_token | inválido | (ausente) | c1 | alto | documentacion |
| api_access_token.I2 | api_access_token | inválido | (token inválido o expirado) | c1 | alto | documentacion |
| account_id.V1 | account_id | válido | (mínimo del rango, 1) | c1 | alto | documentacion |
| account_id.V2 | account_id | válido | 65 | c1 | alto | feedback |
| account_id.I5 | account_id | inválido | (ausente) | c1 | alto | documentacion |
| account_id.I6 | account_id | inválido | (vacío) | c1 | alto | feedback |
| account_id.I7 | account_id | inválido | (cuenta inexistente) | c1 | alto | documentacion |
| account_id.I8 | account_id | inválido | (cuenta existente, ajena a la sesión) | c1 | alto | documentacion |
| name.V1 | name | válido | (nombre único no usado antes, longitud típica, minúsculas/dígitos/guion bajo) | c1 | medio | documentacion |
| name.V2 | name | válido | (nombre único de longitud mínima, 3 caracteres) | c1 | alto | documentacion |
| name.V3 | name | válido | (nombre único de longitud máxima, 179 caracteres) | c1 | alto | documentacion |
| name.I1 | name | inválido | (longitud 2, por debajo del mínimo) | c1 | alto | documentacion |
| name.I2 | name | inválido | (longitud 180, por encima del máximo) | c1 | alto | documentacion |
| name.I3 | name | inválido | (contiene mayúsculas, viola el patrón) | c1 | medio | documentacion |
| name.I4 | name | inválido | (contiene caracteres especiales no permitidos) | c1 | medio | documentacion |
| name.I5 | name | inválido | (contiene espacios) | c1 | medio | documentacion |
| name.I6 | name | inválido | (ausente) | c1 | alto | documentacion |
| name.I7 | name | inválido | (vacío) | c1 | medio | documentacion |
| name.I8 | name | inválido | (nombre ya utilizado en una petición anterior) | c1 | alto | documentacion |
| name.I9 | name | inválido | (contiene signo negativo, ej. -123) | c1 | medio | feedback |
| name.I10 | name | inválido | (contiene punto decimal, ej. 12.5) | c1 | medio | feedback |
| category.V1 | category | válido | MARKETING | c1 | alto | feedback |
| category.V2 | category | válido | UTILITY | c1 | alto | documentacion |
| category.V3 | category | válido | AUTHENTICATION | c6 | alto | feedback |
| category.I1 | category | inválido | (valor fuera de la lista blanca) | c1 | alto | documentacion |
| category.I2 | category | inválido | (ausente) | c1 | alto | documentacion |
| category.I3 | category | inválido | (vacío) | c1 | alto | documentacion |
| category.I4 | category | inválido | (tipo de dato incorrecto, numérico) | c1 | alto | documentacion |
| category.I5 | category | inválido | (caracteres especiales) | c1 | medio | feedback |
| category.I6 | category | inválido | (valor de la lista blanca en minúsculas, ej. marketing) | c1 | alto | feedback |
| lang.V1 | lang | válido | en_US | c1 | alto | feedback |
| lang.V2 | lang | válido | es_MX | c1 | alto | feedback |
| lang.I1 | lang | inválido | (valor fuera de la lista blanca) | c1 | alto | documentacion |
| lang.I2 | lang | inválido | (ausente) | c1 | alto | documentacion |
| lang.I3 | lang | inválido | (vacío) | c1 | medio | documentacion |
| lang.I4 | lang | inválido | (valor de la lista blanca en minúsculas, ej. en_us) | c1 | alto | feedback |
| apps.V1 | apps | válido | (arreglo con un único UUID válido de una app existente de la cuenta) | c1 | alto | documentacion |
| apps.V2 | apps | válido | (arreglo con múltiples UUID válidos de apps existentes de la cuenta) | c1 | alto | documentacion |
| apps.I1 | apps | inválido | (ausente) | c1 | alto | documentacion |
| apps.I2 | apps | inválido | (vacío) | c1 | alto | documentacion |
| apps.I3 | apps | inválido | (arreglo JSON vacío, sin elementos) | c1 | alto | documentacion |
| apps.I4 | apps | inválido | (arreglo con un elemento que no es un UUID válido) | c1 | alto | documentacion |
| apps.I5 | apps | inválido | (no es un arreglo JSON válido) | c1 | alto | documentacion |
| apps.I6 | apps | inválido | (arreglo con UUID inexistente o inactivo) | c1 | alto | feedback |
| apps.I7 | apps | inválido | (arreglo con UUID que no pertenece a la cuenta) | c1 | alto | feedback |
| apps.I8 | apps | inválido | (arreglo con elemento compuesto solo de letras, no es un UUID) | c1 | medio | feedback |
| apps.I9 | apps | inválido | (arreglo con elemento compuesto solo de números, no es un UUID) | c1 | medio | feedback |
| apps.I10 | apps | inválido | (arreglo con elemento con caracteres especiales, no es un UUID) | c1 | medio | feedback |
| apps.I11 | apps | inválido | (arreglo con un UUID existente modificando o agregando un carácter del string original) | c1 | medio | feedback |
| type.V1 | type | válido | (ausente) | c1 | alto | feedback |
| type.V2 | type | válido | TEXT | c2 | alto | feedback |
| type.V3 | type | válido | DOCUMENT | c3 | alto | feedback |
| type.V4 | type | válido | IMAGE | c4 | alto | feedback |
| type.V5 | type | válido | VIDEO | c5 | alto | documentacion |
| type.I1 | type | inválido | (valor fuera de la lista blanca) | c1 | alto | documentacion |
| type.I2 | type | inválido | (vacío) | c1 | alto | feedback |
| type.I3 | type | inválido | (tipo de dato incorrecto, numérico) | c1 | alto | documentacion |
| type.I4 | type | inválido | (caracteres especiales) | c1 | medio | feedback |
| type.I5 | type | inválido | (valor de la lista blanca en minúsculas, ej. text) | c1 | alto | feedback |
| file.V1 | file | válido | (archivo PDF válido, tamaño típico) | c3 | medio | documentacion |
| file.V2 | file | válido | (archivo PDF de tamaño exactamente 100MB, límite máximo) | c3 | alto | documentacion |
| file.V3 | file | válido | (archivo JPEG válido, tamaño típico) | c4 | medio | documentacion |
| file.V4 | file | válido | (archivo PNG válido, tamaño típico) | c4 | medio | documentacion |
| file.V5 | file | válido | (archivo JPEG de tamaño exactamente 5MB, límite máximo) | c4 | alto | feedback |
| file.V6 | file | válido | (archivo MP4 válido, tamaño típico) | c5 | medio | documentacion |
| file.V7 | file | válido | (archivo MP4 de tamaño exactamente 16MB, límite máximo) | c5 | alto | feedback |
| file.V8 | file | válido | (ausente) | c2 | alto | feedback |
| file.V9 | file | válido | (archivo PNG de tamaño exactamente 5MB, límite máximo) | c4 | alto | feedback |
| file.I1 | file | inválido | (ausente cuando type=DOCUMENT) | c3 | alto | documentacion |
| file.I2 | file | inválido | (archivo de tipo no permitido para DOCUMENT, ej. imagen) | c3 | alto | documentacion |
| file.I3 | file | inválido | (archivo PDF que excede 100MB) | c3 | alto | documentacion |
| file.I4 | file | inválido | (ausente cuando type=IMAGE) | c4 | alto | documentacion |
| file.I5 | file | inválido | (archivo de tipo no permitido para IMAGE, ej. PDF) | c4 | alto | documentacion |
| file.I6 | file | inválido | (archivo JPEG/PNG que excede 5MB) | c4 | alto | documentacion |
| file.I7 | file | inválido | (ausente cuando type=VIDEO) | c5 | alto | documentacion |
| file.I8 | file | inválido | (archivo de tipo no permitido para VIDEO, ej. audio) | c5 | alto | documentacion |
| file.I9 | file | inválido | (archivo MP4 que excede 16MB) | c5 | alto | documentacion |
| file.I10 | file | inválido | (archivo presente cuando type=TEXT o ausente) | cruzada | alto | documentacion |
| header.V1 | header | válido | (texto típico sin variables, longitud media) | c2 | alto | feedback |
| header.V2 | header | válido | (texto típico con una única variable {{1}}) | c2 | alto | feedback |
| header.V3 | header | válido | (longitud mínima, 1 carácter) | c2 | medio | feedback |
| header.V4 | header | válido | (longitud máxima, 60 caracteres) | c2 | medio | feedback |
| header.V5 | header | válido | (cadena que alterna entre mayúsculas y minúsculas) | c2 | medio | feedback |
| header.V6 | header | válido | (caracteres especiales) | c2 | medio | feedback |
| header.V7 | header | válido | (ausente) | c1 | medio | documentacion |
| header.I1 | header | inválido | (ausente cuando type=TEXT) | c2 | alto | documentacion |
| header.I2 | header | inválido | (vacío) | c2 | medio | documentacion |
| header.I3 | header | inválido | (longitud 61, por encima del máximo) | c2 | alto | documentacion |
| header.I4 | header | inválido | (contiene salto de línea) | c2 | medio | documentacion |
| header.I5 | header | inválido | (contiene 4 o más espacios consecutivos) | c2 | medio | documentacion |
| header.I6 | header | inválido | (contiene dos o más variables) | c2 | alto | documentacion |
| header.I7 | header | inválido | (presente cuando type≠TEXT) | cruzada | alto | documentacion |
| header_var.V1 | header_var | válido | (valor típico correspondiente a la variable del header) | c2 | alto | feedback |
| header_var.V2 | header_var | válido | (longitud mínima, 1 carácter) | c2 | alto | documentacion |
| header_var.V3 | header_var | válido | (longitud máxima, 60 caracteres) | c2 | medio | feedback |
| header_var.V4 | header_var | válido | (cadena que alterna entre mayúsculas y minúsculas) | c2 | medio | feedback |
| header_var.V5 | header_var | válido | (caracteres especiales) | c2 | medio | feedback |
| header_var.V6 | header_var | válido | (ausente) | c1 | medio | documentacion |
| header_var.I1 | header_var | inválido | (ausente cuando header contiene variable) | c2 | alto | documentacion |
| header_var.I2 | header_var | inválido | (vacío) | c2 | medio | documentacion |
| header_var.I3 | header_var | inválido | (longitud 61, por encima del máximo) | c2 | alto | documentacion |
| header_var.I4 | header_var | inválido | (contiene salto de línea) | c2 | medio | documentacion |
| header_var.I5 | header_var | inválido | (contiene 4 o más espacios consecutivos) | c2 | medio | documentacion |
| header_var.I6 | header_var | inválido | (presente cuando header no contiene variable) | cruzada | alto | documentacion |
| header_var.I7 | header_var | inválido | (presente cuando type≠TEXT) | cruzada | alto | documentacion |
| body.V1 | body | válido | (texto típico sin variables, longitud media) | c1 | alto | feedback |
| body.V2 | body | válido | (texto típico con variables secuenciales {{1}} a {{3}}) | c1 | alto | feedback |
| body.V3 | body | válido | (longitud mínima, 1 carácter) | c1 | medio | feedback |
| body.V4 | body | válido | (longitud máxima, 1024 caracteres) | c1 | medio | feedback |
| body.V5 | body | válido | (texto con el máximo de 10 variables secuenciales) | c1 | alto | documentacion |
| body.V6 | body | válido | (ausente) | c6 | alto | feedback |
| body.V7 | body | válido | (texto con el mínimo de variables, 1 variable {{1}}) | c1 | medio | feedback |
| body.I1 | body | inválido | (ausente cuando category≠AUTHENTICATION) | c1 | alto | documentacion |
| body.I2 | body | inválido | (vacío) | c1 | medio | documentacion |
| body.I3 | body | inválido | (longitud 1025, por encima del máximo) | c1 | alto | documentacion |
| body.I4 | body | inválido | (más de 10 variables) | c1 | alto | documentacion |
| body.I5 | body | inválido | (variables fuera de secuencia, con huecos o repeticiones) | c1 | alto | documentacion |
| body.I6 | body | inválido | (presente cuando category=AUTHENTICATION) | cruzada | alto | documentacion |
| body.I7 | body | inválido | (texto compuesto únicamente por variables, sin texto fijo alrededor) | c1 | medio | feedback |
| body_var.V1 | body_var | válido | (arreglo con un elemento correspondiente a una variable de body) | c1 | alto | feedback |
| body_var.V2 | body_var | válido | (arreglo con tres elementos, valores típicos) | c1 | alto | feedback |
| body_var.V3 | body_var | válido | (elemento de longitud mínima, 1 carácter) | c1 | medio | feedback |
| body_var.V4 | body_var | válido | (elemento de longitud máxima, 1024 caracteres) | c1 | medio | feedback |
| body_var.V5 | body_var | válido | (ausente) | c1 | alto | feedback |
| body_var.V6 | body_var | válido | (arreglo con exactamente 1 elemento, límite mínimo de variables) | c1 | medio | feedback |
| body_var.I1 | body_var | inválido | (ausente cuando body contiene variables) | c1 | alto | documentacion |
| body_var.I2 | body_var | inválido | (vacío) | c1 | medio | documentacion |
| body_var.I3 | body_var | inválido | (no es un arreglo JSON válido) | c1 | alto | documentacion |
| body_var.I4 | body_var | inválido | (cantidad de elementos distinta a la cantidad de variables en body) | c1 | alto | documentacion |
| body_var.I5 | body_var | inválido | (elemento con salto de línea) | c1 | medio | documentacion |
| body_var.I6 | body_var | inválido | (elemento con 4 o más espacios consecutivos) | c1 | medio | documentacion |
| body_var.I7 | body_var | inválido | (presente cuando body no contiene variables) | cruzada | alto | documentacion |
| body_var.I8 | body_var | inválido | (presente cuando category=AUTHENTICATION) | cruzada | alto | documentacion |
| footer.V1 | footer | válido | (texto típico sin variables, longitud media) | c1 | medio | documentacion |
| footer.V2 | footer | válido | (longitud mínima, 1 carácter) | c1 | alto | documentacion |
| footer.V3 | footer | válido | (longitud máxima, 60 caracteres) | c1 | alto | documentacion |
| footer.V4 | footer | válido | (ausente) | c1 | medio | documentacion |
| footer.V5 | footer | válido | (cadena que alterna entre mayúsculas y minúsculas) | c1 | medio | feedback |
| footer.V6 | footer | válido | (cadena de solo números) | c1 | medio | feedback |
| footer.V7 | footer | válido | (cadena de caracteres especiales) | c1 | medio | feedback |
| footer.V8 | footer | válido | (cadena que alterna entre letras, números y caracteres especiales) | c1 | medio | feedback |
| footer.I1 | footer | inválido | (vacío) | c1 | medio | documentacion |
| footer.I2 | footer | inválido | (longitud 61, por encima del máximo) | c1 | alto | documentacion |
| footer.I3 | footer | inválido | (contiene una variable {{1}}, prohibido) | c1 | alto | documentacion |
| footer.I4 | footer | inválido | (presente cuando category=AUTHENTICATION) | cruzada | alto | documentacion |
| security.V1 | security | válido | true | c6 | medio | documentacion |
| security.V2 | security | válido | false | c6 | medio | documentacion |
| security.V3 | security | válido | 1 | c6 | medio | documentacion |
| security.V4 | security | válido | 0 | c6 | medio | documentacion |
| security.V5 | security | válido | (ausente) | c1 | medio | documentacion |
| security.I1 | security | inválido | (valor fuera de la lista blanca) | c6 | alto | documentacion |
| security.I2 | security | inválido | (ausente cuando category=AUTHENTICATION) | c6 | alto | documentacion |
| security.I3 | security | inválido | (vacío) | c6 | medio | documentacion |
| security.I4 | security | inválido | (presente cuando category≠AUTHENTICATION) | cruzada | alto | documentacion |
| security.I5 | security | inválido | (valor de la lista blanca en mayúsculas, ej. TRUE) | c6 | alto | feedback |
| expiration.V1 | expiration | válido | (ausente) | c6 | medio | documentacion |
| expiration.V2 | expiration | válido | (mínimo del rango, 1) | c6 | alto | documentacion |
| expiration.V3 | expiration | válido | (valor típico dentro del rango) | c6 | medio | documentacion |
| expiration.V4 | expiration | válido | (máximo del rango, 90) | c6 | alto | documentacion |
| expiration.I1 | expiration | inválido | (cero) | c6 | alto | documentacion |
| expiration.I2 | expiration | inválido | (máximo + 1, 91) | c6 | alto | documentacion |
| expiration.I3 | expiration | inválido | (tipo de dato incorrecto, string no numérico) | c6 | medio | documentacion |
| expiration.I4 | expiration | inválido | (vacío) | c6 | medio | documentacion |
| expiration.I5 | expiration | inválido | (presente cuando category≠AUTHENTICATION) | cruzada | alto | documentacion |
| expiration.I6 | expiration | inválido | (caracteres especiales) | c6 | medio | feedback |
| expiration.I7 | expiration | inválido | (cadena que alterna entre mayúsculas y minúsculas) | c6 | medio | feedback |
| buttons.V1 | buttons | válido | (ausente) | c1 | alto | documentacion |
| buttons.V2 | buttons | válido | (arreglo con un botón QUICK_REPLY válido) | c1 | alto | documentacion |
| buttons.V3 | buttons | válido | (arreglo con botones agrupados por tipo, cantidad típica) | c1 | alto | documentacion |
| buttons.V4 | buttons | válido | (arreglo con el máximo de 10 botones en total) | c1 | alto | documentacion |
| buttons.V5 | buttons | válido | (arreglo con botones QUICK_REPLY, URL y PHONE_NUMBER agrupados por tipo, dentro de límites) | c1 | alto | feedback |
| buttons.V6 | buttons | válido | (arreglo con botones QUICK_REPLY y PHONE_NUMBER agrupados por tipo, dentro de límites) | c1 | alto | feedback |
| buttons.V7 | buttons | válido | (arreglo con botones URL y PHONE_NUMBER agrupados por tipo, dentro de límites) | c1 | alto | feedback |
| buttons.I1 | buttons | inválido | (vacío) | c1 | alto | documentacion |
| buttons.I2 | buttons | inválido | (arreglo JSON vacío, sin elementos) | c1 | alto | documentacion |
| buttons.I3 | buttons | inválido | (no es un arreglo JSON válido) | c1 | alto | documentacion |
| buttons.I4 | buttons | inválido | (más de 10 botones en total) | c1 | alto | documentacion |
| buttons.I5 | buttons | inválido | (más de 10 botones QUICK_REPLY) | c1 | alto | documentacion |
| buttons.I6 | buttons | inválido | (más de 2 botones URL) | c1 | alto | documentacion |
| buttons.I7 | buttons | inválido | (más de 1 botón PHONE_NUMBER) | c1 | alto | documentacion |
| buttons.I8 | buttons | inválido | (botones del mismo tipo no agrupados, intercalados) | c1 | alto | documentacion |
| buttons.I9 | buttons | inválido | (presente cuando category=AUTHENTICATION) | cruzada | alto | documentacion |
| buttons.type.V1 | buttons.type | válido | QUICK_REPLY | c7 | medio | documentacion |
| buttons.type.V2 | buttons.type | válido | URL | c8 | medio | documentacion |
| buttons.type.V3 | buttons.type | válido | PHONE_NUMBER | c9 | medio | documentacion |
| buttons.type.I1 | buttons.type | inválido | (valor fuera de la lista blanca) | c7 | alto | documentacion |
| buttons.type.I2 | buttons.type | inválido | (ausente) | c7 | alto | documentacion |
| buttons.type.I3 | buttons.type | inválido | (valor de la lista blanca en minúsculas, ej. quick_reply) | c7 | alto | feedback |
| buttons.title.V1 | buttons.title | válido | (texto típico, longitud media) | c7 | medio | documentacion |
| buttons.title.V2 | buttons.title | válido | (longitud mínima, 1 carácter) | c7 | alto | documentacion |
| buttons.title.V3 | buttons.title | válido | (longitud máxima, 25 caracteres) | c7 | alto | documentacion |
| buttons.title.V4 | buttons.title | válido | (cadena que alterna entre mayúsculas y minúsculas) | c7 | medio | feedback |
| buttons.title.V5 | buttons.title | válido | (cadena de solo números) | c7 | medio | feedback |
| buttons.title.V6 | buttons.title | válido | (cadena de caracteres especiales) | c7 | medio | feedback |
| buttons.title.V7 | buttons.title | válido | (cadena que alterna entre letras, números y caracteres especiales) | c7 | medio | feedback |
| buttons.title.I1 | buttons.title | inválido | (ausente) | c7 | alto | documentacion |
| buttons.title.I2 | buttons.title | inválido | (vacío o solo espacios) | c7 | medio | documentacion |
| buttons.title.I3 | buttons.title | inválido | (longitud 26, por encima del máximo) | c7 | alto | documentacion |
| buttons.title.I4 | buttons.title | inválido | (contiene salto de línea) | c7 | medio | documentacion |
| buttons.title.I5 | buttons.title | inválido | (contiene retorno de carro o tabulación) | c7 | medio | documentacion |
| buttons.payload.V1 | buttons.payload | válido | (texto típico, longitud media, para QUICK_REPLY) | c7 | medio | documentacion |
| buttons.payload.V2 | buttons.payload | válido | (longitud mínima, 1 carácter, para QUICK_REPLY) | c7 | alto | documentacion |
| buttons.payload.V3 | buttons.payload | válido | (longitud máxima, 25 caracteres, para QUICK_REPLY) | c7 | alto | documentacion |
| buttons.payload.V4 | buttons.payload | válido | (URL típica http, terminada en dominio válido) | c8 | medio | documentacion |
| buttons.payload.V5 | buttons.payload | válido | (URL típica https, terminada en dominio válido) | c8 | medio | documentacion |
| buttons.payload.V6 | buttons.payload | válido | (URL de longitud máxima, 2000 caracteres) | c8 | alto | documentacion |
| buttons.payload.V7 | buttons.payload | válido | (número típico de dígitos, para PHONE_NUMBER) | c9 | medio | documentacion |
| buttons.payload.V8 | buttons.payload | válido | (número de longitud máxima, 20 dígitos) | c9 | alto | documentacion |
| buttons.payload.V9 | buttons.payload | válido | (PHONE_NUMBER: número nacional típico, solo dígitos) | c9 | alto | feedback |
| buttons.payload.V10 | buttons.payload | válido | (PHONE_NUMBER: número internacional típico, con código de país, solo dígitos) | c9 | alto | feedback |
| buttons.payload.V11 | buttons.payload | válido | (URL válida con múltiples niveles de subdominio) | c8 | medio | feedback |
| buttons.payload.I1 | buttons.payload | inválido | (ausente) | c7 | alto | documentacion |
| buttons.payload.I2 | buttons.payload | inválido | (vacío o solo espacios, para QUICK_REPLY) | c7 | medio | documentacion |
| buttons.payload.I3 | buttons.payload | inválido | (longitud 26, por encima del máximo, para QUICK_REPLY) | c7 | alto | documentacion |
| buttons.payload.I4 | buttons.payload | inválido | (contiene salto de línea, para QUICK_REPLY) | c7 | medio | documentacion |
| buttons.payload.I5 | buttons.payload | inválido | (URL sin protocolo http/https) | c8 | alto | documentacion |
| buttons.payload.I6 | buttons.payload | inválido | (URL con espacios o tabulaciones) | c8 | medio | documentacion |
| buttons.payload.I7 | buttons.payload | inválido | (URL que no termina en un punto seguido de letras/números) | c8 | alto | documentacion |
| buttons.payload.I8 | buttons.payload | inválido | (URL de longitud 2001, por encima del máximo) | c8 | alto | documentacion |
| buttons.payload.I9 | buttons.payload | inválido | (PHONE_NUMBER con caracteres no numéricos) | c9 | alto | documentacion |
| buttons.payload.I10 | buttons.payload | inválido | (PHONE_NUMBER de longitud 21, por encima del máximo) | c9 | alto | documentacion |

**Valores retirados en v2 (no reutilizar sus ID):** `account_id.V3` (máximo del rango), `account_id.I1` (cero), `account_id.I2` (negativo), `account_id.I3` (máximo + 1), `account_id.I4` (string no numérico) — descartados por feedback explícito del usuario.

**Nota de verificación v3:** se revisó `header_var` contra el feedback de v3 y no se requirió ningún cambio de datos: `header_var.V1`/`V2` ya reflejaban `alto`, `header_var.V3` ya reflejaba `media` (ambos existían antes de v2), y `header_var.V4`/`V5` (agregados en v2) ya tenían `media` por la instrucción de alta explícita de "agregar con prioridad media", no por una extensión indebida del cambio de `V3`. No hubo IDs que corregir.

## 4. Reglas de combinación acordadas

- Campos con criticidad de negocio `alta`: `account_id`, `apps`, `category`, `type`, `buttons` (declarado por el usuario en v2). Se aplica como piso absoluto: todo valor de estos campos sin una prioridad puntual indicada explícitamente por el usuario queda en `alto`.
- Campos con criticidad de negocio `baja`: (ninguno declarado)
- Precedencia entre piso de criticidad y prioridad explícita por valor: **confirmado por el usuario en v3** — la instrucción puntual (p. ej. `media` en `apps.I8`-`I11`, `category.I5`, `type.I4`) prevalece sobre el piso `alto` del campo. Sin cambios respecto a lo aplicado en v2.
- Grupos de validación cruzada detectados:
  - `category` ↔ `type`/`file`/`header`/`header_var`/`body`/`body_var`/`footer`/`security`/`expiration`/`buttons` (presencia/ausencia condicionada por `category`).
  - `type` ↔ `file`/`header`/`header_var` (presencia/ausencia condicionada por `type`).
  - `header` ↔ `header_var` (coincidencia de presencia de variable).
  - `body` ↔ `body_var` (coincidencia de conteo de variables).
  - `buttons[].type` ↔ `buttons[].payload` (formato condicionado por tipo de botón).
  - `name` ↔ histórico de peticiones anteriores (unicidad); duplicado produce `400` con mensaje Gupshup `Template Already exists with same namespace and elementName and languageCode` dentro de `errors` (en respuesta parcial `206` o total `400`).
- Campos equivalentes (se combinan en orden inverso): (ninguno detectado)
- Casos a omitir por decisión del usuario: (ninguno)
- Máximo de columnas por matriz: (sin límite)
- Diseño de columnas fijas vs. variables por contexto: **confirmado por el usuario en v2** — los campos comunes (`account_id`, `name`, `category`, `lang`, `apps`, `body`, `body_var`, `footer`, `buttons`) varían únicamente en `c1-sin-header`; en `c2`-`c6` se fijan en una única combinación válida.
- `account_id` de prueba disponible para ejecución: `65` (cuenta válida correspondiente a la sesión). **Confirmado por el usuario en v3**: los valores de `account_id.I7` (inexistente) y `account_id.I8` (ajena a la sesión) se dejan tal como están (indicación, sin instanciar); el valor concreto se asignará al momento de ejecutar la matriz, no en el refinamiento.
- `apps`: fases de validación confirmadas — formato UUID inválido = `400` de validación inicial; UUID inexistente/inactivo o ajeno a la cuenta = error de procesamiento por app, reflejado dentro de `payload`/`success`/`errors` con código `200`/`206`/`400` según cuántas apps de la lista fallen.
- `api-access-token`: reglas de formato/expiración fuera de alcance de este endpoint; solo se valida que el token sea un JWT y que la sesión exista en base de datos.
- Reglas de negocio sin código HTTP específico documentado más allá de `400` general (variables de `body` fuera de secuencia, botones del mismo tipo no agrupados, "header can only contain one variable"): confirmado por el usuario que `400` es correcto.
- `apps`, mensaje "Must be at least 2 characters": confirmado que el mínimo real por elemento es 1 carácter; el mensaje de 2 caracteres es un artefacto de la conversión de campos de texto de `form-data` a JSON, no se modela como regla adicional de negocio.
- `header_var`: **confirmado por el usuario en v3** — el cambio de prioridad a `media` aplica únicamente a los valores que ya existían antes de v2 (`V1`-`V3`); las variantes nuevas agregadas en v2 (`V4`, `V5`) no se ven afectadas por ese cambio puntual (ya tenían `media` por su propia instrucción de alta).

## 5. Preguntas abiertas

Todas las preguntas abiertas de v2 fueron respondidas explícitamente por el usuario en v3 y quedan cerradas (ver sección 4 y sección 6 para el detalle de cada confirmación). No hay preguntas abiertas nuevas en esta versión ni en v4 (aprobación).

| # | Campo | Pregunta | Supuesto aplicado mientras tanto |
|---|---|---|---|
| (ninguna pendiente) | — | — | — |

## 6. Registro de cambios

| v | Acción | Feedback recibido (literal) | Qué se aplicó |
|---|---|---|---|
| 1 | refinamiento inicial | (n/a — primera pasada sobre la documentación) | Derivación completa de contextos, campos y valores a partir de `create_info.md` y `contexto_base.md`. |
| 2 | actualizar (respuestas a preguntas abiertas + modificación de valores) | Respuestas a la sección 5: "1. ¿Qué campos son críticos de negocio...? R = los campos críticos de negocio son: `account_id`, `apps`, `category`, `type` y `buttons`."<br>"2. ¿Existe un mecanismo/cuenta de prueba...? R= Si, el `account_id` disponible para pruebas es el `65`"<br>"3. ¿Qué código HTTP exacto retorna la API cuando `name` ya fue usado...? R= code `400`, retorna un error de gupshup `Template Already exists with same namespace and elementName and languageCode` que viene dentro de `errors` en fallo particial/total { code: 206, success: [...], errors: [...] } { code: 400, errors: [...], message: 'All accounts failed' }"<br>"4. ...¿Es correcta esta separación de fases...? R = \"App IDs must be valid UUIDs\" es parte de las validaciones de campos de entrada al inicio de todo, lo unico que se valida es que los id que estan llegando sean UUIDs, \"App not found or inactive\" es de los errores 400/206 aparece en estos casos `El app no existe en base de datos o está deshabilitado`, `El app no pertenece a la cuenta`"<br>"5. ...R = las reglas de validación y expiración quedan fuera de scope, en el endpoint solo se verifica que el `api-access-token` sea un JWT y que la sesión exista en la base de datos."<br>"6. ...R = Si, se aprueba que los campos comunes (`account_id`, `name`, `category`, `lang`, `apps`, `body`, `body_var`, `footer`, `buttons`) se prueben exhaustivamente solo en el contexto."<br>"7. ...R= lo que se asume es correcto"<br>"8. ...R = lo que se asume es correcto"<br>"9. ...R= el minimo es 1 caracter. el error de 2 caracteres minimo es por la forma en que se estan convirtiendo los campos de texto del form data a json"<br>Modificación de la tabla 3: "account_id: Descarta los valores de la columna: `account_id.V3,account_id.I1, account_id.I2, account_id.I3, account_id.I4`. `account_id.V2, account_id.I6` cambia la prioridad a: `alta`."<br>"name: agrega los valores inválidos: `números negativos`, `números decimales`, con la prioridad: `media`."<br>"category: agrega los valores inválidos: `caracteres especiales` con la prioridad: `media`, `valor dentro de la lista blanca en minúsculas` con la prioridad: `alta`. `category.V1, category.V3, category.V1` cambia la prioridad a: `alta`."<br>"lang: agrega el valor inválido: `valor dentro de la lista blanca en minúsculas` con la prioridad `alta`. `lang.V1, lang.V2` cambia la prioridad a: `alta`."<br>"apps: agrega los valores inválidos: `solo letras`, `solo números`, `caracteres especiales`, `UUID existente modificando/agregando un caracter del string original` con la prioridad: `media`. `apps.I6, apps.I7` reemplaza la palabra app_id por UUID en la columna `Valor`. `apps.V1, apps.V2` cambia la prioridad a: `alta`"<br>"type: agrega los valores inválidos: `caracteres especiales` con la prioridad: `media`, `valor dentro de la lista blanca en minúsculas` con la prioridad: `alta`. `type.V1, type.V2, type.V3, type.V4, type.V1, type.I2` cambiar la prioridad a: `alta`."<br>"file: agrega el valor válido: `ausente cuando Type=TEXT` con la prioridad: `alta`, `(archivo PNG de tamaño exactamente 5MB, límite máximo)` con la prioridad `alta`. `file.V5` reemplaza el valor de la columna `Valor` por: `(archivo JPEG de tamaño exactamente 5MB, límite máximo)`. `file.V7` reemplaza el valor de la columna `Valor` por: `(archivo MP4 de tamaño exactamente 16MB, límite máximo)`."<br>"header: agrega los valores válidos: `cadena que alterna entre mayúsculas y minúsculas`, `caracteres especiales` con la prioridad: `media`. `header.V1, header.V2` cambia la prioridad a: `alta`, para los valores: `header.V3, header.V4` cambia la prioridad a `media`."<br>"header_var: agrega los valores válidos: `cadena que alterna entre mayúsculas y minúsculas`, `caracteres especiales` con la prioridad: `media`. `header_var.V1, header_var.V2` cambia la prioridad a: `alta`, para los valores: `header_var.V3, header_var.V4` cambia la prioridad a `media`."<br>"body: agrega los valores válidos: `ausente cuando category=AUTHENTICATION` con la prioridad: `alta`, `texto con el mínimo de varibles 1` con la prioridad `media`. agrega valor inválido: `solo variables` con la prioridad `media`. `body.V1, body.V2` cambia la prioridad a: `alta`, para los valores: `body.V3, body.V4` cambia la prioridad a `media`."<br>"body_var: agrega los valores válidos: `ausente cuando body no tiene variables` con la prioridad: `alta`, `mínimo de variables 1` con la prioridad `media`. `body_var.V1, body_var.V2` cambia la prioridad a: `alta`, para los valores: `body_var.V3, body_var.V4` cambia la prioridad a `media`."<br>"footer: agrega los valores válidos: `cadena que alterna entre mayúsculas y minúsculas`, `cadena de solo números`, `cadena de caracteres especiales`, `cadena que alterna entre letras, números y caracteres especiales` con la prioridad: `media`."<br>"security: agrega el valor inválido: `valor dentro de la lista blanca en mayúsculas` con la prioridad: `alta`."<br>"expiration: agrega los valores inválidos: `caracteres especiales`, `cadena que alterna entre mayúsculas y minúsculas` con la prioridad: `media`."<br>"buttons: agrega los valores válidos: `arreglo con botones QUICK_REPLY, URL y PHONE_NUMBER agrupados por tipo, dentro de límites)`, `arreglo con botones QUICK_REPLY y PHONE_NUMBER agrupados por tipo, dentro de límites)`, `arreglo con botones URL y PHONE_NUMBER agrupados por tipo, dentro de límites)`, con la prioridad: `alta`."<br>"buttons.type: agrega el valor inválido: `valor dentro de la lista blanca en minúsculas` con la prioridad: `alta`."<br>"buttons.title: agrega los valores válidos: `cadena que alterna entre mayúsculas y minúsculas`, `cadena de solo números`, `cadena de caracteres especiales`, `cadena que alterna entre letras, números y caracteres especiales` con la prioridad: `media`."<br>"buttons.payload: agrega los valores válidos: `PHONE_NUMBER: numero nacional`, `PHONE_NUMBER: numero internacional` con la prioridad `alta`, `URL: múltiples dominios` con la prioridad: `media`." | Se incorporó la criticidad de negocio (`account_id`, `apps`, `category`, `type`, `buttons` = alta) en sección 2 y 4. Se cerraron las 9 preguntas abiertas de v1 (respondidas) y se documentaron en sección 4 como reglas acordadas. Se descartaron 5 valores de `account_id` (V3, I1-I4). Se agregaron 40 valores nuevos distribuidos en `name`, `category`, `lang`, `apps`, `type`, `file`, `header`, `header_var`, `body`, `body_var`, `footer`, `security`, `expiration`, `buttons`, `buttons.type`, `buttons.title`, `buttons.payload`. Se modificó el texto de `apps.I6`, `apps.I7`, `file.V5`, `file.V7`. Se aplicaron los cambios de prioridad puntuales indicados, y el piso de criticidad `alta` al resto de valores de los 5 campos críticos. Se registraron 3 preguntas abiertas nuevas (precedencia piso/valor puntual, ambigüedad de ID en `header_var`, valor concreto de `account_id` para "ajena a la sesión"/"inexistente"). `estado` pasa a `en-revision`; el usuario aclaró explícitamente que esto NO es aprobación del refinamiento completo. |
| 3 | actualizar (respuestas a las 3 preguntas abiertas de v2) | "1. Para account_id: confirmaste 65 como cuenta válida de prueba, pero falta el valor concreto para \"cuenta ajena a la sesión\" e \"inexistente\"...¿Confirmas ese supuesto o tienes valores específicos? R= los valores `cuenta ajena a la sesión` e `inexistente` se quedan tal como estan, no se modifican ya que posteriormente se les asignara el valor."<br>"2. Diste prioridad alta como criticidad de negocio para apps/category/type, pero en algunos casos pediste prioridad media puntual para valores específicos de esos mismos campos. ¿La instrucción puntual (media) prevalece sobre el piso de criticidad (alta), como asumió el subagente? R = si, se queda tal como esta."<br>"3. Tu feedback mencionó header_var.V4, pero ese campo solo tenía V1-V3 en la versión anterior. El subagente interpretó que te referías a la variante nueva que agregaste en la misma instrucción (la de \"caracteres especiales\"). ¿Es correcto? R = no, entonces solo aplica el cambio a los que existen en la versión anterior." | Se cerraron las 3 preguntas abiertas de v2 sin cambios de datos en la sección 3: (1) `account_id.I7`/`I8` se dejan como indicación sin instanciar, valor concreto pendiente de asignación en ejecución; (2) se confirma que la prioridad puntual por valor prevalece sobre el piso de criticidad del campo; (3) se verificó que el cambio de prioridad a `media` en `header_var` ya se había aplicado únicamente a `V1`-`V3` (los existentes antes de v2) y que `V4`/`V5` (nuevos en v2) ya tenían `media` por su propia instrucción de alta, no por una extensión indebida — no se requirió corrección. Las 3 confirmaciones quedaron registradas en la sección 4; la sección 5 queda sin preguntas pendientes. `estado` permanece en `en-revision`; el usuario no ha dado aprobación explícita del refinamiento completo. |
| 4 | actualizar (aprobación explícita del refinamiento) | "El usuario aprueba explícitamente el refinamiento. Marca estado: aprobado (version+1)." | No se modificó ningún valor de la sección 3 ni las reglas de la sección 4: es una aprobación pura, sin nuevo feedback de contenido. `estado` pasa de `en-revision` a `aprobado` por transmisión explícita de la aprobación del usuario. `version` se incrementa a 4 para dejar registro del momento exacto de la aprobación. Con este cambio queda habilitado el modo `matriz` sobre este refinamiento. |
| 4 | matriz generada | (n/a) | 10 CSV escritos: `integrations-gupshup_integrations-templates-create-matriz-c1-sin-header.csv`, `...-c2-header-texto.csv`, `...-c3-header-documento.csv`, `...-c4-header-imagen.csv`, `...-c5-header-video.csv`, `...-c6-autenticacion.csv`, `...-buttons.csv` (c7, QUICK_REPLY), `...-buttons-url.csv` (c8, URL), `...-buttons-phone-number.csv` (c9, PHONE_NUMBER), `...-matriz-cruzada.csv`. Verificación automática (SubagentStop) rechazó el primer intento por 3 causas: (a) BOM UTF-8 interpretado como parte del literal de la columna 1, (b) los rellenos "(ausente)" para campos prohibidos (`file`, `body`, `body_var`) llevaban texto descriptivo en vez del literal exacto `(ausente)`, y a `header`/`header_var`/`security` les faltaba ese valor en la sección 3 (PASO 3.5, condición inactiva → único estado válido, nunca completado), (c) la prioridad de filas válidas en las matrices anidadas de `buttons` estaba fijada a `alto` en vez de calcular `max()` real (PASO 5). Correcciones aplicadas: se quitó el BOM al escribir los CSV; se simplificó el texto de `file.V8`, `body.V6` y `body_var.V5` a `(ausente)` exacto; se agregaron `header.V7`, `header_var.V6` y `security.V5` (`(ausente)`, medio, documentacion) completando el PASO 3.5 para esos campos; se corrigió el cálculo de prioridad de filas válidas para usar `max()` real sobre todas las celdas de la fila. Los 10 CSV se regeneraron. Cobertura verificada: 222/222 IDs de la sección 3 (219 originales + 3 agregados) aparecen en al menos un CSV. Ninguna fila no-cruzada tiene dos campos inválidos simultáneos (escalera correcta). Ningún CSV contiene BOM, celdas vacías, ni celdas sin prefijo de ID. |

## 7. Cobertura

| ID | Valor | Matriz | No. de Caso | Prioridad |
|---|---|---|---|---|
| api_access_token.V1 | (token válido correspondiente a la sesión) | c1-sin-header | 1 | alto |
| api_access_token.I1 | (ausente) | c1-sin-header | 72 | alto |
| api_access_token.I2 | (token inválido o expirado) | c1-sin-header | 73 | alto |
| account_id.V1 | (mínimo del rango, 1) | c1-sin-header | 1 | alto |
| account_id.V2 | 65 | c1-sin-header | 2 | alto |
| account_id.I5 | (ausente) | c1-sin-header | 9 | alto |
| account_id.I6 | (vacío) | c1-sin-header | 10 | alto |
| account_id.I7 | (cuenta inexistente) | c1-sin-header | 11 | alto |
| account_id.I8 | (cuenta existente, ajena a la sesión) | c1-sin-header | 12 | alto |
| name.V1 | (nombre único no usado antes, longitud típica, minúsculas/dígitos/guion bajo) | c1-sin-header | 1 | medio |
| name.V2 | (nombre único de longitud mínima, 3 caracteres) | c1-sin-header | 2 | alto |
| name.V3 | (nombre único de longitud máxima, 179 caracteres) | c1-sin-header | 3 | alto |
| name.I1 | (longitud 2, por debajo del mínimo) | c1-sin-header | 13 | alto |
| name.I2 | (longitud 180, por encima del máximo) | c1-sin-header | 14 | alto |
| name.I3 | (contiene mayúsculas, viola el patrón) | c1-sin-header | 15 | medio |
| name.I4 | (contiene caracteres especiales no permitidos) | c1-sin-header | 16 | medio |
| name.I5 | (contiene espacios) | c1-sin-header | 17 | medio |
| name.I6 | (ausente) | c1-sin-header | 18 | alto |
| name.I7 | (vacío) | c1-sin-header | 19 | medio |
| name.I8 | (nombre ya utilizado en una petición anterior) | c1-sin-header | 20 | alto |
| name.I9 | (contiene signo negativo, ej. -123) | c1-sin-header | 21 | medio |
| name.I10 | (contiene punto decimal, ej. 12.5) | c1-sin-header | 22 | medio |
| category.V1 | MARKETING | c1-sin-header | 1 | alto |
| category.V2 | UTILITY | c1-sin-header | 2 | alto |
| category.V3 | AUTHENTICATION | c6-autenticacion | 1 | alto |
| category.I1 | (valor fuera de la lista blanca) | c1-sin-header | 23 | alto |
| category.I2 | (ausente) | c1-sin-header | 24 | alto |
| category.I3 | (vacío) | c1-sin-header | 25 | alto |
| category.I4 | (tipo de dato incorrecto, numérico) | c1-sin-header | 26 | alto |
| category.I5 | (caracteres especiales) | c1-sin-header | 27 | medio |
| category.I6 | (valor de la lista blanca en minúsculas, ej. marketing) | c1-sin-header | 28 | alto |
| lang.V1 | en_US | c1-sin-header | 1 | alto |
| lang.V2 | es_MX | c1-sin-header | 2 | alto |
| lang.I1 | (valor fuera de la lista blanca) | c1-sin-header | 29 | alto |
| lang.I2 | (ausente) | c1-sin-header | 30 | alto |
| lang.I3 | (vacío) | c1-sin-header | 31 | medio |
| lang.I4 | (valor de la lista blanca en minúsculas, ej. en_us) | c1-sin-header | 32 | alto |
| apps.V1 | (arreglo con un único UUID válido de una app existente de la cuenta) | c1-sin-header | 1 | alto |
| apps.V2 | (arreglo con múltiples UUID válidos de apps existentes de la cuenta) | c1-sin-header | 2 | alto |
| apps.I1 | (ausente) | c1-sin-header | 33 | alto |
| apps.I2 | (vacío) | c1-sin-header | 34 | alto |
| apps.I3 | (arreglo JSON vacío, sin elementos) | c1-sin-header | 35 | alto |
| apps.I4 | (arreglo con un elemento que no es un UUID válido) | c1-sin-header | 36 | alto |
| apps.I5 | (no es un arreglo JSON válido) | c1-sin-header | 37 | alto |
| apps.I6 | (arreglo con UUID inexistente o inactivo) | c1-sin-header | 38 | alto |
| apps.I7 | (arreglo con UUID que no pertenece a la cuenta) | c1-sin-header | 39 | alto |
| apps.I8 | (arreglo con elemento compuesto solo de letras, no es un UUID) | c1-sin-header | 40 | medio |
| apps.I9 | (arreglo con elemento compuesto solo de números, no es un UUID) | c1-sin-header | 41 | medio |
| apps.I10 | (arreglo con elemento con caracteres especiales, no es un UUID) | c1-sin-header | 42 | medio |
| apps.I11 | (arreglo con un UUID existente modificando o agregando un carácter del string original) | c1-sin-header | 43 | medio |
| type.V1 | (ausente) | c1-sin-header | 1 | alto |
| type.V2 | TEXT | c2-header-texto | 1 | alto |
| type.V3 | DOCUMENT | c3-header-documento | 1 | alto |
| type.V4 | IMAGE | c4-header-imagen | 1 | alto |
| type.V5 | VIDEO | c5-header-video | 1 | alto |
| type.I1 | (valor fuera de la lista blanca) | c1-sin-header | 44 | alto |
| type.I2 | (vacío) | c1-sin-header | 45 | alto |
| type.I3 | (tipo de dato incorrecto, numérico) | c1-sin-header | 46 | alto |
| type.I4 | (caracteres especiales) | c1-sin-header | 47 | medio |
| type.I5 | (valor de la lista blanca en minúsculas, ej. text) | c1-sin-header | 48 | alto |
| file.V1 | (archivo PDF válido, tamaño típico) | c3-header-documento | 1 | medio |
| file.V2 | (archivo PDF de tamaño exactamente 100MB, límite máximo) | c3-header-documento | 2 | alto |
| file.V3 | (archivo JPEG válido, tamaño típico) | c4-header-imagen | 1 | medio |
| file.V4 | (archivo PNG válido, tamaño típico) | c4-header-imagen | 2 | medio |
| file.V5 | (archivo JPEG de tamaño exactamente 5MB, límite máximo) | c4-header-imagen | 3 | alto |
| file.V6 | (archivo MP4 válido, tamaño típico) | c5-header-video | 1 | medio |
| file.V7 | (archivo MP4 de tamaño exactamente 16MB, límite máximo) | c5-header-video | 2 | alto |
| file.V8 | (ausente) | c2-header-texto | 1 | alto |
| file.V9 | (archivo PNG de tamaño exactamente 5MB, límite máximo) | c4-header-imagen | 4 | alto |
| file.I1 | (ausente cuando type=DOCUMENT) | c3-header-documento | 3 | alto |
| file.I2 | (archivo de tipo no permitido para DOCUMENT, ej. imagen) | c3-header-documento | 4 | alto |
| file.I3 | (archivo PDF que excede 100MB) | c3-header-documento | 5 | alto |
| file.I4 | (ausente cuando type=IMAGE) | c4-header-imagen | 5 | alto |
| file.I5 | (archivo de tipo no permitido para IMAGE, ej. PDF) | c4-header-imagen | 6 | alto |
| file.I6 | (archivo JPEG/PNG que excede 5MB) | c4-header-imagen | 7 | alto |
| file.I7 | (ausente cuando type=VIDEO) | c5-header-video | 3 | alto |
| file.I8 | (archivo de tipo no permitido para VIDEO, ej. audio) | c5-header-video | 4 | alto |
| file.I9 | (archivo MP4 que excede 16MB) | c5-header-video | 5 | alto |
| file.I10 | (archivo presente cuando type=TEXT o ausente) | cruzada | 1 (cruzada: type+file) | alto |
| header.V1 | (texto típico sin variables, longitud media) | c2-header-texto | 1 | alto |
| header.V2 | (texto típico con una única variable {{1}}) | c2-header-texto | 2 | alto |
| header.V3 | (longitud mínima, 1 carácter) | c2-header-texto | 3 | medio |
| header.V4 | (longitud máxima, 60 caracteres) | c2-header-texto | 4 | medio |
| header.V5 | (cadena que alterna entre mayúsculas y minúsculas) | c2-header-texto | 5 | medio |
| header.V6 | (caracteres especiales) | c2-header-texto | 6 | medio |
| header.V7 | (ausente) | c1-sin-header | 1 | medio |
| header.I1 | (ausente cuando type=TEXT) | c2-header-texto | 7 | alto |
| header.I2 | (vacío) | c2-header-texto | 8 | medio |
| header.I3 | (longitud 61, por encima del máximo) | c2-header-texto | 9 | alto |
| header.I4 | (contiene salto de línea) | c2-header-texto | 10 | medio |
| header.I5 | (contiene 4 o más espacios consecutivos) | c2-header-texto | 11 | medio |
| header.I6 | (contiene dos o más variables) | c2-header-texto | 12 | alto |
| header.I7 | (presente cuando type≠TEXT) | cruzada | 2 (cruzada: type+header) | alto |
| header_var.V1 | (valor típico correspondiente a la variable del header) | c2-header-texto | 1 | alto |
| header_var.V2 | (longitud mínima, 1 carácter) | c2-header-texto | 2 | alto |
| header_var.V3 | (longitud máxima, 60 caracteres) | c2-header-texto | 3 | medio |
| header_var.V4 | (cadena que alterna entre mayúsculas y minúsculas) | c2-header-texto | 4 | medio |
| header_var.V5 | (caracteres especiales) | c2-header-texto | 5 | medio |
| header_var.V6 | (ausente) | c1-sin-header | 1 | medio |
| header_var.I1 | (ausente cuando header contiene variable) | c2-header-texto | 13 | alto |
| header_var.I2 | (vacío) | c2-header-texto | 14 | medio |
| header_var.I3 | (longitud 61, por encima del máximo) | c2-header-texto | 15 | alto |
| header_var.I4 | (contiene salto de línea) | c2-header-texto | 16 | medio |
| header_var.I5 | (contiene 4 o más espacios consecutivos) | c2-header-texto | 17 | medio |
| header_var.I6 | (presente cuando header no contiene variable) | cruzada | 3 (cruzada: header+header_var) | alto |
| header_var.I7 | (presente cuando type≠TEXT) | cruzada | 4 (cruzada: type+header_var) | alto |
| body.V1 | (texto típico sin variables, longitud media) | c1-sin-header | 1 | alto |
| body.V2 | (texto típico con variables secuenciales {{1}} a {{3}}) | c1-sin-header | 2 | alto |
| body.V3 | (longitud mínima, 1 carácter) | c1-sin-header | 3 | medio |
| body.V4 | (longitud máxima, 1024 caracteres) | c1-sin-header | 4 | medio |
| body.V5 | (texto con el máximo de 10 variables secuenciales) | c1-sin-header | 5 | alto |
| body.V6 | (ausente) | c6-autenticacion | 1 | alto |
| body.V7 | (texto con el mínimo de variables, 1 variable {{1}}) | c1-sin-header | 6 | medio |
| body.I1 | (ausente cuando category≠AUTHENTICATION) | c1-sin-header | 49 | alto |
| body.I2 | (vacío) | c1-sin-header | 50 | medio |
| body.I3 | (longitud 1025, por encima del máximo) | c1-sin-header | 51 | alto |
| body.I4 | (más de 10 variables) | c1-sin-header | 52 | alto |
| body.I5 | (variables fuera de secuencia, con huecos o repeticiones) | c1-sin-header | 53 | alto |
| body.I6 | (presente cuando category=AUTHENTICATION) | cruzada | 5 (cruzada: category+body) | alto |
| body.I7 | (texto compuesto únicamente por variables, sin texto fijo alrededor) | c1-sin-header | 54 | medio |
| body_var.V1 | (arreglo con un elemento correspondiente a una variable de body) | c1-sin-header | 1 | alto |
| body_var.V2 | (arreglo con tres elementos, valores típicos) | c1-sin-header | 2 | alto |
| body_var.V3 | (elemento de longitud mínima, 1 carácter) | c1-sin-header | 3 | medio |
| body_var.V4 | (elemento de longitud máxima, 1024 caracteres) | c1-sin-header | 4 | medio |
| body_var.V5 | (ausente) | c1-sin-header | 5 | alto |
| body_var.V6 | (arreglo con exactamente 1 elemento, límite mínimo de variables) | c1-sin-header | 6 | medio |
| body_var.I1 | (ausente cuando body contiene variables) | c1-sin-header | 55 | alto |
| body_var.I2 | (vacío) | c1-sin-header | 56 | medio |
| body_var.I3 | (no es un arreglo JSON válido) | c1-sin-header | 57 | alto |
| body_var.I4 | (cantidad de elementos distinta a la cantidad de variables en body) | c1-sin-header | 58 | alto |
| body_var.I5 | (elemento con salto de línea) | c1-sin-header | 59 | medio |
| body_var.I6 | (elemento con 4 o más espacios consecutivos) | c1-sin-header | 60 | medio |
| body_var.I7 | (presente cuando body no contiene variables) | cruzada | 6 (cruzada: body+body_var) | alto |
| body_var.I8 | (presente cuando category=AUTHENTICATION) | cruzada | 7 (cruzada: category+body_var) | alto |
| footer.V1 | (texto típico sin variables, longitud media) | c1-sin-header | 1 | medio |
| footer.V2 | (longitud mínima, 1 carácter) | c1-sin-header | 2 | alto |
| footer.V3 | (longitud máxima, 60 caracteres) | c1-sin-header | 3 | alto |
| footer.V4 | (ausente) | c1-sin-header | 4 | medio |
| footer.V5 | (cadena que alterna entre mayúsculas y minúsculas) | c1-sin-header | 5 | medio |
| footer.V6 | (cadena de solo números) | c1-sin-header | 6 | medio |
| footer.V7 | (cadena de caracteres especiales) | c1-sin-header | 7 | medio |
| footer.V8 | (cadena que alterna entre letras, números y caracteres especiales) | c1-sin-header | 8 | medio |
| footer.I1 | (vacío) | c1-sin-header | 61 | medio |
| footer.I2 | (longitud 61, por encima del máximo) | c1-sin-header | 62 | alto |
| footer.I3 | (contiene una variable {{1}}, prohibido) | c1-sin-header | 63 | alto |
| footer.I4 | (presente cuando category=AUTHENTICATION) | cruzada | 8 (cruzada: category+footer) | alto |
| security.V1 | true | c6-autenticacion | 1 | medio |
| security.V2 | false | c6-autenticacion | 2 | medio |
| security.V3 | 1 | c6-autenticacion | 3 | medio |
| security.V4 | 0 | c6-autenticacion | 4 | medio |
| security.V5 | (ausente) | c1-sin-header | 1 | medio |
| security.I1 | (valor fuera de la lista blanca) | c6-autenticacion | 5 | alto |
| security.I2 | (ausente cuando category=AUTHENTICATION) | c6-autenticacion | 6 | alto |
| security.I3 | (vacío) | c6-autenticacion | 7 | medio |
| security.I4 | (presente cuando category≠AUTHENTICATION) | cruzada | 9 (cruzada: category+security) | alto |
| security.I5 | (valor de la lista blanca en mayúsculas, ej. TRUE) | c6-autenticacion | 8 | alto |
| expiration.V1 | (ausente) | c6-autenticacion | 1 | medio |
| expiration.V2 | (mínimo del rango, 1) | c6-autenticacion | 2 | alto |
| expiration.V3 | (valor típico dentro del rango) | c6-autenticacion | 3 | medio |
| expiration.V4 | (máximo del rango, 90) | c6-autenticacion | 4 | alto |
| expiration.I1 | (cero) | c6-autenticacion | 9 | alto |
| expiration.I2 | (máximo + 1, 91) | c6-autenticacion | 10 | alto |
| expiration.I3 | (tipo de dato incorrecto, string no numérico) | c6-autenticacion | 11 | medio |
| expiration.I4 | (vacío) | c6-autenticacion | 12 | medio |
| expiration.I5 | (presente cuando category≠AUTHENTICATION) | cruzada | 10 (cruzada: category+expiration) | alto |
| expiration.I6 | (caracteres especiales) | c6-autenticacion | 13 | medio |
| expiration.I7 | (cadena que alterna entre mayúsculas y minúsculas) | c6-autenticacion | 14 | medio |
| buttons.V1 | (ausente) | c1-sin-header | 1 | alto |
| buttons.V2 | (arreglo con un botón QUICK_REPLY válido) | c1-sin-header | 2 | alto |
| buttons.V3 | (arreglo con botones agrupados por tipo, cantidad típica) | c1-sin-header | 3 | alto |
| buttons.V4 | (arreglo con el máximo de 10 botones en total) | c1-sin-header | 4 | alto |
| buttons.V5 | (arreglo con botones QUICK_REPLY, URL y PHONE_NUMBER agrupados por tipo, dentro de límites) | c1-sin-header | 5 | alto |
| buttons.V6 | (arreglo con botones QUICK_REPLY y PHONE_NUMBER agrupados por tipo, dentro de límites) | c1-sin-header | 6 | alto |
| buttons.V7 | (arreglo con botones URL y PHONE_NUMBER agrupados por tipo, dentro de límites) | c1-sin-header | 7 | alto |
| buttons.I1 | (vacío) | c1-sin-header | 64 | alto |
| buttons.I2 | (arreglo JSON vacío, sin elementos) | c1-sin-header | 65 | alto |
| buttons.I3 | (no es un arreglo JSON válido) | c1-sin-header | 66 | alto |
| buttons.I4 | (más de 10 botones en total) | c1-sin-header | 67 | alto |
| buttons.I5 | (más de 10 botones QUICK_REPLY) | c1-sin-header | 68 | alto |
| buttons.I6 | (más de 2 botones URL) | c1-sin-header | 69 | alto |
| buttons.I7 | (más de 1 botón PHONE_NUMBER) | c1-sin-header | 70 | alto |
| buttons.I8 | (botones del mismo tipo no agrupados, intercalados) | c1-sin-header | 71 | alto |
| buttons.I9 | (presente cuando category=AUTHENTICATION) | cruzada | 11 (cruzada: category+buttons) | alto |
| buttons.type.V1 | QUICK_REPLY | buttons | 1 | medio |
| buttons.type.V2 | URL | buttons-url | 1 | medio |
| buttons.type.V3 | PHONE_NUMBER | buttons-phone-number | 1 | medio |
| buttons.type.I1 | (valor fuera de la lista blanca) | buttons | 8 | alto |
| buttons.type.I2 | (ausente) | buttons | 9 | alto |
| buttons.type.I3 | (valor de la lista blanca en minúsculas, ej. quick_reply) | buttons | 10 | alto |
| buttons.title.V1 | (texto típico, longitud media) | buttons | 1 | medio |
| buttons.title.V2 | (longitud mínima, 1 carácter) | buttons | 2 | alto |
| buttons.title.V3 | (longitud máxima, 25 caracteres) | buttons | 3 | alto |
| buttons.title.V4 | (cadena que alterna entre mayúsculas y minúsculas) | buttons | 4 | medio |
| buttons.title.V5 | (cadena de solo números) | buttons | 5 | medio |
| buttons.title.V6 | (cadena de caracteres especiales) | buttons | 6 | medio |
| buttons.title.V7 | (cadena que alterna entre letras, números y caracteres especiales) | buttons | 7 | medio |
| buttons.title.I1 | (ausente) | buttons | 11 | alto |
| buttons.title.I2 | (vacío o solo espacios) | buttons | 12 | medio |
| buttons.title.I3 | (longitud 26, por encima del máximo) | buttons | 13 | alto |
| buttons.title.I4 | (contiene salto de línea) | buttons | 14 | medio |
| buttons.title.I5 | (contiene retorno de carro o tabulación) | buttons | 15 | medio |
| buttons.payload.V1 | (texto típico, longitud media, para QUICK_REPLY) | buttons | 1 | medio |
| buttons.payload.V2 | (longitud mínima, 1 carácter, para QUICK_REPLY) | buttons | 2 | alto |
| buttons.payload.V3 | (longitud máxima, 25 caracteres, para QUICK_REPLY) | buttons | 3 | alto |
| buttons.payload.V4 | (URL típica http, terminada en dominio válido) | buttons-url | 1 | medio |
| buttons.payload.V5 | (URL típica https, terminada en dominio válido) | buttons-url | 2 | medio |
| buttons.payload.V6 | (URL de longitud máxima, 2000 caracteres) | buttons-url | 3 | alto |
| buttons.payload.V7 | (número típico de dígitos, para PHONE_NUMBER) | buttons-phone-number | 1 | medio |
| buttons.payload.V8 | (número de longitud máxima, 20 dígitos) | buttons-phone-number | 2 | alto |
| buttons.payload.V9 | (PHONE_NUMBER: número nacional típico, solo dígitos) | buttons-phone-number | 3 | alto |
| buttons.payload.V10 | (PHONE_NUMBER: número internacional típico, con código de país, solo dígitos) | buttons-phone-number | 4 | alto |
| buttons.payload.V11 | (URL válida con múltiples niveles de subdominio) | buttons-url | 4 | medio |
| buttons.payload.I1 | (ausente) | buttons | 16 | alto |
| buttons.payload.I2 | (vacío o solo espacios, para QUICK_REPLY) | buttons | 17 | medio |
| buttons.payload.I3 | (longitud 26, por encima del máximo, para QUICK_REPLY) | buttons | 18 | alto |
| buttons.payload.I4 | (contiene salto de línea, para QUICK_REPLY) | buttons | 19 | medio |
| buttons.payload.I5 | (URL sin protocolo http/https) | buttons-url | 5 | alto |
| buttons.payload.I6 | (URL con espacios o tabulaciones) | buttons-url | 6 | medio |
| buttons.payload.I7 | (URL que no termina en un punto seguido de letras/números) | buttons-url | 7 | alto |
| buttons.payload.I8 | (URL de longitud 2001, por encima del máximo) | buttons-url | 8 | alto |
| buttons.payload.I9 | (PHONE_NUMBER con caracteres no numéricos) | buttons-phone-number | 5 | alto |
| buttons.payload.I10 | (PHONE_NUMBER de longitud 21, por encima del máximo) | buttons-phone-number | 6 | alto |

### Resumen de cobertura

| Matriz | Columnas válidas | Columnas inválidas | Total | alto | medio | bajo |
|---|---|---|---|---|---|---|
| c1-sin-header | 8 | 65 | 73 | 54 | 19 | 0 |
| c2-header-texto | 6 | 11 | 17 | 11 | 6 | 0 |
| c3-header-documento | 2 | 3 | 5 | 5 | 0 | 0 |
| c4-header-imagen | 4 | 3 | 7 | 7 | 0 | 0 |
| c5-header-video | 2 | 3 | 5 | 5 | 0 | 0 |
| c6-autenticacion | 4 | 10 | 14 | 9 | 5 | 0 |
| buttons | 7 | 12 | 19 | 11 | 8 | 0 |
| buttons-url | 4 | 4 | 8 | 4 | 4 | 0 |
| buttons-phone-number | 4 | 2 | 6 | 5 | 1 | 0 |
| cruzada | 0 | 11 | 11 | 11 | 0 | 0 |
