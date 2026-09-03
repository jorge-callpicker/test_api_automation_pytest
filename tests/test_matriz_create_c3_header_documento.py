from __future__ import annotations

import mimetypes
from pathlib import Path

import pytest
import pytest_check as check

from framework import auth
from framework.assets import load_asset
from framework.matrix import OMIT, build_payload
from framework.variables import resolve

ENDPOINT_PATH = "/integrations/gupshup_integrations/templates/create"

# Casos cuyo archivo sembrado pesa varias decenas de MB o mas (ver los
# GLB-create-file-* en variables.yaml) -- necesitan un timeout mayor al
# default de 30s del cliente HTTP compartido. Override por-request, sin
# tocar framework/http.py ni la fixture http_client (design.md, Risks).
# V1 quedo fuera de este set: tras sembrar file-pdf_valido_tipico_7mb.pdf
# (~7.9MB), vuelve a ser un archivo genuinamente tipico y no lo necesita.
LARGE_FILE_CASE_IDS = {"V2", "I3", "V1-archivo-grande"}
LARGE_FILE_TIMEOUT_SECONDS = 300.0

# Campos que este contexto (c3-header-documento) nunca envia: header/header_var
# no aplican cuando type=DOCUMENT, y security/expiration son exclusivos de
# AUTHENTICATION.
BASE_REQUEST = {
    "header": OMIT,
    "header_var": OMIT,
    "security": OMIT,
    "expiration": OMIT,
}

FIELD_TYPES = {
    "account_id": "Integer",
    "name": "String",
    "category": "String",
    "lang": "String",
    "apps": "String (arreglo JSON)",
    "type": "String",
    "file": "File",
    "header": "String",
    "header_var": "String",
    "body": "String",
    "body_var": "String (arreglo JSON)",
    "footer": "String",
    "security": "String",
    "expiration": "Integer",
    "buttons": "String (arreglo JSON)",
}

# Las 5 filas de inputs/Create/create-matriz-c3-header-documento.csv,
# transcritas una sola vez -- el test no vuelve a leer el CSV. Ninguna fila
# de este CSV rompe la autenticacion, asi que las 5 abren sesion real.
CASES = [
    pytest.param(
        "V1",
        200,
        {
            "account_id": "{{MTZ-create-account_id-minimo_del_rango}}",
            "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}",
            "category": "{{MTZ-create-category-marketing}}",
            "lang": "{{MTZ-create-lang-en_us}}",
            "apps": "{{GLB-create-app_id_valido}}",
            "type": "{{MTZ-create-type-document}}",
            "file": "{{GLB-create-file-pdf_valido_tipico}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-ausente}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="V1",
    ),
    pytest.param(
        "V2",
        200,
        {
            "account_id": "{{MTZ-create-account_id-minimo_del_rango}}",
            "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}",
            "category": "{{MTZ-create-category-marketing}}",
            "lang": "{{MTZ-create-lang-en_us}}",
            "apps": "{{GLB-create-app_id_valido}}",
            "type": "{{MTZ-create-type-document}}",
            "file": "{{GLB-create-file-pdf_max_100mb}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-ausente}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="V2",
    ),
    pytest.param(
        "I1",
        400,
        {
            "account_id": "{{MTZ-create-account_id-minimo_del_rango}}",
            "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}",
            "category": "{{MTZ-create-category-marketing}}",
            "lang": "{{MTZ-create-lang-en_us}}",
            "apps": "{{GLB-create-app_id_valido}}",
            "type": "{{MTZ-create-type-document}}",
            "file": "{{MTZ-create-file-ausente_cuando_type_document}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-ausente}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="I1",
    ),
    pytest.param(
        "I2",
        400,
        {
            "account_id": "{{MTZ-create-account_id-minimo_del_rango}}",
            "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}",
            "category": "{{MTZ-create-category-marketing}}",
            "lang": "{{MTZ-create-lang-en_us}}",
            "apps": "{{GLB-create-app_id_valido}}",
            "type": "{{MTZ-create-type-document}}",
            "file": "{{GLB-create-file-tipo_invalido}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-ausente}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="I2",
    ),
    pytest.param(
        "I3",
        400,
        {
            "account_id": "{{MTZ-create-account_id-minimo_del_rango}}",
            "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}",
            "category": "{{MTZ-create-category-marketing}}",
            "lang": "{{MTZ-create-lang-en_us}}",
            "apps": "{{GLB-create-app_id_valido}}",
            "type": "{{MTZ-create-type-document}}",
            "file": "{{GLB-create-file-pdf_excede_100mb}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-ausente}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="I3",
    ),
]

# Caso suplementario -- NO proviene de una fila de
# inputs/Create/create-matriz-c3-header-documento.csv (que solo tiene las 5
# filas de CASES arriba). Agregado a pedido del QA durante el apply de este
# change para cubrir un archivo valido de tamano grande pero dentro del
# rango permitido (docs.md: DOCUMENT/PDF <= 100MB), distinto del limite
# exacto que ya cubre V2. Id deliberadamente fuera del esquema V<n>/I<n>
# -- que es posicional y se deriva del CSV -- para que no colisione si el
# CSV se regenera con una fila nueva en esa posicion. Ver proposal.md,
# "Caso suplementario (no derivado del CSV)".
CASES_SUPLEMENTARIOS = [
    pytest.param(
        "V1-archivo-grande",
        200,
        {
            "account_id": "{{MTZ-create-account_id-minimo_del_rango}}",
            "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}",
            "category": "{{MTZ-create-category-marketing}}",
            "lang": "{{MTZ-create-lang-en_us}}",
            "apps": "{{GLB-create-app_id_valido}}",
            "type": "{{MTZ-create-type-document}}",
            "file": "{{GLB-create-file-pdf_valido_50mb}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-ausente}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="V1-archivo-grande",
    ),
]

CASES_TODAS = CASES + CASES_SUPLEMENTARIOS


def _resolve_all(deviations: dict) -> dict:
    return {field: resolve(value, tc_id=None) for field, value in deviations.items()}


def _build_files(payload: dict, field_types: dict) -> dict:
    """Arma el `files=` de la peticion, con dispatch para el campo `file`.

    Todo campo viaja como parte de texto (`(None, str(value))`), salvo el
    de tipo `File`: ese necesita una parte real con filename/content-type,
    leida desde `assets/` via `framework.assets.load_asset` -- nunca
    generada por el proyecto (ver design.md, Decision 2).
    """
    files = {}
    for field, value in payload.items():
        if field_types.get(field) == "File":
            content_type, _ = mimetypes.guess_type(value)
            files[field] = (
                Path(value).name,
                load_asset(value),
                content_type or "application/octet-stream",
            )
        else:
            files[field] = (None, str(value))
    return files


def _ejecutar_caso(
    role: str,
    *,
    settings,
    http_client,
    case_id: str,
    expected_status: int,
    deviations: dict,
) -> None:
    """Ejecuta una fila de la matriz con el rol indicado.

    Alcance de este change: solo rol Admin (ver proposal.md, "Alcance de
    rol"). El parametro `role` se mantiene explicito, igual que en
    tests/test_matriz_create_c2_header_texto.py, para que un change hermano
    de SuperAdmin pueda reutilizar esta funcion sin duplicarla.
    """
    resolved = _resolve_all(deviations)
    payload = build_payload(BASE_REQUEST, resolved, FIELD_TYPES)

    tokens = auth.obtain_session_tokens(
        role, settings=settings, http_client=http_client, account_id=resolved["account_id"]
    )
    headers = {"api-access-token": tokens.api_access_token}

    files = _build_files(payload, FIELD_TYPES)
    post_kwargs = {"files": files, "headers": headers}
    if case_id in LARGE_FILE_CASE_IDS:
        post_kwargs["timeout"] = LARGE_FILE_TIMEOUT_SECONDS

    response = http_client.post(ENDPOINT_PATH, **post_kwargs)
    http_client.last_request = response.request

    assert response.status_code == expected_status, (
        f"{case_id}: esperado {expected_status}, recibido {response.status_code} "
        f"body={response.text}"
    )

    try:
        response.json()
        es_json = True
    except ValueError:
        es_json = False
    check.is_true(es_json, f"{case_id}: la respuesta no es JSON valido: {response.text[:500]!r}")

    # docs.md declara "Mirror keys: ninguna" para este endpoint -- no se invoca
    # framework.mirror.assert_mirror.


@pytest.mark.parametrize(("case_id", "expected_status", "deviations"), CASES_TODAS)
def test_matriz_create_c3_header_documento(
    settings, http_client, case_id, expected_status, deviations
):
    """Contexto c3-header-documento: type=DOCUMENT con file.

    Incluye las 5 filas de la matriz (`V1`, `V2`, `I1`, `I2`, `I3`) mas 1
    caso suplementario (`V1-archivo-grande`) que no proviene del CSV -- ver
    CASES_SUPLEMENTARIOS arriba y proposal.md, "Caso suplementario".

    Requiere que el QA haya sembrado los 5 archivos descritos en
    variables.yaml -> globals (GLB-create-file-*) bajo assets/create/file/
    antes de ejecutar -- ver tasks.md, "4. Siembra de assets (QA)". Sin
    eso, los casos con archivo fallan con FileNotFoundError explicito desde
    framework.assets.load_asset, no con un error ambiguo de httpx.
    """
    _ejecutar_caso(
        "Admin",
        settings=settings,
        http_client=http_client,
        case_id=case_id,
        expected_status=expected_status,
        deviations=deviations,
    )
