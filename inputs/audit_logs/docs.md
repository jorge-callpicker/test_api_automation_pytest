Aquí tienes la documentación de la API de Chatwoot para listar registros de auditoría, convertida a Markdown con una estructura clara y profesional.

---

# List Audit Logs in Account

Obtén los detalles de los registros de auditoría para una cuenta.

> **Nota:** Este endpoint solo está disponible en las ediciones Enterprise y requiere que la función `audit_logs` esté habilitada.

## Endpoint

```http
GET /api/v1/accounts/{account_id}/audit_logs
```

## Autorización

Este token se puede obtener visitando la página de perfil o mediante la consola de Rails. Proporciona acceso a los endpoints según los niveles de permisos del usuario. Este token puede ser guardado por un sistema externo cuando el usuario es creado vía API, para realizar actividades en nombre del usuario.

| Key | Value |
| --- | ----- |
| **api_access_token** | `string` (requerido) |

## Parámetros

### Path Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `account_id` | `integer` | El ID numérico de la cuenta. |

### Query Parameters

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `page` | `integer` | Número de página para la paginación. |

## Ejemplos de código

### cURL

```bash
curl --request GET \
  --url 'https://app.chatwoot.com/api/v1/accounts/{account_id}/audit_logs?page=1' \
  --header 'api_access_token: <your_token>'
```

### Python

```python
import requests

url = "https://app.chatwoot.com/api/v1/accounts/{account_id}/audit_logs?page=1"
headers = {"api_access_token": "<your_token>"}

response = requests.get(url, headers=headers)
print(response.text)
```

### JavaScript (Fetch)

```javascript
const options = {
  method: 'GET',
  headers: { api_access_token: '<your_token>' }
};

fetch('https://app.chatwoot.com/api/v1/accounts/{account_id}/audit_logs?page=1', options)
  .then(res => res.json())
  .then(res => console.log(res))
  .catch(err => console.error(err));
```

### PHP (cURL)

```php
<?php
$curl = curl_init();

curl_setopt_array($curl, [
  CURLOPT_URL => "https://app.chatwoot.com/api/v1/accounts/{account_id}/audit_logs?page=1",
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_ENCODING => "",
  CURLOPT_MAXREDIRS => 10,
  CURLOPT_TIMEOUT => 30,
  CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
  CURLOPT_CUSTOMREQUEST => "GET",
  CURLOPT_HTTPHEADER => [ "api_access_token: <your_token>" ],
]);

$response = curl_exec($curl);
$err = curl_error($curl);

curl_close($curl);

if ($err) {
  echo "cURL Error #:" . $err;
} else {
  echo $response;
}
?>
```

### Go

```go
package main

import (
  "fmt"
  "io"
  "net/http"
)

func main() {
  url := "https://app.chatwoot.com/api/v1/accounts/{account_id}/audit_logs?page=1"
  req, _ := http.NewRequest("GET", url, nil)
  req.Header.Add("api_access_token", "<your_token>")

  res, _ := http.DefaultClient.Do(req)
  defer res.Body.Close()

  body, _ := io.ReadAll(res.Body)
  fmt.Println(string(body))
}
```

### Java (Unirest)

```java
HttpResponse response = Unirest.get("https://app.chatwoot.com/api/v1/accounts/{account_id}/audit_logs?page=1")
  .header("api_access_token", "<your_token>")
  .asString();
```

### Ruby

```ruby
require 'uri'
require 'net/http'

url = URI("https://app.chatwoot.com/api/v1/accounts/{account_id}/audit_logs?page=1")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)
request["api_access_token"] = '<your_token>'

response = http.request(request)
puts response.read_body
```

## Respuestas

### Success (200 OK)

```json
{
  "per_page": 25,
  "total_entries": 150,
  "current_page": 1,
  "audit_logs": [
    {
      "id": 123,
      "auditable_id": 123,
      "auditable_type": "",
      "auditable": {},
      "associated_id": 123,
      "associated_type": "",
      "user_id": 123,
      "user_type": "",
      "username": "",
      "audited_changes": {},
      "version": 123,
      "comment": "",
      "request_uuid": "",
      "created_at": 123,
      "remote_address": ""
    }
  ]
}
```

#### Atributos del objeto `audit_logs`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | `integer` | ID del registro de auditoría |
| `auditable_id` | `integer` | ID del objeto auditable |
| `auditable_type` | `string` | Tipo del objeto auditable |
| `auditable` | `object` | Objeto auditable |
| `associated_id` | `integer` | ID del objeto asociado |
| `associated_type` | `string` | Tipo del objeto asociado |
| `user_id` | `integer` | ID del usuario que realizó la acción |
| `user_type` | `string` | Tipo de usuario |
| `username` | `string` | Nombre del usuario |
| `audited_changes` | `object` | Cambios realizados |
| `version` | `integer` | Versión del registro |
| `comment` | `string` | Comentario |
| `request_uuid` | `string` | UUID de la solicitud |
| `created_at` | `integer` | Fecha de creación (timestamp) |
| `remote_address` | `string` | Dirección IP remota |

### Error

```json
{
  "description": "",
  "errors": [
    {
      "field": "",
      "message": "",
      "code": ""
    }
  ]
}
```