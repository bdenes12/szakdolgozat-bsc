import pytest

from alerts.models import Alert
from pipelines.models import PipelineRun
from validations.models import ValidationReport, ValidationResult, ValidationRun
from validations.services import ValidationService


@pytest.mark.django_db
def _validation_run():
    pipeline = PipelineRun.objects.create(status=PipelineRun.RunStatuses.COMPLETED)

    return ValidationRun.objects.create(pipeline_run=pipeline, status=ValidationRun.ValidationRunStatuses.COMPLETED)


@pytest.mark.django_db
def _result(vr, column_name, check_type, status):
    return ValidationResult.objects.create(
        validation_run=vr,
        schema_name="public",
        table_name="invoices",
        column_name=column_name,
        check_type=check_type,
        status=status,
        metrics={},
        applied_thresholds={},
        message="",
    )


@pytest.mark.django_db
def _alert(vr, column_name):
    return Alert.objects.create(
        validation_run=vr,
        alert_type=Alert.AlertType.VALUE_OVERLAP,
        severity=Alert.SeverityType.CRITICAL,
        schema_name="public",
        table_name="invoices",
        column_name=column_name,
        message="overlap",
    )


@pytest.mark.django_db
def test_generate_report_creates_html():
    vr = _validation_run()
    _result(
        vr, "paid_amount", ValidationResult.CheckTypes.VALUE_OVERLAP, ValidationResult.ValidationResultStatuses.FAIL
    )
    _result(vr, "email", ValidationResult.CheckTypes.COLUMN_TYPE, ValidationResult.ValidationResultStatuses.PASS)
    _alert(vr, "paid_amount")

    report = ValidationService().generate_report(vr)

    assert report.id is not None
    assert "invoices" in report.html_content
    assert "paid_amount" in report.html_content
    assert "MAGAS" in report.html_content
    assert ValidationReport.objects.filter(validation_run=vr).count() == 1


@pytest.mark.django_db
def test_generate_report_second_call_creates_another():
    vr = _validation_run()
    _result(vr, "x", ValidationResult.CheckTypes.ROW_COUNT, ValidationResult.ValidationResultStatuses.PASS)

    ValidationService().generate_report(vr)
    ValidationService().generate_report(vr)

    assert ValidationReport.objects.filter(validation_run=vr).count() == 2
