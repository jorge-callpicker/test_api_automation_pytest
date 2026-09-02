## ADDED Requirements

### Requirement: Evidencia de aserciones individuales en tests TC-XXX
El sistema SHALL documentar en el reporte, para cada test `TC-XXX` ejecutado,
una entrada por cada aserción realizada dentro de ese test (la dura de
status code y cada `pytest_check.check(...)` posterior), indicando su
etiqueta, su resultado (pasó/falló) y su mensaje — independientemente de si
el test en conjunto pasó o falló. Este requirement aplica exclusivamente a
tests `TC-XXX`; los tests de matriz (`test_matriz_*`) mantienen el
comportamiento existente (bloque de fallo solo cuando el test falla).

#### Scenario: TC-XXX exitoso con múltiples aserciones
- **WHEN** un test `TC-XXX` ejecuta varias aserciones y todas pasan
- **THEN** el reporte de ese test incluye una entrada por cada aserción
  ejecutada, mostrando su etiqueta y que su resultado fue exitoso

#### Scenario: TC-XXX fallido con aserciones mixtas
- **WHEN** un test `TC-XXX` ejecuta varias aserciones y al menos una falla
- **THEN** el reporte incluye una entrada por cada aserción ejecutada antes
  del corte del test — tanto las que pasaron como las que fallaron —, con su
  etiqueta, su resultado y, para las fallidas, su mensaje

#### Scenario: Test de matriz no incluye el log de aserciones individuales
- **WHEN** un test de matriz (`test_matriz_*`) ejecuta sus aserciones,
  pase o falle
- **THEN** el reporte de ese test no incluye la tabla de aserciones
  individuales — mantiene el mismo contenido que antes de este change
