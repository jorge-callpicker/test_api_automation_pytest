El metodo `POST /oauth/token` sirve para obtener un token que permite consumir las APIs pertenecientes a Callpicker Chat.
En esta ocasion requiero una rutina que me permita generar el `api_access_token` cumpliendo los siguientes requerimientos.

# Consideraciones
1. Tengo varios roles:
    - Rol "Tango" (Super Administrador): Permite seleccionar cualquier cuenta y tiene acceso a funciones basicas (como cualquier cliente) y especializadas o de administración (tipo Sudo)
    - Admin: Solo administra una sola cuenta y tiene las funciones basicas
    - Supervisor: Administra varias cuentas con un mismo usuario, cada cuenta tiene el mismo nivel de funcionalidad de un usuario Admin
    - Asistente: Pertenece a una sola cuenta y tiene funcionalidades limitadas
    - Customer: Usuario con el mismo nivel de acceso que Admin pero que solo se usa para consumir las APIs
    - Extension: usuario del sistema que solo funciona para consumir ciertas funcionalidades relacionadas, por ejemplo llamadas y su historial o configuración minima de su cuenta
    - Extension Supervisora: usuario del sistema con el mismo nivel de acceso que "Extension" pero que permite revisar la informacion y/o configuración de otra Extension asignada
2. Cada usuario cuenta con dos parametros que se van usar en el metodo ya mencionado para obtener un token de acceso:
    - `client_id`
    - `client_secret`
3. Un usuario/cuenta puede tener multiples scopes activados, por cada `scope` se genera un token de acceso

# Requerimientos
Se requiere generar una rutina que me permita obtener uno o varios `api_access_token` para utilizarlas en el consumo de endpoints posteriores,tomando en cuenta lo siguiente:
1. Solo se va generar el token de acceso de los usuarios que tengan los siguientes datos:
    - `client_id`
    - `client_secret`
    - `scope`
2. Un usuario puede tener multiples scopes, se tiene que generar un token de acceso por cada usuario/scope
3. Se deben utilizar variables, de esta manera el proyecto esta listo para ingresar esa información y/o cambios que surjan durante el test

Revisa mi información, realiza preguntas antes de realizar un propose, de lo contrario dime si estamos listos para generar un propose.