from __future__ import annotations

import pytest
import pytest_check as check

from framework import auth
from framework.matrix import OMIT, build_payload
from framework.variables import resolve

ENDPOINT_PATH = "/integrations/gupshup_integrations/templates/create"

# Campos que este contexto (c2-header-texto) nunca envia: file no aplica a
# type=TEXT, y security/expiration son exclusivos de AUTHENTICATION.
BASE_REQUEST = {
    "file": OMIT,
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

# Las 18 filas de inputs/Create/create-matriz-c2-header-texto.csv, transcritas
# una sola vez -- el test no vuelve a leer el CSV. Ninguna fila de este CSV
# rompe la autenticacion (a diferencia de c1), asi que todas abren sesion real.
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
            "type": "{{MTZ-create-type-text}}",
            "header": "{{MTZ-create-header-texto_tipico_sin_variables}}",
            "header_var": "{{MTZ-create-header_var-ausente}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}",
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
            "type": "{{MTZ-create-type-text}}",
            "header": "{{MTZ-create-header-texto_tipico_con_una_unica_variable}}",
            "header_var": "{{MTZ-create-header_var-longitud_minima}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="V2",
    ),
    pytest.param(
        "V3",
        200,
        {
            "account_id": "{{MTZ-create-account_id-minimo_del_rango}}",
            "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}",
            "category": "{{MTZ-create-category-marketing}}",
            "lang": "{{MTZ-create-lang-en_us}}",
            "apps": "{{GLB-create-app_id_valido}}",
            "type": "{{MTZ-create-type-text}}",
            "header": "{{MTZ-create-header-longitud_minima}}",
            "header_var": "{{MTZ-create-header_var-ausente}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="V3",
    ),
    pytest.param(
        "V4",
        200,
        {
            "account_id": "{{MTZ-create-account_id-minimo_del_rango}}",
            "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}",
            "category": "{{MTZ-create-category-marketing}}",
            "lang": "{{MTZ-create-lang-en_us}}",
            "apps": "{{GLB-create-app_id_valido}}",
            "type": "{{MTZ-create-type-text}}",
            "header": "{{MTZ-create-header-texto_tipico_con_una_unica_variable}}",
            "header_var": "{{MTZ-create-header_var-longitud_maxima}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="V4",
    ),
    pytest.param(
        "V5",
        200,
        {
            "account_id": "{{MTZ-create-account_id-minimo_del_rango}}",
            "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}",
            "category": "{{MTZ-create-category-marketing}}",
            "lang": "{{MTZ-create-lang-en_us}}",
            "apps": "{{GLB-create-app_id_valido}}",
            "type": "{{MTZ-create-type-text}}",
            "header": "{{MTZ-create-header-longitud_maxima_con_variable}}",
            "header_var": "{{MTZ-create-header_var-cadena_que_alterna_entre_mayusculas_y}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="V5",
    ),
    pytest.param(
        "V6",
        200,
        {
            "account_id": "{{MTZ-create-account_id-minimo_del_rango}}",
            "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}",
            "category": "{{MTZ-create-category-marketing}}",
            "lang": "{{MTZ-create-lang-en_us}}",
            "apps": "{{GLB-create-app_id_valido}}",
            "type": "{{MTZ-create-type-text}}",
            "header": "{{MTZ-create-header-cadena_que_alterna_con_variable}}",
            "header_var": "{{MTZ-create-header_var-caracteres_especiales}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="V6",
    ),
    pytest.param(
        "V7",
        200,
        {
            "account_id": "{{MTZ-create-account_id-minimo_del_rango}}",
            "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}",
            "category": "{{MTZ-create-category-marketing}}",
            "lang": "{{MTZ-create-lang-en_us}}",
            "apps": "{{GLB-create-app_id_valido}}",
            "type": "{{MTZ-create-type-text}}",
            "header": "{{MTZ-create-header-caracteres_especiales_con_variable}}",
            "header_var": "{{MTZ-create-header_var-valor_tipico_correspondiente_a_la_variable}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="V7",
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
            "type": "{{MTZ-create-type-text}}",
            "header": "{{MTZ-create-header-ausente_cuando_type_text}}",
            "header_var": "{{MTZ-create-header_var-valor_tipico_correspondiente_a_la_variable}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}",
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
            "type": "{{MTZ-create-type-text}}",
            "header": "{{MTZ-create-header-vacio}}",
            "header_var": "{{MTZ-create-header_var-valor_tipico_correspondiente_a_la_variable}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}",
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
            "type": "{{MTZ-create-type-text}}",
            "header": "{{MTZ-create-header-longitud_61}}",
            "header_var": "{{MTZ-create-header_var-valor_tipico_correspondiente_a_la_variable}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="I3",
    ),
    pytest.param(
        "I4",
        400,
        {
            "account_id": "{{MTZ-create-account_id-minimo_del_rango}}",
            "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}",
            "category": "{{MTZ-create-category-marketing}}",
            "lang": "{{MTZ-create-lang-en_us}}",
            "apps": "{{GLB-create-app_id_valido}}",
            "type": "{{MTZ-create-type-text}}",
            "header": "{{MTZ-create-header-contiene_salto_de_linea}}",
            "header_var": "{{MTZ-create-header_var-valor_tipico_correspondiente_a_la_variable}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="I4",
    ),
    pytest.param(
        "I5",
        400,
        {
            "account_id": "{{MTZ-create-account_id-minimo_del_rango}}",
            "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}",
            "category": "{{MTZ-create-category-marketing}}",
            "lang": "{{MTZ-create-lang-en_us}}",
            "apps": "{{GLB-create-app_id_valido}}",
            "type": "{{MTZ-create-type-text}}",
            "header": "{{MTZ-create-header-contiene_4_o_mas_espacios}}",
            "header_var": "{{MTZ-create-header_var-valor_tipico_correspondiente_a_la_variable}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="I5",
    ),
    pytest.param(
        "I6",
        400,
        {
            "account_id": "{{MTZ-create-account_id-minimo_del_rango}}",
            "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}",
            "category": "{{MTZ-create-category-marketing}}",
            "lang": "{{MTZ-create-lang-en_us}}",
            "apps": "{{GLB-create-app_id_valido}}",
            "type": "{{MTZ-create-type-text}}",
            "header": "{{MTZ-create-header-contiene_dos_o_mas_variables}}",
            "header_var": "{{MTZ-create-header_var-valor_tipico_correspondiente_a_la_variable}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="I6",
    ),
    pytest.param(
        "I7",
        400,
        {
            "account_id": "{{MTZ-create-account_id-minimo_del_rango}}",
            "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}",
            "category": "{{MTZ-create-category-marketing}}",
            "lang": "{{MTZ-create-lang-en_us}}",
            "apps": "{{GLB-create-app_id_valido}}",
            "type": "{{MTZ-create-type-text}}",
            "header": "{{MTZ-create-header-texto_tipico_con_variable}}",
            "header_var": "{{MTZ-create-header_var-ausente_cuando_header_contiene_variable}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="I7",
    ),
    pytest.param(
        "I8",
        400,
        {
            "account_id": "{{MTZ-create-account_id-minimo_del_rango}}",
            "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}",
            "category": "{{MTZ-create-category-marketing}}",
            "lang": "{{MTZ-create-lang-en_us}}",
            "apps": "{{GLB-create-app_id_valido}}",
            "type": "{{MTZ-create-type-text}}",
            "header": "{{MTZ-create-header-texto_tipico_sin_variables}}",
            "header_var": "{{MTZ-create-header_var-vacio}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="I8",
    ),
    pytest.param(
        "I9",
        400,
        {
            "account_id": "{{MTZ-create-account_id-minimo_del_rango}}",
            "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}",
            "category": "{{MTZ-create-category-marketing}}",
            "lang": "{{MTZ-create-lang-en_us}}",
            "apps": "{{GLB-create-app_id_valido}}",
            "type": "{{MTZ-create-type-text}}",
            "header": "{{MTZ-create-header-texto_tipico_sin_variables}}",
            "header_var": "{{MTZ-create-header_var-longitud_61}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="I9",
    ),
    pytest.param(
        "I10",
        400,
        {
            "account_id": "{{MTZ-create-account_id-minimo_del_rango}}",
            "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}",
            "category": "{{MTZ-create-category-marketing}}",
            "lang": "{{MTZ-create-lang-en_us}}",
            "apps": "{{GLB-create-app_id_valido}}",
            "type": "{{MTZ-create-type-text}}",
            "header": "{{MTZ-create-header-texto_tipico_sin_variables}}",
            "header_var": "{{MTZ-create-header_var-contiene_salto_de_linea}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="I10",
    ),
    pytest.param(
        "I11",
        400,
        {
            "account_id": "{{MTZ-create-account_id-minimo_del_rango}}",
            "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}",
            "category": "{{MTZ-create-category-marketing}}",
            "lang": "{{MTZ-create-lang-en_us}}",
            "apps": "{{GLB-create-app_id_valido}}",
            "type": "{{MTZ-create-type-text}}",
            "header": "{{MTZ-create-header-texto_tipico_sin_variables}}",
            "header_var": "{{MTZ-create-header_var-contiene_4_o_mas_espacios}}",
            "body": "{{MTZ-create-body-texto_tipico_sin_variables}}",
            "body_var": "{{MTZ-create-body_var-ausente}}",
            "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}",
            "buttons": "{{MTZ-create-buttons-ausente}}",
        },
        id="I11",
    ),
]


def _resolve_all(deviations: dict) -> dict:
    return {field: resolve(value, tc_id=None) for field, value in deviations.items()}


# CASES_SA se deriva de CASES en vez de transcribirse (mismo patron que
# tests/test_matriz_create_c1_sin_header.py, decision 7 de su design.md). A
# diferencia de c1, ninguna fila se omite: c2-header-texto no rompe la
# autenticacion en ninguna de sus 18 filas y todas usan el mismo account_id
# (MTZ-create-account_id-minimo_del_rango = 65 = GLB-account_id_valido), asi
# que no hay caso analogo al cruce de cuentas de I4 en c1. La numeracion queda
# alineada y sin huecos: SA-V1..SA-V7, SA-I1..SA-I11.
CASES_SA = [
    pytest.param(f"SA-{case_id}", expected_status, deviations, id=f"SA-{case_id}")
    for case_id, expected_status, deviations in (case.values for case in CASES)
]


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

    El cuerpo vive aqui una sola vez para que los dos roles emitan exactamente
    el mismo request salvo la credencial de sesion -- mismo patron que
    tests/test_matriz_create_c1_sin_header.py. A diferencia de c1, no hace
    falta logica de fallback de cuenta de sesion ni ramas sin sesion: las 18
    filas de este CSV ya resuelven account_id al mismo valor y ninguna omite
    el header api-access-token.
    """
    resolved = _resolve_all(deviations)
    payload = build_payload(BASE_REQUEST, resolved, FIELD_TYPES)

    tokens = auth.obtain_session_tokens(
        role, settings=settings, http_client=http_client, account_id=resolved["account_id"]
    )
    headers = {"api-access-token": tokens.api_access_token}

    files = {field: (None, str(value)) for field, value in payload.items()}
    response = http_client.post(ENDPOINT_PATH, files=files, headers=headers)
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
    # framework.mirror.assert_mirror. Aplica igual a los casos de exito de
    # cualquier rol.


@pytest.mark.parametrize(("case_id", "expected_status", "deviations"), CASES)
def test_matriz_create_c2_header_texto(settings, http_client, case_id, expected_status, deviations):
    """Contexto c2-header-texto: type=TEXT con header/header_var.

    A diferencia de c1-sin-header, ninguna fila de este CSV rompe la
    autenticacion -- las 18 abren sesion real contra GLB-account_id_valido
    con el rol Admin (ver proposal.md, "Alcance de rol").
    """
    _ejecutar_caso(
        "Admin",
        settings=settings,
        http_client=http_client,
        case_id=case_id,
        expected_status=expected_status,
        deviations=deviations,
    )


@pytest.mark.parametrize(("case_id", "expected_status", "deviations"), CASES_SA)
def test_matriz_create_c2_header_texto_super_admin(
    settings, http_client, case_id, expected_status, deviations
):
    """Misma matriz, rol SuperAdmin.

    Verifica que un rol elevado no relaja ninguna validacion de campo: las 18
    filas producen el mismo codigo HTTP que con Admin. Cero casos omitidos
    (ver proposal.md, "Cero omisiones").
    """
    _ejecutar_caso(
        "SuperAdmin",
        settings=settings,
        http_client=http_client,
        case_id=case_id,
        expected_status=expected_status,
        deviations=deviations,
    )
