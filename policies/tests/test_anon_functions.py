import pytest

from policies.anon_functions import expected_parameters

CASES = [
    # nincs paraméter
    ("fake_city", []),
    # oszlopparaméteres, egyetlen argumentum -> semmi nem marad
    ("partial_email", []),
    ("hash", []),
    # oszlopparaméteres, több szóból álló típus
    ("noise", [("ratio", "double precision", True)]),
    # oszlopparaméteres, több kötelező paraméter
    ("partial", [("prefix", "integer", True), ("padding", "text", True), ("suffix", "integer", True)]),
    ("digest", [("salt", "text", True), ("algorithm", "text", True)]),
    # oszlopparaméteres, interval típus
    ("dnoise", [("noise_range", "interval", True)]),
    # oszlopparaméteres, DEFAULT idézőjeles értékkel
    ("generalize_daterange", [("step", "text", False)]),
    # oszlopparaméteres, DEFAULT számmal
    ("generalize_int4range", [("step", "integer", False)]),
    # oszlopparaméteres, több szavas oszloptípus, ami kimarad
    ("generalize_tsrange", [("step", "text", False)]),
    # oszlopparaméteres, DEFAULT NULL
    ("pseudo_city", [("salt", "text", False)]),
    # nem oszlopparaméteres, egy kötelező
    ("random_string", [("l", "integer", True)]),
    ("random_phone_prefix", [("prefix", "text", True)]),
    # nem oszlopparaméteres, range típus
    ("random_string_range", [("r", "int4range", True)]),
    # nem oszlopparaméteres, két kötelező
    ("random_int_between", [("start", "integer", True), ("stop", "integer", True)]),
    ("random_date_between", [("date_start", "timestamptz", True), ("date_end", "timestamptz", True)]),
    # csupa opcionális
    ("lorem_ipsum", [("paragraphs", "integer", False), ("words", "integer", False), ("characters", "integer", False)]),
    # ismeretlen függvény
    ("nincs_ilyen", []),
]


@pytest.mark.parametrize("function_name, expected", CASES)
def test_expected_parameters(function_name, expected):
    assert expected_parameters(function_name) == expected
