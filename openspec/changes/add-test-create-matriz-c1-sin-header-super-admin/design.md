## Context

Ver `proposal.md` → *Why* para la motivación.

Estado actual: `tests/test_matriz_create_c1_sin_header.py` tiene una función de
test con 73 casos parametrizados, en verde (73/73 `PASSED`, 2026-08-25). Su
cuerpo hace tres cosas: resolver las `{{...}}` de la fila, construir el payload
con `matrix.build_payload`, y decidir los headers según el caso (sesión real, sin
header, o token basura). El rol está **hardcodeado** como literal `"Admin"` en la
llamada a `auth.obtain_session_tokens`.

Restricciones que moldean el enfoque:

- `framework.auth` ya resuelve credenciales por rol vía `_ROLE_CREDENTIALS`; no
  hace falta tocar el framework.
- El endpoint liga el token a una cuenta en `selectAccount`, así que el rol solo
  influye aguas arriba de la petición bajo prueba. La única diferencia observable
  entre roles está en el privilegio de cruce de cuentas.
- `-x` es obligatorio en matrices, y ambos roles van a convivir en un archivo.
- Este es el primer change de variante por rol del repo. Lo que se decida aquí lo
  heredan las nueve matrices restantes de `inputs/Create/`.

## Goals / Non-Goals

**Goals:**

- Añadir el rol sin duplicar el cuerpo del test ni la lógica de headers.
- Que el camino de `Admin` siga produciendo exactamente el mismo request que hoy,
  para que su 73/73 verde siga siendo comparable.
- Dejar una convención de ids y de estructura reutilizable por las demás
  matrices, no una solución particular de `c1`.
- Que el reporte por corrida deje separados los dos roles sin depender de
  coincidencias frágiles de substring.

**Non-Goals (de diseño):**

- No se generaliza a N roles ni se introduce una fixture de rol en el framework.
  Con dos roles, la parametrización explícita es más legible que una abstracción.
- No se toca `matrix.build_payload`, `generators.py` ni `variables.py`.
- No se rediseña la estrategia de sesión por caso (ver decisión 5).

## Decisions

### Decisión 1 — Segundo change sobre el mismo CSV, no un CSV por rol

La regla del repo pide un change por CSV. La alternativa fiel habría sido pedir
al proyecto generador un `create-matriz-c1-sin-header-sadmin.csv`.

Se descarta: sería un archivo con 70 filas idénticas a las de `c1` salvo la
credencial, y ante cualquier regeneración de `c1` los dos quedarían
desincronizados sin que nada lo detecte. El delta real entre roles es una
credencial y tres omisiones — no justifica un artefacto paralelo.

La desviación queda declarada en `proposal.md` → *Desviación de cardinalidad*.

### Decisión 2 — Mismo archivo, dos funciones, helper compartido

Tres opciones consideradas:

| Opción | Por qué no / por qué sí |
|---|---|
| Archivo nuevo `..._super_admin.py` | Duplicaría `BASE_REQUEST`, `FIELD_TYPES` y toda la lógica de headers. Dos copias que divergen en el primer arreglo. |
| Una función parametrizada sobre `CASES + CASES_SA` con el rol en la tupla | Compacta, pero el reporte lista los 143 casos en un continuo y aislar un rol depende del prefijo del id — con la trampa de que `-k "V1"` captura también `SA-V1` por substring. |
| **Dos funciones + helper privado** ← elegida | El reporte agrupa por nombre de función, así que los roles se leen separados. El QA aísla un rol con `-k` sobre el nombre de función, sin ambigüedad de substring. El cuerpo vive una sola vez. |

El helper recibe el rol como primer parámetro y contiene el cuerpo íntegro que
hoy tiene la función de `Admin`. Ambas funciones de test quedan reducidas a su
`parametrize` más la llamada.

### Decisión 3 — Numeración alineada, con hueco en `SA-I4`

`SA-I<n>` designa el mismo caso del CSV que `I<n>`. Al omitirse el caso 12, el id
`SA-I4` simplemente no existe.

La alternativa —renumerar contiguo `SA-I1..SA-I62`— cumple al pie de la letra la
regla *"los ids son posicionales dentro de su grupo"*, pero desplaza todos los
ids a partir del cuarto: `SA-I30` designaría el caso 31. Comparar el resultado de
un caso entre roles exigiría una tabla de traducción, y cualquier lectura del
reporte se vuelve propensa a error.

Se prioriza la trazabilidad sobre la contigüidad. La desviación de la regla queda
declarada en `proposal.md`.

**Precedente para las demás matrices**: prefijo de rol + numeración alineada al
rol base, con hueco donde el rol variante no aplica.

### Decisión 4 — Dos criterios distintos de omisión, ambos explícitos

Las tres omisiones no son del mismo tipo y conviene no confundirlas:

- **Por privilegio de rol** (`I4`): la fila sí es aplicable, pero su código
  esperado cambia con el rol. Se omite porque verificar el `200` implicaría
  probar cruce de cuentas, declarado fuera de alcance.
- **Por independencia estructural del rol** (`I64`, `I65`): la fila nunca abre
  sesión, así que el request es idéntico byte a byte en ambos roles. Ejecutarla
  otra vez no aporta información.

El segundo criterio es mecánico y reutilizable: **toda fila cuyo caso no invoque
`obtain_session_tokens` se omite en las variantes de rol.** El primero exige
juicio caso por caso y debe justificarse por escrito cada vez.

### Decisión 5 — La estrategia de sesión por caso no cambia

El helper conserva tal cual la lógica actual: si el `account_id` de la fila
coincide con `GLB-account_id_valido`, se usa ese; en cualquier otro caso
(ausente/vacío/inexistente/mutado) la sesión se abre contra `GLB-account_id_valido`
para poder llegar a la validación del campo bajo prueba.

Se consideró abrir la sesión de `SuperAdmin` contra la cuenta que declara cada
fila, aprovechando su privilegio. Se descarta: cambiaría el request de todos los
casos de error respecto al rol `Admin`, y entonces una diferencia de resultado
entre roles ya no sería atribuible al rol sino a la cuenta de sesión. La
invariante que este change verifica exige que el resto del request sea idéntico.

### Decisión 6 — Sin sidecar; el reporte por corrida es el registro

`reports/<timestamp>/report.html` ya adjunta cURL, status, headers y body de cada
caso en todos los outcomes desde `2026-08-26-update-framework-report-per-run`, y
lista los dos roles con sus ids. El sidecar no aportaría nada que el reporte no
tenga, y mantenerlo obligaría a inventar una representación de dos roles sobre un
CSV de una sola columna de resultado.

La limpieza de `reannotate.py` y de las reglas que aún exigen el sidecar es un
change de framework posterior — ver `proposal.md` → *Non-Goals*.

## Risks / Trade-offs

**El refactor puede alterar el request del rol `Admin`** → El helper debe
recibir el cuerpo actual sin modificaciones de comportamiento: mismo orden de
operaciones, mismos `files=`, mismos asserts. La verificación es una corrida de
`Admin` sola antes de tocar nada más; si los 73 no siguen en verde, el refactor
está mal y no se avanza a `SuperAdmin`.

**`-x` corta antes de llegar a `SuperAdmin`** → Con ambos roles en un archivo,
un fallo de `Admin` impide ver nada de la variante. Las instrucciones de
ejecución al QA filtran por nombre de función para correr cada rol por separado;
la corrida conjunta se reserva para cuando ambos estén verdes.

**`GLB-create-apps_ids_validos` sin re-ejecutar** → La variable contiene hoy el
mismo UUID que `GLB-create-app_id_otra_cuenta` y alimenta `V2/V4/V6/V8`; con este
change pasa a alimentar 8 casos en vez de 4. Si la corrida se detiene en un caso
`V`, ese es el primer lugar donde mirar antes de sospechar del rol. No se corrige
en este change: es un dato del ambiente que decide el QA.

**El `200` de `SuperAdmin` en el caso 12 es un supuesto, no un hecho** → Se
omite la fila apoyándose en una afirmación del QA que este change no verifica.
Si más adelante resultara que el endpoint responde `401` también para
`SuperAdmin`, la omisión estaría descartando un caso válido y habría que
reincorporarlo como `SA-I4`. El hueco en la numeración deja el sitio libre para
justamente eso.

**La convención `SA-*` no está en `openspec/config.yaml`** → Queda como
precedente en un change archivado, no como regla. La siguiente variante de rol
podría inventar otra convención sin que nada lo impida. Elevarla a regla es
trabajo del change de limpieza que también retira el sidecar.

## Open Questions

Ninguna que bloquee la implementación o el desglose de tareas.
