from __future__ import annotations

import functools
import json
from datetime import datetime
from html import escape
from pathlib import Path

import httpx
import pytest

from framework.auth import fetch_tokens
from framework.config import Settings, load_variables, role_credentials
from framework.db import engine as build_engine
from framework.http import client as build_client
from framework.http import to_curl
from framework.variables import resolve

_engine_cache: dict[int, object] = {}
_JSON_REPORT_FILE_DEFAULT = ".report.json"


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    report_dir = Path("reports") / datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir.mkdir(parents=True, exist_ok=True)

    if not config.option.htmlpath:
        config.option.htmlpath = str(report_dir / "report.html")

    if getattr(config.option, "json_report_file", None) == _JSON_REPORT_FILE_DEFAULT:
        config.option.json_report_file = str(report_dir / "resultados.json")


def _get_engine(settings: Settings):
    key = id(settings)
    if key not in _engine_cache:
        _engine_cache[key] = build_engine(settings)
    return _engine_cache[key]


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()


@pytest.fixture(scope="session")
def http_client(settings: Settings):
    test_client = build_client(settings)
    yield test_client
    test_client.close()


@pytest.fixture(scope="function")
def db_conn(settings: Settings):
    conn = _get_engine(settings).connect()
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def access_tokens(settings: Settings, http_client) -> dict[str, dict[str, str]]:
    oauth_roles = load_variables()["globals"].get("GLB-oauth_roles", {})
    credentials_by_role = {role: role_credentials(settings, role) for role in oauth_roles}
    return fetch_tokens(http_client, oauth_roles, credentials_by_role)


@pytest.fixture(scope="function")
def resolve_payload():
    def factory(tc_id: str):
        return functools.partial(resolve, tc_id=tc_id)

    return factory


def _format_response_body(response: httpx.Response) -> str:
    content_type = response.headers.get("content-type", "")
    if "json" in content_type:
        try:
            return json.dumps(response.json(), indent=2, ensure_ascii=False)
        except ValueError:
            pass
    return response.text


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call":
        return

    pytest_html = item.config.pluginmanager.getplugin("html")
    if pytest_html is None:
        return

    extra = getattr(report, "extras", [])

    http_client_ = item.funcargs.get("http_client")
    last_request = getattr(http_client_, "last_request", None) if http_client_ else None
    if last_request is not None:
        curl = escape(to_curl(last_request))
        extra.append(pytest_html.extras.html(f"<h4>cURL (ultima request)</h4><pre>{curl}</pre>"))

    last_response = getattr(http_client_, "last_response", None) if http_client_ else None
    if last_response is not None:
        body = escape(_format_response_body(last_response))
        extra.append(
            pytest_html.extras.html(
                f"<h4>Response (status {last_response.status_code})</h4><pre>{body}</pre>"
            )
        )

    if call.excinfo is not None:
        failure = escape(str(call.excinfo.value))
        extra.append(
            pytest_html.extras.html(
                f"<h4>Aserciones de pytest-check fallidas</h4><pre>{failure}</pre>"
            )
        )

    report.extras = extra
