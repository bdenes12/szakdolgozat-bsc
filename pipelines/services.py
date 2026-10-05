from .models import PipelineRun
from .dlt_adapter import prod_to_staging, staging_to_dev
from anonymization.services import apply_policies, apply_staging_labels
from validations.services import ValidationService

class PipelineService:

    def start_pipeline(self):

        pipeline_obj = PipelineRun.objects.create(status=PipelineRun.RunStatuses.RUNNING)

        try:
            self.transfer_to_staging(pipeline_obj)

            self.apply_anonymization()

            self.transfer_to_development(pipeline_obj)

            ValidationService().run_validation(pipeline_obj)

            pipeline_obj.mark_completed()

            return pipeline_obj
        
        except Exception as e:
            pipeline_obj.mark_failed(err_message=str(e))
            raise

    def transfer_to_staging(self, pipeline_obj):
        prod_to_staging()

    def transfer_to_development(self, pipeline_obj):
        staging_to_dev() 

    def apply_anonymization(self):
        apply_policies()
        apply_staging_labels()
