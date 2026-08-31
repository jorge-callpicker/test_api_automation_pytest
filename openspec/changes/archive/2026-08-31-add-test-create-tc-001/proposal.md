## Why

**Tipo de change: TC** (`add-test-<endpoint>-tc-<nnn>`), sobre `TC-001` de
`inputs/Create/casos-de-prueba.md` ("Creación mono-app sin encabezado
(Marketing)"). Es el **primer change tipo TC de todo el repo** — hasta ahora
solo se habían implementado changes de matriz (`c1-sin-header`,
`c2-header-texto`) sobre este mismo endpoint (`createTemplate`, slug corto
`create`).

**Rol: `Admin`**, tal como lo fija el propio TC-001. No hay una variante
`SuperAdmin` de este caso en `casos-de-prueba.md` (a diferencia de TC-002,
que ya nace como Super admin), así que este change no tiene hermano de rol.

**Requerimiento validado**: `CA01`, `RN.GEN2`, `F3.RN1`, `INT.RN4`,
`AUTH.RN2`, `F8.RN1` (citados tal como aparecen en TC-001).

**Decisiones tomadas durante exploración previa** (ver conversación de
`/opsx:explore`), todas ya reflejadas en los artefactos de entrada:

1. **Auth**: el TC-001 original pedía un header con token fijo
   (`{{GLB-token_admin}}`). Se descarta esa redacción a favor del mecanismo
   ya construido y usado por los dos changes de matriz:
   `auth.obtain_session_tokens("Admin", account_id=..., settings=...,
   http_client=...)` (login + selectAccount en vivo contra `USR_ADMIN` /
   `PSW_ADMIN`). `GLB_TOKEN_ADMIN` queda sin consumidor.
2. **Assert de auditoría**: el Assert 3 original pedía lectura directa de
   una BD `chat`/tabla `audits` que el framework nunca configuró (solo hay
   una conexión de BD, la de `oauth`). El QA corrigió `casos-de-prueba.md`
   durante la exploración: el Assert 3 ahora es `[API log Chatwot]` y usa
   exactamente el mecanismo que ya existe en `framework/audit_logs.py`
   (`find_audit_log` contra `GET /api/v1/accounts/{account_id}/audit_logs`),
   el mismo patrón que TC-002 en adelante.
3. **Assert de BD (`oauth.templates_gupshup`)**: primer consumidor real del
   fixture `db_conn` de `tests/conftest.py` (existía desde antes, sin
   ningún test que lo usara). Columnas verificadas contra el esquema real
   que el QA agregó a la sección "Bases de datos utilizadas" de `docs.md`:
   `app_id`, `account_id`, `template_code_name`, `languageCode`,
   `category` — todas presentes tal cual en `templates_gupshup`.
4. **Unicidad de `name`** (`docs.md`, Nota2: "El campo name debe ser siempre
   diferente en cada petición nueva"): en vez de declarar
   `TC-001-nombre_plantilla` como variable estática en `variables.yaml`, el
   propio archivo de test la calcula en Python llamando directamente a
   `framework.generators.unique_lowercase(length=8)` y concatenando el
   prefijo `tc_1_` (→ `tc_1_<8 caracteres>`, 13 caracteres totales, dentro
   del rango 3–179 de `name`). El prefijo permite identificar en BD/ambiente
   qué plantillas nacieron de este caso específico.

   **Excepción documentada a la convención de variables**: `openspec/config.yaml`
   declara que todo dato dinámico sale de exactamente cuatro fuentes
   (`.env`, `globals`, `test_cases.TC-XXX`, `matrix_values`), todas resueltas
   vía `variables.resolve()`. Este es el primer valor de un test que no nace
   de ninguna de esas cuatro fuentes: se decidió así, a pedido explícito del
   QA, para no tocar `src/framework/generators.py` ni `src/framework/variables.py`
   — ni el generador ni el resolver de variables `TC-*` cambian. La
   alternativa (extender `_resolve_name` en `variables.py` para que `TC-*`
   acepte la misma forma `{generator, params}` que ya soporta `MTZ-*`) queda
   descartada para este change por ser una decisión de framework reutilizable
   que el QA prefirió no tomar todavía.
5. **Variables `{{GLB-account_id_sesion}}` / `{{GLB-app_id_activo_1}}`** del
   TC-001 original: no existen con ese nombre literal en `variables.yaml`.
   Se mapean, sin crear alias nuevos, a las ya sembradas
   `GLB-account_id_valido` (65) y `GLB-create-app_id_valido` (mismas que
   usan `c1`/`c2`).
6. **Nombre de archivo**: `test_tc_001_creacion_mono_app_sin_encabezado.py`
   se acorta a `tests/test_create_tc_001.py` (`test_create_tc_001` la
   función) — habrá varios endpoints y varios TC, y el nombre largo no
   escala. `tests/__init__.py` existe (paquete Python), así que el nombre
   debe ser un identificador válido: guion bajo, nunca guion.
7. **Aislamiento del reporte**: el Assert 3 (auditoría) hace una petición
   HTTP adicional después de la petición al endpoint bajo prueba. Si
   reutilizara el `http_client` de la fixture, el hook
   `pytest_runtest_makereport` de `conftest.py` — que toma
   `http_client.last_request`/`last_response` al terminar el test —
   registraría en el reporte la petición a Chatwoot (auditoría) en vez de
   la petición a Plantillas, que es la que interesa observar (lo que
   estamos probando es el API de Plantillas, no el de auditoría). Se
   resuelve con un `httpx.Client()` plano, sin los event hooks de
   `framework.http.client()`, instanciado solo en este archivo de test
   exclusivamente para la llamada de verificación a `audit_logs` — cero
   cambios en `framework/http.py`, `audit_logs.py` ni `conftest.py`.
8. **Corrección de convención descubierta**: verificado empíricamente
   (`pytest --collect-only -k "SMOKE-003"` contra
   `tests/test_smoke_audit_logs.py`, que ya usa
   `@pytest.mark.tc("SMOKE-003")`) que `-k` compara contra el node id
   (ruta + función + parámetros), nunca contra el argumento de un
   marcador custom — el resultado fue **0 tests seleccionados**. El
   comando de ejecución para TC individual que documenta
   `openspec/config.yaml` (`pytest --stepwise -k "TC-001" -v`) selecciona
   cero tests tal como está escrito, porque ningún identificador Python
   puede llevar el guion de "TC-001" — la misma limitación que
   `config.yaml` ya reconoce para matrices ("el patrón de `-k` usa guion
   bajo, no el sufijo con guiones") nunca se extendió al comando de TC
   individual. Como TC-001 es el primer change tipo TC del repo, es la
   primera vez que esto se pone a prueba. Se corrige el ejemplo de
   `openspec/config.yaml` como tarea de este change (ver `tasks.md`), y
   este change usa `pytest --stepwise -k "create_tc_001" -v` (coincide con
   el nombre de archivo/función de la decisión 6, y evita colisión con un
   futuro `TC-001` de otro endpoint).

## What Changes

- Añade `tests/test_create_tc_001.py` con `test_create_tc_001`, marcado
  `@pytest.mark.tc("TC-001")` (mismo marcador que ya usa
  `tests/test_smoke_audit_logs.py`; el marcador documenta la trazabilidad
  aunque `-k` no pueda usarlo para seleccionar el test — ver decisión 8).
- Construye la petición base de `docs.md` (form-data) con
  `account_id`, `name`, `category=MARKETING`, `lang=en_US`, `apps` (una sola
  app), `body` con una variable `{{1}}`, `body_var` con un elemento — sin
  `type`/`header`/`header_var`/`file` (contexto "sin encabezado", como
  `c1-sin-header`).
- Autentica con `auth.obtain_session_tokens("Admin", account_id=..., ...)`.
- Assert 1 (duro): `status == 200`, `payload[0].app_id ==
  {{GLB-create-app_id_valido}}` (soft para el resto del objeto `template`).
- Assert 2 (soft, `pytest_check.check`): vía `db_conn`, existe una fila en
  `oauth.templates_gupshup` con `app_id`, `account_id`,
  `template_code_name = name generado`, `languageCode = en_US`,
  `category = MARKETING`.
- Assert 3 (soft): vía `framework.audit_logs.find_audit_log`, existe un
  registro con `auditable_type = "Template"`, `source = "admin_chat"`,
  `associated_id = account_id`, y `comment` que referencia el `name`
  generado (patrón `Se creó la plantilla {name} (#{template_id})...`, sin
  fijar `template_id`/`inbox_name`/`inbox_id` que son valores runtime).
  Usa un `httpx.Client()` propio, distinto del `http_client` de la
  fixture, para no pisar en el reporte la petición al endpoint bajo
  prueba (ver decisión 7).
- Variables nuevas en `variables.yaml → test_cases.TC-001.variables:`:
  - `TC-001-body_var_ejemplo`: valor literal típico para `body_var[0]`
    (Ruta 1 estática).
  - **`TC-001-nombre_plantilla` NO se declara aquí** — ver "Excepción
    documentada" en `Why`; se calcula en el propio test.
- Variables `{{GLB-*}}` reutilizadas sin cambio: `GLB-account_id_valido`,
  `GLB-create-app_id_valido`. Cero variables `GLB-*` nuevas.
- **Cero cambios en `src/framework/`.** No se toca `generators.py` (se
  invoca `unique_lowercase` tal como está) ni `variables.py`.
- No se sigue el freno duro de "módulos pendientes": no aplica ninguna ruta
  runtime nueva sobre `MTZ-*` (este change no usa `matrix_values`) ni hay
  mirror keys (`docs.md` declara "No hay campos que validar en esta
  sección").
- Sin limpieza automatizada post-corrida: `docs.md` no documenta un
  endpoint de borrado de templates; la nota de "limpieza posterior" del
  TC-001 queda fuera de alcance (`"si el entorno lo permite"`, condicional).

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `create`: se agregan dos requerimientos nuevos que hoy no tiene la spec
  — ambos son comportamiento observable ejercitado por primera vez por un
  TC (los changes de matriz solo cubrían el contrato de respuesta HTTP, no
  los efectos secundarios de una creación exitosa):
  - **Persistencia local de la plantilla creada**: al crear exitosamente,
    el sistema registra una fila en `oauth.templates_gupshup` asociada a
    `app_id`/`account_id` con los datos de la petición.
  - **Registro de auditoría en creación exitosa**: al crear exitosamente,
    el sistema genera una entrada de auditoría (visible vía
    `GET /audit_logs` de Chatwoot) con `auditable_type=Template`,
    `source=admin_chat`, `associated_id=account_id` y un `comment`
    trazable al template creado.

## Impact

- **Código nuevo**: `tests/test_create_tc_001.py`. Sin cambios en
  `src/framework/`.
- `openspec/config.yaml` — corrige el ejemplo de comando de ejecución para
  TC individual (de `-k "TC-001"`, que selecciona 0 tests, a la forma con
  guion bajo). Cambio de documentación de convención, no de comportamiento
  de ningún test existente.
- `variables.yaml` — 1 entrada nueva en `test_cases.TC-001.variables:`
  (`TC-001-body_var_ejemplo`). Cero entradas nuevas en `globals:` ni en
  `matrix_values:`.
- `openspec/specs/create/spec.md` — 2 requerimientos nuevos (ver
  Capabilities).
- **Ambiente**: cada corrida crea 1 plantilla nueva en la cuenta `65`, con
  `name` prefijado `tc_1_` para trazabilidad, sin colisión con las que crean
  `c1`/`c2`. No se limpia automáticamente (sin endpoint de borrado
  documentado).
- **Primeros consumidores reales** en este repo: el fixture `db_conn`
  (asserts de BD) y el marcador `@pytest.mark.tc` fuera de un smoke test.

### Non-Goals

- No se implementa el rol `SuperAdmin` para este TC (no existe esa variante
  en `casos-de-prueba.md`).
- No se extiende `variables.py`/`generators.py` para que `TC-XXX-*` soporte
  generadores declarativos — queda como decisión pendiente si un futuro
  change lo necesita (ver "Excepción documentada" en `Why`).
- No se implementan los TC-002 en adelante ni las matrices restantes de
  `inputs/Create/`.
