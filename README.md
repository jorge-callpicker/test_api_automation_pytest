# Automatización de pruebas de API — OpenSpec + Claude Code

Repositorio de pruebas automatizadas para endpoints de APIs REST del
equipo de QA, construido con [OpenSpec](https://github.com/Fission-AI/OpenSpec)
(Spec-Driven Development) y Claude Code.

Cada caso de prueba (`TC-XXX`) se implementa como un change proposal
independiente. La disciplina completa vive en `openspec/config.yaml` —
este README describe cómo **operar** el repo día a día.

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
│       ├── docs.md            # Documentación del endpoint
│       ├── matriz-raiz.csv    # Partición de equivalencias + valores límite
│       └── casos-prueba.md    # Casos AAA con IDs TC-XXX
├── src/framework/             # Framework de tests (creado por el 1er change)
├── tests/                     # Tests por endpoint (creados por change por TC)
├── reports/                   # Reportes HTML/JSON de cada ejecución (git-ignored)
├── variables.yaml             # Variables no sensibles versionadas
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
la clave `seed:` que describe qué debe existir en la BD.

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
crear el esqueleto sobre el cual todos los TC posteriores se
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
     tipo(clase), tecnica(nombre), rol(nombre), impacto(nivel).

3. Estructura de carpetas y archivos:
   src/framework/__init__.py
   src/framework/config.py     # pydantic-settings + loader YAML
   src/framework/http.py       # cliente httpx + cURL generator
   src/framework/db.py         # engine SQLAlchemy Core con AUTOCOMMIT
   src/framework/variables.py  # interpolación {{...}} en dicts/strings
   src/framework/reannotate.py # script CLI para reanotar la matriz CSV
   tests/__init__.py
   tests/conftest.py           # fixtures compartidos

4. `src/framework/config.py`:
   - Clase `Settings(BaseSettings)` con
     `model_config = SettingsConfigDict(env_file=".env", extra="ignore")`.
   - Campos requeridos: GLB_URL_BASE (str), GLB_TOKEN_ADMIN (str),
     DB_HOST (str), DB_PORT (int), DB_NAME (str), DB_USER (str),
     DB_PASSWORD (str).
   - Función `load_variables() -> dict` que lee `variables.yaml` desde
     la raíz del proyecto y retorna el dict con secciones `globals` y
     `test_cases`.

5. `src/framework/variables.py`:
   - Función `resolve(payload, tc_id) -> dict | str | list` que acepta
     un payload (dict/str/list anidados) y sustituye placeholders
     `{{nombre-var}}`. Orden de resolución:
       1. Si el nombre empieza con `GLB-` → busca primero en `Settings`
          (aplicando la regla: guion → underscore, upper); si no está,
          en `variables.yaml → globals`.
       2. Si el nombre empieza con `TC-XXX-` → solo se resuelve si el
          prefijo `TC-XXX` coincide con el `tc_id` pasado; en caso
          contrario `KeyError` con mensaje claro.
   - Detecta placeholders con regex `\{\{([A-Za-z0-9_-]+)\}\}`.
   - Preserva el tipo cuando el placeholder ocupa el string completo
     (ej: `"{{GLB-account_id_valido}}"` → int, no str).

6. `src/framework/http.py`:
   - Función `client(settings) -> httpx.Client` que devuelve un cliente
     síncrono con `base_url=settings.GLB_URL_BASE` y timeout 30s.
   - Función `to_curl(request: httpx.Request) -> str` que construye el
     comando cURL equivalente con headers y body, para logging en fallos.

7. `src/framework/db.py`:
   - Función `engine(settings) -> sqlalchemy.Engine` que construye un
     engine MySQL usando `pymysql`, con
     `isolation_level="AUTOCOMMIT"`.

8. `tests/conftest.py` con fixtures:
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

9. `src/framework/reannotate.py` como script CLI:
   - Uso: `python -m framework.reannotate --matrix <ruta> --results <ruta>`
   - Lee `resultados.json` (pytest-json-report) y añade/actualiza en el
     CSV las columnas `ultimo_resultado` (PASSED/FAILED/SKIPPED) y
     `ultima_ejecucion` (ISO 8601). El matching es por columna `TC` o
     `id` del CSV contra los nodeids que contengan `TC-XXX`.

10. Sección `[tool.ruff]` en pyproject.toml con:
    - line-length = 100
    - target-version = "py311"
    - lint.select = ["E", "F", "I", "B", "UP", "SIM", "RUF"]

11. Un smoke test opcional `tests/test_smoke.py` que:
    - Verifica que `Settings()` carga sin excepción (leyendo `.env`).
    - Verifica que `load_variables()` retorna un dict con `globals` y
      `test_cases`.
    - NO hace request HTTP ni consulta a BD.
    - Marcado con `@pytest.mark.tc("SMOKE-001")`.

# Fuera de alcance

- No implementar ningún `test_<endpoint>_<tc>.py`. Los TC específicos
  vendrán en changes posteriores (uno por TC).
- No hacer llamadas reales a APIs desde este change.
- No modificar `variables.yaml`, `.env.example` ni `openspec/config.yaml`.

# Aceptación

- `pip install -e ".[dev]"` corre sin errores.
- `pytest --collect-only` reporta al menos el smoke test.
- `pytest tests/test_smoke.py -v` pasa (asumiendo `.env` completo).
- `ruff check .` pasa limpio.
- `python -c "from framework.config import Settings, load_variables;
   from framework.variables import resolve; print('ok')"` imprime `ok`.
````

</details>

Cuando Claude termine el proposal, revísalo (`openspec/changes/add-test-framework-base/`),
ajusta lo que haga falta y lanza:

```
/opsx:apply
```

Al terminar, ejecuta manualmente:

```bash
pip install -e ".[dev]"
pytest --collect-only
pytest tests/test_smoke.py -v
ruff check .
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
   - `docs.md`
   - `matriz-raiz.csv` (+ CSVs anidados si aplica)
   - `casos-prueba.md`
3. Añade al `variables.yaml`, bajo `test_cases:`, un bloque por cada
   `TC-XXX` del `casos-prueba.md`, con `description`, `seed` y
   `variables` (placeholders `[REQUIERE RESPUESTA: ...]`).
4. Siembra los datos descritos en `seed` en el ambiente de pruebas y
   reemplaza los placeholders por los valores reales.

---

## Implementar un TC (ciclo por caso)

Para cada `TC-XXX` del endpoint, en el chat de Claude Code:

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

Claude te dará un comando exacto. Típicamente:

```bash
pytest --stepwise -k "TC-001" -v \
    --html=reports/report.html --self-contained-html \
    --json-report --json-report-file=reports/resultados.json
```

### 5. Retroalimenta

Pega la salida de pytest en el chat. Tres escenarios:

- **Pasó**: `TC-001 pasó, todo verde`.
- **Falló el test**: pega el traceback completo. Claude analizará y
  propondrá corrección.
- **Bloqueo del ambiente**: describe el problema. Claude NO tocará el
  test; sugerirá pasos para desbloquear.

Si Claude corrige, repite el paso 4.

### 6. Archive y commit

Cuando el test pase:

```
/opsx:archive
```

Y luego:

```bash
git add openspec/changes/archive/add-test-... tests/... variables.yaml
git commit -m "test(<endpoint>): implementa TC-XXX"
```

---

## Reanotar la matriz CSV con resultados

Tras cada corrida:

```bash
python -m framework.reannotate \
    --matrix inputs/<endpoint>/matriz-raiz.csv \
    --results reports/resultados.json
```

Se añaden/actualizan las columnas `ultimo_resultado` y `ultima_ejecucion`
en el CSV. Commit por separado, no mezclar con implementación de TC.

---

## Convenciones no negociables

- **1 change proposal = 1 `TC-XXX`**. No agrupar.
- **Cero literales de negocio en tests**. Todo pasa por `{{...}}`.
- **Prefijos**: `GLB-*` global, `TC-XXX-*` exclusivo del caso.
- **Soft assertions**: `pytest_check.check(...)` en todas las
  validaciones salvo la primera (status code HTTP), que sí es `assert`
  duro.
- **BD**: SQLAlchemy Core con AUTOCOMMIT. No transacciones desde tests.
- **Claude NUNCA ejecuta pytest** contra el ambiente. Tú ejecutas.

---

## Troubleshooting

**Claude intenta ejecutar pytest**: recuérdale `CLAUDE.md`. Bloquea.

**Variable no resuelve en runtime**: verifica prefijo (`GLB-` vs
`TC-XXX-`), que esté en `variables.yaml` o `.env`, y que el `tc_id` del
test coincida con el prefijo `TC-XXX-` de la variable.

**Test pasa pero la matriz no se reanota**: la corrida requiere los
flags `--json-report --json-report-file=reports/resultados.json`.

**OpenSpec no reconoce `config.yaml`**: valida sintaxis YAML con
`python -c "import yaml; yaml.safe_load(open('openspec/config.yaml'))"`.

**Placeholder `[REQUIERE RESPUESTA: ...]` en runtime**: no llenaste
`variables.yaml` o `.env` completo. El framework debe fallar con
mensaje claro; si no, es un bug del cargador de variables.

---

## Referencias

- OpenSpec (Fission-AI): https://github.com/Fission-AI/OpenSpec
- Claude Code: https://docs.claude.com/en/docs/claude-code
- pytest: https://docs.pytest.org
- pytest-check (soft asserts): https://github.com/okken/pytest-check
- httpx: https://www.python-httpx.org
- SQLAlchemy Core: https://docs.sqlalchemy.org/en/20/core/
- pydantic-settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
