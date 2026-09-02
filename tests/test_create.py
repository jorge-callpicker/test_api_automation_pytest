from __future__ import annotations

import httpx
import pytest
import pytest_check as check
from sqlalchemy import text

from framework import auth
from framework.assert_log import step
from framework.audit_logs import find_audit_log
from framework.generators import unique_lowercase
from framework.matrix import build_payload
from framework.variables import resolve

ENDPOINT_PATH = "/integrations/gupshup_integrations/templates/create"

FIELD_TYPES = {
    "account_id": "Integer",
    "name": "String",
    "category": "String",
    "lang": "String",
    "apps": "String (arreglo JSON)",
    "body": "String",
    "body_var": "String (arreglo JSON)",
}


@pytest.mark.tc("TC-001")
@pytest.mark.tipo("Positivo")
@pytest.mark.tecnica("Happy path base")
@pytest.mark.rol("Admin")
@pytest.mark.impacto("Alto")
@pytest.mark.prioridad("Alta")
@pytest.mark.criticidad("Crítica")
def test_create_tc_001(settings, http_client, db_conn, assert_log):
    """TC-001 - Creacion mono-app sin encabezado (Marketing).

    Ver inputs/Create/casos-de-prueba.md y
    openspec/changes/add-test-create-tc-001/proposal.md para el detalle de
    las decisiones (auth via obtain_session_tokens, assert de auditoria via
    audit_logs.py con cliente HTTP aislado, name generado en codigo).
    """
    # Arrange: nombre unico prefijado "tc_1_" para trazar en BD/ambiente qué
    # plantillas nacieron de este caso (ver proposal.md, decisión 4).
    nombre_plantilla = f"tc_1_{unique_lowercase(length=8)}"

    deviations = {
        "account_id": "{{GLB-account_id_valido}}",
        "name": nombre_plantilla,
        "category": "MARKETING",
        "lang": "en_US",
        "apps": "{{GLB-create-app_id_valido}}",
        "body": "{{TC-001-body_texto}}",
        "body_var": ["{{TC-001-body_var_ejemplo}}"],
    }
    resolved = resolve(deviations, tc_id="TC-001")
    payload = build_payload({}, resolved, FIELD_TYPES)

    account_id = resolved["account_id"]
    app_id = resolved["apps"][0]

    tokens = auth.obtain_session_tokens(
        "Admin", account_id=account_id, settings=settings, http_client=http_client
    )
    headers = {"api-access-token": tokens.api_access_token}

    # Act
    files = {field: (None, str(value)) for field, value in payload.items()}
    response = http_client.post(ENDPOINT_PATH, files=files, headers=headers)
    http_client.last_request = response.request

    # Assert 1 [Respuesta] -- status es duro, el resto de este caso es soft.
    assert response.status_code == 200, (
        f"TC-001: esperado 200, recibido {response.status_code} body={response.text}"
    )

    body = response.json()
    payload_resp = body.get("payload") or []
    step(
        assert_log,
        "Assert 1 [Respuesta] payload no vacío",
        check.is_true,
        len(payload_resp) >= 1,
        f"TC-001: 'payload' vacío en la respuesta: {body!r}",
    )
    if payload_resp:
        primer = payload_resp[0]
        step(
            assert_log,
            "Assert 1 [Respuesta] app_id",
            check.equal,
            primer.get("app_id"),
            app_id,
            f"TC-001: app_id inesperado en payload[0]: {primer.get('app_id')!r}",
        )
        step(
            assert_log,
            "Assert 1 [Respuesta] template presente",
            check.is_true,
            "template" in primer,
            f"TC-001: falta el objeto 'template' en payload[0]: {primer!r}",
        )

    # Assert 2 [Base de datos] -- oauth.templates_gupshup.
    fila = (
        db_conn.execute(
            text(
                "SELECT app_id, account_id, template_code_name, languageCode, category "
                "FROM templates_gupshup "
                "WHERE app_id = :app_id AND account_id = :account_id "
                "AND template_code_name = :name "
                "ORDER BY id DESC LIMIT 1"
            ),
            {"app_id": app_id, "account_id": account_id, "name": nombre_plantilla},
        )
        .mappings()
        .first()
    )
    if fila is None:
        step(
            assert_log,
            "Assert 2 [BD] fila encontrada",
            check.is_true,
            False,
            f"TC-001: no se encontró fila en oauth.templates_gupshup para "
            f"app_id={app_id!r} account_id={account_id!r} "
            f"template_code_name={nombre_plantilla!r}",
        )
    else:
        step(
            assert_log,
            "Assert 2 [BD] languageCode",
            check.equal,
            fila["languageCode"],
            "en_US",
            f"TC-001: languageCode inesperado: {fila['languageCode']!r}",
        )
        step(
            assert_log,
            "Assert 2 [BD] category",
            check.equal,
            fila["category"],
            "MARKETING",
            f"TC-001: category inesperado: {fila['category']!r}",
        )

    # Assert 3 [API log Chatwot] -- cliente HTTP propio, sin los event hooks
    # de framework.http.client(), para que el reporte no registre esta
    # petición en vez de la petición al endpoint bajo prueba (ver
    # proposal.md, decisión 7).
    audit_client = httpx.Client(timeout=30.0)
    try:
        entrada = find_audit_log(
            account_id,
            lambda entry: nombre_plantilla in (entry.get("comment") or ""),
            settings=settings,
            http_client=audit_client,
        )
    finally:
        audit_client.close()

    if entrada is None:
        step(
            assert_log,
            "Assert 3 [Auditoría] entrada encontrada",
            check.is_true,
            False,
            f"TC-001: no se encontró entrada de auditoría con 'comment' que "
            f"referencie {nombre_plantilla!r} para account_id={account_id!r}",
        )
    else:
        step(
            assert_log,
            "Assert 3 [Auditoría] auditable_type",
            check.equal,
            entrada.get("auditable_type"),
            "Template",
            f"TC-001: auditable_type inesperado: {entrada.get('auditable_type')!r}",
        )
        step(
            assert_log,
            "Assert 3 [Auditoría] source",
            check.equal,
            entrada.get("source"),
            "admin_chat",
            f"TC-001: source inesperado: {entrada.get('source')!r}",
        )
        step(
            assert_log,
            "Assert 3 [Auditoría] associated_id",
            check.equal,
            entrada.get("associated_id"),
            account_id,
            f"TC-001: associated_id inesperado: {entrada.get('associated_id')!r}",
        )
