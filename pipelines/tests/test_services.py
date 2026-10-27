from unittest.mock import MagicMock

import psycopg2
import pytest
from dlt.pipeline.exceptions import PipelineStepFailed
from sqlalchemy.exc import OperationalError as SQLAlchemyOperationalError

from pipelines.models import PipelineRun
from pipelines.services import PipelineService


@pytest.mark.django_db
def test_successful_run_marks_completed():
    mock_staging = MagicMock()
    mock_dev = MagicMock()
    mock_anonymize = MagicMock()
    mock_validation = MagicMock()

    pipeline = PipelineService(
        transfer_to_staging=mock_staging,
        transfer_to_dev=mock_dev,
        anonymize=mock_anonymize,
        validation_service=mock_validation,
    ).start_pipeline()

    pipeline.refresh_from_db()

    assert pipeline.status == PipelineRun.RunStatuses.COMPLETED
    assert pipeline.finished_at is not None
    mock_validation.run_validation.assert_called_once_with(pipeline)


@pytest.mark.django_db
def test_db_error_in_staging_mark_failed():
    mock_staging = MagicMock(side_effect=psycopg2.OperationalError())
    mock_dev = MagicMock()
    mock_anonymize = MagicMock()
    mock_validation = MagicMock()

    pipeline = PipelineService(
        transfer_to_staging=mock_staging,
        transfer_to_dev=mock_dev,
        anonymize=mock_anonymize,
        validation_service=mock_validation,
    ).start_pipeline()

    pipeline.refresh_from_db()

    assert pipeline.status == PipelineRun.RunStatuses.FAILED
    assert pipeline.error_message == "Adatbázis nem érhető el (PROD -> STAGING)"
    mock_anonymize.assert_not_called()
    mock_dev.assert_not_called()
    mock_validation.run_validation.assert_not_called()


@pytest.mark.django_db
def test_sqlalchemy_error_in_dev_marks_failed():
    sqlalchemy_error = SQLAlchemyOperationalError(
        statement="SELECT * FROM dual", params=[], orig=Exception("Kapcsolati hiba")
    )

    mock_staging = MagicMock()
    mock_dev = MagicMock(side_effect=sqlalchemy_error)
    mock_anonymize = MagicMock()
    mock_validation = MagicMock()

    pipeline = PipelineService(
        transfer_to_staging=mock_staging,
        transfer_to_dev=mock_dev,
        anonymize=mock_anonymize,
        validation_service=mock_validation,
    ).start_pipeline()

    pipeline.refresh_from_db()

    assert pipeline.status == PipelineRun.RunStatuses.FAILED
    assert pipeline.error_message == "Adatbázis nem érhető el (STAGING -> DEV)"
    mock_staging.assert_called_once()
    mock_anonymize.assert_called_once()
    mock_validation.run_validation.assert_not_called()


@pytest.mark.django_db
def test_step_failed_in_dev_transfer_marks_failed():
    pipelinestep_error = PipelineStepFailed(MagicMock(), "load", None, Exception("Hiba"))

    mock_staging = MagicMock()
    mock_dev = MagicMock(side_effect=pipelinestep_error)
    mock_anonymize = MagicMock()
    mock_validation = MagicMock()

    pipeline = PipelineService(
        transfer_to_staging=mock_staging,
        transfer_to_dev=mock_dev,
        anonymize=mock_anonymize,
        validation_service=mock_validation,
    ).start_pipeline()

    pipeline.refresh_from_db()

    assert pipeline.status == PipelineRun.RunStatuses.FAILED
    assert pipeline.error_message == "Sikertelen áttöltés (STAGING -> DEV)"
    mock_anonymize.assert_called_once()
    mock_validation.run_validation.assert_not_called()


@pytest.mark.django_db
def test_unexpected_error_in_anonymization_marks_failed():
    mock_staging = MagicMock()
    mock_dev = MagicMock()
    mock_anonymize = MagicMock(side_effect=ValueError())
    mock_validation = MagicMock()

    pipeline = PipelineService(
        transfer_to_staging=mock_staging,
        transfer_to_dev=mock_dev,
        anonymize=mock_anonymize,
        validation_service=mock_validation,
    ).start_pipeline()

    pipeline.refresh_from_db()

    assert pipeline.status == PipelineRun.RunStatuses.FAILED
    assert pipeline.error_message == "Sikertelen lépés: Anonimizálás"
    mock_staging.assert_called_once()
    mock_dev.assert_not_called()
    mock_validation.run_validation.assert_not_called()


@pytest.mark.django_db
def test_db_error_in_anonymization_marks_failed():
    mock_staging = MagicMock()
    mock_dev = MagicMock()
    mock_anonymize = MagicMock(side_effect=psycopg2.OperationalError())
    mock_validation = MagicMock()

    pipeline = PipelineService(
        transfer_to_staging=mock_staging,
        transfer_to_dev=mock_dev,
        anonymize=mock_anonymize,
        validation_service=mock_validation,
    ).start_pipeline()

    pipeline.refresh_from_db()

    assert pipeline.status == PipelineRun.RunStatuses.FAILED
    assert pipeline.error_message == "Adatbázis nem érhető el (Anonimizálás)"
    mock_staging.assert_called_once()
    mock_dev.assert_not_called()
    mock_validation.run_validation.assert_not_called()


@pytest.mark.django_db
def test_db_error_in_validation_marks_failed():
    mock_staging = MagicMock()
    mock_dev = MagicMock()
    mock_anonymize = MagicMock()
    mock_validation = MagicMock()

    mock_validation.run_validation.side_effect = psycopg2.OperationalError()

    pipeline = PipelineService(
        transfer_to_staging=mock_staging,
        transfer_to_dev=mock_dev,
        anonymize=mock_anonymize,
        validation_service=mock_validation,
    ).start_pipeline()

    pipeline.refresh_from_db()

    assert pipeline.status == PipelineRun.RunStatuses.FAILED
    assert pipeline.error_message == "Adatbázis nem érhető el (Validáció)"
    mock_staging.assert_called_once()
    mock_dev.assert_called_once()
    mock_anonymize.assert_called_once()


@pytest.mark.django_db
def test_error_message_contains_no_pii():
    mock_staging = MagicMock()
    mock_dev = MagicMock()
    mock_anonymize = MagicMock(side_effect=ValueError("john@example.com"))
    mock_validation = MagicMock()

    pipeline = PipelineService(
        transfer_to_staging=mock_staging,
        transfer_to_dev=mock_dev,
        anonymize=mock_anonymize,
        validation_service=mock_validation,
    ).start_pipeline()

    pipeline.refresh_from_db()

    assert pipeline.status == PipelineRun.RunStatuses.FAILED
    assert "john@example.com" not in pipeline.error_message
