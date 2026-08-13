import pytest

from framework.config import load_variables


@pytest.mark.tc("SMOKE-001")
def test_settings_loads_without_exception(settings):
    assert settings.GLB_URL_BASE
    assert settings.GLB_TOKEN_ADMIN


@pytest.mark.tc("SMOKE-001")
def test_load_variables_returns_globals_and_test_cases():
    variables = load_variables()
    assert "globals" in variables
    assert "test_cases" in variables


@pytest.mark.tc("SMOKE-002")
def test_access_tokens_issued_for_every_active_role_and_scope(access_tokens):
    oauth_roles = load_variables()["globals"].get("GLB-oauth_roles", {})
    assert oauth_roles, "GLB-oauth_roles no debe estar vacio para esta prueba"

    for role, role_config in oauth_roles.items():
        assert role in access_tokens
        for scope in role_config.get("scopes", []):
            assert access_tokens[role].get(scope)
