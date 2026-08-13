# Callpicker oAuth API — `/oauth/token`

> Fuente: [`definitions/oauth/definition.yaml`](../definitions/oauth/definition.yaml), [`paths/token.yml`](../definitions/oauth/paths/token.yml).

## Descripción

Genera un nuevo token de autenticación para consumir una API específica de Callpicker®.

La autenticación se basa en el estándar **OAuth 2.0** (flujo `client_credentials`). Puntos importantes del contexto general de la API (`definitions/oauth/definition.yaml`):

- Cada API de Callpicker® requiere un token específico para esa API — el token generado aquí solo funciona con el `scope` (API) indicado en la petición.
- El acceso a las APIs de Callpicker® está disponible únicamente para clientes registrados con acceso API autorizado; debe solicitarse su activación al representante de ventas.
- Una vez habilitado, las credenciales (`CLIENT ID` y `CLIENT SECRET`) y los scopes habilitados se consultan en la sección **API** del menú **Configuración** del panel de administración de Callpicker.
- Las credenciales no deben exponerse: cualquier mal uso o cargo generado por malas prácticas de seguridad o codificación es responsabilidad exclusiva del cliente.

## Verbo y Endpoint

| | |
|---|---|
| **Verbo** | `POST` |
| **Endpoint** | `/oauth/token` |
| **URL base** | `https://api.callpicker.com/` |
| **Content-Type** | `form-data` (ver [nota](#notas-e-inconsistencias-detectadas-en-el-spec)) |
| **operationId** | `token` |
| **Seguridad** | Ninguna declarada — este endpoint es el que **emite** las credenciales de acceso (`client_id`/`client_secret` van en el body, no como token previo). |

## Request Body Schema

Objeto con los siguientes campos, todos **requeridos**:

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `grant_type` | `string` | Sí | Tipo de autenticación a usar. Cada scope requiere un tipo de `grant_type` específico. Valor documentado: `client_credentials`. |
| `scope` | `string` | Sí | Nombre de la API a consumir. El token generado solo funcionará con la API indicada aquí (p. ej. `call_details`). |
| `client_id` | `string` | Sí | CLIENT ID de la cuenta, disponible en la sección API del panel de administración de Callpicker. |
| `client_secret` | `string` | Sí | CLIENT SECRET de la cuenta, disponible en la misma sección. |

## Request Samples

**Como formulario (`application/x-www-form-urlencoded`, equivalente al `form-data` declarado en el spec)**

```
grant_type=client_credentials&scope=call_details&client_id=CU.3344.243413443&client_secret=7ghdssgaj22lmnms8822sq190d
```

**cURL**

```sh
curl -X POST "https://api.callpicker.com/oauth/token" \
  -d grant_type=client_credentials \
  -d scope=call_details \
  -d client_id=CU.3344.243413443 \
  -d client_secret=7ghdssgaj22lmnms8822sq190d
```

## Responses

### `200` — Successful response

| Campo | Tipo | Descripción |
|---|---|---|
| `code` | `integer` | Código de respuesta. |
| `access_token` | `string` | Token de autenticación generado (string de 128 caracteres). |
| `token_type` | `string` | Tipo de token que usa la API actual. `bearer` por defecto. |
| `expires_in` | `string` (fecha) | Fecha de expiración del token. Cada scope retorna tiempos de expiración distintos; al expirar, debe solicitarse un nuevo token. |
| `scope` | `string` | Scope (API) para el que es válido el token. |

### `400` — invalid_request

Retornado en caso de parámetros inválidos. El esquema es `oneOf` entre dos formas:

**`Undefined required parameter`**

| Campo | Tipo | Descripción |
|---|---|---|
| `code` | `integer` | Código de error. |
| `error` | `string` | Mensaje de error (`invalid_request`). |
| `error_description` | `string` | Descripción del error, p. ej. `Undefined parameter grant_type`. |

**`Invalid param value`**

| Campo | Tipo | Descripción |
|---|---|---|
| `code` | `integer` | Código de error. |
| `error` | `string` | Mensaje de error (`invalid_request`). |
| `error_description` | `string` | Descripción del error, p. ej. `Invalid value for parameter scope`. |

### `401` — unauthorized_client

Retornado en caso de scope o token inválido. **El spec no define un `content`/schema para esta respuesta.**

### `403` — Forbidden

El spec declara el esquema `oneOf` → `Undefined required parameter` (ver arriba) para este código. Ver la nota sobre esta inconsistencia [abajo](#notas-e-inconsistencias-detectadas-en-el-spec).

### `405` — Bad Request

Retornado en caso de formato de solicitud inválido. **El spec no define un `content`/schema para esta respuesta.**

### `500` — Internal Server Error

Retornado en caso de errores internos del servidor. **El spec no define un `content`/schema para esta respuesta.**

## Response Samples

**`200` — Successful response**

```json
{
  "code": 200,
  "access_token": "2ec55193476876c3425811db0322c5b316ed5608237ca0b4f7e9ee2a897b079066ea16407f111c961baf01e9a918265e7c5d471d00b4d673a8affbdbf196acc9",
  "token_type": "bearer",
  "expires_in": "2018-08-01 21:09:13",
  "scope": "call_details"
}
```

**`400` — Undefined required parameter**

```json
{
  "code": 400,
  "error": "invalid_request",
  "error_description": "Undefined parameter grant_type"
}
```

**`400` — Invalid param value**

```json
{
  "code": 400,
  "error": "invalid_request",
  "error_description": "Invalid value for parameter scope"
}
```

**`403` — Forbidden** (esquema reutilizado, ver nota)

```json
{
  "code": 400,
  "error": "invalid_request",
  "error_description": "Undefined parameter grant_type"
}
```

## Notas e inconsistencias detectadas en el spec

`definitions/oauth/` usa un formato más antiguo que el resto del repositorio (sin `schemas/request.yaml`/`response.yaml` separados ni globals de error reutilizables como en `call_details`). Al documentarlo tal cual está definido, se detectaron las siguientes inconsistencias en el YAML fuente — se documentan aquí por transparencia, sin corregirlas, ya que no fueron parte del alcance solicitado:

1. **Tipos JSON Schema inválidos**: `code: { type: int }` y `expires_in: { type: date }` no son tipos válidos de OpenAPI/JSON Schema (deberían ser `integer` y `string`/`format: date-time` respectivamente). Se documentaron aquí como `integer` y `string (fecha)` para reflejar la intención.
2. **`content-type` del request body**: el spec declara `form-data`, que no es un media type MIME válido (los valores estándar serían `application/x-www-form-urlencoded` o `multipart/form-data`). Se asumió `application/x-www-form-urlencoded` para el sample, por ser el estándar en flujos OAuth2 `client_credentials`.
3. **Ejemplo `scope` desalineado**: en la respuesta `200`, el campo `scope` tiene `example: 200` pero `description: calls` — valores cruzados. En este documento se usó `call_details` (el scope real usado en el request de ejemplo) para el sample.
4. **Schema `403` probablemente incorrecto**: la respuesta `403` referencia `Undefined required parameter` (la misma schema que un caso de `400`), cuando por el `description: Forbbiden` (sic) y el contexto (credenciales inválidas) probablemente debería referenciar el schema `Invalid client credentials`, definido en `definition.yaml` pero **nunca referenciado** desde ningún path.
5. **Respuestas `401`, `405`, `500` sin `content`**: a diferencia de `call_details`, estos códigos no tienen schema de error asociado en el spec.
6. **Sin componente de seguridad (`securitySchemes`)**: coherente con que este es el endpoint que emite el token, pero distinto del patrón `userApiToken`/`tangoApiToken` usado en el resto de las APIs.

### Relaciones de archivos (vía CodeGraph / lectura de referencias)

Igual que en el documento de `call_details-calls.md`, `codegraph node` reporta `definitions/oauth/paths/token.yml` y `definitions/oauth/definition.yaml` como *"configuration/data file, no dependents"* — no resuelve `$ref` entre YAML. La cadena real de referencias se determinó leyendo los archivos directamente:

- `definitions/oauth/definition.yaml` → declara la ruta `/oauth/token` apuntando a `./paths/token.yml`, y define inline (en `components.schemas`) los tres esquemas de error usados por los paths: `Undefined required parameter`, `Invalid param value`, `Invalid client credentials`.
- `paths/token.yml` → referencia esos esquemas con rutas relativas al archivo padre: `../definition.yaml#/components/schemas/<Nombre>`.
- No hay dependencia hacia `definitions/globals/` (a diferencia de `call_details`), ya que este módulo no reutiliza los esquemas de error globales del resto del repositorio.

Endpoints relacionados dentro de la misma API: `/oauth/validate_credentials`, `/oauth/validate_client_products`.
