## Purpose

Define cómo el framework de pruebas genera y conserva la evidencia de cada
ejecución de pytest, para que el QA pueda comparar corridas sucesivas y
auditar manualmente tanto los fallos como los casos exitosos.

## ADDED Requirements

### Requirement: Carpeta de reporte por ejecución
El sistema SHALL escribir el reporte HTML y el reporte JSON de cada sesión
de pytest dentro de una carpeta nueva bajo `reports/`, nombrada con el
timestamp de inicio de esa sesión, en vez de sobrescribir un reporte fijo
en la raíz de `reports/`.

#### Scenario: Dos ejecuciones consecutivas sin flags explícitos
- **WHEN** el QA ejecuta `pytest` dos veces seguidas sin pasar `--html` ni
  `--json-report-file`
- **THEN** cada ejecución produce su propia carpeta bajo `reports/` con un
  `report.html` y un `resultados.json` propios, y el reporte de la primera
  ejecución sigue existiendo intacto después de la segunda

#### Scenario: QA especifica un path de reporte explícito
- **WHEN** el QA invoca `pytest` pasando `--html` y/o
  `--json-report-file` con un path propio
- **THEN** el sistema respeta esos paths y no los sobrescribe con la
  carpeta calculada automáticamente

### Requirement: Evidencia de request y response en todo caso ejecutado
El sistema SHALL adjuntar al reporte, para cada test ejecutado
independientemente de su resultado (`passed`, `failed` o `skipped`), el
cURL de la última petición HTTP realizada por ese test, y — cuando exista
una respuesta HTTP disponible para esa petición — el código de estado, los
headers y el cuerpo de esa respuesta.

#### Scenario: Test exitoso con una petición HTTP
- **WHEN** un test hace una petición HTTP y todas sus aserciones pasan
- **THEN** el reporte de ese test incluye el cURL de la petición y el
  status/headers/body de la respuesta recibida

#### Scenario: Test fallido con una petición HTTP
- **WHEN** un test hace una petición HTTP y alguna de sus aserciones falla
- **THEN** el reporte de ese test sigue incluyendo el cURL de la petición y
  el status/headers/body de la respuesta recibida, igual que en un caso
  exitoso

#### Scenario: Test sin ninguna petición HTTP
- **WHEN** un test no realiza ninguna petición HTTP antes de finalizar
- **THEN** el reporte de ese test no incluye sección de cURL ni de
  respuesta
