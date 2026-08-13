"""Test temporal — change fix-report-inline-extras, tarea 3.2.

Dispara una request real via `http_client` y una aserción de
`pytest_check` que falla a propósito, únicamente para ejercitar el hook
`pytest_runtest_makereport` de `conftest.py` y permitir verificar
visualmente (Firefox + Chrome/Brave) que el cURL y la aserción fallida
aparecen inline en la fila expandida de `reports/report.html`, sin URIs
`data:`. Se elimina en la tarea 3.4 tras la verificación del QA.
"""

import pytest
import pytest_check


@pytest.mark.tc("SMOKE-REPORT-EXTRAS")
def test_report_extras_render_inline(http_client):
    response = http_client.get("/")

    assert response.status_code < 500

    with pytest_check.check("Fallo intencional para verificar el reporte (temporal, tarea 3.2)"):
        raise AssertionError
