## Purpose

Define el comportamiento observable de la generación de reportes de
ejecución de pytest: dónde se escriben, cómo se aíslan entre corridas, y
qué evidencia de la petición HTTP queda registrada por caso de prueba.

## Requirements

### Requirement: Aislamiento de reportes por ejecución
El sistema SHALL escribir el reporte HTML (pytest-html) y el reporte JSON
(pytest-json-report) de cada ejecución de pytest en una carpeta nueva y
distinta de las de ejecuciones anteriores, sin requerir que quien ejecuta
el comando especifique manualmente una ruta distinta cada vez.

#### Scenario: Dos ejecuciones consecutivas no se pisan
- **WHEN** se ejecuta `pytest` una vez y luego se ejecuta `pytest`
  nuevamente sin cambiar ningún argumento de la línea de comandos
- **THEN** existen dos carpetas de reporte distintas bajo `reports/`, cada
  una con su propio `report.html` y `resultados.json`, y ambas siguen
  siendo legibles después de la segunda corrida

#### Scenario: Ruta explícita sigue siendo respetada
- **WHEN** quien ejecuta pytest pasa explícitamente `--html=<ruta>` o
  `--json-report-file=<ruta>`
- **THEN** el reporte se escribe en la ruta indicada, sin que el
  aislamiento automático por carpeta la sobrescriba

### Requirement: Evidencia de request/response en todo caso de prueba
El sistema SHALL adjuntar al reporte HTML, para todo caso de prueba que
haya realizado al menos una petición HTTP — sin importar si terminó en
estado exitoso (`passed`) o fallido (`failed`/`error`) — el cURL de la
última petición HTTP realizada y el status code junto con el body completo
de la última respuesta recibida.

#### Scenario: Caso individual exitoso incluye cURL y respuesta
- **WHEN** un test AAA (`TC-XXX`) termina en `passed`
- **THEN** el reporte HTML de ese caso contiene el bloque de cURL de la
  última request y un bloque con el status code y el body de la última
  response, sin truncar ni redactar su contenido

#### Scenario: Fila exitosa de una matriz incluye cURL y respuesta
- **WHEN** una fila parametrizada de un test de matriz (`V1..Vn`) termina
  en `passed`
- **THEN** el reporte HTML de esa fila parametrizada contiene el mismo
  bloque de cURL y de respuesta que un TC individual exitoso

#### Scenario: Caso fallido también incluye cURL y respuesta
- **WHEN** un caso de prueba (TC o fila de matriz) termina en estado
  distinto de `passed` (`failed`, `error`) y existe una última respuesta
  registrada para ese caso
- **THEN** el reporte HTML contiene el mismo bloque de cURL y de respuesta
  que un caso exitoso, además del detalle de las aserciones de
  `pytest-check` que hayan fallado

#### Scenario: Caso sin petición HTTP no genera bloques vacíos
- **WHEN** un caso de prueba termina en cualquier estado sin haber llegado
  a realizar una petición HTTP (por ejemplo, falla antes del `Act`)
- **THEN** el reporte HTML no contiene bloque de cURL ni de respuesta para
  ese caso
