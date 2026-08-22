Quiero explorar la reescritura de src/framework/reannotate.py. El alcance es
UN archivo de código, más sus tests. No toques ningún otro módulo de
src/framework/, ni los archivos de configuración (openspec/config.yaml,
CLAUDE.md, README.md), ni docs/examples/. Esos tres archivos de configuración
son la fuente de verdad del contrato: léelos primero.

# Qué hace este módulo

Toma el reporte JSON de una corrida de pytest y produce un CSV anotado con el
resultado de cada caso de la matriz, para que el QA vea de un golpe qué filas
pasaron y cuáles no.

Invocación actual, que se conserva:

    python -m framework.reannotate --matrix <ruta-csv> --results <ruta-json>

# Estado actual del archivo — 91 líneas, no sirve

El archivo existe y corre, pero está escrito contra un contrato que ya no es
el vigente. Fallos concretos, todos verificables leyéndolo:

1. Línea 57: abre el CSV con encoding="utf-8". Los CSV de matriz vienen en
   UTF-8 CON BOM, así que el nombre de la primera columna llega como
   "\ufeffCampo" y ninguna comparación con "Campo" acierta.
2. Línea 58: csv.DictReader(f) sin delimiter, o sea coma. Los CSV usan ";",
   así que cada fila se parsea como un único campo gigante.
3. Líneas 47-51: exige una columna llamada "TC" o "id" y lanza ValueError si
   no la encuentra. Los CSV de matriz tienen "Campo" como primera columna.
4. Líneas 10 y 19-23: el único matcher de nodeid es la regex tc[-_]?(\d+).
   NO existe manejo de nodeids parametrizados [V<n>] / [I<n>], que es
   precisamente lo que produce una matriz. Línea 39-40: cualquier nodeid que
   no matchee se descarta en silencio.
5. Línea 74: escribe EN SITIO sobre matrix_path. Eso viola la regla de que el
   CSV de inputs/ nunca se modifica.
6. _OUTCOME_MAP (líneas 12-16) solo cubre passed/failed/skipped. Con la
   política de hallazgos vigente, pytest también reporta xfailed y xpassed.
7. No distingue las filas de metadatos (¿Requerido?, Tipo Validación, Tipo de
   Dato) de las filas de caso. Si una clave coincidiera, las anotaría.
8. El timestamp (líneas 30-34) sale de report["created"], que es el inicio de
   la corrida, y se aplica igual a todos los tests.

Trátalo como reescritura, no como parche. Lo único claramente reusable es la
forma general del CLI y el uso de pytest-json-report como entrada.

# Contrato vigente — ya cerrado, no lo reabras

Del CSV de entrada:

- Separador ";". UTF-8 CON BOM: hay que abrir con "utf-8-sig".
- Fila = caso de prueba. Columna = campo.
- Columna 1 se llama "Campo": lleva el número consecutivo del caso en las
  filas de caso, y el nombre del metadato en las filas de metadatos.
- Penúltima columna "Código HTTP Esperado", última "Prioridad".
- Tras el encabezado hay tres filas de metadatos: "¿Requerido?",
  "Tipo Validación", "Tipo de Dato". En ellas las dos últimas columnas van
  vacías.
- Las filas cruzadas traen sufijo en su celda de "Campo", con la forma
  "N (cruzada: campoA+campoB)".

De la derivación de ids, que es la parte crítica para este módulo:

- El CSV limpio NO trae ids de caso. Se derivan de "Código HTTP Esperado",
  que cumple el rol de "Resultado": < 400 es éxito y recibe V1..Vn (el 206
  cuenta como éxito), >= 400 es error y recibe I1..In.
- La numeración es POSICIONAL dentro de su grupo, en orden de aparición de
  las filas. V1 es la primera fila con < 400; I1 la primera con >= 400.

De la salida:

- Se escribe un SIDECAR en reports/anotado-<nombre>.csv.
- El CSV de inputs/ NUNCA se modifica. Es artefacto generado por otro
  proyecto; escribirle encima lo desincroniza de su fuente y una regeneración
  pisaría las anotaciones.
- El sidecar es el CSV de entrada con dos columnas añadidas al final:
  ultimo_resultado y ultima_ejecucion (ISO 8601).
- Se escribe preservando el BOM, para que siga abriéndose bien en Excel.
- La bandera -x es OBLIGATORIA en corridas de matriz, así que una corrida
  típica solo llega hasta el primer fallo. Las filas que no se ejecutaron
  quedan con ultimo_resultado VACÍO, y eso tiene que ser distinguible de un
  SKIPPED.
- Sigue existiendo la ruta de TC individual: nodeids que contengan TC-XXX
  mapean a la fila del CSV que tenga ese TC en su columna de trazabilidad,
  SI la matriz tiene esa columna. Los CSV de ejemplo no la tienen, así que
  esa ruta es condicional, no obligatoria.

# Restricción de dependencias

src/framework/matrix.py NO existe todavía, y su implementación es alcance de
otro change. Este módulo necesita derivar los ids V/I del CSV para poder
mapear los nodeids, que es exactamente una de las cosas que matrix.py hará.

Esa tensión es una de las preguntas centrales de esta exploración, no algo
que puedas resolver dando por hecho que matrix.py existe. No lo importes sin
justificar la decisión.

Tampoco puedes verificar el módulo de punta a punta: sin matrix.py no hay
test de matriz que corra, así que no hay un resultados.json real de matriz
contra el que probar. La estrategia de verificación es parte de lo que quiero
que propongas.

# Insumos disponibles

- docs/examples/ tiene 8 CSV reales de un mismo endpoint, ya limpios, con
  todos los casos extremos del formato: BOM, filas cruzadas con sufijo,
  objeto anidado con notación buttons[].type, conjuntos de campos distintos
  entre contextos, y volúmenes de 13 a 87 casos. Úsalos como material de
  verdad y como fixtures; NO los modifiques.
- El README de docs/examples/ describe el proyecto que los generó.
- pytest-json-report 1.5.0 es la versión pinneada. Su formato de salida
  (claves "created", "tests", "nodeid", "outcome") es el contrato de entrada.

# Lo que quiero de la exploración

1. La cuestión de la derivación de ids. Tres caminos posibles: duplicar una
   derivación mínima dentro de reannotate.py; extraer un helper compartido
   pequeño que luego matrix.py consuma; o declarar la dependencia y esperar.
   Argumenta el trade-off, incluyendo qué pasa si las dos derivaciones se
   desincronizan.

2. Desambiguación de nodeids. Un nodeid de matriz tiene la forma
   tests/<endpoint>/test_matriz_<nombre>.py::test_matriz_<nombre>[V1]. Un
   mismo resultados.json puede contener varias matrices del mismo endpoint,
   y todas tienen un caso [V1]. ¿Cómo se filtra para que solo se anoten los
   resultados de la matriz que se pasó por --matrix? Ojo con la normalización:
   el archivo es matriz-c2-noauth-text.csv y el test es
   test_matriz_c2_noauth_text — guiones contra guiones bajos.

3. Cómo se deriva la ruta del sidecar: del stem de --matrix, de un argumento
   nuevo, o de una convención. Qué pasa si reports/ no existe.

4. Cómo se preservan al escribir las tres filas de metadatos y sus celdas
   finales vacías, y qué valor llevan en las dos columnas nuevas.

5. Tratamiento de outcomes. Al menos passed, failed, skipped, xfailed y
   xpassed, dado que la política de hallazgos usa xfail(strict=True). Un
   xpassed es señal de que el endpoint se corrigió y el hallazgo hay que
   revisarlo, así que no debería verse igual que un passed.

6. Distinción entre "no ejecutado" y "skipped". Como el sidecar se genera
   siempre desde el CSV original y no se acumula, ¿basta con dejar la celda
   vacía, o conviene un valor explícito? Piensa en cómo lo lee un humano en
   Excel.

7. Casos degenerados: resultados.json sin tests de matriz; un id [V9] que no
   tiene fila correspondiente porque el CSV se regeneró y se corrió;
   resultados.json de una corrida de otra matriz; CSV con cero filas de
   éxito. ¿Cuáles son error con exit code distinto de cero y cuáles son
   advertencia?

8. Estrategia de tests unitarios: qué resultados.json sintéticos hacen falta
   y qué CSV de docs/examples/ conviene usar en cada caso. Cubre como mínimo
   el BOM, el delimitador, la derivación V/I con un 206 de por medio, el
   filtrado por nombre de matriz, y el corte por -x a mitad de la matriz.

9. Si esto es un change o dos, y si el helper de derivación (en caso de que
   propongas extraerlo) debe ir en el mismo change o esperar al de matrix.py.

Lee openspec/config.yaml (secciones "Formato del CSV de matriz", "Derivación
de los ids V/I", "Reporte y trazabilidad", "Arquitectura objetivo" y
"Hallazgos"), README.md (sección "Anotar los resultados de la matriz" y
"Arquitectura pendiente"), src/framework/reannotate.py completo,
pyproject.toml, y al menos dos CSV de docs/examples/ — uno de contexto grande
y el de objeto anidado. No escribas código en esta fase.
