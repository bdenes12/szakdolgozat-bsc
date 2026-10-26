import pytest

from policies.suggestion_rules import match_rule

SUGGESTION_CASES = [
    ("emial", "text", ("DIRECT_IDENTIFIER", "partial_email", [], "name~email ratio:(0.80)")),
    ("frist_name", "text", ("DIRECT_IDENTIFIER", "fake_first_name", [], "name~first_name ratio:(0.90)")),
    ("lastname", "text", ("DIRECT_IDENTIFIER", "fake_last_name", [], "name~last_name ratio:(0.94)")),
    ("adress", "text", ("QUASI_IDENTIFIER", "fake_address", [], "name~address ratio:(0.92)")),
    ("tag", "text", ("SENSITIVE", "hash", [], "type=text")),
    ("mail_city", "text", ("QUASI_IDENTIFIER", "fake_city", [], "name=city")),
    ("phone_count", "integer", ("SENSITIVE", "noise", [0.15], "type=integer")),
    ("fee", "text", ("SENSITIVE", "hash", [], "type=text")),
    ("address_id", "integer", ("TECHNICAL", None, [], "name=_id")),
    ("kid", "integer", ("SENSITIVE", "noise", [0.15], "type=integer")),
    ("notes", "text", ("SENSITIVE", "lorem_ipsum", [1], "name=note")),
    ("country", "character varying", ("QUASI_IDENTIFIER", "fake_country", [], "name=country")),
]


@pytest.mark.parametrize("column, dtype, expected", SUGGESTION_CASES)
def test_match_rule(column, dtype, expected):
    assert match_rule(column, dtype) == expected
