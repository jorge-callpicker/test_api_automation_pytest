from __future__ import annotations

import json
import re

import pytest

from framework.matrix import OMIT, build_payload
from framework.variables import resolve

_FAKE_SETTINGS = object()  # no se toca en la rama MTZ-/TC-, solo en GLB-


def test_build_payload_ausente_omite_la_key():
    base = {"account_id": 65, "name": "algo"}
    result = build_payload(base, {"account_id": OMIT}, field_types={})
    assert "account_id" not in result
    assert result["name"] == "algo"


def test_build_payload_vacio_emite_string_vacio():
    result = build_payload({}, {"footer": ""}, field_types={"footer": "String"})
    assert result["footer"] == ""


def test_build_payload_serializa_arreglo_json_nativo_como_string():
    field_types = {"apps": "String (arreglo JSON)"}
    result = build_payload({}, {"apps": ["uuid-1"]}, field_types)
    assert result["apps"] == json.dumps(["uuid-1"])
    assert isinstance(result["apps"], str)


def test_build_payload_no_reserializa_string_deliberadamente_invalido():
    field_types = {"apps": "String (arreglo JSON)"}
    result = build_payload({}, {"apps": "no es un arreglo json"}, field_types)
    assert result["apps"] == "no es un arreglo json"


def test_build_payload_deviation_sobreescribe_base():
    base = {"category": "MARKETING"}
    result = build_payload(base, {"category": "UTILITY"}, field_types={})
    assert result["category"] == "UTILITY"


def test_resolve_mtz_literal():
    variables = {"matrix_values": {"MTZ-test-account_id-min": 1}}
    value = resolve(
        "{{MTZ-test-account_id-min}}", tc_id=None, settings=_FAKE_SETTINGS, variables=variables
    )
    assert value == 1


def test_resolve_mtz_generador_dispatch():
    variables = {
        "matrix_values": {
            "MTZ-test-name-unico": {"generator": "unique_lowercase", "params": {"length": 7}}
        }
    }
    value = resolve(
        "{{MTZ-test-name-unico}}", tc_id=None, settings=_FAKE_SETTINGS, variables=variables
    )
    assert re.fullmatch(r"[a-z0-9]{7}", value)


def test_resolve_mtz_generador_no_cachea_entre_llamadas():
    variables = {
        "matrix_values": {
            "MTZ-test-name-unico": {"generator": "unique_lowercase", "params": {"length": 12}}
        }
    }
    first = resolve(
        "{{MTZ-test-name-unico}}", tc_id=None, settings=_FAKE_SETTINGS, variables=variables
    )
    second = resolve(
        "{{MTZ-test-name-unico}}", tc_id=None, settings=_FAKE_SETTINGS, variables=variables
    )
    assert first != second


def test_resolve_mtz_no_declarada_lanza_keyerror():
    with pytest.raises(KeyError):
        resolve(
            "{{MTZ-test-account_id-no_declarada}}",
            tc_id=None,
            settings=_FAKE_SETTINGS,
            variables={"matrix_values": {}},
        )


def test_resolve_glb_no_se_afecta_por_la_rama_mtz():
    class FakeSettings:
        GLB_ACCOUNT_ID_VALIDO = 65

    variables = {"globals": {}, "matrix_values": {}}
    value = resolve(
        "{{GLB-account_id_valido}}", tc_id=None, settings=FakeSettings(), variables=variables
    )
    assert value == 65
