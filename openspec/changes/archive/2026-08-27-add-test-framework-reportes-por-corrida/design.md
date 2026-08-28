## Context

Ver `proposal.md - Why` para la motivación. Estado actual relevante:

- `tests/conftest.py:51-79` define `pytest_runtest_makereport` como
  `hookwrapper`, filtrando con `if report.when != "call" or not
  report.failed: return` — solo corre para fallos.
- `src/framework/http.py:10-18` construye el `httpx.Client` y solo
  registra `instance.last_request` vía `event_hooks["request"]`. No existe
  tracking de la respuesta.
- Los comandos documentados (`CLAUDE.md`) invocan pytest con
  `--html=reports/report.html --json-report-file=reports/resultados.json`
  fijos, por lo que cada corrida sobrescribe a la anterior.
- No existe ningún `pytest_configure` en el proyecto hoy.

## Goals / Non-Goals

**Goals:**
- Que ninguna corrida de pytest sobrescriba el reporte de la corrida
  anterior, sin que el QA tenga que recordar cambiar una ruta a mano.
- Que todo caso (`passed` o `failed`) deje en el HTML la misma evidencia
  de cURL más el body/status de la última respuesta, sin distinción por
  resultado.
- Mantener el reporte HTML autocontenido (`--self-contained-html`) intacto.

**Non-Goals:**
- Redactar headers sensibles (`Authorization`) del cURL embebido —
  decisión explícita del QA de mantener el comportamiento actual.
- Truncar o dar formato especial a bodies de respuesta grandes o binarios
  — decisión explícita del QA de embeberlos tal cual.
- Política de retención/limpieza de carpetas `reports/<timestamp>/`
  antiguas.
- Cambiar el esquema de `resultados.json` (pytest-json-report) más allá de
  su ubicación.

## Decisions

### 1. Carpeta por timestamp calculada en `pytest_configure`

Se agrega un hook `pytest_configure(config)` en `tests/conftest.py` que:

1. Calcula `reports/<YYYYMMDD_HHMMSS>/` una sola vez por proceso de pytest
   (un solo `datetime.now()` al inicio de la sesión, no por test).
2. Solo sobreescribe `config.option.htmlpath` cuando el plugin `pytest-html`
   está activo y el QA **no** pasó `--html` explícitamente (`config.option
   .htmlpath` sigue en su default `None`/vacío al momento de
   `pytest_configure`). Mismo criterio para la opción de ruta de
   `pytest-json-report` (`config.option.json_report_file`).
3. Crea la carpeta con `Path.mkdir(parents=True, exist_ok=True)` antes de
   que los plugins de reporte intenten escribir en ella.

Alternativa considerada: resolver la ruta desde un wrapper de shell o
`Makefile` que genere el nombre de carpeta y lo pase como argumento. Se
descarta porque el QA ejecuta pytest directamente (ver "Ciclo
humano-en-medio" en `openspec/config.yaml`) y añadir un wrapper obligatorio
contradice la simplicidad de los comandos documentados.

Alternativa considerada: usar `addopts` en `pyproject.toml` con una ruta
fija más un post-proceso que renombre la carpeta después de correr. Se
descarta porque pytest-html y pytest-json-report abren sus archivos de
salida en `pytest_configure`/`pytest_sessionstart`, antes de que exista
oportunidad de renombrar sin condiciones de carrera.

### 2. Tracking de `last_response` en `http.py`

Se añade un segundo `event_hooks["response"]` en `framework.http.client`,
simétrico al ya existente para `request`, que guarda la última
`httpx.Response` en `instance.last_response`. Requiere leer
`response.read()` (o acceder a `.content`) dentro del hook para que el body
esté disponible de forma síncrona antes de que el cliente cierre el
stream, ya que `httpx` con cliente síncrono por defecto no descarga el
body completo hasta que se accede a él.

### 3. Relajar la condición de `pytest_runtest_makereport`

La condición pasa de `if report.when != "call" or not report.failed:
return` a `if report.when != "call": return`. Dentro del cuerpo, cURL y
bloque de respuesta ya no dependen del resultado del caso: cURL se
adjunta siempre que haya `last_request`, y el bloque de respuesta
(status + body) se adjunta siempre que exista `last_response` —
`passed` o `failed` reciben exactamente la misma evidencia. El bloque de
asserts fallidos se mantiene condicionado a `call.excinfo is not None`
(comportamiento ya existente, ortogonal al resultado).

Revisión: la primera versión de este change condicionaba el bloque de
respuesta a `report.passed`. El QA verificó manualmente el change contra
un ambiente sustituto (PokeAPI) y pidió que el bloque de respuesta
aparezca también en fallos, ya que ver qué contestó el endpoint es
igual de útil (o más) para diagnosticar un caso `failed` que uno
`passed`. Se retira la condición por completo en vez de agregar un caso
especial para fallos.

## Risks / Trade-offs

- **[Riesgo] Tokens en texto plano en más reportes.** Al extender el cURL
  a todos los casos exitosos (incluidas las N filas de una matriz), el
  token de `Authorization` aparecerá en muchos más archivos HTML de los
  que aparece hoy (que solo cubre fallos). → Mitigación: ninguna en este
  change, por decisión explícita del QA; documentado en
  `proposal.md - What Changes` para que quede trazado y no oculto.
- **[Riesgo] Reportes HTML más pesados.** Bodies de respuesta sin truncar
  en cada fila `V1..Vn` de una matriz grande incrementan el tamaño del
  `report.html` autocontenido. → Mitigación: ninguna en este change, por
  decisión explícita del QA; si se vuelve un problema operativo, se atiende
  como change independiente (truncado/paginación).
- **[Riesgo] Crecimiento sin límite de `reports/`.** Cada corrida deja una
  carpeta nueva que nunca se borra automáticamente. → Mitigación: ninguna
  en este change; administración manual a cargo del QA (fuera de alcance,
  ver Non-Goals).
- **[Riesgo] Cliente síncrono no descarga el body de streaming responses.**
  Si algún endpoint devuelve una respuesta en streaming, acceder a
  `response.content` dentro del event hook fuerza la descarga completa
  antes de que el test la consuma normalmente. → Mitigación: el stack de
  este proyecto usa `httpx.Client` sync sin streaming explícito en ningún
  test existente; si un change futuro introduce streaming, deberá revisar
  este hook.

## Migration Plan

No aplica migración de datos. Es un cambio de comportamiento del framework
de pruebas: al aplicarse, la próxima corrida de pytest ya escribe en la
carpeta nueva y ya incluye evidencia en casos exitosos. No requiere
coordinación con el ambiente bajo prueba ni con `variables.yaml`.

Rollback: revertir el commit del change restaura el hook original de
`conftest.py` y el cliente `http.py` sin estado adicional que limpiar —
las carpetas `reports/<timestamp>/` ya generadas permanecen en disco y no
interfieren con la ejecución en modo anterior.
