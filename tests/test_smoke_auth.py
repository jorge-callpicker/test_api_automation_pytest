import pytest
import pytest_check as check


@pytest.mark.tc("SMOKE-002")
@pytest.mark.parametrize("role", ["SuperAdmin", "Admin"])
def test_session_tokens_resolves_both_tokens_for_role(session_tokens, role):
    tokens = session_tokens(role)

    assert isinstance(tokens.api_token, str) and tokens.api_token
    check.is_true(
        isinstance(tokens.api_access_token, str) and tokens.api_access_token,
        f"api_access_token vacío o de tipo incorrecto para rol '{role}'",
    )
