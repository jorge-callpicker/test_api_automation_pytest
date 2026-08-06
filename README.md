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
├── .gitignore                 # Reglas de exclusión de git
├── openspec/
│   ├── config.yaml            # Contexto y reglas inyectados en cada artefacto
│   ├── specs/                 # Specs por endpoint (crecen con /opsx:archive)
│   └── changes/               # Changes activos + carpeta archive/
├── inputs/
│   └── <endpoint>/            # Artefactos de entrada por endpoint
│       ├── docs.md            # Documentación del endpoint
│       ├── matriz-raiz.csv    # Partición de equivalencias + valores límite
│       └── casos-prueba.md    # Casos AAA con IDs TC-XXX
├── src/framework/             # Framework de tests (bootstrapeado, ver Setup inicial)
├── tests/                     # Tests por endpoint (creados por change por TC)
├── reports/                   # Reportes HTML/JSON de cada ejecución (git-ignored)
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
la clave `seed:` que describe qué debe existir en la BD.

### 5. Verifica la instalación

Con el entorno virtual activo y `.env` completo:

```bash
pytest --collect-only
pytest tests/test_smoke.py -v
ruff check .
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
