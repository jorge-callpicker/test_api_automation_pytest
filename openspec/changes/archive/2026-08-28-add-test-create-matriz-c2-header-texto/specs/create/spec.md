## MODIFIED Requirements

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
