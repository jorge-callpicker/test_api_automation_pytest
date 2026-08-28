# Automatización de pruebas de API — OpenSpec + Claude Code

Repositorio de pruebas automatizadas para endpoints de APIs REST del
equipo de QA, construido con [OpenSpec](https://github.com/Fission-AI/OpenSpec)
(Spec-Driven Development) y Claude Code.

Cada endpoint se cubre con dos tipos de change proposal independientes:

- **Un change por cada `TC-XXX`** del `casos-prueba.md` (formato AAA).
- **Un change por cada matriz CSV** (uno por contexto de aplicación, uno por
  objeto anidado, uno de validación cruzada) que implementa **todas** las
  filas del CSV en un solo test parametrizado.

La disciplina completa vive en `openspec/config.yaml`. Este README
describe cómo **operar** el repo día a día.

> **Estado actual — la ruta de matriz es ejecutable con condiciones.**
> Faltan `src/framework/generators.py` y `mirror.py`. Un change de matriz
> que los necesite (valores de resolución runtime, o mirror keys declaradas
> en `docs.md`) se detiene tras el proposal; uno que no los necesite corre
> el ciclo completo. Ver
> [Arquitectura pendiente](#arquitectura-pendiente).

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
│   └── <endpoint-slug>/       # Artefactos de entrada por endpoint
│       ├── docs.md            # Contrato + "Mirror keys en respuesta" + mapeo de slug
│       ├── matriz-<ctx>.csv   # Uno por contexto (fila = caso, columna = campo)
│       ├── matriz-<objeto>.csv# Uno por objeto anidado
│       ├── matriz-cruzada.csv # Validación cruzada
│       ├── casos-prueba.md    # Casos AAA con IDs TC-XXX
│       └── hallazgos.md       # Discrepancias reales endpoint vs matriz
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

El repositorio arranca **sin código Python**. El framework se construye
como el primer change de OpenSpec para que quede trazado y versionado.

Abre Claude Code en la raíz del repo y en el chat escribe:

```
/opsx:propose add-test-framework-base
```

Y a continuación pega este prompt exactamente:

> **Nota histórica.** Este prompt se ejecutó ya y su change está archivado,
> pero **quedó incompleto**: los módulos `matrix.py`, `generators.py` y
> `mirror.py` nunca se crearon. Las especificaciones 8, 9 y 10 de este prompt están
> **superadas** por [Arquitectura pendiente](#arquitectura-pendiente), que
> refleja el contrato vigente del CSV. En particular, la **8** (parser del
> CSV consumido por el test) ya no aplican: el CSV no es dependencia de ejecución 
> y no se produce ningún artefacto CSV de resultados. Se conserva aquí como registro 
> de lo que se pidió, no como instrucción a re-ejecutar.

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

11. `tests/conftest.py` con fixtures:
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

12. Sección `[tool.ruff]` en pyproject.toml con:
    - line-length = 100
    - target-version = "py311"
    - lint.select = ["E", "F", "I", "B", "UP", "SIM", "RUF"]

13. Un smoke test opcional `tests/test_smoke.py` que:
    - Verifica que `Settings()` carga sin excepción (leyendo `.env`).
    - Verifica que `load_variables()` retorna un dict con las tres
      secciones `globals`, `test_cases` y `matrix_values`.
    - Verifica que `matrix.load_matrix` no rompe con un CSV mínimo
      inline (fixtura con StringIO).
    - Verifica que `generators.int_above_max(10) == 11`.
    - NO hace request HTTP ni consulta a BD.
    - Marcado con `@pytest.mark.tc("SMOKE-001")`.

14. Al finalizar la implementación, ejecutar como parte del change:
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

Los reportes quedan en tu host al salir del contenedor, porque son el mismo
archivo (bind mount), no una copia.

### 4. Sal del contenedor

```bash
exit
```

El contenedor se elimina solo (`--rm`); la imagen queda cacheada para
la próxima vez.

---

## Arquitectura pendiente

La ruta de TC individual funciona. La ruta de matriz funciona **con
condiciones**. Estado real de `src/framework/`:

| Módulo           | Rol                                          | Estado        | ¿Bloquea la matriz?                    |
|------------------|----------------------------------------------|---------------|----------------------------------------|
| `config.py`      | pydantic-settings + loader YAML              | Existe        | —                                      |
| `variables.py`   | Interpolación `{{...}}`                      | Existe        | —                                      |
| `http.py`        | Cliente httpx + generador de cURL            | Existe        | —                                      |
| `db.py`          | Engine SQLAlchemy con AUTOCOMMIT             | Existe        | —                                      |
| `generators.py`  | Generadores + CLI `--catalog`                | **No existe** | Sí, si el change usa ruta runtime      |
| `mirror.py`      | Assert de espejo por key JSON exacta         | **No existe** | Sí, si `docs.md` declara mirror keys   |

### El CSV no es dependencia de ejecución

El CSV es base de conocimiento **de diseño**. El test que se genera es una
proyección materializada de él: los casos quedan escritos como argumentos de
`pytest.mark.parametrize` con sus ids `V<n>`/`I<n>` ya derivados, y los
valores en `variables.yaml`. **El test corre sin que el CSV exista en
disco**, y ningún módulo del framework lo abre en runtime.

Por eso no hay un `matrix.py` bloqueante: leer el CSV es trabajo del modelo
al escribir el proposal, no del test al ejecutarse. Si en el futuro se
implementa un lector de CSV, será una utilidad **offline** de autoría.

El precio es que CSV y test pueden divergir. La sincronización se controla
por el hash SHA-256 registrado en el change (ver
[Cuando el generador emite una versión nueva del CSV](#cuando-el-generador-emite-una-versión-nueva-del-csv)).

**Consecuencia operativa**: un change de matriz que resuelva todos sus
valores de forma estática o sembrada y cuyo endpoint no declare mirror keys
llega hasta la ejecución. Si necesita `generators.py` o `mirror.py`, Claude
lo detiene tras el proposal declarando la dependencia faltante.

### Contrato que deben cumplir los módulos faltantes

Resumen; la especificación normativa está en `openspec/config.yaml`.

**`generators.py`** — al set inicial de 11 hay que añadir los que las
matrices reales exigen: string único no usado antes, texto con N variables
`{{n}}` en secuencia, texto con hueco / desorden / repetición en la
secuencia, arreglo JSON con N elementos, URL válida de longitud N, teléfono
de N dígitos y texto con N espacios consecutivos. El catálogo se regenera
con `python -m framework.generators --catalog`; nunca a mano.

**`mirror.py`** — assert de espejo por key JSON exacta, nunca por substring,
solo en casos con `status < 400`, cada key con `pytest_check.check`.

La API concreta de estos módulos **no está fijada** por el contrato: se
diseña en el change que los implemente.

---

## Añadir un endpoint nuevo

### De dónde vienen las matrices

Los CSV **no se escriben aquí**. Los produce un proyecto aparte: un agente de
Claude Code que deriva particiones de equivalencia y valores límite a partir
de la documentación del endpoint. Ese proyecto entrega, por endpoint:

- Un `<endpoint>-refinamiento.md` — la memoria del proceso: contextos,
  valores por campo, criticidad, preguntas abiertas, registro de cambios.
- Varios `<endpoint>-matriz-*.csv` — uno por contexto de aplicación, uno por
  objeto anidado, uno de validación cruzada.

Dos condiciones antes de traerlos:

1. **El CSV tiene que estar limpio.** El generador emite las celdas como
   `<campo>.<id> | <valor>` y su script `limpiar-matriz.sh` quita el prefijo.
   Si ves ese prefijo en una celda, el archivo no está listo — devuélvelo.
2. **El refinamiento tiene que estar en `estado: aprobado`.** Si no lo está,
   los CSV en disco pueden reflejar valores viejos.

Hay un ejemplo real de los 8 CSV de un endpoint en [docs/examples/](docs/examples/),
junto con el README del proyecto que los generó.

### Pasos

1. Crea `inputs/<endpoint-slug>/`. El slug es **corto** (ej:
   `inputs/templates-create/`), no el nombre largo del archivo de origen.
2. Copia ahí los CSV, renombrándolos a `matriz-<nombre>.csv` donde
   `<nombre>` es el sufijo del contexto, el objeto anidado o `cruzada`:

   ```
   integrations-gupshup_integrations-templates-create-matriz-c2-noauth-text.csv
     → inputs/templates-create/matriz-c2-noauth-text.csv
   ```

3. Escribe a mano el `docs.md`, que debe incluir:
   - La sección `## Mirror keys en respuesta` (ver siguiente sección).
   - El **mapeo del slug**: nombre corto usado aquí ↔ nombre largo del
     proyecto generador.
   - La **ruta al `-refinamiento.md`** de origen. Ese archivo **no se
     versiona aquí**, así que `docs.md` queda como único portador en-repo de
     las reglas de validación del endpoint.
4. Coloca el `casos-prueba.md` si el endpoint también tiene TC del flujo AAA.
5. Añade al `variables.yaml`, bajo `test_cases:`, un bloque por cada
   `TC-XXX`, con `description`, `seed` y `variables` (placeholders
   `[REQUIERE RESPUESTA: ...]`).
6. Siembra los datos descritos en `seed` en el ambiente de pruebas y
   reemplaza los placeholders por los valores reales.

La sección `matrix_values:` se poblará cuando corras el primer change de
matriz para ese endpoint.

### Cuando el generador emite una versión nueva del CSV

Cada change de matriz archiva el hash SHA-256 del CSV que implementó. Antes
de proponer sobre el mismo CSV, compara:

```bash
sha256sum inputs/<endpoint-slug>/matriz-<nombre>.csv
```

Si difiere del registrado en el change archivado, el CSV se regeneró. Como la
identidad de los casos es **posicional** y los ids ya están escritos en el
test, el test queda desalineado de su fuente: hay que revisar el change
contra el CSV nuevo y volver a ejecutar la matriz completa.

---

## Convenciones del `docs.md`

`docs.md` es obligatorio y lo escribes tú a mano. El agente que genera las
matrices **no lo produce**, y su `-refinamiento.md` no se versiona aquí, así
que este archivo es el único portador en-repo de las reglas de validación
del endpoint. Tres cosas que debe incluir además del contrato:

### 1. Mapeo del slug

```markdown
## Mapeo de nombres

| Uso                          | Nombre                                                   |
|------------------------------|----------------------------------------------------------|
| Slug en este repo            | `templates-create`                                        |
| Nombre en proyecto generador | `integrations-gupshup_integrations-templates-create`      |
| Refinamiento de origen       | `../qa-ep-bva/docs/matrices/...-refinamiento.md` (v4)     |
```

El slug corto es el que se usa en `inputs/<slug>/` y en los nombres
`MTZ-<slug>-<campo>-<indicacion>`. Sin él, las variables pasan de 90
caracteres.

### 2. Estructura de la petición base

De aquí sale la petición base que cada matriz usa como punto de partida:
campos, tipos, cuáles son condicionales y bajo qué condición. Las matrices
solo declaran **desviaciones** respecto a esta base.

### 3. Sección "Mirror keys en respuesta"

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
- El assert corre **solo en casos de éxito**, definidos como
  `Código HTTP Esperado < 400`. Eso incluye el `206` de éxito parcial: la
  respuesta parcial sí devuelve el recurso creado.

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
pytest --stepwise -k "TC-001" -v --self-contained-html --json-report
```

Cada corrida escribe en una carpeta nueva `reports/<YYYYMMDD_HHMMSS>/`
(`report.html` + `resultados.json`); no hace falta indicar rutas.

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

> **Hoy este flujo puede detenerse en el paso 2.** Faltan `generators.py` y
> `mirror.py` — ver [Arquitectura pendiente](#arquitectura-pendiente). Si la
> matriz necesita alguno (valores de resolución runtime, o mirror keys en
> `docs.md`), el proposal se genera como inventario revisable pero
> `/opsx:apply` no producirá código. Si no los necesita, el flujo completo
> corre normal.

### 1. Propose

```
/opsx:propose add-test-<endpoint-slug>-matriz-<nombre>
```

Un change por CSV. Para un endpoint con seis contextos, un objeto anidado y
una matriz cruzada, son ocho:

```
/opsx:propose add-test-templates-create-matriz-c1-noauth-sin-type
/opsx:propose add-test-templates-create-matriz-c2-noauth-text
...
/opsx:propose add-test-templates-create-matriz-buttons
/opsx:propose add-test-templates-create-matriz-cruzada
```

Claude:

1. Lee `inputs/<endpoint>/matriz-<nombre>.csv` (`;`, UTF-8 con BOM) y
   verifica que esté limpio. Deriva los ids desde `Código HTTP Esperado`:
   `< 400` → `V1..Vn` (incluye `206`), `>= 400` → `I1..In`, posicionales
   dentro de su grupo.
2. Construye la petición base del contexto a partir de `docs.md`. Cada caso
   es esa base más la desviación de su fila.
3. Por cada celda elige una de las tres rutas de resolución — estática
   (default), runtime (solo por disparador semántico) o sembrada (cuando el
   valor depende del ambiente) — y registra la variable correspondiente:
   `MTZ-*` en `matrix_values:` para las dos primeras, `GLB-*` con bloque
   `seed:` en `globals:` para la tercera.
4. Lee `inputs/<endpoint>/docs.md § Mirror keys en respuesta` y lista las
   keys aplicables.
5. Genera proposal + tasks, incluyendo el inventario de casos con su
   prioridad y el hash SHA-256 del CSV.

### 2. Revisa

Abre `openspec/changes/add-test-.../proposal.md`. Verifica:

- Que el inventario de casos cubra **todas** las filas del CSV, con los ids
  `V<n>`/`I<n>` bien derivados del código HTTP.
- Que las variables propuestas cubran todas las celdas, y que las de
  resolución sembrada estén en `globals:` con su `seed:`, no en
  `matrix_values:`.
- Que el slug usado sea el corto y que los campos anidados estén
  transliterados (`buttons[].type` → `buttons_type`).
- Que las mirror keys correspondan a `docs.md`.
- Que ningún generador nuevo se añada sin tarea de regenerar el catálogo.
- Que el hash del CSV esté registrado.

Ajusta los archivos si algo hace falta antes de aplicar.

### 3. Apply

```
/opsx:apply
```

Claude genera:

- `tests/<endpoint>/test_matriz_<nombre>.py` — único test parametrizado
  con ids `V1..Vn` e `I1..In`.
- Entradas nuevas en `variables.yaml → matrix_values:` y, si aplica, en
  `globals:` con sus bloques `seed:`, con placeholders
  `[REQUIERE RESPUESTA: ...]` donde el valor concreto lo deba llenar el QA.
- Si aplica, generador nuevo en `src/framework/generators.py` +
  `docs/generators-catalog.md` regenerado.

**Antes de ejecutar**: llena cada `[REQUIERE RESPUESTA: ...]` que haya
quedado, y siembra en el ambiente lo que describan los bloques `seed:`.

### 4. Ejecuta manualmente

Comando específico de matriz — la bandera `-x` es **obligatoria** para
fail-fast al primer error:

```bash
pytest --stepwise -x -k "matriz-<nombre>" -v --self-contained-html --json-report
```

Cada corrida escribe en una carpeta nueva `reports/<YYYYMMDD_HHMMSS>/`
(`report.html` + `resultados.json`); no hace falta indicar rutas.

### 5. Retroalimenta

Tres escenarios:

- **Todas las filas pasan**: `matriz-<nombre>: N/N filas verdes`.
  Procede a `/opsx:archive`.
- **Corta en la fila N**: pega el traceback del caso `[V<n>]` o `[I<n>]`
  específico. Claude analiza si es bug del test, dato faltante en
  `variables.yaml`, o discrepancia real del endpoint. Si es discrepancia
  real, se marca `xfail(strict=True)` y se registra en
  `inputs/<endpoint-slug>/hallazgos.md` — **no se "arregla" el test para
  pasar**.
- **Bloqueo del ambiente**: descripción del problema. Claude no toca
  el test.

Si Claude corrige, repite paso 4.

### 6. Archive y commit

```
/opsx:archive
```

```bash
git add openspec/changes/archive/add-test-... tests/... variables.yaml \
        src/framework/generators.py docs/generators-catalog.md \
        inputs/<endpoint-slug>/hallazgos.md
git commit -m "test(<endpoint>): implementa matriz-<nombre>"
```

---

## Evidencia de la corrida

La evidencia son los dos reportes que produce pytest, y nada más:

- `reports/<YYYYMMDD_HHMMSS>/report.html` — reporte HTML autocontenido.
  Todo caso que haya realizado una petición HTTP incluye el cURL de la
  última request y el status code + body completo de la última
  respuesta, sin redactar ni truncar — tanto en éxito (`passed`) como en
  fallo (`failed`). Los casos fallidos además muestran el detalle de las
  soft assertions que fallaron.
- `reports/<YYYYMMDD_HHMMSS>/resultados.json` — resultado por caso, para
  consumo programático.

**No se anota ningún CSV.** El CSV de `inputs/` no se modifica ni se copia
para marcarlo con `PASS`/`FAIL`: los reportes ya cubren esa función, y el
CSV es un artefacto generado por otro proyecto.

La trazabilidad caso ↔ fila del CSV se lee del propio nodeid, sin archivo
intermedio:

- `test_matriz_<nombre>[V<n>]` → n-ésima fila con
  `Código HTTP Esperado < 400`.
- `test_matriz_<nombre>[I<n>]` → n-ésima fila con
  `Código HTTP Esperado >= 400`.

Como `-x` corta al primer fallo, los casos posteriores no aparecen en el
reporte. Eso **no** es lo mismo que `SKIPPED`.

Los reportes viven en `reports/` (git-ignored). Cada corrida crea su propia
carpeta `reports/<YYYYMMDD_HHMMSS>/`, así que no se sobrescriben entre sí —
las de corridas anteriores quedan disponibles como evidencia sin necesidad
de copiarlas a mano.

---

## Convenciones no negociables

- **1 change proposal = 1 unidad codificable**:
  - Un TC del `.md` → un change (`add-test-...-tc-<nnn>`).
  - Una matriz CSV → un change (`add-test-...-matriz-<nombre>`).
- **Cero literales de negocio en tests**. Todo pasa por `{{...}}`.
- **Prefijos**: `GLB-*` global, `TC-XXX-*` exclusivo del caso,
  `MTZ-<endpoint>-<campo>-<slug_indicacion>` exclusivo de matriz.
- **Soft assertions**: `pytest_check.check(...)` en todas las
  validaciones salvo la primera (status code HTTP), que sí es `assert`
  duro.
- **BD**: SQLAlchemy Core con AUTOCOMMIT. No transacciones desde tests.
- **Matriz siempre con `-x`**. Sin excepción.
- **El CSV de `inputs/` nunca se modifica ni se lee en ejecución.** Es base
  de conocimiento de diseño; el test es una proyección materializada de él.
  Los resultados de la corrida viven solo en `reports/`.
- **Assert de espejo solo por key JSON exacta**, sin substring matching, y
  solo en casos con `status < 400` (incluye el `206`).
- **`(ausente)` no es `null`.** `(ausente)` omite la key; `(vacío)` la emite
  con `""`.
- **Discrepancia real = hallazgo, no ajuste.** `xfail(strict=True)` más
  entrada en `inputs/<endpoint-slug>/hallazgos.md`.
- **La `Prioridad` del CSV es metadato de implementación**, no de ejecución.
  No genera markers ni filtra corridas.
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

**No se generó `resultados.json`**: la corrida requiere el flag
`--json-report`; el archivo aparece en la carpeta
`reports/<YYYYMMDD_HHMMSS>/` de esa ejecución.

**OpenSpec no reconoce `config.yaml`**: valida sintaxis YAML con
`python -c "import yaml; yaml.safe_load(open('openspec/config.yaml'))"`.

**Placeholder `[REQUIERE RESPUESTA: ...]` en runtime**: no llenaste
`variables.yaml` o `.env` completo. El framework debe fallar con
mensaje claro; si no, es un bug del cargador de variables.

**Matriz falla en la primera fila (`V1`) sin razón aparente**: revisa la
sección `Mirror keys en respuesta` de `docs.md` — probablemente hay una
key declarada como `Sí` que la respuesta real no incluye como key JSON.

**La primera columna del CSV se llama `﻿Campo` en vez de `Campo`**: se
abrió con `utf-8` en vez de `utf-8-sig`. Los CSV del proyecto generador
vienen en UTF-8 **con BOM**.

**La matriz entera falla con el mismo error de validación**: revisa si el
campo es de tipo `String (arreglo JSON)`. Esos viajan serializados como
string (`"apps": "[\"uuid\"]"`), no como arreglo nativo.

**Los ids `V<n>`/`I<n>` del test no coinciden con las filas del CSV**: el CSV
se regeneró y la identidad es posicional. Compara el hash contra el del
change archivado, revisa el change contra el CSV nuevo y vuelve a correr la
matriz completa.

**Alguna celda del CSV trae `<campo>.<id> | <valor>`**: el archivo no pasó
la fase de limpieza del proyecto generador. Devuélvelo para limpiar; no lo
consumas así.

**Un change de matriz se detiene tras el proposal**: la matriz necesita
`generators.py` (tiene valores de resolución runtime) o `mirror.py` (su
`docs.md` declara mirror keys), y ninguno existe todavía. El `Why` del
proposal dice cuál. Ver [Arquitectura pendiente](#arquitectura-pendiente).

**Un test de matriz falla con `FileNotFoundError` sobre un `.csv`**: está mal
implementado. El CSV no es dependencia de ejecución — los casos deben estar
materializados en el código. Es un bug del test, no del ambiente.

**Generador nuevo no aparece en el catálogo**: no se regeneró
`docs/generators-catalog.md`. Ejecuta manualmente:
`python -m framework.generators --catalog > docs/generators-catalog.md`.

---

## Comandos importantes

**Verificar qué selecciona un patrón `-k` antes de correrlo** (sin ejecutar
nada):

```bash
pytest --collect-only
```

**TC individual** del `.md` AAA:

```bash
pytest --stepwise -k "TC-001" -v
```

**Matriz completa**, con reporte HTML + JSON — `-x` es obligatorio (ver
[Convenciones no negociables](#convenciones-no-negociables)):

```bash
pytest --stepwise -x -k "matriz_<nombre>" -v --self-contained-html --json-report
```

El patrón `-k` usa **guion bajo**, no el sufijo del CSV con guiones: el
nombre real de la función parametrizada es `test_matriz_<nombre>`
(ej. `matriz_create_c1_sin_header`), no `matriz-<nombre>`.

**Diagnóstico sin fail-fast** — ver todos los fallos de una corrida en vez
de detenerse en el primero, para triage antes de decidir qué corregir:

```bash
pytest -k "matriz_<nombre>" -v --tb=short --self-contained-html --json-report
```

No sustituye la corrida final con `-x` que decide si el change se archiva.

**Reintentar solo los últimos fallidos**:

```bash
pytest --last-failed -v
```

**Reiniciar el cache de `--stepwise`** — ignora qué filas ya pasaron y
corre la matriz completa de nuevo. Útil tras cambiar datos/variables que
afectan filas que el cache todavía marca como "passed":

```bash
pytest --sw-reset -x -k "matriz_<nombre>" -v
```

**Lint + format antes de commit**:

```bash
ruff check --fix .
ruff format .
```



## Referencias

- OpenSpec (Fission-AI): https://github.com/Fission-AI/OpenSpec
- Claude Code: https://docs.claude.com/en/docs/claude-code
- pytest: https://docs.pytest.org
- pytest-check (soft asserts): https://github.com/okken/pytest-check
- httpx: https://www.python-httpx.org
- SQLAlchemy Core: https://docs.sqlalchemy.org/en/20/core/
- pydantic-settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
