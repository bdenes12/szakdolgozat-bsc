from policies.suggestion_rules import match_rule


def test_match_rule():
    assert ("DIRECT_IDENTIFIER", "partial_email", [], "name=email") == match_rule("email", "character varying")
    assert ("SENSITIVE", "noise", [0.15], "name=amount") == match_rule("paid_amount", "numeric")
    assert ("QUASI_IDENTIFIER", "dnoise", ["365 days"], "name=birth") == match_rule("birth_date", "date")
    assert ("SENSITIVE", "hash", [], "type=character varying") == match_rule("specialty", "character varying")
    assert ("TECHNICAL", None, [], "name=_id") == match_rule("patient_id", "integer")
    assert ("DIRECT_IDENTIFIER", "hash", [], "name=national_health") == match_rule(
        "national_health_id", "character varying"
    )
    assert ("TECHNICAL", None, [], "type=boolean") == match_rule("is_chronic", "boolean")
    assert ("TECHNICAL", None, [], "fallback") == match_rule("payload", "jsonb")
