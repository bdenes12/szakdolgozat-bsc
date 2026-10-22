import pytest

from policies.models import AnonFunction, ColumnPolicy, DataCategory, MaskingStrategy, PolicySuggestion
from policies.services import SuggestionService


@pytest.mark.django_db
def _category(name):
    obj, _ = DataCategory.objects.get_or_create(name=name, defaults={"maximum_overlap": 0, "description": name})

    return obj


@pytest.mark.django_db
def _strategy():
    fn, _ = AnonFunction.objects.get_or_create(name="hash", defaults={"function": "anon.hash"})

    obj, _ = MaskingStrategy.objects.get_or_create(
        name="hash", defaults={"anon_function": fn, "parameters": [], "description": "hash"}
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
    s = _suggestion("email", "DIRECT_IDENTIFIER", _strategy())
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
    s = _suggestion("dup_col", "DIRECT_IDENTIFIER", _strategy())
    ok, skipped = SuggestionService().accept_suggestion([s])

    assert ok == 1
    assert skipped == 0

    ok, skipped = SuggestionService().accept_suggestion([s])

    assert ok == 0
    assert skipped == 1
    assert s.status == PolicySuggestion.SuggestionStatus.ACCEPTED
    assert ColumnPolicy.objects.filter(column_name="dup_col").count() == 1
