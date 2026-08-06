# CLAUDE.md — Instrucciones de sesión

Este archivo se lee automáticamente al inicio de cada sesión de Claude Code.
Complementa `openspec/config.yaml` — **no repite** información ya declarada
allí. Si hay conflicto, `openspec/config.yaml` gana.

## Contexto rápido

Repositorio de automatización de pruebas para APIs REST usando OpenSpec
(Fission-AI) + Claude Code. La disciplina, el stack pinneado, la convención
de variables y las reglas por artefacto están en `openspec/config.yaml`
(campos `context` y `rules`). Consúltalo antes de proponer o implementar.

## Artefactos de entrada por endpoint

Para cada endpoint bajo prueba, encuentras tres archivos en
`inputs/<endpoint>/`:

- `docs.md` — documentación del endpoint (rutas, validaciones, respuestas).
- `matriz-raiz.csv` — matriz de partición de equivalencias y valores límite.
  Puede haber archivos adicionales `matriz-<objeto-anidado>.csv`.
- `casos-prueba.md` — casos de prueba en formato AAA con IDs `TC-XXX`.

**Léelos antes** de proponer o implementar cualquier change. Si alguno
falta, detente y pide que se genere primero (con el skill correspondiente
del equipo de refinamiento).

## Ciclo de trabajo — RESPETAR

Cada change proposal implementa **un solo** `TC-XXX`. Después de aplicar
un change, tu turno **termina** con las instrucciones de ejecución para el
QA. **No asumas éxito de la ejecución sin retroalimentación humana
explícita.** Si el QA responde con salida de pytest indicando fallos,
corriges y devuelves nuevas instrucciones. Si responde que pasó, procedes
al archivado.

Comportamientos prohibidos:

- Intentar ejecutar `pytest` tú mismo contra el ambiente real del QA.
- Marcar tareas del proposal como completadas antes de la retroalimentación.
- Archivar un change sin confirmación explícita del QA.
- Inventar valores para variables faltantes en `variables.yaml` o `.env`.
  En su lugar, marca la variable con el placeholder
  `[REQUIERE RESPUESTA: <descripción + ejemplo>]` y añade una tarea al
  proposal para completarla.
- Hardcodear valores literales de negocio (IDs, tokens, URLs, cuerpos de
  respuesta esperados) en el código de test. Todo va por `{{...}}`.

## Comandos frecuentes (referencia rápida)

Los ejecuta el QA — tú los sugieres, no los invocas:

```bash
# Instalar deps (primera vez)
pip install -e ".[dev]"

# Ejecutar un TC específico con stepwise
pytest --stepwise -k "TC-001" -v

# Reintentar solo los últimos fallidos
pytest --last-failed -v

# Correr todo con reporte HTML autocontenido y JSON
pytest \
    --html=reports/report.html --self-contained-html \
    --json-report --json-report-file=reports/resultados.json

# Lint + format antes de commit
ruff check --fix .
ruff format .
```

Comandos OpenSpec (se escriben en el chat de Claude Code, no en terminal):

```
/opsx:explore          # opcional, para pensar antes de proponer
/opsx:propose add-test-<endpoint>-tc-<nnn>
/opsx:apply
/opsx:archive
```

## Resolución de variables — recordatorio

Antes de generar código de test, verifica que cada `{{...}}` referenciada
en el caso AAA exista en:

- `.env.example` (para `GLB-*` sensibles: tokens, URL base, credenciales BD).
- `variables.yaml` (para `GLB-*` no sensibles y todos los `TC-XXX-*`).

Si una variable no existe en ninguno, añadirla es un cambio válido del
proposal. Documenta qué debe sembrar el QA en `variables.yaml` mediante
la clave `seed:` del bloque `TC-XXX`.

## Formato de retroalimentación esperada del QA

Cuando el QA responda tras ejecutar, esperas uno de estos tres formatos:

- **Éxito**: `TC-XXX pasó` + opcionalmente el bloque `PASSED` de pytest.
  Acción: procede a `/opsx:archive`.
- **Fallo del test**: pegado del bloque `FAILED` con traceback y, si
  aplica, la request/response cruda (cURL + JSON de body).
  Acción: analiza la causa (código de test vs dato sembrado vs endpoint),
  corrige el mínimo posible y devuelve nuevas instrucciones de ejecución.
- **Bloqueo del ambiente**: descripción del problema (BD caída, endpoint
  500, dato faltante).
  Acción: NO corrijas el test — sugiere pasos de desbloqueo del ambiente.

## Cuando dudes

- **Sobre el stack o versiones** → `openspec/config.yaml` → `context`.
- **Sobre cómo estructurar un proposal, tasks, specs o design** →
  `openspec/config.yaml` → `rules`.
- **Sobre cómo operar el repo (comandos, flujo día a día)** → `README.md`.
- **Sobre qué prueba un TC específico** → `inputs/<endpoint>/casos-prueba.md`.
- **Sobre validaciones o respuestas del endpoint** → `inputs/<endpoint>/docs.md`.
