from __future__ import annotations

import functools
from html import escape

import pytest

from framework import auth
from framework.auth import SessionTokens
from framework.config import Settings
from framework.db import engine as build_engine
from framework.http import client as build_client
from framework.http import to_curl
from framework.variables import resolve

_engine_cache: dict[int, object] = {}


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

    if report.when != "call" or not report.failed:
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

    if call.excinfo is not None:
        failure = escape(str(call.excinfo.value))
        extra.append(
            pytest_html.extras.html(
                f"<h4>Aserciones de pytest-check fallidas</h4><pre>{failure}</pre>"
            )
        )

    report.extras = extra
