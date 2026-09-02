## Purpose

Define cómo el framework de pruebas obtiene conexiones de base de datos para
aserciones post-request, permitiendo consultar más de un schema del mismo
servidor sin duplicar credenciales de conexión por cada uno.

## ADDED Requirements

### Requirement: Conexión por schema con credenciales compartidas
El sistema SHALL exponer una fixture de conexión de base de datos por cada
schema soportado (`oauth`, `callpicker`, `chat`), reutilizando el mismo host,
puerto, usuario y password de conexión para los tres, y variando únicamente
el nombre del schema al que se conecta cada una.

#### Scenario: Conexión a oauth (comportamiento existente sin cambios)
- **WHEN** un test solicita la fixture `db_conn`
- **THEN** recibe una conexión abierta contra el schema configurado en
  `DB_NAME` (`oauth`), sin requerir ningún cambio en la configuración actual

#### Scenario: Conexión a callpicker
- **WHEN** un test solicita la fixture `db_conn_callpicker`
- **THEN** recibe una conexión abierta contra el schema configurado en
  `DB_NAME_CALLPICKER`, usando el mismo host, puerto, usuario y password que
  `db_conn`

#### Scenario: Conexión a chat
- **WHEN** un test solicita la fixture `db_conn_chat`
- **THEN** recibe una conexión abierta contra el schema configurado en
  `DB_NAME_CHAT`, usando el mismo host, puerto, usuario y password que
  `db_conn`

#### Scenario: Aislamiento de conexión por test
- **WHEN** dos tests distintos solicitan la misma fixture de conexión (por
  ejemplo, ambos `db_conn_callpicker`)
- **THEN** cada uno recibe su propia conexión con scope de función, que se
  cierra al finalizar ese test — igual que el comportamiento actual de
  `db_conn`
