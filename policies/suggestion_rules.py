TEXT = ("character varying", "text")
NUM  = ("numeric", "integer", "bigint", "smallint", "double precision", "real")
DATE = ("date", "timestamp without time zone", "timestamp with time zone")

RULES = [
    (("email",),                                   TEXT, "DIRECT_IDENTIFIER", "partial_email",   []),
    (("first_name", "firstname", "given_name"),    TEXT, "DIRECT_IDENTIFIER", "fake_first_name", []),
    (("last_name", "surname", "mother_name"),      TEXT, "DIRECT_IDENTIFIER", "fake_last_name",  []),
    (("phone", "mobile"),                          TEXT, "DIRECT_IDENTIFIER", "random_phone",    []),
    (("iban", "account_number"),                   TEXT, "DIRECT_IDENTIFIER", "fake_iban",       []),
    (("taj", "national_health", "ssn", "passport", "license_number"), TEXT, "DIRECT_IDENTIFIER", "hash", []),
    (("amount", "price", "salary", "premium", "total"), NUM, "SENSITIVE",     "noise",           [0.15]),
    (("birth", "dob"),                             DATE, "QUASI_IDENTIFIER",  "dnoise",          ["365 days"]),
    (("city",),                                    TEXT, "QUASI_IDENTIFIER",  "fake_city",       []),
    (("postal", "zip", "postcode"),                TEXT, "QUASI_IDENTIFIER",  "fake_postcode",   []),
    (("street", "address"),                        TEXT, "QUASI_IDENTIFIER",  "fake_address",    []),
    (("_id", "uuid"),                              None, "TECHNICAL",         None,              []),
    (("_at", "created", "updated"),                DATE, "TECHNICAL",         None,              []),
    (None,                                         TEXT, "SENSITIVE",         "hash",            []),
    (None,                                         NUM,  "SENSITIVE",         "noise",           [0.15]),
    (None,                                         DATE, "QUASI_IDENTIFIER",  "dnoise",          ["365 days"]),
    (None,                                         ("boolean",), "TECHNICAL", None,              []),
]
FALLBACK = ("TECHNICAL", None, [])

def match_rule(column_name, data_type):

    name = column_name.lower()
    dt = data_type.lower()

    for patterns, types, category, anon_fn, params in RULES:

        if patterns is None and dt in types:
            reason = f"type={dt}"

            return(category, anon_fn, list(params), reason)

        if patterns is not None:
            if any(pattern in name for pattern in patterns):
                found_pattern = next((pattern for pattern in patterns if pattern in name), None)
                reason = f"name={found_pattern}"

                return(category, anon_fn, list(params), reason)

    
    return(*FALLBACK, "fallback")