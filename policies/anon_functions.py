# Szűrt PostgreSQL Anonymizer függvények a seedhez.
# Forrás: anon_functions_mask.txt
# is_column_name_parameter: az első SQL-argumentum a maszkolandó oszlop értéke-e.

ANON_FUNCTIONS = {
    "fake_address": {
        "anon_function": "anon.fake_address",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis cím.",
    },
    "fake_city": {
        "anon_function": "anon.fake_city",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis város.",
    },
    "fake_company": {
        "anon_function": "anon.fake_company",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis cégnév.",
    },
    "fake_country": {
        "anon_function": "anon.fake_country",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis ország.",
    },
    "fake_email": {
        "anon_function": "anon.fake_email",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Teljesen hamis e-mail.",
    },
    "fake_first_name": {
        "anon_function": "anon.fake_first_name",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis keresztnév.",
    },
    "fake_iban": {
        "anon_function": "anon.fake_iban",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis IBAN.",
    },
    "fake_last_name": {
        "anon_function": "anon.fake_last_name",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis vezetéknév.",
    },
    "fake_postcode": {
        "anon_function": "anon.fake_postcode",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis irányítószám.",
    },
    "fake_siret": {
        "anon_function": "anon.fake_siret",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis SIRET.",
    },
    "dummy_bic": {
        "anon_function": "anon.dummy_bic",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis BIC.",
    },
    "dummy_building_number": {
        "anon_function": "anon.dummy_building_number",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis házszám.",
    },
    "dummy_cell_number": {
        "anon_function": "anon.dummy_cell_number",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis mobilszám.",
    },
    "dummy_city_name": {
        "anon_function": "anon.dummy_city_name",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis városnév.",
    },
    "dummy_company_name": {
        "anon_function": "anon.dummy_company_name",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis cégnév.",
    },
    "dummy_country_code": {
        "anon_function": "anon.dummy_country_code",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis országkód.",
    },
    "dummy_country_name": {
        "anon_function": "anon.dummy_country_name",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis országnév.",
    },
    "dummy_credit_card_number": {
        "anon_function": "anon.dummy_credit_card_number",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis bankkártyaszám.",
    },
    "dummy_first_name": {
        "anon_function": "anon.dummy_first_name",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis keresztnév (dummy).",
    },
    "dummy_health_insurance_code": {
        "anon_function": "anon.dummy_health_insurance_code",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis TAJ-szerű kód.",
    },
    "dummy_isin": {
        "anon_function": "anon.dummy_isin",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis ISIN.",
    },
    "dummy_last_name": {
        "anon_function": "anon.dummy_last_name",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis vezetéknév (dummy).",
    },
    "dummy_name": {
        "anon_function": "anon.dummy_name",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis teljes név.",
    },
    "dummy_phone_number": {
        "anon_function": "anon.dummy_phone_number",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis telefonszám.",
    },
    "dummy_post_code": {
        "anon_function": "anon.dummy_post_code",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis irányítószám (dummy).",
    },
    "dummy_safe_email": {
        "anon_function": "anon.dummy_safe_email",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis e-mail.",
    },
    "dummy_street_name": {
        "anon_function": "anon.dummy_street_name",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis utcanév.",
    },
    "dummy_username": {
        "anon_function": "anon.dummy_username",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis felhasználónév.",
    },
    "dummy_uuidv4": {
        "anon_function": "anon.dummy_uuidv4",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis UUID.",
    },
    "dummy_zip_code": {
        "anon_function": "anon.dummy_zip_code",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Hamis ZIP.",
    },
    "dummy_first_name_locale": {
        "anon_function": "anon.dummy_first_name_locale",
        "argumentum_data_types": "locale text",
        "is_column_name_parameter": False,
        "description": "Hamis keresztnév, locale a parameters-ben.",
    },
    "dummy_last_name_locale": {
        "anon_function": "anon.dummy_last_name_locale",
        "argumentum_data_types": "locale text",
        "is_column_name_parameter": False,
        "description": "Hamis vezetéknév, locale a parameters-ben.",
    },
    "dummy_phone_number_locale": {
        "anon_function": "anon.dummy_phone_number_locale",
        "argumentum_data_types": "locale text",
        "is_column_name_parameter": False,
        "description": "Hamis telefon, locale a parameters-ben.",
    },
    "dummy_city_name_locale": {
        "anon_function": "anon.dummy_city_name_locale",
        "argumentum_data_types": "locale text",
        "is_column_name_parameter": False,
        "description": "Hamis város, locale a parameters-ben.",
    },
    "dummy_post_code_locale": {
        "anon_function": "anon.dummy_post_code_locale",
        "argumentum_data_types": "locale text",
        "is_column_name_parameter": False,
        "description": "Hamis irányítószám, locale a parameters-ben.",
    },
    "random_date": {
        "anon_function": "anon.random_date",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Véletlen időbélyeg.",
    },
    "random_id": {
        "anon_function": "anon.random_id",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Véletlen bigint azonosító.",
    },
    "random_phone": {
        "anon_function": "anon.random_phone",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Véletlen telefonszám.",
    },
    "random_phone_prefix": {
        "anon_function": "anon.random_phone",
        "argumentum_data_types": "prefix text",
        "is_column_name_parameter": False,
        "description": "Véletlen telefon, prefix a parameters-ben.",
    },
    "random_phone_with_format": {
        "anon_function": "anon.random_phone_with_format",
        "argumentum_data_types": "format text",
        "is_column_name_parameter": False,
        "description": "Véletlen telefon, formátum a parameters-ben.",
    },
    "random_string": {
        "anon_function": "anon.random_string",
        "argumentum_data_types": "l integer",
        "is_column_name_parameter": False,
        "description": "Véletlen szöveg, hossz a parameters-ben.",
    },
    "random_string_range": {
        "anon_function": "anon.random_string",
        "argumentum_data_types": "r int4range",
        "is_column_name_parameter": False,
        "description": "Véletlen szöveg, hossztartomány a parameters-ben.",
    },
    "random_int_between": {
        "anon_function": "anon.random_int_between",
        "argumentum_data_types": "start integer, stop integer",
        "is_column_name_parameter": False,
        "description": "Véletlen egész, tartomány a parameters-ben.",
    },
    "random_bigint_between": {
        "anon_function": "anon.random_bigint_between",
        "argumentum_data_types": "start bigint, stop bigint",
        "is_column_name_parameter": False,
        "description": "Véletlen bigint, tartomány a parameters-ben.",
    },
    "random_date_between": {
        "anon_function": "anon.random_date_between",
        "argumentum_data_types": "date_start timestamptz, date_end timestamptz",
        "is_column_name_parameter": False,
        "description": "Véletlen dátum, tartomány a parameters-ben.",
    },
    "random_zip": {
        "anon_function": "anon.random_zip",
        "argumentum_data_types": "",
        "is_column_name_parameter": False,
        "description": "Véletlen ZIP.",
    },
    "random_hash": {
        "anon_function": "anon.random_hash",
        "argumentum_data_types": "seed text",
        "is_column_name_parameter": True,
        "description": "Hash az oszlop értékéből.",
    },
    "lorem_ipsum": {
        "anon_function": "anon.lorem_ipsum",
        "argumentum_data_types": "paragraphs integer DEFAULT 5, words integer DEFAULT 0, characters integer DEFAULT 0",
        "is_column_name_parameter": False,
        "description": "Helykitöltő szöveg.",
    },
    "noise": {
        "anon_function": "anon.noise",
        "argumentum_data_types": "noise_value anyelement, ratio double precision",
        "is_column_name_parameter": True,
        "description": "Numerikus zaj; a parameters egy arány, pl. [0.15].",
    },
    "dnoise": {
        "anon_function": "anon.dnoise",
        "argumentum_data_types": "noise_value anyelement, noise_range interval",
        "is_column_name_parameter": True,
        "description": 'Dátumzaj; a parameters egy intervallum, pl. ["365 days"].',
    },
    "partial": {
        "anon_function": "anon.partial",
        "argumentum_data_types": "ov text, prefix integer, padding text, suffix integer",
        "is_column_name_parameter": True,
        "description": 'Részleges maszk; parameters pl. [2, "****", 2].',
    },
    "partial_email": {
        "anon_function": "anon.partial_email",
        "argumentum_data_types": "ov text",
        "is_column_name_parameter": True,
        "description": "Részleges e-mail; parameters [].",
    },
    "digest": {
        "anon_function": "anon.digest",
        "argumentum_data_types": "val text, salt text, algorithm text",
        "is_column_name_parameter": True,
        "description": 'Digest; parameters pl. ["mysalt", "sha256"].',
    },
    "hash": {
        "anon_function": "anon.hash",
        "argumentum_data_types": "seed text",
        "is_column_name_parameter": True,
        "description": "Hash az oszlopból.",
    },
    "generalize_daterange": {
        "anon_function": "anon.generalize_daterange",
        "argumentum_data_types": "val date, step text DEFAULT 'decade'",
        "is_column_name_parameter": True,
        "description": "Dátum általánosítás; parameters opcionális step.",
    },
    "generalize_int4range": {
        "anon_function": "anon.generalize_int4range",
        "argumentum_data_types": "val integer, step integer DEFAULT 10",
        "is_column_name_parameter": True,
        "description": "Egész általánosítás.",
    },
    "generalize_int8range": {
        "anon_function": "anon.generalize_int8range",
        "argumentum_data_types": "val bigint, step bigint DEFAULT 10",
        "is_column_name_parameter": True,
        "description": "Bigint általánosítás.",
    },
    "generalize_numrange": {
        "anon_function": "anon.generalize_numrange",
        "argumentum_data_types": "val numeric, step integer DEFAULT 10",
        "is_column_name_parameter": True,
        "description": "Numeric általánosítás.",
    },
    "generalize_tsrange": {
        "anon_function": "anon.generalize_tsrange",
        "argumentum_data_types": "val timestamp without time zone, step text DEFAULT 'decade'",
        "is_column_name_parameter": True,
        "description": "Timestamp általánosítás.",
    },
    "generalize_tstzrange": {
        "anon_function": "anon.generalize_tstzrange",
        "argumentum_data_types": "val timestamp with time zone, step text DEFAULT 'decade'",
        "is_column_name_parameter": True,
        "description": "Timestamptz általánosítás.",
    },
    "pseudo_city": {
        "anon_function": "anon.pseudo_city",
        "argumentum_data_types": "seed anyelement, salt text DEFAULT NULL",
        "is_column_name_parameter": True,
        "description": "Állandó hamis város a seedből.",
    },
    "pseudo_company": {
        "anon_function": "anon.pseudo_company",
        "argumentum_data_types": "seed anyelement, salt text DEFAULT NULL",
        "is_column_name_parameter": True,
        "description": "Állandó hamis cég a seedből.",
    },
    "pseudo_country": {
        "anon_function": "anon.pseudo_country",
        "argumentum_data_types": "seed anyelement, salt text DEFAULT NULL",
        "is_column_name_parameter": True,
        "description": "Állandó hamis ország a seedből.",
    },
    "pseudo_email": {
        "anon_function": "anon.pseudo_email",
        "argumentum_data_types": "seed anyelement, salt text DEFAULT NULL",
        "is_column_name_parameter": True,
        "description": "Állandó hamis e-mail a seedből.",
    },
    "pseudo_first_name": {
        "anon_function": "anon.pseudo_first_name",
        "argumentum_data_types": "seed anyelement, salt text DEFAULT NULL",
        "is_column_name_parameter": True,
        "description": "Állandó hamis keresztnév a seedből.",
    },
    "pseudo_iban": {
        "anon_function": "anon.pseudo_iban",
        "argumentum_data_types": "seed anyelement, salt text DEFAULT NULL",
        "is_column_name_parameter": True,
        "description": "Állandó hamis IBAN a seedből.",
    },
    "pseudo_last_name": {
        "anon_function": "anon.pseudo_last_name",
        "argumentum_data_types": "seed anyelement, salt text DEFAULT NULL",
        "is_column_name_parameter": True,
        "description": "Állandó hamis vezetéknév a seedből.",
    },
    "pseudo_siret": {
        "anon_function": "anon.pseudo_siret",
        "argumentum_data_types": "seed anyelement, salt text DEFAULT NULL",
        "is_column_name_parameter": True,
        "description": "Állandó hamis SIRET a seedből.",
    },
}


def expected_parameters(function_name):
    parameters = []

    spec = ANON_FUNCTIONS.get(function_name)
    if not spec or not spec.get("argumentum_data_types"):
        return parameters

    if spec.get("is_column_name_parameter"):
        argumentum_data_types = spec.get("argumentum_data_types").split(",")[1:]

    else:
        argumentum_data_types = spec.get("argumentum_data_types").split(",")
    
    cleaned_list = [x.strip() for x in argumentum_data_types]

    for argumentum in cleaned_list:
        if " DEFAULT " in argumentum:
            required = False
            argumentum = argumentum.split(" DEFAULT ")[0]
        else:
            required = True

        name = argumentum.split(" ")[0]
        data_type = argumentum.split(" ")[1:]
        data_type = " ".join(data_type)

        parameters.append((name, data_type, required))

    return parameters
