## Why

El contrato de reporte ya fue actualizado (`openspec/config.yaml`, `CLAUDE.md`,
`README.md`): la evidencia de una corrida son únicamente `reports/report.html`
y `reports/resultados.json`, y ningún change de matriz debe producir una
copia anotada del CSV de entrada. Esto elimina por completo la razón de ser
de `src/framework/reannotate.py` (script CLI que reanotaba `matriz-*.csv`
con `PASS`/`FAIL`) y de `docs/reannotate_explore.md` (brief de exploración
para reescribirlo contra ese contrato). Ninguno de los dos tiene ya un
consumidor: `reannotate.py` no está importado por ningún test ni registrado
como entry point en `pyproject.toml`, y `docs/reannotate_explore.md`
documenta una tarea que ya no aplica. Este change es infraestructura —
encaja en la fila "Framework o helpers reutilizables" de la tabla de
decisión de `CLAUDE.md` — y no cambia ningún comportamiento observable de
los tests: el sidecar ya estaba fuera de uso desde la actualización de
config, esto solo retira el código y el doc que quedaron huérfanos.

## What Changes

- Elimina `src/framework/reannotate.py` (91 líneas): implementaba un
  contrato de sidecar CSV que ya no existe (abría el CSV de `inputs/` en
  modo escritura, cosa que el contrato vigente prohíbe explícitamente).
- Elimina `docs/reannotate_explore.md` (163 líneas): su premisa completa
  era explorar cómo reescribir `reannotate.py` contra el contrato del
  sidecar; sin sidecar, no hay nada que reescribir.
- No modifica `openspec/config.yaml`, `CLAUDE.md` ni `README.md` — ya
  reflejan el contrato vigente (sin sidecar, sin mención a `reannotate`).
- No modifica `tests/`, `pyproject.toml` ni ningún change archivado: se
  verificó que ninguno referencia el módulo o el doc que se eliminan.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

Ninguna. Este change no altera ningún requirement observable de un
endpoint ni del framework — retira código y documentación que ya estaban
huérfanos tras la actualización previa del contrato de reporte. Por eso
`.openspec.yaml` declara `skip_specs: true`.

## Impact

- **Código**: `src/framework/reannotate.py` (borrado completo).
- **Documentación**: `docs/reannotate_explore.md` (borrado completo).
- **Sin impacto en tests**: `tests/test_smoke.py` y `tests/conftest.py` no
  importan `framework.reannotate`.
- **Sin impacto en dependencias**: no hay entry point ni script en
  `pyproject.toml` que referencie el módulo.
- **Sin impacto en changes archivados**: `openspec/changes/archive/*`
  mencionan `reannotate.py` como registro histórico de lo que se construyó
  en su momento; no se tocan.
