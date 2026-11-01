from unittest.mock import patch

import pytest

from policies.models import ColumnPolicy, DataCategory
from validations.checks import KAnonymityCheck, RowCountCheck, ValueOverlapCheck
from validations.models import ValidationResult

ROWCOUNT_CASES = [
    (100, 100, 100, ValidationResult.ValidationResultStatuses.PASS, "A sorok száma egyezik"),
    (100, 100, 90, ValidationResult.ValidationResultStatuses.FAIL, "A sorok száma nem egyezik"),
    (100, 90, 80, ValidationResult.ValidationResultStatuses.FAIL, "A sorok száma nem egyezik"),
    (100, 90, 100, ValidationResult.ValidationResultStatuses.FAIL, "A sorok száma nem egyezik"),
]

K_METRICS_CASES = [
    ([3, 2, 1, 4], 3, {"k": 1, "n_classes": 4, "n_rows": 10, "unique_ratio": 0.1, "below_k_ratio": 0.3}),
    ([10, 8, 6], 5, {"k": 6, "n_classes": 3, "n_rows": 24, "unique_ratio": 0.0, "below_k_ratio": 0.0}),
    ([], 5, None),
]

K_HIST_CASES = [
    ([3, 2, 1, 4], 3, {"labels": ["1", "2-2", "3+"], "counts": [1, 2, 7]}),
    ([10, 8, 6], 5, {"labels": ["1", "2-4", "5+"], "counts": [0, 0, 24]}),
    ([], 5, None)
]


@pytest.mark.django_db
def _category(overlap):
    obj, _ = DataCategory.objects.get_or_create(
        name="DATA_CATEGORY", maximum_overlap=overlap, description="TEST_CATEGORY"
    )

    return obj


@pytest.mark.django_db
def _policy(category, value_overlap):
    obj, _ = ColumnPolicy.objects.get_or_create(
        schema_name="public",
        table_name="table",
        column_name="column",
        quality_checks={"value_overlap": value_overlap},
        data_category=category,
    )

    return obj


@pytest.mark.django_db
def _qi_policy(table, column, min_k=5, enabled=True):
    spec = {"enabled": enabled}
    if min_k is not None:
        spec["min_k"] = min_k

    return ColumnPolicy.objects.create(
        schema_name="public",
        table_name=table,
        column_name=column,
        quality_checks={"k_anonymity": spec},
    )


def _k_check(policies, target_label="dev", fail_status=None, target_schema="public"):
    if fail_status is None:
        fail_status = ValidationResult.ValidationResultStatuses.WARNING
    return KAnonymityCheck(
        "postgres://prod",
        "postgres://staging",
        "postgres://dev",
        policies,
        "postgres://target",
        target_schema,
        target_label,
        fail_status,
    )


@pytest.mark.parametrize("prod_count, staging_count, dev_count, expected_status, expected_msg", ROWCOUNT_CASES)
def test_row_count_check_execute(prod_count, staging_count, dev_count, expected_status, expected_msg):
    check = RowCountCheck(
        prod_dsn="postgres://prod_db", staging_dsn="postgres://staging_db", dev_dsn="postgres://dev_db", policies=[]
    )

    with (
        patch.object(RowCountCheck, "_table_names", return_value=[("public", "table")]),
        patch.object(RowCountCheck, "_count", side_effect=[prod_count, staging_count, dev_count]),
    ):
        results = check.execute()

    assert len(results) == 1
    result = results[0]

    assert result["schema_name"] == "public"
    assert result["table_name"] == "table"
    assert result["check_type"] == ValidationResult.CheckTypes.ROW_COUNT

    assert result["status"] == expected_status
    assert result["message"] == expected_msg

    assert result["metrics"]["prod_table_count"] == prod_count
    assert result["metrics"]["staging_table_count"] == staging_count
    assert result["metrics"]["dev_table_count"] == dev_count


def test_row_count_check_execute_with_two_table():
    check = RowCountCheck(
        prod_dsn="postgres://prod_db", staging_dsn="postgres://staging_db", dev_dsn="postgres://dev_db", policies=[]
    )

    with (
        patch.object(RowCountCheck, "_table_names", return_value=[("public", "table_1"), ("public", "table_2")]),
        patch.object(RowCountCheck, "_count", side_effect=[100, 100, 100, 100, 90, 80]),
    ):
        results = check.execute()

    assert len(results) == 2
    result_t1 = results[0]
    result_t2 = results[1]

    assert result_t1["schema_name"] == "public"
    assert result_t1["table_name"] == "table_1"
    assert result_t1["metrics"]["prod_table_count"] == 100
    assert result_t1["metrics"]["staging_table_count"] == 100
    assert result_t1["metrics"]["dev_table_count"] == 100

    assert result_t2["schema_name"] == "public"
    assert result_t2["table_name"] == "table_2"
    assert result_t2["metrics"]["prod_table_count"] == 100
    assert result_t2["metrics"]["staging_table_count"] == 90
    assert result_t2["metrics"]["dev_table_count"] == 80


@pytest.mark.django_db
def test_value_overlap_no_leak_passes():
    test_data_category = _category(overlap=0)

    test_policy = _policy(test_data_category, True)

    check = ValueOverlapCheck(
        prod_dsn="postgres://prod_db",
        staging_dsn="postgres://staging_db",
        dev_dsn="postgres://dev_db",
        policies=[test_policy],
    )

    with (
        patch.object(ValueOverlapCheck, "_column_values", side_effect=({"a", "b"}, {"c", "d"})),
    ):
        results = check.execute()

    assert len(results) == 1
    result = results[0]

    assert result["schema_name"] == "public"
    assert result["table_name"] == "table"
    assert result["column_name"] == "column"
    assert result["check_type"] == ValidationResult.CheckTypes.VALUE_OVERLAP
    assert result["status"] == ValidationResult.ValidationResultStatuses.PASS

    assert result["metrics"]["leaks_count"] == 0
    assert result["metrics"]["overlap_ratio"] == 0
    assert result["metrics"]["prod_distinct_count"] == 2
    assert result["metrics"]["dev_distinct_count"] == 2


@pytest.mark.django_db
def test_value_overlap_leak_fails():
    test_data_category = _category(overlap=0)

    test_policy = _policy(test_data_category, True)

    check = ValueOverlapCheck(
        prod_dsn="postgres://prod_db",
        staging_dsn="postgres://staging_db",
        dev_dsn="postgres://dev_db",
        policies=[test_policy],
    )

    with (
        patch.object(ValueOverlapCheck, "_column_values", side_effect=({"a", "b"}, {"b", "c"})),
    ):
        results = check.execute()

    assert len(results) == 1
    result = results[0]

    assert result["schema_name"] == "public"
    assert result["table_name"] == "table"
    assert result["column_name"] == "column"
    assert result["check_type"] == ValidationResult.CheckTypes.VALUE_OVERLAP
    assert result["status"] == ValidationResult.ValidationResultStatuses.FAIL

    assert result["metrics"]["leaks_count"] == 1
    assert result["metrics"]["overlap_ratio"] == 50
    assert result["metrics"]["prod_distinct_count"] == 2
    assert result["metrics"]["dev_distinct_count"] == 2


@pytest.mark.django_db
def test_value_overlap_within_threshold_passes():
    test_data_category = _category(overlap=60)

    test_policy = _policy(test_data_category, True)

    check = ValueOverlapCheck(
        prod_dsn="postgres://prod_db",
        staging_dsn="postgres://staging_db",
        dev_dsn="postgres://dev_db",
        policies=[test_policy],
    )

    with (
        patch.object(ValueOverlapCheck, "_column_values", side_effect=({"a", "b"}, {"b", "c"})),
    ):
        results = check.execute()

    assert len(results) == 1
    result = results[0]

    assert result["schema_name"] == "public"
    assert result["table_name"] == "table"
    assert result["column_name"] == "column"
    assert result["check_type"] == ValidationResult.CheckTypes.VALUE_OVERLAP
    assert result["status"] == ValidationResult.ValidationResultStatuses.PASS

    assert result["metrics"]["leaks_count"] == 1
    assert result["metrics"]["overlap_ratio"] == 50
    assert result["metrics"]["prod_distinct_count"] == 2
    assert result["metrics"]["dev_distinct_count"] == 2


@pytest.mark.django_db
def test_value_overlap_without_category_skipped():
    test_policy = _policy(None, True)

    check = ValueOverlapCheck(
        prod_dsn="postgres://prod_db",
        staging_dsn="postgres://staging_db",
        dev_dsn="postgres://dev_db",
        policies=[test_policy],
    )

    with (
        patch.object(ValueOverlapCheck, "_column_values", side_effect=({"a", "b"}, {"b", "c"})),
    ):
        results = check.execute()

    assert results == []


@pytest.mark.django_db
def test_value_overlap_empty_prod_skipped():
    test_data_category = _category(overlap=60)

    test_policy = _policy(test_data_category, True)

    check = ValueOverlapCheck(
        prod_dsn="postgres://prod_db",
        staging_dsn="postgres://staging_db",
        dev_dsn="postgres://dev_db",
        policies=[test_policy],
    )

    with (
        patch.object(ValueOverlapCheck, "_column_values", side_effect=({}, {"b", "c"})),
    ):
        results = check.execute()

    assert results == []


@pytest.mark.django_db
def test_value_overlap_disabled_skips_db():
    test_data_category = _category(overlap=100)

    test_policy = _policy(test_data_category, False)

    check = ValueOverlapCheck(
        prod_dsn="postgres://prod_db",
        staging_dsn="postgres://staging_db",
        dev_dsn="postgres://dev_db",
        policies=[test_policy],
    )

    with (
        patch.object(ValueOverlapCheck, "_column_values", side_effect=({"a", "b"}, {"c", "d"})) as mock_values,
    ):
        results = check.execute()

    assert results == []
    mock_values.assert_not_called()


@pytest.mark.parametrize("sizes, min_k, expected", K_HIST_CASES)
def test_class_size_hist(sizes, min_k, expected):
    assert _k_check([])._class_size_hist(sizes, min_k) == expected


@pytest.mark.parametrize("sizes, min_k, expected", K_METRICS_CASES)
def test_k_metrics(sizes, min_k, expected):
    assert _k_check([])._k_metrics(sizes, min_k) == expected


@pytest.mark.django_db
def test_k_anonymity_disabled_skips_db():
    check = _k_check([_qi_policy("patients", "birth_date", enabled=False)])

    with patch.object(KAnonymityCheck, "_class_sizes") as mock_sizes:
        results = check.execute()

    assert results == []
    mock_sizes.assert_not_called()


@pytest.mark.django_db
def test_k_anonymity_missing_min_k_defaults_to_five():
    check = _k_check([_qi_policy("patients", "birth_date", min_k=None)])

    with patch.object(KAnonymityCheck, "_class_sizes", side_effect=[[10, 8, 6], [10, 8, 6]]):
        results = check.execute()

    assert results[0]["applied_thresholds"]["min_k"] == 5


@pytest.mark.django_db
def test_k_anonymity_uses_max_min_k():
    policies = [_qi_policy("patients", "birth_date", min_k=10), _qi_policy("patients", "gender", min_k=5)]

    check = _k_check(policies)

    with patch.object(KAnonymityCheck, "_class_sizes", side_effect=[[10, 8, 6], [10, 8, 6]]):
        results = check.execute()

    assert len(results) == 1
    assert results[0]["applied_thresholds"]["min_k"] == 10
    assert "gender" in results[0]["column_name"]
    assert "birth_date" in results[0]["column_name"]


@pytest.mark.django_db
def test_k_anonymity_dev_warning():
    check = _k_check(
        [_qi_policy("patients", "gender")],
        target_label="dev",
        fail_status=ValidationResult.ValidationResultStatuses.WARNING,
    )

    with patch.object(KAnonymityCheck, "_class_sizes", side_effect=[[3, 2, 1, 4], [3, 2, 1, 4]]) as mock_sizes:
        results = check.execute()

    result = results[0]

    assert result["status"] == ValidationResult.ValidationResultStatuses.WARNING
    assert result["metrics"]["target"] == "dev"
    assert result["metrics"]["k"] == 1
    assert result["column_policy"] is None
    assert result["column_name"] == "gender"
    mock_sizes.assert_any_call("postgres://prod", "public", "patients", ["gender"])
    mock_sizes.assert_any_call("postgres://target", "public", "patients", ["gender"])


@pytest.mark.django_db
def test_k_anonymity_analytics_fail():
    check = _k_check(
        [_qi_policy("patients", "gender")],
        target_label="analytics",
        target_schema="analytics",
        fail_status=ValidationResult.ValidationResultStatuses.FAIL,
    )

    with patch.object(KAnonymityCheck, "_class_sizes", side_effect=[[3, 2, 1, 4], [3, 2, 1, 4]]) as mock_sizes:
        results = check.execute()

    result = results[0]

    assert result["status"] == ValidationResult.ValidationResultStatuses.FAIL
    assert result["metrics"]["target"] == "analytics"
    assert result["check_type"] == ValidationResult.CheckTypes.K_ANONYMITY


@pytest.mark.django_db
def test_k_anonymity_pass_when_k_equals_min_k():
    check = _k_check([_qi_policy("patients", "gender", min_k=5)])

    with patch.object(KAnonymityCheck, "_class_sizes", side_effect=[[3, 2, 1, 4], [5, 6, 7]]):
        results = check.execute()

    assert results[0]["status"] == ValidationResult.ValidationResultStatuses.PASS
    assert results[0]["metrics"]["k"] == 5


@pytest.mark.django_db
def test_k_anonymity_empty_sizes_skipped():
    check = _k_check([_qi_policy("patients", "gender")])

    with patch.object(KAnonymityCheck, "_class_sizes", side_effect=[[], [10, 8, 6]]):
        results = check.execute()

    assert results == []
