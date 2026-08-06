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
