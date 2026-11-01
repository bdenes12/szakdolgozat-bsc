from unittest.mock import patch

import pytest

from policies.models import AnonFunction, ColumnPolicy, DataCategory, MaskingStrategy, PolicySuggestion
from policies.services import SuggestionService, PolicyService


PK_FK_CASES = [
    ("patient_id", True, False, "pk"),
    ("dept_id", False, True, "fk"),
    ("email", True, False, "pk"),
]


@pytest.mark.django_db
def _category(name):
    obj, _ = DataCategory.objects.get_or_create(name=name, defaults={"maximum_overlap": 0, "description": name})

    return obj


@pytest.mark.django_db
def _strategy(name, function, parameters):
    fn, _ = AnonFunction.objects.get_or_create(name=name, defaults={"function": function})

    obj, _ = MaskingStrategy.objects.get_or_create(
        name=name, defaults={"anon_function": fn, "parameters": parameters, "description": name}
    )

    return obj


@pytest.mark.django_db
def _suggestion(column_name, category_name, strategy=None):
    return PolicySuggestion.objects.create(
        schema_name="public",
        table_name="table",
        column_name=column_name,
        data_type="integer",
        suggested_category=_category(category_name),
        suggested_strategy=strategy,
        status=PolicySuggestion.SuggestionStatus.PENDING,
    )


@pytest.mark.django_db
def test_accept_pending_creates_column_policy():
    s = _suggestion("email", "DIRECT_IDENTIFIER", _strategy("hash", "anon.hash", []))
    ok, _ = SuggestionService().accept_suggestion([s])

    assert ok == 1
    assert s.status == PolicySuggestion.SuggestionStatus.ACCEPTED
    assert ColumnPolicy.objects.filter(
        schema_name=s.schema_name,
        table_name=s.table_name,
        column_name=s.column_name,
        target_environment=ColumnPolicy.EnvironmentTypes.DEVELOPMENT,
        masking_policy="",
    ).exists()


@pytest.mark.django_db
def test_accept_technical_without_strategy():
    s = _suggestion("id_col", "TECHNICAL", None)
    ok, _ = SuggestionService().accept_suggestion([s])

    assert ok == 1
    assert (
        ColumnPolicy.objects.filter(
            schema_name=s.schema_name,
            table_name=s.table_name,
            column_name=s.column_name,
            target_environment=ColumnPolicy.EnvironmentTypes.DEVELOPMENT,
            masking_policy="",
        )
        .values_list("masking_strategy", flat=True)
        .first()
        == None
    )


@pytest.mark.django_db
def test_accept_non_technical_without_strategy_skips():
    s = _suggestion("notes", "DIRECT_IDENTIFIER", None)
    _, skipped = SuggestionService().accept_suggestion([s])

    assert skipped == 1
    assert ColumnPolicy.objects.count() == 0


@pytest.mark.django_db
def test_accept_duplicate_skips():
    s = _suggestion("dup_col", "DIRECT_IDENTIFIER", _strategy("hash", "anon.hash", []))
    ok, skipped = SuggestionService().accept_suggestion([s])

    assert ok == 1
    assert skipped == 0

    ok, skipped = SuggestionService().accept_suggestion([s])

    assert ok == 0
    assert skipped == 1
    assert s.status == PolicySuggestion.SuggestionStatus.ACCEPTED
    assert ColumnPolicy.objects.filter(column_name="dup_col").count() == 1


@pytest.mark.django_db
def test_generate_suggestions_creates_fuzzy_match(monkeypatch):
    direct_identifier_category = _category("DIRECT_IDENTIFIER")
    partial_email = _strategy("partial_email", "anon.partial_email", [])

    monkeypatch.setenv("PRODUCTION_DSN", "x")

    with (
        patch.object(
            PolicyService, "find_missing_policies", return_value=("DEVELOPMENT", [("public", "patients", "emial")])
        ),
        patch.object(
            PolicyService,
            "get_column_metadata",
            return_value={("public", "patients", "emial"): {"data_type": "text", "is_pk": False, "is_fk": False}},
        ),
    ):
        suggestion_created = SuggestionService().generate_suggestions()

    assert suggestion_created == 1
    suggestion = PolicySuggestion.objects.get()
    assert "name~email ratio:(0.80); fn=partial_email" == suggestion.reason
    assert suggestion.suggested_category == direct_identifier_category
    assert suggestion.suggested_strategy == partial_email


@pytest.mark.django_db
def test_generate_suggestions_skips_existing(monkeypatch):
    _category("DIRECT_IDENTIFIER")
    _strategy("partial_email", "anon.partial_email", [])

    monkeypatch.setenv("PRODUCTION_DSN", "x")

    with (
        patch.object(
            PolicyService, "find_missing_policies", return_value=("DEVELOPMENT", [("public", "patients", "emial")])
        ),
        patch.object(
            PolicyService,
            "get_column_metadata",
            return_value={("public", "patients", "emial"): {"data_type": "text", "is_pk": False, "is_fk": False}},
        ),
    ):
        SuggestionService().generate_suggestions()
        SuggestionService().generate_suggestions()

    assert PolicySuggestion.objects.count() == 1
    suggestion = PolicySuggestion.objects.get()
    assert suggestion.schema_name == "public"
    assert suggestion.table_name == "patients"
    assert suggestion.column_name == "emial"
    assert "name~email ratio:(0.80); fn=partial_email" == suggestion.reason


@pytest.mark.parametrize("column_name, is_pk, is_fk, expected_reason", PK_FK_CASES)
def test_suggest_for_column_pk_and_fk_are_technical(column_name, is_pk, is_fk, expected_reason):
    result = SuggestionService().suggest_for_column(column_name, "integer", is_pk, is_fk)

    assert result == ("TECHNICAL", None, [], expected_reason)


def test_generate_suggestions_without_dsn_raises(monkeypatch):
    monkeypatch.delenv("PRODUCTION_DSN", raising=False)

    with pytest.raises(ValueError, match="Hiányzik a PRODUCTION_DSN"):
        SuggestionService().generate_suggestions()
