from unittest.mock import patch

import pytest

from policies.models import ColumnPolicy, DataCategory
from validations.checks import RowCountCheck, ValueOverlapCheck
from validations.models import ValidationResult

ROWCOUNT_CASES = [
    (100, 100, 100, ValidationResult.ValidationResultStatuses.PASS, "A sorok száma egyezik"),
    (100, 100, 90, ValidationResult.ValidationResultStatuses.FAIL, "A sorok száma nem egyezik"),
    (100, 90, 80, ValidationResult.ValidationResultStatuses.FAIL, "A sorok száma nem egyezik"),
    (100, 90, 100, ValidationResult.ValidationResultStatuses.FAIL, "A sorok száma nem egyezik"),
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
