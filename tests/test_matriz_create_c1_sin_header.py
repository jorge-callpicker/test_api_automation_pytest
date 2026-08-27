from __future__ import annotations

import pytest
import pytest_check as check

from framework import auth
from framework.matrix import OMIT, build_payload
from framework.variables import resolve

ENDPOINT_PATH = "/integrations/gupshup_integrations/templates/create"

# Campos que este contexto (c1-sin-header) nunca envia: no hay type/file/header
# en la peticion base -- salvo las 5 filas (I36-I40) que prueban "type" en si
# mismo, ya cubiertas como deviation explicita en CASES.
BASE_REQUEST = {
    "file": OMIT,
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

# Las 73 filas de inputs/Create/create-matriz-c1-sin-header.csv, transcritas una
# sola vez (ver design.md decision 1) -- el test no vuelve a leer el CSV.
CASES = [
    pytest.param("V1", 200, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="V1"),
    pytest.param("V2", 200, {"account_id": "{{MTZ-create-account_id-65}}", "name": "{{MTZ-create-name-nombre_unico_de_longitud_minima}}", "category": "{{MTZ-create-category-utility}}", "lang": "{{MTZ-create-lang-es_mx}}", "apps": "{{GLB-create-apps_ids_validos}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_con_variables_secuenciales_1}}", "body_var": "{{MTZ-create-body_var-arreglo_con_tres_elementos}}", "footer": "{{MTZ-create-footer-longitud_minima}}", "buttons": "{{MTZ-create-buttons-arreglo_con_un_boton_quick_reply}}"}, id="V2"),
    pytest.param("V3", 200, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_de_longitud_maxima}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-longitud_minima}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-longitud_maxima}}", "buttons": "{{MTZ-create-buttons-arreglo_con_botones_agrupados_por_tipo}}"}, id="V3"),
    pytest.param("V4", 200, {"account_id": "{{MTZ-create-account_id-65}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-utility}}", "lang": "{{MTZ-create-lang-es_mx}}", "apps": "{{GLB-create-apps_ids_validos}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-longitud_maxima}}", "body_var": "{{MTZ-create-body_var-elemento_de_longitud_maxima}}", "footer": "{{MTZ-create-footer-ausente}}", "buttons": "{{MTZ-create-buttons-arreglo_con_el_maximo_de_10}}"}, id="V4"),
    pytest.param("V5", 200, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_de_longitud_minima}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_con_el_maximo_de_10}}", "body_var": "{{MTZ-create-body_var-arreglo_con_10_elementos_correspondientes_a}}", "footer": "{{MTZ-create-footer-cadena_que_alterna_entre_mayusculas_y}}", "buttons": "{{MTZ-create-buttons-arreglo_con_botones_quick_reply}}"}, id="V5"),
    pytest.param("V6", 200, {"account_id": "{{MTZ-create-account_id-65}}", "name": "{{MTZ-create-name-nombre_unico_de_longitud_maxima}}", "category": "{{MTZ-create-category-utility}}", "lang": "{{MTZ-create-lang-es_mx}}", "apps": "{{GLB-create-apps_ids_validos}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_con_el_minimo_de_variables}}", "body_var": "{{MTZ-create-body_var-arreglo_con_exactamente_1_elemento}}", "footer": "{{MTZ-create-footer-cadena_de_solo_numeros}}", "buttons": "{{MTZ-create-buttons-arreglo_con_botones_quick_reply_y}}"}, id="V6"),
    pytest.param("V7", 200, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-cadena_de_caracteres_especiales}}", "buttons": "{{MTZ-create-buttons-arreglo_con_botones_url_y_phone}}"}, id="V7"),
    pytest.param("V8", 200, {"account_id": "{{MTZ-create-account_id-65}}", "name": "{{MTZ-create-name-nombre_unico_de_longitud_minima}}", "category": "{{MTZ-create-category-utility}}", "lang": "{{MTZ-create-lang-es_mx}}", "apps": "{{GLB-create-apps_ids_validos}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_con_variables_secuenciales_1}}", "body_var": "{{MTZ-create-body_var-arreglo_con_tres_elementos}}", "footer": "{{MTZ-create-footer-cadena_que_alterna_entre_letras}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="V8"),
    pytest.param("I1", 400, {"account_id": "{{MTZ-create-account_id-ausente}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I1"),
    pytest.param("I2", 400, {"account_id": "{{MTZ-create-account_id-vacio}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I2"),
    pytest.param("I3", 401, {"account_id": "{{GLB-create-account_id_inexistente}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I3"),
    pytest.param("I4", 401, {"account_id": "{{GLB-create-account_id_ajeno}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I4"),
    pytest.param("I5", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-longitud_2}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I5"),
    pytest.param("I6", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-longitud_180}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I6"),
    pytest.param("I7", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-contiene_mayusculas}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I7"),
    pytest.param("I8", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-contiene_caracteres_especiales_no_permitidos}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I8"),
    pytest.param("I9", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-contiene_espacios}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I9"),
    pytest.param("I10", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-ausente}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I10"),
    pytest.param("I11", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-vacio}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I11"),
    pytest.param("I12", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{GLB-create-name_ya_utilizado}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I12"),
    pytest.param("I13", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-contiene_signo_negativo}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I13"),
    pytest.param("I14", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-contiene_punto_decimal}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I14"),
    pytest.param("I15", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-valor_fuera_de_la_lista_blanca}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I15"),
    pytest.param("I16", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-ausente}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I16"),
    pytest.param("I17", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-vacio}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I17"),
    pytest.param("I18", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-tipo_de_dato_incorrecto}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I18"),
    pytest.param("I19", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-caracteres_especiales}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I19"),
    pytest.param("I20", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-valor_de_la_lista_blanca_en}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I20"),
    pytest.param("I21", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-valor_fuera_de_la_lista_blanca}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I21"),
    pytest.param("I22", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-ausente}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I22"),
    pytest.param("I23", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-vacio}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I23"),
    pytest.param("I24", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-valor_de_la_lista_blanca_en}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I24"),
    pytest.param("I25", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{MTZ-create-apps-ausente}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I25"),
    pytest.param("I26", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{MTZ-create-apps-vacio}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I26"),
    pytest.param("I27", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{MTZ-create-apps-arreglo_json_vacio}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I27"),
    pytest.param("I28", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{MTZ-create-apps-arreglo_con_un_elemento_que_no}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I28"),
    pytest.param("I29", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{MTZ-create-apps-no_es_un_arreglo_json_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I29"),
    pytest.param("I30", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_inactivo}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I30"),
    pytest.param("I31", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_otra_cuenta}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I31"),
    pytest.param("I32", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{MTZ-create-apps-arreglo_solo_letras}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I32"),
    pytest.param("I33", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{MTZ-create-apps-arreglo_solo_numeros}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I33"),
    pytest.param("I34", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{MTZ-create-apps-arreglo_con_elemento_con_caracteres_especiales}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I34"),
    pytest.param("I35", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido_mutado}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I35"),
    pytest.param("I36", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-valor_fuera_de_la_lista_blanca}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I36"),
    pytest.param("I37", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-vacio}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I37"),
    pytest.param("I38", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-tipo_de_dato_incorrecto}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I38"),
    pytest.param("I39", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-caracteres_especiales}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I39"),
    pytest.param("I40", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-valor_de_la_lista_blanca_en}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I40"),
    pytest.param("I41", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-ausente_cuando_category_authentication}}", "body_var": "{{MTZ-create-body_var-arreglo_con_un_elemento_correspondiente_a}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I41"),
    pytest.param("I42", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-vacio}}", "body_var": "{{MTZ-create-body_var-arreglo_con_un_elemento_correspondiente_a}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I42"),
    pytest.param("I43", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-longitud_1025}}", "body_var": "{{MTZ-create-body_var-arreglo_con_un_elemento_correspondiente_a}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I43"),
    pytest.param("I44", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-mas_de_10_variables}}", "body_var": "{{MTZ-create-body_var-arreglo_con_un_elemento_correspondiente_a}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I44"),
    pytest.param("I45", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-variables_fuera_de_secuencia}}", "body_var": "{{MTZ-create-body_var-arreglo_con_un_elemento_correspondiente_a}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I45"),
    pytest.param("I46", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_compuesto_unicamente_por_variables}}", "body_var": "{{MTZ-create-body_var-arreglo_con_un_elemento_correspondiente_a}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I46"),
    pytest.param("I47", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_con_el_minimo_de_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I47"),
    pytest.param("I48", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-vacio}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I48"),
    pytest.param("I49", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-no_es_un_arreglo_json_valido}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I49"),
    pytest.param("I50", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-cantidad_de_elementos_distinta_a_la}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I50"),
    pytest.param("I51", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-elemento_con_salto_de_linea}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I51"),
    pytest.param("I52", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-elemento_con_4_o_mas_espacios}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I52"),
    pytest.param("I53", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-vacio}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I53"),
    pytest.param("I54", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-longitud_61}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I54"),
    pytest.param("I55", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-contiene_una_variable_1}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I55"),
    pytest.param("I56", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-vacio}}"}, id="I56"),
    pytest.param("I57", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-arreglo_json_vacio}}"}, id="I57"),
    pytest.param("I58", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-no_es_un_arreglo_json_valido}}"}, id="I58"),
    pytest.param("I59", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-mas_de_10_botones_en_total}}"}, id="I59"),
    pytest.param("I60", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-mas_de_10_botones_quick_reply}}"}, id="I60"),
    pytest.param("I61", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-mas_de_2_botones_url}}"}, id="I61"),
    pytest.param("I62", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-mas_de_1_boton_phone_number}}"}, id="I62"),
    pytest.param("I63", 400, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-botones_del_mismo_tipo_no_agrupados}}"}, id="I63"),
    pytest.param("I64", 401, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I64"),
    pytest.param("I65", 401, {"account_id": "{{MTZ-create-account_id-minimo_del_rango}}", "name": "{{MTZ-create-name-nombre_unico_no_usado_antes}}", "category": "{{MTZ-create-category-marketing}}", "lang": "{{MTZ-create-lang-en_us}}", "apps": "{{GLB-create-app_id_valido}}", "type": "{{MTZ-create-type-ausente}}", "body": "{{MTZ-create-body-texto_tipico_sin_variables}}", "body_var": "{{MTZ-create-body_var-ausente}}", "footer": "{{MTZ-create-footer-texto_tipico_sin_variables}}", "buttons": "{{MTZ-create-buttons-ausente}}"}, id="I65"),
]


# Los tres casos que el rol SuperAdmin no ejecuta (ver design.md decision 4):
#   I4  -- account_id de una cuenta ajena. SuperAdmin SI alcanza cuentas ajenas,
#          asi que el endpoint responderia 200 y no el 401 que declara la matriz.
#          Verificar ese 200 seria probar cruce de cuentas, fuera de alcance.
#   I64 -- peticion sin header api-access-token.
#   I65 -- header con token estatico invalido.
# Los dos ultimos nunca abren sesion: su request es identico byte a byte en
# cualquier rol, asi que repetirlos no aporta informacion.
_OMITIDOS_SA = {"I4", "I64", "I65"}

# CASES_SA se deriva de CASES en vez de transcribirse (ver design.md decision 7).
# La invariante que verifica este change es que las desviaciones de cada fila
# sean identicas entre roles; derivarlas la vuelve una propiedad estructural del
# codigo en lugar de algo que hay que confiar que la transcripcion respeto.
# La numeracion es alineada, no contigua: SA-I<n> designa el mismo caso del CSV
# que I<n>, y al omitirse I4 el id SA-I4 simplemente no existe (decision 3).
CASES_SA = [
    pytest.param(f"SA-{case_id}", expected_status, deviations, id=f"SA-{case_id}")
    for case_id, expected_status, deviations in (case.values for case in CASES)
    if case_id not in _OMITIDOS_SA
]


def _resolve_all(deviations: dict) -> dict:
    return {field: resolve(value, tc_id=None) for field, value in deviations.items()}


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

    El cuerpo vive aqui una sola vez para que los dos roles emitan exactamente el
    mismo request salvo la credencial de sesion: la invariante que verifica el
    change `add-test-create-matriz-c1-sin-header-super-admin` exige esa identidad
    estructural, y dos copias del cuerpo no podrian garantizarla (ver design.md
    decision 2).
    """
    resolved = _resolve_all(deviations)
    payload = build_payload(BASE_REQUEST, resolved, FIELD_TYPES)

    account_id_en_payload = resolved["account_id"]
    glb_account_id_valido = resolve("{{GLB-account_id_valido}}", tc_id=None)
    # La sesion siempre se autentica contra una cuenta real y accesible para el
    # token de prueba. account_id_inexistente/ajeno tambien son enteros
    # positivos, pero el token no tiene acceso a esas cuentas -- por eso la
    # comparacion es contra la cuenta valida conocida, no un simple chequeo de
    # "es entero positivo". Cuando el valor de la fila SI coincide con esa
    # cuenta (los casos que prueban que account_id coincida con la sesion), se
    # reutiliza; en cualquier otro caso (ausente/vacio/inexistente/ajeno/
    # mutado) se usa la cuenta de prueba por defecto para poder llegar a la
    # validacion de campos (ver design.md decision 5).
    if account_id_en_payload == glb_account_id_valido:
        session_account_id = account_id_en_payload
    else:
        session_account_id = glb_account_id_valido

    # I64/I65 no abren sesion: el request es identico byte a byte en cualquier
    # rol, asi que solo existen en el arreglo del rol base (ver design.md
    # decision 4). Ningun id `SA-*` alcanza estas dos ramas.
    if case_id == "I64":
        headers = {}
    elif case_id == "I65":
        headers = {
            "api-access-token": resolve(
                "{{MTZ-create-api_access_token-token_invalido_o_expirado}}", tc_id=None
            )
        }
    else:
        tokens = auth.obtain_session_tokens(
            role, settings=settings, http_client=http_client, account_id=session_account_id
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
    # framework.mirror.assert_mirror (ver design.md decision 4 del change de
    # `Admin`). Aplica igual a los casos de exito de cualquier rol.


@pytest.mark.parametrize(("case_id", "expected_status", "deviations"), CASES)
def test_matriz_create_c1_sin_header(settings, http_client, case_id, expected_status, deviations):
    _ejecutar_caso(
        "Admin",
        settings=settings,
        http_client=http_client,
        case_id=case_id,
        expected_status=expected_status,
        deviations=deviations,
    )


@pytest.mark.parametrize(("case_id", "expected_status", "deviations"), CASES_SA)
def test_matriz_create_c1_sin_header_super_admin(
    settings, http_client, case_id, expected_status, deviations
):
    """Misma matriz, rol SuperAdmin.

    Verifica que un rol elevado no relaja ninguna validacion de campo: las 70
    filas aplicables deben producir el mismo codigo HTTP que con Admin. Los 70
    casos abren sesion real -- ninguno alcanza las ramas sin sesion del helper,
    porque I64/I65 estan en `_OMITIDOS_SA`.
    """
    _ejecutar_caso(
        "SuperAdmin",
        settings=settings,
        http_client=http_client,
        case_id=case_id,
        expected_status=expected_status,
        deviations=deviations,
    )
