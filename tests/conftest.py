from __future__ import annotations

import functools
import json
from datetime import datetime
from html import escape
from pathlib import Path

import pytest

from framework import auth
from framework.auth import SessionTokens
from framework.config import Settings
from framework.db import engine as build_engine
from framework.http import client as build_client
from framework.http import to_curl
from framework.variables import resolve

_engine_cache: dict[int, object] = {}

# Default de pytest-json-report cuando el QA no pasa --json-report-file.
_JSON_REPORT_FILE_DEFAULT = ".report.json"


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    run_dir = Path("reports") / datetime.now().strftime("%Y%m%d-%H%M%S")

    needs_html = config.option.htmlpath is None
    needs_json = config.getoption("json_report_file", None) in (
        None,
        _JSON_REPORT_FILE_DEFAULT,
    )
    if needs_html or needs_json:
        run_dir.mkdir(parents=True, exist_ok=True)

    if needs_html:
        config.option.htmlpath = str(run_dir / "report.html")
    if needs_json:
        config.option.json_report_file = str(run_dir / "resultados.json")


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
    test_client.last_request = None
    yield test_client
    test_client.close()


@pytest.fixture(scope="function")
def db_conn(settings: Settings):
    conn = _get_engine(settings).connect()
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def session_tokens(settings: Settings, http_client):
    cache: dict[str, SessionTokens] = {}

    def factory(role: str) -> SessionTokens:
        if role not in cache:
            cache[role] = auth.obtain_session_tokens(
                role, settings=settings, http_client=http_client
            )
        return cache[role]

    return factory


@pytest.fixture(scope="function")
def resolve_payload():
    def factory(tc_id: str):
        return functools.partial(resolve, tc_id=tc_id)

    return factory


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
        try:
            body = json.dumps(last_response.json(), indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, ValueError):
            body = last_response.text
        headers = "\n".join(f"{key}: {value}" for key, value in last_response.headers.items())
        response_html = (
            f"<h4>Respuesta (ultima request)</h4>"
            f"<pre>Status: {last_response.status_code}\n\n"
            f"{escape(headers)}\n\n"
            f"{escape(body)}</pre>"
        )
        extra.append(pytest_html.extras.html(response_html))

    if call.excinfo is not None:
        failure = escape(str(call.excinfo.value))
        extra.append(
            pytest_html.extras.html(
                f"<h4>Aserciones de pytest-check fallidas</h4><pre>{failure}</pre>"
            )
        )

    report.extras = extra
