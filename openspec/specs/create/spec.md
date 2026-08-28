## Purpose

Define el contrato observable de `POST /integrations/gupshup_integrations/templates/create` (`createTemplate`): qué combinaciones de campos produce cada código HTTP, y qué reglas de validación exhibe el endpoint independientemente del contexto de aplicación bajo prueba.

## Requirements

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

### Requirement: Creación exitosa de plantilla
El sistema SHALL responder `200` cuando la plantilla se crea en todas las apps de Gupshup enlistadas, y `206` cuando se crea solo en algunas.

#### Scenario: Éxito total
- **WHEN** todos los campos requeridos son válidos y todas las apps en `apps` aceptan la creación
- **THEN** el sistema responde `200` con `{ code: 200, payload: [...] }`

#### Scenario: Éxito parcial
- **WHEN** la plantilla se crea en algunas apps de `apps` pero falla en otras
- **THEN** el sistema responde `206` con `{ code: 206, success: [...], errors: [...] }`

#### Scenario: Fallo total en Gupshup
- **WHEN** ninguna app de `apps` acepta la creación de la plantilla
- **THEN** el sistema responde `400` con `{ code: 400, errors: [...], message: 'All accounts failed' }`

### Requirement: Validación de campos principales requeridos
El sistema SHALL responder `400` cuando `account_id`, `name`, `category`, `lang` o `apps` están ausentes, vacíos, o no cumplen su formato — y SHALL aceptar la petición cuando todos son válidos.

#### Scenario: account_id ausente
- **WHEN** `account_id` no se envía
- **THEN** el sistema responde `400`

#### Scenario: name fuera del patrón permitido
- **WHEN** `name` contiene mayúsculas, espacios, o caracteres fuera de `[a-z0-9_]`, o su longitud está fuera de 3–179 caracteres
- **THEN** el sistema responde `400`

#### Scenario: category fuera de la lista blanca
- **WHEN** `category` no es exactamente `MARKETING`, `UTILITY` o `AUTHENTICATION`
- **THEN** el sistema responde `400`

#### Scenario: apps no es un arreglo de UUIDs válidos
- **WHEN** `apps` está vacío, ausente, no es un arreglo JSON válido, o contiene un elemento que no es un UUID
- **THEN** el sistema responde `400`

### Requirement: Reglas condicionales de encabezado (type/file/header)
El sistema SHALL exigir `file` cuando `type` es `DOCUMENT`, `IMAGE` o `VIDEO`, SHALL exigir `header` cuando `type` es `TEXT`, y SHALL prohibir ambos cuando `type` está ausente. Cuando `type` es `TEXT`, `header` SHALL tener entre 1 y 60 caracteres, SHALL contener a lo sumo una variable `{{1}}`, y SHALL NOT contener saltos de línea ni 4 o más espacios consecutivos. `header_var` SHALL ser requerido si y solo si `header` contiene esa variable.

#### Scenario: type fuera de la lista blanca
- **WHEN** `type` está presente pero no es `TEXT`, `DOCUMENT`, `IMAGE` ni `VIDEO`
- **THEN** el sistema responde `400`

#### Scenario: Petición válida sin encabezado
- **WHEN** `type`, `file`, `header` y `header_var` están ausentes y el resto de campos requeridos son válidos
- **THEN** el sistema acepta la petición (`200` o `206`)

#### Scenario: header ausente siendo type TEXT
- **WHEN** `type` es `TEXT` y `header` no se envía
- **THEN** el sistema responde `400`

#### Scenario: header válido sin variable no requiere header_var
- **WHEN** `type` es `TEXT` y `header` no contiene ninguna variable `{{1}}`
- **THEN** `header_var` no debe enviarse, y la petición es válida si el resto de campos lo son

#### Scenario: header con variable requiere header_var
- **WHEN** `type` es `TEXT` y `header` contiene la variable `{{1}}`
- **THEN** `header_var` SHALL enviarse con un valor entre 1 y 60 caracteres, o el sistema responde `400`

#### Scenario: header_var presente sin variable en header
- **WHEN** `type` es `TEXT`, `header` no contiene ninguna variable, y `header_var` se envía de todas formas (con cualquier valor, incluido vacío)
- **THEN** el sistema responde `400`

#### Scenario: header fuera de longitud o formato
- **WHEN** `type` es `TEXT` y `header` está vacío, supera 60 caracteres, contiene un salto de línea, contiene 4 o más espacios consecutivos, o contiene dos o más variables
- **THEN** el sistema responde `400`

#### Scenario: header_var fuera de longitud o formato
- **WHEN** `type` es `TEXT`, `header` contiene la variable `{{1}}`, y `header_var` está vacío, supera 60 caracteres, contiene un salto de línea, o contiene 4 o más espacios consecutivos
- **THEN** el sistema responde `400`

### Requirement: Reglas de cuerpo del mensaje (body/body_var)
El sistema SHALL exigir `body` salvo que `category` sea `AUTHENTICATION`, SHALL exigir que la cantidad de variables `{{n}}` en `body` coincida exactamente con la cantidad de elementos de `body_var`, y SHALL rechazar variables fuera de secuencia o repetidas.

#### Scenario: body sin variables no requiere body_var
- **WHEN** `body` no contiene ninguna variable `{{n}}`
- **THEN** `body_var` no debe enviarse, y la petición es válida si el resto de campos lo son

#### Scenario: body con variables requiere body_var del mismo tamaño
- **WHEN** `body` contiene variables secuenciales `{{1}}..{{n}}`
- **THEN** `body_var` SHALL ser un arreglo con exactamente `n` elementos, o el sistema responde `400`

#### Scenario: Variables fuera de secuencia
- **WHEN** las variables de `body` no aparecen en orden `{{1}}, {{2}}, ...` sin huecos ni repeticiones
- **THEN** el sistema responde `400`

### Requirement: Reglas de footer
El sistema SHALL aceptar `footer` opcional entre 1 y 60 caracteres sin variables `{{n}}`, y SHALL responder `400` fuera de ese rango o si contiene una variable.

#### Scenario: footer con variable prohibida
- **WHEN** `footer` contiene una secuencia `{{n}}`
- **THEN** el sistema responde `400`

#### Scenario: footer fuera de longitud
- **WHEN** `footer` tiene más de 60 caracteres
- **THEN** el sistema responde `400`

### Requirement: Reglas de botones (buttons)
El sistema SHALL exigir que los botones estén agrupados por tipo, respetando los máximos por tipo (10 `QUICK_REPLY`, 2 `URL`, 1 `PHONE_NUMBER`) y un máximo total de 10, y SHALL responder `400` si se exceden o si no están agrupados.

#### Scenario: Botones dentro de límites y agrupados
- **WHEN** `buttons` es un arreglo no vacío con botones agrupados por tipo dentro de los máximos por tipo
- **THEN** la petición es válida si el resto de campos lo son

#### Scenario: Botones del mismo tipo intercalados
- **WHEN** los botones de un mismo `type` no están contiguos entre sí en el arreglo
- **THEN** el sistema responde `400`

#### Scenario: Máximo de botones excedido
- **WHEN** el arreglo `buttons` supera 10 elementos en total, o supera el máximo permitido de algún tipo
- **THEN** el sistema responde `400`

### Requirement: Sin espejo de campos entrada→respuesta
El sistema SHALL NOT requerir que ninguna key de la respuesta coincida exactamente con un campo homónimo del request para este endpoint, ya que `docs.md` no declara mirror keys.

#### Scenario: Ninguna key de respuesta se valida por espejo
- **WHEN** se recibe una respuesta de éxito (`200` o `206`)
- **THEN** no se ejecuta ningún assert de espejo entrada→respuesta, porque `docs.md` no declara mirror keys para este endpoint
