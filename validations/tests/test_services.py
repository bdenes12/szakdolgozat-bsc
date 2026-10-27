from unittest.mock import MagicMock

import psycopg2
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


def _fake_result(status="PASS"):
    return {
        "schema_name": "public",
        "table_name": "patients",
        "column_name": "email",
        "check_type": ValidationResult.CheckTypes.VALUE_OVERLAP,
        "status": status,
        "metrics": {},
        "applied_thresholds": {},
        "message": "",
        "column_policy": None,
    }


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


@pytest.mark.django_db
def test_run_validation_saves_results_and_completes():
    pipeline = PipelineRun.objects.create(status=PipelineRun.RunStatuses.RUNNING)

    mock_check = MagicMock()
    mock_check.execute.return_value = [_fake_result("PASS"), _fake_result("FAIL")]

    mock_policy_service = MagicMock()
    mock_policy_service.find_missing_policies.return_value = ("DEVELOPMENT", [])

    mock_alert_service = MagicMock()

    validation_run = ValidationService(
        checks=[mock_check],
        policy_service=mock_policy_service,
        alert_service=mock_alert_service,
    ).run_validation(pipeline)

    validation_run.refresh_from_db()

    assert validation_run.status == ValidationRun.ValidationRunStatuses.COMPLETED
    assert ValidationResult.objects.filter(validation_run=validation_run).count() == 2
    assert ValidationReport.objects.filter(validation_run=validation_run).exists()
    mock_alert_service.create_alerts.assert_called_once()


@pytest.mark.django_db
def test_alert_error_rolls_back_results(): # Le lehet tesztelni úgy is, hogy az atomic sort kommentezem és úgy lefuttatom és akkor látom hogy FAIL
    pipeline = PipelineRun.objects.create(status=PipelineRun.RunStatuses.RUNNING)

    mock_check = MagicMock()
    mock_check.execute.return_value = [_fake_result("PASS"), _fake_result("FAIL")]

    mock_policy_service = MagicMock()
    mock_policy_service.find_missing_policies.return_value = ("DEVELOPMENT", [])

    mock_alert_service = MagicMock()
    mock_alert_service.create_alerts.side_effect = RuntimeError()

    with pytest.raises(RuntimeError):
        ValidationService(
            checks=[mock_check],
            policy_service=mock_policy_service,
            alert_service=mock_alert_service,
        ).run_validation(pipeline)

    validation_run = ValidationRun.objects.get(pipeline_run=pipeline)

    assert validation_run.status == ValidationRun.ValidationRunStatuses.FAILED
    assert validation_run.error_message == "Validáció sikertelen"
    assert ValidationResult.objects.filter(validation_run=validation_run).count() == 0


@pytest.mark.django_db
def test_db_error_in_checks_marks_failed():
    pipeline = PipelineRun.objects.create(status=PipelineRun.RunStatuses.RUNNING)

    mock_check = MagicMock()
    mock_check.execute.side_effect = psycopg2.OperationalError()
    mock_policy_service = MagicMock()
    mock_alert_service = MagicMock()

    with pytest.raises(psycopg2.OperationalError):
        ValidationService(
            checks=[mock_check],
            policy_service=mock_policy_service,
            alert_service=mock_alert_service,
        ).run_validation(pipeline)

    validation_run = ValidationRun.objects.get(pipeline_run=pipeline)

    assert validation_run.status == ValidationRun.ValidationRunStatuses.FAILED
    assert validation_run.error_message == "Adatbázis nem érhető el"


@pytest.mark.django_db
def test_missing_policies_passed_to_alert_service():
    pipeline = PipelineRun.objects.create(status=PipelineRun.RunStatuses.RUNNING)

    mock_check = MagicMock()
    mock_policy_service = MagicMock()
    mock_policy_service.find_missing_policies.return_value = ("DEVELOPMENT", [("public", "table", "column")])
    mock_alert_service = MagicMock()

    validation_run = ValidationService(
        checks=[mock_check],
        policy_service=mock_policy_service,
        alert_service=mock_alert_service,
    ).run_validation(pipeline)

    validation_run.refresh_from_db()

    mock_alert_service.create_missing_policy_alerts.assert_called_once_with(
        validation_run, [("public", "table", "column")], "DEVELOPMENT"
    )
