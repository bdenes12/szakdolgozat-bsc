from validations.models import ValidationRun
from pipelines.models import PipelineRun


class ValidationService:

    def run_validation(self, pipeline_run: PipelineRun):

        validation_run_obj = ValidationRun.objects.create(pipeline_run=pipeline_run, status=ValidationRun.ValidationRunStatuses.RUNNING)

