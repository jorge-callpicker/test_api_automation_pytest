# Endopoints

## Login

Using Chat Callpicker credentials but agent user, you can obtain JWT for using on rest of the endpoints.

**URL PATH:** {{GLB-url_cp_api}}/panel_chat/login
**Request Body schema:** application/json
- username: required, string
- password: required, string

### Request sample
```json
{
  "username": "test@test.com",
  "password": "12345"
}
```

### Response sample
**200**
```json
{
  "code": 200,
  "message": "Success",
  "payload": {
    "api_token": "abcde12345.",
    "user": {
      "role": "SuperAdmin",
      "name": "Fulanito",
      "id": 0,
      "account_id": 0
    }
  }
}
```

**400**
```json
{
  "code": 400,
  "message": "Missing parameters",
  "errors": []
}
```

**401**
```json
{
  "code": 401,
  "message": "Invalid login",
  "errors": {
    "success": false,
    "errors": [
      "Invalid login credentials. Please try again."
    ]
  }
}
```

**403**
```json
{
  "code": 403,
  "message": "Invalid user",
  "errors": []
}
```

## Select Account 
Once you select an account, user obtains a new JWT that holds Gupshup Apps data necessary to get all templates from Gupshup API.

**URL PATH:** {{GLB-url_cp_api}}/panel_chat/selectAccount/{account_id}

**Path Parameters:**
- account_id: required, integer, ID from Chat Callpicker. Necessary to obtains templates from Gupshup API via inboxes.
    - Example: 1

**Header Parameters**
- api_access_token: required, string, Initial JWT. This can be obtain after users login.
    - Example: qwerty1234567890

### Response sample
**200**
```json
{
  "code": 200,
  "message": "Success",
  "payload": {
    "api_key": "123456"
  }
}
```

**400**
```json
{
  "code": 400,
  "message": "Missing Account ID",
  "errors": []
}
```

**401**
```json
{
  "code": 401,
  "message": "El token proporcionado no es válido. Por favor, solicita uno nuevo e intenta nuevamente.",
  "errors": []
}
```

**406**
```json
{
  "code": 406,
  "message": "La sesión no es válida. Por favor, inicia sesión nuevamente.",
  "errors": []
}
```

**500**
```json
{
  "code": 400,
  "message": "Gupshup Error",
  "errors": {
    "key": "Error"
  }
}
```

# Flujo de autenticación de la API de Admin Chat y la obtención de IDs.

**Login de Panel Chat.**

**Roles de usuario**

Admin/ Super admin

**Propósito.**

Iniciar sesión en el sistema utilizando las credenciales de usuario (correo electrónico y contraseña) para obtener la información inicial de la sesión y el primer API token. 

**Metodo:** POST

**Ruta:***{{dominio\_de\_callpicker\_chat\_api}}/panel\_chat/login*

**Pasos a seguir:**

* Configurar una petición POST a la ruta *{{dominio\_de\_callpicker\_chat\_api}}/panel\_chat/login.*  
* Incluir en el cuerpo de la petición (body) en formato JSON los campos username (correo electrónico) y password (contraseña).  
* Enviar la petición para obtener la respuesta con la información de la sesión y el API token inicial payload.api\_token.

***Nota:*** Los pasos de inicio de sesión aplican tanto para el rol de Admin como para Super admin, no hay ninguna distinción entre los roles. 

**Seleccionar Cuenta**

**Roles de usuario**

Admin/ Super admin

**Propósito.**

Seleccionar la cuenta específica en la que se operará dentro de Admin Chat para generar el token de sesión definitivo (api-access-token) que contiene el contexto completo del usuario y la cuenta.

**Metodo:** GET

**Ruta:***{{dominio\_de\_callpicker\_chat\_api}}/panel\_chat/selectAccount/{{ACCOUNT\_ID}}*

**Pasos a seguir:**

* Configurar una petición GET a la ruta *{{dominio\_de\_callpicker\_chat\_api}}/panel\_chat/selectAccount/*  
* Agregar el account\_id al final de la URL e.j. *{{dominio\_de\_callpicker\_chat\_api}}/panel\_chat/selectAccount/{{ACCOUNT\_ID}}*  
* Incluir en la cabecera (header) la clave api-access-token obtenida previamente en el login.  
* Ejecutar la petición para recibir el token de sesión definitivo api-access-token en payload.api\_key.

***Nota:*** Los pasos de selección de cuenta aplican tanto para el rol de Admin como para Super admin, no hay ninguna distinción entre los roles. 

**Listar Inboxes.**

**Roles de usuario**

Admin/ Super admin

**Propósito.**

Consultar los inboxes asociados a la cuenta seleccionada para obtener el `inbox_id` y el `app_id` (ID de la aplicación de Gupshup), los cuales serán utilizados para el consumo de los endpoints de la API de Templates.

**Metodo:** POST

**Ruta:***{{dominio\_de\_callpicker\_chat\_api}}/integrations/gupshup\_integrations/inbox/admin*

**Pasos a seguir:**

* Configurar una petición POST a la ruta *{{dominio\_de\_callpicker\_chat\_api}}/integrations/gupshup\_integrations/inbox/admin*  
* Agregar en las cabeceras (headers) la clave api-access-token con el token de sesión obtenido al seleccionar la cuenta.  
* Incluir en el cuerpo de la petición (body) en formato JSON los campos account\_id  
*  (ID de la cuenta) e inbox\_types (para listar solo inboxes de gupshup siempre debe tener el valor \["Channel::Api:gupshup"\])  
* Ejecutar la petición para recibir todos los inboxes disponibles de tipo gupshup y obtener el payload\[0\].id (`inbox_id)` y el payload\[0\].extras.app\_id (`app_id)` de cada uno de ellos. 

**Listar Plantillas.**

**Roles de usuario**

Admin/ Super admin

**Propósito.**

Obtener el listado de plantillas existentes para una cuenta e inbox específicos, permitiendo visualizar los detalles y obtener el identificador de cada plantilla (`template_id`), el cual será utilizado para el consumo de los endpoints de la API de Templates.

**Metodo:** GET

**Ruta:***{{dominio\_de\_callpicker\_chat\_api}}/integrations/gupshup\_integrations/templates/admin*

**Pasos a seguir:**

* Configurar una petición GET a la ruta *{{dominio\_de\_callpicker\_chat\_api}}/integrations/gupshup\_integrations/templates/admin*  
* Agregar en la cabecera (header) la clave api-access-token con el token de sesión de la cuenta seleccionada.  
* Pasar como parámetros en la URL (params) los valores de account\_id e inbox\_id (obtenido en el listado de inboxes).  
* Enviar la petición para obtener la lista de plantillas y extraer el ID de cada plantilla payload.records\[0\].id (`template_id`).


**Ejemplos de consumo de la API con los identificadores y tokens obtenidos.**

**Crear Plantilla.**

**Roles de usuario**

Admin/ Super admin

**Propósito.**

Registrar o crear una nueva plantilla de WhatsApp.

**Metodo:** POST

**Ruta:***{{dominio\_de\_callpicker\_chat\_api}}/integrations/gupshup\_integrations/templates/create*

**Pasos a seguir:**

* Configurar una petición POST a la ruta *{{dominio\_de\_callpicker\_chat\_api}}/integrations/gupshup\_integrations/templates/create*  
* Agregar en los headers la clave api-access-token con el token de sesión de la cuenta seleccionada.  
* Definir el cuerpo de la petición (body) en formato form-data.  
* Incluir los campos de texto requeridos con sus respectivos valores, como account\_id y app\_id.  
* Si la plantilla requiere un archivo multimedia, definir la clave con tipo file y cargar el archivo desde el equipo local.  
* Enviar la petición para registrar la plantilla.

**Eliminar Plantilla.**

**Roles de usuario**

Admin/ Super admin

**Propósito.**

Realizar la eliminación lógica (*soft delete*) de una plantilla registrada previamente en el sistema.

**Metodo:** POST

**Ruta:***{{dominio\_de\_callpicker\_chat\_api}}/integrations/gupshup\_integrations/templates/delete*

**Pasos a seguir:**

* Configurar una petición POST a la ruta *{{dominio\_de\_callpicker\_chat\_api}}/integrations/gupshup\_integrations/templates/delete*  
* Incluir en la cabecera (header) la clave api-access-token con el token de sesión obtenido tras seleccionar la cuenta.  
* Enviar en el cuerpo de la petición (body) un objeto JSON (raw) con los campos requeridos, account\_id, inbox\_id y template\_id  
* Enviar la petición para eliminar la plantilla.
