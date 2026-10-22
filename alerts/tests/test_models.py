import pytest

from alerts.models import Alert
from pipelines.models import PipelineRun
from validations.models import ValidationRun


@pytest.mark.django_db
def test_resolve_alert():
    pipeline = PipelineRun.objects.create(status=PipelineRun.RunStatuses.COMPLETED)
    vr = ValidationRun.objects.create(pipeline_run=pipeline, status=ValidationRun.ValidationRunStatuses.COMPLETED)
    alert = Alert.objects.create(
        validation_run=vr,
        alert_type=Alert.AlertType.VALUE_OVERLAP,
        schema_name="public",
        table_name="t",
        column_name="c",
        message="m",
    )

    alert.resolve()

    assert alert.is_resolved == True
    assert alert.resolved_at is not None
