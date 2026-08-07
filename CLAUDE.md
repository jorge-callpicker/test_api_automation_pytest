# CLAUDE.md — Instrucciones de sesión

Este archivo se lee automáticamente al inicio de cada sesión de Claude Code.
Complementa `openspec/config.yaml` — **no repite** información ya declarada
allí. Si hay conflicto, `openspec/config.yaml` gana.

## Contexto rápido

Repositorio de automatización de pruebas para APIs REST usando OpenSpec
(Fission-AI) + Claude Code. La disciplina, el stack pinneado, la convención
de variables, la política de matrices y las reglas por artefacto están en
`openspec/config.yaml` (campos `context` y `rules`). Consúltalo antes de
proponer o implementar.

## Artefactos de entrada por endpoint

Para cada endpoint bajo prueba, encuentras tres archivos en
`inputs/<endpoint>/`:

- `docs.md` — documentación del endpoint. Incluye la sección
  `## Mirror keys en respuesta` que declara qué keys del request se
  espejan como key JSON exacta en la respuesta (usada por el assert
  de espejo).
- `matriz-raiz.csv` — matriz de particiones y valores límite (separador
  `;`; columna = caso). Puede haber `matriz-<objeto-anidado>.csv`.
- `casos-prueba.md` — casos AAA con IDs `TC-XXX`.

**Léelos antes** de proponer o implementar cualquier change. Si alguno
falta, detente y pide que se genere primero (con el skill correspondiente
del equipo de refinamiento).

## Dos tipos de change proposal — tabla de decisión

| Origen del caso                             | Tipo de change                              | Cardinalidad          |
|---------------------------------------------|---------------------------------------------|-----------------------|
| Un `TC-XXX` del `casos-prueba.md`           | `add-test-<endpoint>-tc-<nnn>`              | Uno por TC            |
| Una matriz CSV completa (raíz o anidado)    | `add-test-<endpoint>-matriz-<nombre>`       | Uno por CSV           |
| Framework o helpers reutilizables           | `add-test-framework-base` (o similar)       | Uno por refactor      |

Cada change de matriz implementa **todos los casos del CSV** en un solo
test parametrizado con IDs `V1..Vn` (columnas de válidos) e `I1..In`
(columnas de inválidos). Nunca un archivo de test por columna.

## Ciclo de trabajo — RESPETAR

Cada change proposal produce código, se detiene y **espera
retroalimentación humana**. Después de aplicar, tu turno termina con las
instrucciones de ejecución para el QA. **No asumas éxito de la ejecución
sin retroalimentación explícita.** Si el QA responde con salida de pytest
indicando fallos, corriges y devuelves nuevas instrucciones. Si responde
que pasó, procedes al archivado.

Comportamientos prohibidos:

- Intentar ejecutar `pytest` tú mismo contra el ambiente real del QA.
- Marcar tareas del proposal como completadas antes de la retroalimentación.
- Archivar un change sin confirmación explícita del QA.
- Inventar valores para variables faltantes en `variables.yaml` o `.env`.
  En su lugar, marca la variable con `[REQUIERE RESPUESTA: <descripción + ejemplo>]`
  y añade una tarea al proposal para completarla.
- Hardcodear valores literales de negocio (IDs, tokens, URLs, cuerpos de
  respuesta esperados) en el código de test. Todo va por `{{...}}`.
- Editar `docs/generators-catalog.md` a mano. Ese archivo se regenera
  desde los docstrings de `src/framework/generators.py`.

## Política de resolución de indicaciones entre paréntesis (matrices)

Cuando una celda del CSV contiene una indicación en lenguaje natural entre
paréntesis (ej. `(entero fuera de rango superior)`, `(cadena aleatoria de
500 caracteres)`), decide entre dos rutas:

- **Preferida por defecto — resolución estática**: escoge un valor concreto
  que satisface la indicación, regístralo como `MTZ-<endpoint>-<campo>-<abrev>`
  en `variables.yaml → matrix_values:` con comentario que copia la
  indicación original entre paréntesis, y consúmelo como literal.
- **Solo cuando la indicación implica variedad — resolución en runtime**:
  añade o reusa una función en `src/framework/generators.py`. La variable
  `MTZ-*` en `variables.yaml` sigue existiendo, pero su valor es una
  referencia `{ generator: nombre, params: {...} }`.

Regla de oro: si dudas, elige estática. Es más auditable y determinística.
Los casos legítimos de runtime son minoría (aleatoriedad, variedad entre
corridas para ampliar cobertura). Si añades un generador nuevo, **debes**
incluir una tarea de regenerar el catálogo:

```bash
python -m framework.generators --catalog > docs/generators-catalog.md
```

## Política del assert de espejo entrada → respuesta

- Aplica **solo a casos de éxito** (`V1..Vn` de matriz, TC positivos del `.md`).
- Match **exclusivamente por key JSON exacta**. Si `template_id` está en el
  request y como key en `response.json()`, valida que coincidan.
- **No hacer match por substring**. Si el ID aparece dentro de un
  `"message": "Template [1234] deleted"`, se ignora silenciosamente.
- Fuente de verdad: sección `## Mirror keys en respuesta` en `docs.md` del
  endpoint. Si la sección falta o dice `Mirror keys: ninguna`, no se
  ejecuta ningún assert de espejo.
- Cada key declarada se evalúa con `pytest_check.check(...)` (soft assertion).

## Ejecución — `-x` obligatorio en matrices

Comandos que sugieres al QA (nunca los invocas tú):

```bash
# TC individual del .md AAA
pytest --stepwise -k "TC-001" -v

# Matriz completa — la bandera -x es OBLIGATORIA
pytest --stepwise -x -k "matriz-raiz" -v

# Reintentar solo los últimos fallidos
pytest --last-failed -v

# Corrida con reportes HTML autocontenido + JSON
pytest \
    --html=reports/report.html --self-contained-html \
    --json-report --json-report-file=reports/resultados.json

# Lint + format antes de commit
ruff check --fix .
ruff format .
```

El `-x` en matriz corta al primer fallo del test parametrizado. Sin `-x`
el runner continuaría con todas las columnas, saturando el reporte y
retrasando el feedback al desarrollador. Nunca omitir en matrices.

Comandos OpenSpec (se escriben en el chat de Claude Code, no en terminal):

```
/opsx:explore          # opcional, para pensar antes de proponer
/opsx:propose add-test-<endpoint>-tc-<nnn>
/opsx:propose add-test-<endpoint>-matriz-<nombre>
/opsx:apply
/opsx:archive
```

## Resolución de variables — recordatorio

Antes de generar código de test, verifica que cada `{{...}}` referenciada
exista en:

- `.env.example` (para `GLB-*` sensibles: tokens, URL base, credenciales BD).
- `variables.yaml → globals:` (para `GLB-*` no sensibles).
- `variables.yaml → test_cases.TC-XXX:` (para `TC-XXX-*`).
- `variables.yaml → matrix_values:` (para `MTZ-*`).

Si una variable no existe, añadirla es un cambio válido del proposal.
Documenta:

- En `TC-XXX-*`: qué debe sembrar el QA (bloque `seed:`).
- En `MTZ-*`: la indicación original del CSV como comentario en la línea
  anterior.

## Formato de retroalimentación esperada del QA

Cuando el QA responda tras ejecutar, esperas uno de estos formatos:

- **Éxito (TC)**: `TC-XXX pasó` + opcionalmente bloque `PASSED` de pytest.
  Acción: procede a `/opsx:archive`.
- **Éxito (matriz)**: `matriz-<nombre>: N/N columnas verdes`. Acción:
  procede a `/opsx:archive`.
- **Fallo del test**: pegado del bloque `FAILED` con traceback y, si aplica,
  la request/response cruda (cURL + JSON de body). En matriz, el `-x` hace
  que el bloque venga con id parametrizado `[V<n>]` o `[I<n>]` específico.
  Acción: analiza si es bug del test, dato faltante en `variables.yaml`,
  o discrepancia real del endpoint. Corrige el mínimo posible y devuelve
  nuevas instrucciones de ejecución.
- **Bloqueo del ambiente**: descripción del problema (BD caída, endpoint
  500 en cualquier request, dato faltante). Acción: NO corrijas el test.
  Sugiere pasos de desbloqueo del ambiente.

## Cuando dudes

- **Sobre el stack o versiones** → `openspec/config.yaml` → `context`.
- **Sobre cómo estructurar un proposal, tasks, specs o design** →
  `openspec/config.yaml` → `rules`.
- **Sobre cómo operar el repo (comandos, flujo día a día)** → `README.md`.
- **Sobre qué prueba un TC específico** → `inputs/<endpoint>/casos-prueba.md`.
- **Sobre las columnas de una matriz** → `inputs/<endpoint>/matriz-<nombre>.csv`.
- **Sobre validaciones, respuestas o mirror keys del endpoint** →
  `inputs/<endpoint>/docs.md`.
- **Sobre generadores disponibles** → `docs/generators-catalog.md`.
