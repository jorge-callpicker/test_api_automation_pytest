## Purpose

Define cómo el framework de pruebas genera y conserva la evidencia de cada
ejecución de pytest, para que el QA pueda comparar corridas sucesivas y
auditar manualmente tanto los fallos como los casos exitosos.

## Requirements

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

### Requirement: Evidencia de aserciones individuales en tests TC-XXX
El sistema SHALL documentar en el reporte, para cada test `TC-XXX` ejecutado,
una entrada por cada aserción realizada dentro de ese test (la dura de
status code y cada `pytest_check.check(...)` posterior), indicando su
etiqueta, su resultado (pasó/falló) y su mensaje — independientemente de si
el test en conjunto pasó o falló. Este requirement aplica exclusivamente a
tests `TC-XXX`; los tests de matriz (`test_matriz_*`) mantienen el
comportamiento existente (bloque de fallo solo cuando el test falla).

#### Scenario: TC-XXX exitoso con múltiples aserciones
- **WHEN** un test `TC-XXX` ejecuta varias aserciones y todas pasan
- **THEN** el reporte de ese test incluye una entrada por cada aserción
  ejecutada, mostrando su etiqueta y que su resultado fue exitoso

#### Scenario: TC-XXX fallido con aserciones mixtas
- **WHEN** un test `TC-XXX` ejecuta varias aserciones y al menos una falla
- **THEN** el reporte incluye una entrada por cada aserción ejecutada antes
  del corte del test — tanto las que pasaron como las que fallaron —, con su
  etiqueta, su resultado y, para las fallidas, su mensaje

#### Scenario: Test de matriz no incluye el log de aserciones individuales
- **WHEN** un test de matriz (`test_matriz_*`) ejecuta sus aserciones,
  pase o falle
- **THEN** el reporte de ese test no incluye la tabla de aserciones
  individuales — mantiene el mismo contenido que antes de este change
