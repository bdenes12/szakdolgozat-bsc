import Levenshtein

TEXT = ("character varying", "text")
NUM = ("numeric", "integer", "bigint", "smallint", "double precision", "real")
DATE = ("date", "timestamp without time zone", "timestamp with time zone")

RULES = [
    (("email",), TEXT, "DIRECT_IDENTIFIER", "partial_email", []),
    (("full_name", "patient_name", "contact_name"), TEXT, "DIRECT_IDENTIFIER", "dummy_name", []),
    (("first_name", "firstname", "given_name", "middle_name"), TEXT, "DIRECT_IDENTIFIER", "fake_first_name", []),
    (
        ("last_name", "surname", "family_name", "mother_name", "maiden_name"),
        TEXT,
        "DIRECT_IDENTIFIER",
        "fake_last_name",
        [],
    ),
    (("username", "user_name", "login"), TEXT, "DIRECT_IDENTIFIER", "dummy_username", []),
    (("phone", "mobile", "fax"), TEXT, "DIRECT_IDENTIFIER", "random_phone", []),
    (("iban", "account_number", "bank_account"), TEXT, "DIRECT_IDENTIFIER", "fake_iban", []),
    (("credit_card", "card_number"), TEXT, "DIRECT_IDENTIFIER", "dummy_credit_card_number", []),
    (
        (
            "taj",
            "national_health",
            "ssn",
            "passport",
            "license_number",
            "policy_number",
            "tax_number",
            "tax_id",
            "personal_id",
        ),
        TEXT,
        "DIRECT_IDENTIFIER",
        "hash",
        [],
    ),
    (
        ("amount", "price", "salary", "premium", "total", "cost", "fee", "income", "balance"),
        NUM,
        "SENSITIVE",
        "noise",
        [0.15],
    ),
    (("birth", "dob"), DATE, "QUASI_IDENTIFIER", "dnoise", ["365 days"]),
    (("death", "deceased"), DATE, "QUASI_IDENTIFIER", "dnoise", ["365 days"]),
    (("city",), TEXT, "QUASI_IDENTIFIER", "fake_city", []),
    (("country",), TEXT, "QUASI_IDENTIFIER", "fake_country", []),
    (("postal", "zip", "postcode"), TEXT, "QUASI_IDENTIFIER", "fake_postcode", []),
    (("street", "address"), TEXT, "QUASI_IDENTIFIER", "fake_address", []),
    (("note", "comment", "remark"), ("text",), "SENSITIVE", "lorem_ipsum", [1]),
    (("_id", "uuid", "guid"), None, "TECHNICAL", None, []),
    (("_at", "created", "updated", "modified"), DATE, "TECHNICAL", None, []),
    (None, TEXT, "SENSITIVE", "hash", []),
    (None, NUM, "SENSITIVE", "noise", [0.15]),
    (None, DATE, "QUASI_IDENTIFIER", "dnoise", ["365 days"]),
    (None, ("boolean",), "TECHNICAL", None, []),
]

FALLBACK = ("TECHNICAL", None, [])

THRESHOLD = 0.8


def match_rule(column_name, data_type):
    name = column_name.lower()
    dt = data_type.lower()
    candidates = [name, *name.split("_")]

    for patterns, types, category, anon_fn, params in RULES:
        if patterns is not None and (types is None or dt in types) and any(pattern in name for pattern in patterns):
            found_pattern = next((pattern for pattern in patterns if pattern in name), None)
            reason = f"name={found_pattern}"

            return (category, anon_fn, list(params), reason)

    best = None
    for patterns, types, category, anon_fn, params in RULES:
        if patterns is None or category == "TECHNICAL" or (types is not None and dt not in types):
            continue
        for pattern in patterns:
            for candidate in candidates:
                score = Levenshtein.ratio(candidate, pattern)
                if score >= THRESHOLD and (best is None or score > best[0]):
                    best = (score, category, pattern, anon_fn, list(params))

    if best is not None:
        score, category, pattern, anon_fn, params = best
        return (category, anon_fn, params, f"name~{pattern} ratio:({score:.2f})")

    for patterns, types, category, anon_fn, params in RULES:
        if patterns is None and dt in types:
            reason = f"type={dt}"

            return (category, anon_fn, list(params), reason)

    return (*FALLBACK, "fallback")
