import pytest

from alerts.models import Alert
from alerts.services import AlertService
from pipelines.models import PipelineRun
from policies.models import ColumnPolicy
from validations.models import ValidationResult, ValidationRun

K_ANONYMITY_STATUS_CASES = [
    (ValidationResult.ValidationResultStatuses.FAIL, 1),
    (ValidationResult.ValidationResultStatuses.WARNING, 0),
]


@pytest.mark.django_db
def _validation_run():
    pipeline = PipelineRun.objects.create(status=PipelineRun.RunStatuses.COMPLETED)

    return ValidationRun.objects.create(pipeline_run=pipeline, status=ValidationRun.ValidationRunStatuses.COMPLETED)


@pytest.mark.django_db
def test_create_alerts_from_fail_result():
    vr = _validation_run()
    fail_result = ValidationResult.objects.create(
        validation_run=vr,
        schema_name="public",
        table_name="invoices",
        column_name="paid_amount",
        check_type=ValidationResult.CheckTypes.VALUE_OVERLAP,
        status=ValidationResult.ValidationResultStatuses.FAIL,
        message="overlap",
    )
    AlertService().create_alerts(vr, [fail_result])

    assert Alert.objects.count() == 1
    alert = Alert.objects.get()
    assert alert.alert_type == Alert.AlertType.VALUE_OVERLAP
    assert alert.severity == Alert.SeverityType.CRITICAL
    assert alert.column_name == "paid_amount"


@pytest.mark.django_db
def test_create_alerts_skips_pass_result():
    vr = _validation_run()
    pass_result = ValidationResult.objects.create(
        validation_run=vr,
        schema_name="public",
        table_name="invoices",
        column_name="paid_amount",
        check_type=ValidationResult.CheckTypes.VALUE_OVERLAP,
        status=ValidationResult.ValidationResultStatuses.PASS,
        message="overlap",
    )
    AlertService().create_alerts(vr, [pass_result])

    assert Alert.objects.count() == 0


@pytest.mark.django_db
def test_create_missing_policy_alerts():
    vr = _validation_run()
    AlertService().create_missing_policy_alerts(
        vr, [("public", "t", "phone")], ColumnPolicy.EnvironmentTypes.DEVELOPMENT
    )

    assert Alert.objects.count() == 1
    alert = Alert.objects.get()
    assert alert.alert_type == Alert.AlertType.MISSING_POLICY
    assert alert.severity == Alert.SeverityType.INFO
    assert alert.column_name == "phone"

@pytest.mark.django_db
@pytest.mark.parametrize("status, expected_count", K_ANONYMITY_STATUS_CASES)
def test_create_alerts_k_anonymity_only_on_fail(status, expected_count):
    vr = _validation_run()
    result = ValidationResult.objects.create(
        validation_run=vr,
        schema_name="public",
        table_name="patients",
        column_name="birth_date, gender",
        check_type=ValidationResult.CheckTypes.K_ANONYMITY,
        status=status,
        message="k",
    )
    AlertService().create_alerts(vr, [result])

    assert Alert.objects.count() == expected_count
    if expected_count:
        assert Alert.objects.get().alert_type == Alert.AlertType.K_ANONYMITY