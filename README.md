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
- **Python 3.11+** para el framework de tests — o **Docker**, como
  alternativa si Python no está disponible o no se ejecuta
  correctamente en tu máquina (ver [Ejecutar con Docker](#ejecutar-con-docker)).
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
├── .gitignore                 # Reglas de exclusión de git
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
├── Dockerfile                 # Imagen alternativa a instalar Python local
├── .dockerignore              # Exclusiones del build context (secretos, .venv, etc.)
├── pyproject.toml             # Dependencias y config de pytest/ruff
├── variables.yaml             # Variables no sensibles versionadas
├── env.example                # Plantilla de secretos y URLs
├── .env                       # Secretos reales (git-ignored)
├── CLAUDE.md                  # Handoff de sesión para Claude Code
└── README.md                  # (este archivo)
```

---

## Setup inicial (una sola vez por clon)

El framework (`pyproject.toml`, `src/framework/`, `tests/conftest.py`)
ya está versionado en el repo — no hay que generarlo, solo instalarlo.

### 1. Clona el repositorio

```bash
git clone <repo>
cd <repo>
```

Si es la primera vez que usas OpenSpec en esta máquina, instala la CLI
(ver Prerrequisitos) y corre `openspec init`. Si detecta que
`openspec/config.yaml` ya existe, elige **"keep existing"** — solo
regenerará los archivos de skills para tu asistente de IA si faltan
(en este repo ya están versionados en `.claude/`).

### 2. Crea el entorno virtual e instala dependencias

Usa siempre un entorno virtual — nunca instales el stack pinneado sobre
el Python global de tu máquina.

```bash
python -m venv .venv
```

Actívalo:

```powershell
# PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# Git Bash
source .venv/Scripts/activate
```

Con el entorno activo (verás el prefijo `(.venv)` en el prompt), instala
el proyecto en modo editable con las dependencias de runtime y dev:

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### 3. Llena secretos

```bash
cp env.example .env
```

Abre `.env` y reemplaza cada `[REQUIERE RESPUESTA: ...]` con el valor
real del ambiente (URL base, token admin, credenciales de BD). **Nunca
commitees `.env`** (ya está en `.gitignore`).

### 4. Llena variables versionadas

Abre `variables.yaml` y reemplaza cada `[REQUIERE RESPUESTA: ...]` con
el valor sembrado en el ambiente de pruebas. Antes de cada `TC-XXX` está
la clave `seed:` que describe qué debe existir en la BD. La sección
`matrix_values:` empieza vacía y se poblará al ejecutar el primer change
de matriz.

### 5. Verifica la instalación

Con el entorno virtual activo y `.env` completo:

```bash
pytest --collect-only
pytest tests/test_smoke.py -v
ruff check .
python -m framework.generators --catalog > docs/generators-catalog.md
```

Los tres deben pasar en verde. Si algo falla, revisa
[Troubleshooting](#troubleshooting).

> **Nota histórica**: el framework se construyó como el primer change
> proposal de OpenSpec (`add-test-framework-base`), para quedar trazado
> y versionado en vez de venir precargado. El proposal, su design.md y
> tasks.md quedaron archivados en
> `openspec/changes/archive/2026-08-06-add-test-framework-base/` — no
> necesitas volver a ejecutarlo en un clon nuevo; solo instalar y
> configurar como arriba.

---

## Ejecutar con Docker

Alternativa al setup con `venv` (pasos 1-2 de arriba) si Python 3.11+
no está instalado o no se ejecuta correctamente en tu máquina. El
contenedor **no usa `venv`** — instala el stack directamente en su
Python de sistema, ya que el propio contenedor es el aislamiento.

Los pasos 3 y 4 del setup (`.env` y `variables.yaml`) siguen aplicando
igual: se editan en tu máquina host, no dentro del contenedor.

### 1. Construye la imagen (una vez, y cada vez que cambie `pyproject.toml`)

```bash
docker build -t api-test-framework .
```

### 2. Llena `.env` y `variables.yaml` en el host

Sigue los pasos [3](#3-llena-secretos) y [4](#4-llena-variables-versionadas)
de arriba tal cual, sobre los archivos del repo en tu máquina.

### 3. Entra al contenedor

```bash
docker run -it --rm \
    --env-file .env \
    -v "$(pwd):/app" \
    api-test-framework
```

- `--env-file .env` inyecta los secretos como variables de entorno del
  proceso — `pydantic-settings` los lee igual que en local. El archivo
  nunca se copia dentro de la imagen.
- `-v "$(pwd):/app"` monta todo el repo sobre `/app`, así `tests/`,
  `variables.yaml` y `reports/` se comparten en ambas direcciones sin
  reconstruir la imagen.
- En PowerShell, reemplaza `$(pwd)` por `${PWD}`.

Dentro del contenedor caes en un shell (`bash`) con el paquete ya
instalado en modo editable. Corre los mismos comandos de siempre:

```bash
pytest --collect-only
pytest --stepwise -k "TC-001" -v
pytest --last-failed -v
ruff check --fix . && ruff format .
```

Los reportes y la matriz reanotada quedan en tu host al salir del
contenedor, porque son el mismo archivo (bind mount), no una copia.

### 4. Sal del contenedor

```bash
exit
```

El contenedor se elimina solo (`--rm`); la imagen queda cacheada para
la próxima vez.

---

## Ejecutar con Docker

Alternativa al setup con `venv` (pasos 1-2 de arriba) si Python 3.11+
no está instalado o no se ejecuta correctamente en tu máquina. El
contenedor **no usa `venv`** — instala el stack directamente en su
Python de sistema, ya que el propio contenedor es el aislamiento.

Los pasos 3 y 4 del setup (`.env` y `variables.yaml`) siguen aplicando
igual: se editan en tu máquina host, no dentro del contenedor.

### 1. Construye la imagen (una vez, y cada vez que cambie `pyproject.toml`)

```bash
docker build -t api-test-framework .
```

### 2. Llena `.env` y `variables.yaml` en el host

Sigue los pasos [3](#3-llena-secretos) y [4](#4-llena-variables-versionadas)
de arriba tal cual, sobre los archivos del repo en tu máquina.

### 3. Entra al contenedor

```bash
docker run -it --rm \
    --env-file .env \
    -v "$(pwd):/app" \
    api-test-framework
```

- `--env-file .env` inyecta los secretos como variables de entorno del
  proceso — `pydantic-settings` los lee igual que en local. El archivo
  nunca se copia dentro de la imagen.
- `-v "$(pwd):/app"` monta todo el repo sobre `/app`, así `tests/`,
  `variables.yaml` y `reports/` se comparten en ambas direcciones sin
  reconstruir la imagen.
- En PowerShell, reemplaza `$(pwd)` por `${PWD}`.

Dentro del contenedor caes en un shell (`bash`) con el paquete ya
instalado en modo editable. Corre los mismos comandos de siempre:

```bash
pytest --collect-only
pytest --stepwise -k "TC-001" -v
pytest --last-failed -v
ruff check --fix . && ruff format .
```

Los reportes y la matriz reanotada quedan en tu host al salir del
contenedor, porque son el mismo archivo (bind mount), no una copia.

### 4. Sal del contenedor

```bash
exit
```

El contenedor se elimina solo (`--rm`); la imagen queda cacheada para
la próxima vez.

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

- Que las variables listadas existen en `variables.yaml` o `env.example`.
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
