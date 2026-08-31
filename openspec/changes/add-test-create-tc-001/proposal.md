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

## What Changes

- Añade `tests/test_tc_001_creacion_mono_app_sin_encabezado.py` con
  `test_tc_001_creacion_mono_app_sin_encabezado`, marcado
  `@pytest.mark.tc("TC-001")` (mismo marcador que ya usa
  `tests/test_smoke_audit_logs.py`).
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

- **Código nuevo**: `tests/test_tc_001_creacion_mono_app_sin_encabezado.py`.
  Sin cambios en `src/framework/`.
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
