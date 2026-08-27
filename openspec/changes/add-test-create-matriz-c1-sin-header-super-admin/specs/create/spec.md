## MODIFIED Requirements

### Requirement: Autenticación de sesión
El sistema SHALL rechazar la petición con `401 Unauthorized` cuando el header `api-access-token` está ausente, es inválido/expirado, o corresponde a una sesión sin privilegio de cruce de cuentas cuya cuenta no coincide con `account_id`.

#### Scenario: Header de autenticación ausente
- **WHEN** la petición no incluye el header `api-access-token`
- **THEN** el sistema responde `401` con `{ code: 401, message: "Unauthorized" }`

#### Scenario: Token inválido o expirado
- **WHEN** el header `api-access-token` contiene un valor que no corresponde a una sesión vigente
- **THEN** el sistema responde `401`

#### Scenario: account_id no corresponde a la sesión
- **WHEN** `account_id` es una cuenta existente distinta de la asociada a la sesión del token enviado, y el rol de esa sesión no tiene privilegio de operar sobre cuentas ajenas
- **THEN** el sistema responde `401`

#### Scenario: account_id inexistente
- **WHEN** `account_id` es un entero positivo que no corresponde a ninguna cuenta del sistema
- **THEN** el sistema responde `401`, independientemente del rol de la sesión

## ADDED Requirements

### Requirement: Invariancia de la validación de campos respecto al rol
El sistema SHALL aplicar las mismas reglas de validación de campos —formato, longitud, listas blancas, obligatoriedad y validaciones cruzadas— produciendo el mismo código HTTP para una petición idéntica, sea cual sea el rol de la sesión que la emite. Un rol elevado SHALL NOT relajar ninguna validación de campo.

Esta invariante no alcanza a la comprobación de correspondencia entre `account_id` y la cuenta de la sesión, que sí depende del privilegio de cruce de cuentas del rol y está cubierta por el requerimiento *Autenticación de sesión*.

#### Scenario: Petición válida aceptada por igual en todo rol
- **WHEN** una petición con todos los campos requeridos válidos se emite desde una sesión de rol `Admin`, y la misma petición se emite desde una sesión de rol `SuperAdmin` sobre la misma cuenta
- **THEN** el sistema acepta ambas con el mismo código de éxito (`200` o `206`)

#### Scenario: Campo requerido ausente rechazado por igual en todo rol
- **WHEN** una petición omite un campo requerido (`account_id`, `name`, `category`, `lang` o `apps`) y se emite desde sesiones de roles distintos sobre la misma cuenta
- **THEN** el sistema responde `400` en todos los casos

#### Scenario: Campo fuera de formato rechazado por igual en todo rol
- **WHEN** una petición envía un campo que viola su patrón, longitud o lista blanca —por ejemplo `name` con mayúsculas, `category` fuera de la lista blanca, o `apps` con un elemento que no es un UUID— y se emite desde sesiones de roles distintos sobre la misma cuenta
- **THEN** el sistema responde `400` en todos los casos

#### Scenario: Validación cruzada rechazada por igual en todo rol
- **WHEN** una petición viola una regla cruzada —por ejemplo la cantidad de elementos de `body_var` no coincide con la cantidad de variables de `body`, o los botones de un mismo tipo no están agrupados— y se emite desde sesiones de roles distintos sobre la misma cuenta
- **THEN** el sistema responde `400` en todos los casos
