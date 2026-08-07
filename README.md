# Automatización de pruebas de API — OpenSpec + Claude Code

Repositorio de pruebas automatizadas para endpoints de APIs REST del
equipo de QA, construido con [OpenSpec](https://github.com/Fission-AI/OpenSpec)
(Spec-Driven Development) y Claude Code.

Cada endpoint se cubre con dos tipos de change proposal independientes:

- **Un change por cada `TC-XXX`** del `casos-prueba.md` (formato AAA).
- **Un change por cada matriz CSV** (`raiz` + un CSV por objeto anidado)
  que implementa **todas** las columnas del CSV en un solo test
  parametrizado.

La disciplina completa vive en `openspec/config.yaml`. Este README
describe cómo **operar** el repo día a día.

---

## Prerrequisitos

- **Node.js 18+** para la CLI de OpenSpec.
- **Python 3.11+** para el framework de tests.
- **Claude Code** instalado y autenticado.
- Acceso al ambiente de pruebas del API (URL base + token admin) y a
  su base de datos (para aserciones de estado).

Instalación única de la CLI de OpenSpec:

```bash
npm install -g @fission-ai/openspec@latest
```

---

## Estructura del repositorio

```
.
├── .claude/
│   └── settings.json          # Permisos preaprobados para Claude Code
├── openspec/
│   ├── config.yaml            # Contexto y reglas inyectados en cada artefacto
│   ├── specs/                 # Specs por endpoint (crecen con /opsx:archive)
│   └── changes/               # Changes activos + carpeta archive/
├── inputs/
│   └── <endpoint>/            # Artefactos de entrada por endpoint
│       ├── docs.md            # Contrato + sección "Mirror keys en respuesta"
│       ├── matriz-raiz.csv    # Partición de equivalencias (columna = caso)
│       └── casos-prueba.md    # Casos AAA con IDs TC-XXX
├── src/framework/             # Framework de tests (creado por el 1er change)
├── tests/                     # Tests por endpoint (creados por change)
├── docs/
│   └── generators-catalog.md  # Autogenerado desde src/framework/generators.py
├── reports/                   # Reportes HTML/JSON de cada ejecución (git-ignored)
├── variables.yaml             # globals + test_cases + matrix_values
├── .env.example               # Plantilla de secretos y URLs
├── .env                       # Secretos reales (git-ignored)
├── CLAUDE.md                  # Handoff de sesión para Claude Code
└── README.md                  # (este archivo)
```

---

## Setup inicial (una sola vez por clon)

### 1. Clona e inicializa

```bash
git clone <repo>
cd <repo>
openspec init
```

Si `openspec init` detecta que `openspec/config.yaml` ya existe, elige
**"keep existing"**. Solo debe regenerar los archivos de skills para tu
asistente de IA (Claude Code, Cursor, etc).

### 2. Llena secretos

```bash
cp .env.example .env
```

Abre `.env` y reemplaza cada `[REQUIERE RESPUESTA: ...]` con el valor
real del ambiente. **Nunca commitees `.env`** (ya está en `.gitignore`).

### 3. Llena variables versionadas

Abre `variables.yaml` y reemplaza cada `[REQUIERE RESPUESTA: ...]` con
el valor sembrado en el ambiente de pruebas. Antes de cada `TC-XXX` está
la clave `seed:` que describe qué debe existir en la BD. La sección
`matrix_values:` empieza vacía y se poblará al ejecutar el primer change
de matriz.

### 4. Bootstrap del framework — primer change proposal

El repositorio arranca **sin código Python**. El framework se construye
como el primer change de OpenSpec para que quede trazado y versionado.

Abre Claude Code en la raíz del repo y en el chat escribe:

```
/opsx:propose add-test-framework-base
```

Y a continuación pega este prompt exactamente:

<details>
<summary><b>📋 Prompt de bootstrap (clic para expandir)</b></summary>

````
Necesito el bootstrap del framework de automatización de pruebas de APIs
para este repositorio. Este es el PRIMER change proposal y su objetivo es
crear el esqueleto sobre el cual todos los TC y matrices posteriores se
implementarán. Basa todas las decisiones en `openspec/config.yaml`.

# Alcance

Crear:

1. `pyproject.toml` con Python >= 3.11 y las siguientes dependencias
   pinneadas exactas (no usar rangos ni `^`, `~`):

   Runtime:
   - pytest == 9.1.1
   - pytest-html == 4.2.0
   - pytest-check == 2.9.1
   - pytest-json-report == 1.5.0
   - httpx == 0.28.1
   - sqlalchemy == 2.0.51
   - pymysql[rsa] == 1.2.0
   - pydantic == 2.13.4
   - pydantic-settings == 2.14.2
   - PyYAML (última estable menor)

   Dev:
   - ruff == 0.16.1

2. Sección `[tool.pytest.ini_options]` en pyproject.toml con:
   - addopts = "--strict-markers -ra --tb=short"
   - testpaths = ["tests"]
   - Marcadores registrados: tc(id), prioridad(nivel), criticidad(nivel),
     tipo(clase), tecnica(nombre), rol(nombre), impacto(nivel), matriz(nombre).

3. Estructura de carpetas y archivos:
   src/framework/__init__.py
   src/framework/config.py     # pydantic-settings + loader YAML
   src/framework/http.py       # cliente httpx + cURL generator
   src/framework/db.py         # engine SQLAlchemy Core con AUTOCOMMIT
   src/framework/variables.py  # interpolación {{...}} con soporte MTZ-*
   src/framework/matrix.py     # parser CSV `;`, transposición, IDs V/I
   src/framework/generators.py # catálogo de generadores + CLI --catalog
   src/framework/mirror.py     # assert de espejo por key JSON exacta
   src/framework/reannotate.py # script CLI para reanotar la matriz CSV
   tests/__init__.py
   tests/conftest.py           # fixtures compartidos
   docs/                       # carpeta para docs/generators-catalog.md

4. `src/framework/config.py`:
   - Clase `Settings(BaseSettings)` con
     `model_config = SettingsConfigDict(env_file=".env", extra="ignore")`.
   - Campos requeridos: GLB_URL_BASE (str), GLB_TOKEN_ADMIN (str),
     DB_HOST (str), DB_PORT (int), DB_NAME (str), DB_USER (str),
     DB_PASSWORD (str).
   - Función `load_variables() -> dict` que lee `variables.yaml` desde
     la raíz del proyecto y retorna el dict con secciones `globals`,
     `test_cases` y `matrix_values`.

5. `src/framework/variables.py`:
   - Función `resolve(payload, tc_id=None) -> dict | str | list | int` que
     acepta un payload (dict/str/list anidados) y sustituye placeholders
     `{{nombre-var}}`. Orden de resolución según prefijo:
       1. `GLB-*` → primero en `Settings` (guion → underscore, upper); si
          no está, en `variables.yaml → globals`.
       2. `TC-XXX-*` → solo se resuelve si el prefijo `TC-XXX` coincide
          con el `tc_id` pasado; en caso contrario `KeyError` con mensaje
          claro. Fuente: `variables.yaml → test_cases[TC-XXX].variables`.
       3. `MTZ-*` → busca en `variables.yaml → matrix_values`. Si el
          valor es un dict con keys `generator` y `params`, resuelve
          invocando `getattr(framework.generators, generator)(**params)`
          y retorna el valor generado. Si es literal, lo retorna.
   - Detecta placeholders con regex `\{\{([A-Za-z0-9_-]+)\}\}`.
   - Preserva el tipo cuando el placeholder ocupa el string completo
     (ej: `"{{GLB-account_id_valido}}"` → int, no str).
   - Lanza `KeyError` con mensaje claro si una variable no existe. Nunca
     retorna el placeholder sin resolver.

6. `src/framework/http.py`:
   - Función `client(settings) -> httpx.Client` que devuelve un cliente
     síncrono con `base_url=settings.GLB_URL_BASE` y timeout 30s.
   - Función `to_curl(request: httpx.Request) -> str` que construye el
     comando cURL equivalente con headers y body, para logging en fallos.

7. `src/framework/db.py`:
   - Función `engine(settings) -> sqlalchemy.Engine` que construye un
     engine MySQL usando `pymysql`, con `isolation_level="AUTOCOMMIT"`.

8. `src/framework/matrix.py`:
   - Función `load_matrix(path: Path) -> MatrixData` que:
     - Lee un CSV con separador `;`.
     - Valida que existen las filas literales `Resultado` y
       `Código HTTP esperado` (case-sensitive).
     - Detecta las columnas y las clasifica según `Resultado`:
       Éxito → grupo válidos (ids V1..Vn en orden posicional),
       Error  → grupo inválidos (ids I1..In en orden posicional).
   - `MatrixData` es un dataclass/pydantic model que expone
     `cases: list[MatrixCase]` con orden [V1, V2, ..., Vn, I1, I2, ..., In].
   - Cada `MatrixCase` tiene: `id: str` (V1/I3/etc), `fields: dict[str, Any]`
     (por-campo el valor de la celda: literal directo o
     `{ generator, params }`), `expected_status: int`,
     `expected_result: Literal["Éxito", "Error"]`.
   - Método `MatrixData.parametrize_args()` que retorna
     `(argnames, argvalues, ids)` para usar directamente en
     `pytest.mark.parametrize`.

9. `src/framework/generators.py`:
   - Set inicial de funciones (todas con docstring de una línea que
     empieza con la abreviatura entre corchetes, para el catálogo):
     - `int_min(min_val: int) -> int` — `[min] Retorna el valor mínimo permitido.`
     - `int_max(max_val: int) -> int` — `[max] Retorna el valor máximo permitido.`
     - `int_below_min(min_val: int) -> int` — `[outmin] Retorna min_val - 1.`
     - `int_above_max(max_val: int) -> int` — `[outmax] Retorna max_val + 1.`
     - `wrong_type_string(sample: str = "abc") -> str` — `[type] Retorna un string donde se esperaba entero.`
     - `wrong_type_none() -> None` — `[null] Retorna None.`
     - `empty_string() -> str` — `[empty] Retorna cadena vacía.`
     - `regex_violating(regex: str, sample: str = "!!!") -> str` —
       `[regex] Retorna un string que viola el regex dado.`
     - `random_string(length: int) -> str` — `[len_min|len_max|len_outmax] String aleatorio de longitud exacta.`
     - `len_below_min(min_len: int) -> str` — `[len_outmin] String de longitud min_len - 1.`
     - `len_above_max(max_len: int) -> str` — `[len_outmax] String de longitud max_len + 1.`
   - CLI: `python -m framework.generators --catalog` imprime a stdout un
     Markdown con tabla `| Función | Abreviatura | Firma | Descripción |`
     construida por introspección de las funciones del módulo (inspecciona
     nombre, signature, y primer línea del docstring). Redirigir a
     `docs/generators-catalog.md` para persistir.
   - El catálogo NUNCA se edita a mano — su fuente de verdad son los
     docstrings.

10. `src/framework/mirror.py`:
    - Función `assert_mirrored(request_payload: dict, response_json: dict, keys: list[str]) -> None`.
    - Para cada `key` en `keys`:
      - Si `key not in request_payload`: raise `KeyError` (bug del test).
      - Si `key not in response_json`: skip silencioso (la doc declaró
        la key pero la respuesta no la contiene como key JSON).
      - Si ambas presentes: `pytest_check.check(
        request_payload[key] == response_json[key],
        f"mirror {key}: request={request_payload[key]} response={response_json[key]}")`.
    - No hace match por substring bajo ninguna circunstancia.

11. `src/framework/reannotate.py` como script CLI:
    - Uso: `python -m framework.reannotate --matrix <ruta> --results <ruta>`.
    - Lee `resultados.json` (pytest-json-report) y añade/actualiza en el
      CSV las columnas o filas de trazabilidad. Mapeo:
      - Nodeids que contengan `TC-XXX` → columna del CSV con ese TC en la
        fila de trazabilidad (si aplica).
      - Nodeids parametrizados de forma `test_matriz_<nombre>[V<n>]` y
        `[I<n>]` → n-ésima columna del grupo válidos o inválidos del CSV
        correspondiente (por posición).
    - Actualiza `ultimo_resultado` (PASSED/FAILED/SKIPPED) y
      `ultima_ejecucion` (ISO 8601) en cada columna probada.

12. `tests/conftest.py` con fixtures:
    - `settings` (scope=session)
    - `http_client` (scope=session, yield con `.close()` al final)
    - `db_conn` (scope=function, con `.close()` al final)
    - `resolve_payload` (scope=function) → factory que dado un `tc_id`
      retorna un callable equivalente a
      `functools.partial(resolve, tc_id=tc_id)`.
    - Hook `pytest_runtest_makereport` que en caso de fallo adjunta al
      reporte HTML el cURL de la última request (leído de un atributo
      del cliente) y detalles de las aserciones de pytest-check que
      fallaron.

13. Sección `[tool.ruff]` en pyproject.toml con:
    - line-length = 100
    - target-version = "py311"
    - lint.select = ["E", "F", "I", "B", "UP", "SIM", "RUF"]

14. Un smoke test opcional `tests/test_smoke.py` que:
    - Verifica que `Settings()` carga sin excepción (leyendo `.env`).
    - Verifica que `load_variables()` retorna un dict con las tres
      secciones `globals`, `test_cases` y `matrix_values`.
    - Verifica que `matrix.load_matrix` no rompe con un CSV mínimo
      inline (fixtura con StringIO).
    - Verifica que `generators.int_above_max(10) == 11`.
    - NO hace request HTTP ni consulta a BD.
    - Marcado con `@pytest.mark.tc("SMOKE-001")`.

15. Al finalizar la implementación, ejecutar como parte del change:
    `python -m framework.generators --catalog > docs/generators-catalog.md`
    y committear el archivo generado.

# Fuera de alcance

- No implementar ningún test contra endpoints reales. Los TC y matrices
  específicos vendrán en changes posteriores (uno por TC, uno por CSV).
- No hacer llamadas reales a APIs desde este change.
- No modificar `variables.yaml`, `.env.example` ni `openspec/config.yaml`.

# Aceptación

- `pip install -e ".[dev]"` corre sin errores.
- `pytest --collect-only` reporta al menos el smoke test.
- `pytest tests/test_smoke.py -v` pasa (asumiendo `.env` completo).
- `ruff check .` pasa limpio.
- `python -c "from framework.config import Settings, load_variables;
   from framework.variables import resolve;
   from framework.matrix import load_matrix;
   from framework.generators import int_above_max;
   from framework.mirror import assert_mirrored; print('ok')"` imprime `ok`.
- `python -m framework.generators --catalog | head -5` imprime la tabla
  inicial del catálogo.
- `docs/generators-catalog.md` existe y contiene una tabla con al menos
  las 11 funciones del set inicial.
````

</details>

Cuando Claude termine el proposal, revísalo
(`openspec/changes/add-test-framework-base/`), ajusta lo que haga falta y
lanza:

```
/opsx:apply
```

Al terminar, ejecuta manualmente:

```bash
pip install -e ".[dev]"
pytest --collect-only
pytest tests/test_smoke.py -v
ruff check .
python -m framework.generators --catalog > docs/generators-catalog.md
```

Si todo pasa, responde a Claude "framework instalado, todo verde" y él
archivará el change:

```
/opsx:archive
```

Commit:

```bash
git add .
git commit -m "chore: bootstrap framework base (add-test-framework-base)"
```

---

## Añadir un endpoint nuevo

1. Crea `inputs/<endpoint-slug>/` (ej: `inputs/templates-delete/`).
2. Coloca ahí los tres artefactos generados por los skills de
   refinamiento del equipo:
   - `docs.md` (incluyendo la sección `## Mirror keys en respuesta`,
     ver siguiente sección).
   - `matriz-raiz.csv` (+ CSVs anidados si aplica).
   - `casos-prueba.md`.
3. Añade al `variables.yaml`, bajo `test_cases:`, un bloque por cada
   `TC-XXX` del `casos-prueba.md`, con `description`, `seed` y
   `variables` (placeholders `[REQUIERE RESPUESTA: ...]`).
4. Siembra los datos descritos en `seed` en el ambiente de pruebas y
   reemplaza los placeholders por los valores reales.

La sección `matrix_values:` se poblará automáticamente cuando corras el
primer change de matriz para ese endpoint.

---

## Convención en `docs.md`: sección "Mirror keys en respuesta"

Para que el assert de espejo entrada → respuesta funcione, cada `docs.md`
de endpoint incluye una sección obligatoria que declara qué keys del
request se espejan como key JSON **exacta** en la respuesta:

```markdown
## Mirror keys en respuesta

| Key del request | Presente como key JSON en respuesta |
|-----------------|-------------------------------------|
| account_id      | Sí                                  |
| inbox_id        | Sí                                  |
| template_id     | No (solo aparece embebida en `message`) |
```

Reglas:

- Solo las filas con **Sí** se validan. Las de **No** documentan
  explícitamente que aparece embebido en algún string y por diseño
  no se valida (evita match por substring).
- Si la sección no existe o todas las filas dicen **No**, el assert
  de espejo se omite silenciosamente para ese endpoint.
- El nombre de la sección es exacto: `## Mirror keys en respuesta`. El
  parser del framework busca por este encabezado.

---

## Implementar un TC del `.md` AAA (ciclo por caso)

Para cada `TC-XXX` del `casos-prueba.md`, en el chat de Claude Code:

### 1. Propose

```
/opsx:propose add-test-<endpoint-slug>-tc-<nnn>
```

Ejemplo: `/opsx:propose add-test-templates-delete-tc-001`.

Claude lee `inputs/<endpoint>/casos-prueba.md`, encuentra el TC y
genera un proposal con `proposal.md` + `tasks.md` (una tarea por assert
AAA + una tarea final bloqueante de ejecución).

### 2. Revisa

Abre `openspec/changes/add-test-.../proposal.md` y `tasks.md`. Verifica:

- Que las variables listadas existen en `variables.yaml` o `.env.example`.
- Que cada assert del AAA está representado como tarea.
- Que la citación de `CA-XX` / `F1.RNX` corresponde.
- Que no hay literales de negocio en el diseño.

Ajusta directamente los archivos si algo hace falta.

### 3. Apply

```
/opsx:apply
```

Claude genera `tests/<endpoint>/test_tc_<nnn>.py`.

### 4. Ejecuta manualmente

```bash
pytest --stepwise -k "TC-001" -v \
    --html=reports/report.html --self-contained-html \
    --json-report --json-report-file=reports/resultados.json
```

### 5. Retroalimenta

Pega la salida en el chat. Tres escenarios:

- **Pasó**: `TC-001 pasó, todo verde`.
- **Falló el test**: pega el traceback completo.
- **Bloqueo del ambiente**: describe el problema (Claude no tocará el test).

### 6. Archive y commit

```
/opsx:archive
```

```bash
git add openspec/changes/archive/add-test-... tests/... variables.yaml
git commit -m "test(<endpoint>): implementa TC-XXX"
```

---

## Implementar la matriz de un endpoint (un change por CSV)

Todos los casos de una matriz CSV se implementan en un solo change
proposal como un único test parametrizado. En el chat de Claude Code:

### 1. Propose

```
/opsx:propose add-test-<endpoint-slug>-matriz-<nombre>
```

Ejemplos:

- `/opsx:propose add-test-templates-delete-matriz-raiz`
- Si hay anidados: adicionalmente
  `/opsx:propose add-test-templates-create-matriz-body`

Claude:

1. Lee `inputs/<endpoint>/matriz-<nombre>.csv` (separador `;`) y lo
   transpone (columna → caso).
2. Por cada celda:
   - Si es literal → propone variable `MTZ-<endpoint>-<campo>-<abrev>`
     en `variables.yaml → matrix_values:` con la indicación original
     entre paréntesis como comentario.
   - Si es indicación entre paréntesis → escoge resolución estática
     (default) o generador runtime. Si añade un generador nuevo, lo
     registra en `src/framework/generators.py` con docstring y regenera
     `docs/generators-catalog.md`.
3. Lee `inputs/<endpoint>/docs.md § Mirror keys en respuesta` y lista
   las keys aplicables en el proposal.
4. Genera proposal + tasks (transponer, resolver variables, invocar
   mirror en casos de éxito, ejecutar con `-x`).

### 2. Revisa

Abre `openspec/changes/add-test-.../proposal.md`. Verifica:

- Que las variables `MTZ-*` propuestas cubran todas las celdas del CSV.
- Que las abreviaturas correspondan al catálogo fijo (`min`, `outmax`,
  etc.) o tengan comentario justificando una novedosa.
- Que las mirror keys correspondan a `docs.md`.
- Que ningún generador nuevo se añada sin tarea de regenerar el catálogo.

Ajusta los archivos si algo hace falta antes de aplicar.

### 3. Apply

```
/opsx:apply
```

Claude genera:

- `tests/<endpoint>/test_matriz_<nombre>.py` — único test parametrizado
  con ids `V1..Vn` e `I1..In`.
- Entradas nuevas en `variables.yaml → matrix_values:` con placeholders
  `[REQUIERE RESPUESTA: ...]` donde el valor concreto lo deba llenar
  el QA.
- Si aplica, generador nuevo en `src/framework/generators.py` +
  `docs/generators-catalog.md` regenerado.

**Antes de ejecutar**, revisa `variables.yaml → matrix_values:` y llena
cada `[REQUIERE RESPUESTA: ...]` que haya quedado.

### 4. Ejecuta manualmente

Comando específico de matriz — la bandera `-x` es **obligatoria** para
fail-fast al primer error:

```bash
pytest --stepwise -x -k "matriz-<nombre>" -v \
    --html=reports/report.html --self-contained-html \
    --json-report --json-report-file=reports/resultados.json
```

### 5. Retroalimenta

Tres escenarios:

- **Todas las columnas pasan**: `matriz-<nombre>: N/N columnas verdes`.
  Procede a `/opsx:archive`.
- **Corta en la columna N**: pega el traceback del caso `[V<n>]` o
  `[I<n>]` específico. Claude analiza si es bug del test, dato faltante
  en `variables.yaml`, o discrepancia real del endpoint. Si es
  discrepancia real, se documenta como hallazgo — **no se "arregla" el
  test para pasar**.
- **Bloqueo del ambiente**: descripción del problema. Claude no toca
  el test.

Si Claude corrige, repite paso 4.

### 6. Archive y commit

```
/opsx:archive
```

```bash
git add openspec/changes/archive/add-test-... tests/... variables.yaml \
        src/framework/generators.py docs/generators-catalog.md
git commit -m "test(<endpoint>): implementa matriz-<nombre>"
```

---

## Reanotar la matriz CSV con resultados

Tras cada corrida:

```bash
python -m framework.reannotate \
    --matrix inputs/<endpoint>/matriz-<nombre>.csv \
    --results reports/resultados.json
```

El script mapea:

- Nodeids con `TC-XXX` → columna del CSV con ese TC (si la matriz tiene
  fila de trazabilidad a TC).
- Nodeids parametrizados `test_matriz_<nombre>[V<n>]` → n-ésima columna
  de válidos del CSV correspondiente.
- Nodeids parametrizados `test_matriz_<nombre>[I<n>]` → n-ésima columna
  de inválidos.

Añade/actualiza `ultimo_resultado` y `ultima_ejecucion` por columna.
Commit por separado, no mezclar con implementación.

---

## Convenciones no negociables

- **1 change proposal = 1 unidad codificable**:
  - Un TC del `.md` → un change (`add-test-...-tc-<nnn>`).
  - Una matriz CSV → un change (`add-test-...-matriz-<nombre>`).
- **Cero literales de negocio en tests**. Todo pasa por `{{...}}`.
- **Prefijos**: `GLB-*` global, `TC-XXX-*` exclusivo del caso,
  `MTZ-<endpoint>-<campo>-<abrev>` exclusivo de matriz.
- **Soft assertions**: `pytest_check.check(...)` en todas las
  validaciones salvo la primera (status code HTTP), que sí es `assert`
  duro.
- **BD**: SQLAlchemy Core con AUTOCOMMIT. No transacciones desde tests.
- **Matriz siempre con `-x`**. Sin excepción.
- **Assert de espejo solo por key JSON exacta**. Sin substring matching.
- **`docs/generators-catalog.md` nunca se edita a mano**. Se regenera
  con `python -m framework.generators --catalog`.
- **Claude NUNCA ejecuta pytest** contra el ambiente. Tú ejecutas.

---

## Troubleshooting

**Claude intenta ejecutar pytest**: recuérdale `CLAUDE.md`. Bloquea.

**Variable no resuelve en runtime**: verifica prefijo (`GLB-` /
`TC-XXX-` / `MTZ-`), que esté en la sección correcta de `variables.yaml`
o `.env`, y — si es `TC-XXX-*` — que el `tc_id` del test coincida con
el prefijo `TC-XXX-` de la variable.

**Test pasa pero la matriz no se reanota**: la corrida requiere los
flags `--json-report --json-report-file=reports/resultados.json`.

**OpenSpec no reconoce `config.yaml`**: valida sintaxis YAML con
`python -c "import yaml; yaml.safe_load(open('openspec/config.yaml'))"`.

**Placeholder `[REQUIERE RESPUESTA: ...]` en runtime**: no llenaste
`variables.yaml` o `.env` completo. El framework debe fallar con
mensaje claro; si no, es un bug del cargador de variables.

**Matriz falla en la primera columna sin razón aparente**: revisa la
sección `Mirror keys en respuesta` de `docs.md` — probablemente hay una
key declarada como `Sí` que la respuesta real no incluye como key JSON.

**Generador nuevo no aparece en el catálogo**: no se regeneró
`docs/generators-catalog.md`. Ejecuta manualmente:
`python -m framework.generators --catalog > docs/generators-catalog.md`.

---

## Referencias

- OpenSpec (Fission-AI): https://github.com/Fission-AI/OpenSpec
- Claude Code: https://docs.claude.com/en/docs/claude-code
- pytest: https://docs.pytest.org
- pytest-check (soft asserts): https://github.com/okken/pytest-check
- httpx: https://www.python-httpx.org
- SQLAlchemy Core: https://docs.sqlalchemy.org/en/20/core/
- pydantic-settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
