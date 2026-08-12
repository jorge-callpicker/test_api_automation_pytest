import pytest
import pytest_check as check

from framework.audit_logs import fetch_audit_logs_page
from framework.config import load_variables


@pytest.mark.tc("SMOKE-003")
def test_fetch_audit_logs_page_returns_first_page(settings, http_client):
    account_id = load_variables()["globals"]["GLB-account_id_valido"]

    body = fetch_audit_logs_page(account_id, settings=settings, http_client=http_client)

    assert "audit_logs" in body, f"Respuesta inesperada del ambiente Chatwoot: {body}"
    check.equal(body.get("current_page"), 1, f"current_page inesperado: {body!r}")
    check.is_true(
        isinstance(body.get("audit_logs"), list),
        f"'audit_logs' no es una lista: {body.get('audit_logs')!r}",
    )
