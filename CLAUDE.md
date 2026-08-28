# CLAUDE.md — Instrucciones de sesión

Este archivo se lee automáticamente al inicio de cada sesión de Claude Code.
Complementa `openspec/config.yaml` — **no repite** información ya declarada
allí. Si hay conflicto, `openspec/config.yaml` gana.

## Instrucciones iniciales
- Habla y responde en español
- El idioma para trabajar OpenSpec tambien es español

## Contexto rápido

Repositorio de automatización de pruebas para APIs REST usando OpenSpec
(Fission-AI) + Claude Code. La disciplina, el stack pinneado, la convención
de variables, la política de matrices y las reglas por artefacto están en
`openspec/config.yaml` (campos `context` y `rules`). Consúltalo antes de
proponer o implementar.

## Artefactos de entrada por endpoint

Para cada endpoint bajo prueba, encuentras en `inputs/<endpoint-slug>/`:

- `docs.md` — documentación del endpoint. **Obligatorio**: sin él no se
  propone matriz. De aquí sale la estructura de la petición base, el mapeo
  entre el slug corto y el nombre largo del proyecto generador, y la sección
  `## Mirror keys en respuesta` que declara qué keys del request se espejan
  como key JSON exacta en la respuesta. Como el `-refinamiento.md` del
  proyecto generador no se versiona aquí, `docs.md` es el único portador
  en-repo de las reglas de validación.
- `matriz-<nombre>.csv` — matriz de particiones y valores límite. Separador
  `;`, UTF-8 **con BOM**, y **fila = caso, columna = campo**. Hay varios por
  endpoint: uno por contexto de aplicación, uno por objeto anidado y uno de
  validación cruzada. Formato completo en `openspec/config.yaml`. Es base de
  conocimiento **de diseño**: se lee al proponer y al generar el código,
  nunca durante la corrida (ver abajo).
- `casos-prueba.md` — casos AAA con IDs `TC-XXX`.
- `hallazgos.md` — discrepancias reales entre el endpoint y la matriz. Se
  crea cuando aparece la primera.

**Léelos antes** de proponer o implementar cualquier change. Si alguno
falta, detente y pide que se genere primero (con el skill correspondiente
del equipo de refinamiento).

Si alguna celda del CSV trae un prefijo de ID con la forma
`<campo>.<id> | <valor>`, el archivo no pasó la fase de limpieza del
proyecto generador: detente y pide que se limpie.

## Dos tipos de change proposal — tabla de decisión

| Origen del caso                                       | Tipo de change                        | Cardinalidad     |
|-------------------------------------------------------|---------------------------------------|------------------|
| Un `TC-XXX` del `casos-prueba.md`                     | `add-test-<endpoint>-tc-<nnn>`        | Uno por TC       |
| Una matriz CSV completa (contexto, anidado o cruzada)  | `add-test-<endpoint>-matriz-<nombre>` | Uno por CSV      |
| Framework o helpers reutilizables                     | `add-test-framework-base` (o similar) | Uno por refactor |

El `<nombre>` es el sufijo del CSV: un contexto de aplicación
(`c2-noauth-text`), un objeto anidado (`buttons`) o `cruzada`. Un endpoint
con seis contextos, un anidado y una cruzada son **ocho changes hermanos**.

Cada change de matriz implementa **todos los casos del CSV** en un solo test
parametrizado. Los IDs se derivan de la columna `Código HTTP Esperado`, que
cumple el rol de `Resultado`: `< 400` → `V1..Vn` (incluye el `206`),
`>= 400` → `I1..In`, posicionales dentro de su grupo. Nunca un archivo de
test por fila.

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
- Modificar el CSV de `inputs/`. Es un artefacto generado por otro proyecto.
- Generar una copia anotada del CSV, o escribir `PASS`/`FAIL` en cualquier
  matriz. La evidencia de la corrida son `reports/report.html` y
  `reports/resultados.json`, y nada más.
- Leer el CSV desde el código de test: abrirlo en runtime, importar un
  parser, o pasar su ruta como parámetro del test (ver abajo).
- Ajustar el valor esperado de un test para que pase cuando el endpoint
  discrepa de la matriz. Eso es un hallazgo: `xfail(strict=True)` con razón
  y entrada en `inputs/<endpoint-slug>/hallazgos.md`.
- **Generar código de test de matriz cuando el change necesite un módulo
  bloqueante que no existe** (ver abajo).

### El CSV no es dependencia de ejecución

El código de test es una **proyección materializada** del CSV, no un
consumidor de él. Al generar el test:

- Los casos van escritos en el código como argumentos de
  `pytest.mark.parametrize`, con los ids `V<n>`/`I<n>` ya derivados.
- Los valores van en `variables.yaml` y se consumen con `{{...}}`.
- El test corre sin que el CSV exista en disco.

Si el CSV se regenera, el test queda desalineado de su fuente: se compara el
hash SHA-256 y se revisa el change. No hay resincronización automática.

### Freno duro condicional — módulos pendientes

`src/framework/generators.py` y `mirror.py` **no existen**. Antes de generar
código de test de matriz, evalúa si este change los necesita:

- Alguna celda cae en ruta de resolución **runtime** → necesita
  `generators.py` → **detente**.
- `docs.md` declara al menos una **mirror key** → necesita `mirror.py` →
  **detente**.
- Ninguno de los dos — todos los valores estáticos o sembrados, sin mirror
  keys → **genera el código** y sigue el ciclo completo.

Al detenerte: proposal completo, dependencia declarada en `Why`, y ahí para.
No escribas un test que no puede correr ni dupliques la lógica del módulo
faltante dentro del archivo de test.

`matrix.py` tampoco existe, pero **no bloquea**: el CSV lo lees tú al
proponer, no el test al ejecutar.

## Política de resolución de indicaciones entre paréntesis (matrices)

Cuando una celda del CSV contiene una indicación en lenguaje natural entre
paréntesis, decide entre **tres** rutas:

- **Preferida por defecto — resolución estática**: escoge un valor concreto
  que satisface la indicación, regístralo como
  `MTZ-<endpoint>-<campo>-<slug_indicacion>` en
  `variables.yaml → matrix_values:` con comentario que copia la indicación
  original entre paréntesis, y consúmelo como literal. Si la celda ya trae
  el literal dentro del paréntesis (ej. `(2147483649 — máximo del rango más
  1)`), tómalo de ahí; `(cero)` es `0`.
- **Resolución en runtime**: añade o reusa una función en
  `src/framework/generators.py`. La variable `MTZ-*` sigue existiendo, pero
  su valor es una referencia `{ generator: nombre, params: {...} }`.
- **Resolución sembrada**: cuando el valor depende de datos que deben
  preexistir en el ambiente (`(token vigente de otra cuenta)`, `(app
  deshabilitada)`, `(template ya creado)`). **No va a `matrix_values:`**: va
  a `variables.yaml → globals:` como `GLB-*` con bloque `seed:`, valor
  inicial `[REQUIERE RESPUESTA: ...]`, más una tarea de siembra para el QA.

El disparador de runtime es **semántico, nunca por nombre de campo**. Solo
estos cuatro obligan a runtime:

| Disparador   | Marca en la indicación                     |
|--------------|--------------------------------------------|
| Unicidad     | "no usado antes", "único", "que no exista" |
| Aleatoriedad | "aleatorio", "cualquier"                   |
| Variedad     | "variado", "distinto en cada"              |
| Volumen      | longitud o cardinalidad alta con contenido indiferente |

Si aparece un caso de runtime que no encaja en los cuatro, **amplía esa
tabla en `openspec/config.yaml`** como parte del change. No lo resuelvas ad
hoc ni lo particularices por campo: el criterio tiene que seguir sirviendo
para el endpoint que venga después.

Regla de oro: si dudas entre estática y runtime, elige estática — es más
auditable y determinística. Si la indicación menciona un dato que tiene que
preexistir en el ambiente, es sembrada. Si añades un generador nuevo,
**debes** incluir una tarea de regenerar el catálogo:

```bash
python -m framework.generators --catalog > docs/generators-catalog.md
```

## Semántica de las celdas al construir la petición

La petición base del contexto se deriva de `docs.md`; cada caso es esa base
más la desviación de su fila. Los valores siempre por `{{...}}`.

- `(ausente)` — el campo **no se envía**: la key no se emite. No es `null`.
- `(vacío)` — la key **sí** se emite, con `""`.
- Campos con `Tipo de Dato` igual a `String (arreglo JSON)` viajan
  **serializados como string**: `"apps": "[\"uuid\"]"`, no
  `"apps": ["uuid"]`. Por eso un caso como `(string de 1 carácter — mínimo
  de 2 caracteres del string serializado menos 1)` es verificable: los dos
  caracteres mínimos son los corchetes de `[]`.
- La coerción según `Tipo de Dato` **debe poder no aplicarse**: casos como
  `(texto no numérico)` en un campo `Integer` son inválidos a propósito.
- Cada matriz usa **solo sus propias columnas**. Los conjuntos de campos
  difieren entre contextos y eso es correcto por diseño. Para matrices de
  objeto anidado, la petición padre se declara en `variables.yaml → globals:`.

## Política del assert de espejo entrada → respuesta

- Aplica **solo a casos de éxito** (`V1..Vn` de matriz, TC positivos del
  `.md`). Éxito se define por el código HTTP: `status < 400`, lo que
  **incluye el `206`** de éxito parcial.
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
# -k usa guion bajo: es substring del nombre real de la función
# (test_matriz_<endpoint>_<nombre>, ej. test_matriz_create_c2_header_texto),
# no el sufijo del CSV con guiones.
pytest --stepwise -x -k "matriz_create_c2_header_texto" -v

# Reintentar solo los últimos fallidos
pytest --last-failed -v

# Corrida con reportes HTML autocontenido + JSON
# (cada corrida escribe sola en su propia carpeta reports/<timestamp>/)
pytest --self-contained-html --json-report

# Lint + format antes de commit
ruff check --fix .
ruff format .
```

El `-x` en matriz corta al primer fallo del test parametrizado. Sin `-x`
el runner continuaría con todos los casos, saturando el reporte y
retrasando el feedback al desarrollador. Nunca omitir en matrices.

Consecuencia para el reporte: una corrida típica solo llega hasta el primer
fallo, así que los casos posteriores no aparecen en `resultados.json` — no
es lo mismo que `SKIPPED`.

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
- En `GLB-*` de resolución sembrada (valores de matriz que dependen del
  ambiente): bloque `seed:` con lo que debe existir, valor inicial
  `[REQUIERE RESPUESTA: ...]` y una tarea de siembra en el proposal.

Recuerda el slug corto: las variables `MTZ-*` usan `templates-create`, no el
nombre largo del archivo del proyecto generador. El mapeo vive en `docs.md`.
Los campos anidados se transliteran: `buttons[].type` → `buttons_type`.

## Formato de retroalimentación esperada del QA

Cuando el QA responda tras ejecutar, esperas uno de estos formatos:

- **Éxito (TC)**: `TC-XXX pasó` + opcionalmente bloque `PASSED` de pytest.
  Acción: procede a `/opsx:archive`.
- **Éxito (matriz)**: `matriz-<nombre>: N/N filas verdes`. Acción:
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
- **Sobre los campos y casos de una matriz** →
  `inputs/<endpoint>/matriz-<nombre>.csv` (columna = campo, fila = caso).
- **Sobre por qué existe un caso de matriz** → el `-refinamiento.md` del
  proyecto generador, referenciado por ruta desde `docs.md`.
- **Sobre validaciones, respuestas o mirror keys del endpoint** →
  `inputs/<endpoint>/docs.md`.
- **Sobre generadores disponibles** → `docs/generators-catalog.md`.
