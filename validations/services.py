import os
from validations.models import ValidationRun, ValidationResult
from pipelines.models import PipelineRun
from policies.services import PolicyService
from policies.models import ColumnPolicy
from alerts.services import AlertService
from validations.checks import RowCountCheck, ColumnTypeCheck, ValueOverlapCheck, StatisticalQualityCheck

class ValidationService:         

    def run_validation(self, pipeline_run: PipelineRun):

        validation_run_obj = ValidationRun.objects.create(pipeline_run=pipeline_run, status=ValidationRun.ValidationRunStatuses.RUNNING)

        try:
            check_results = self.execute_checks()
            save_results = self.save_results(validation_run_obj, check_results)
            
            AlertService().create_alerts(validation_run_obj, save_results)
            
            environment, missing_policies = PolicyService().find_missing_policies(os.getenv("PRODUCTION_DSN"), ColumnPolicy.EnvironmentTypes.DEVELOPMENT)
            AlertService().create_missing_policy_alerts(validation_run_obj, missing_policies, environment)

            validation_run_obj.mark_completed()

        except Exception as e:
            validation_run_obj.mark_failed(str(e))
            raise

        return validation_run_obj


    def execute_checks(self):

        prod_dsn = os.getenv("PRODUCTION_DSN")
        staging_dsn = os.getenv("STAGING_DSN")
        dev_dsn = os.getenv("DEV_DSN")
        policies = PolicyService().get_active_policies(ColumnPolicy.EnvironmentTypes.DEVELOPMENT)

        results = []

        checks = [RowCountCheck(prod_dsn, staging_dsn, dev_dsn, policies), ColumnTypeCheck(prod_dsn, staging_dsn, dev_dsn, policies), 
                  ValueOverlapCheck(prod_dsn, staging_dsn, dev_dsn, policies), StatisticalQualityCheck(prod_dsn, staging_dsn, dev_dsn, policies)]

        for check in checks:
            results.extend(check.execute())

        return results

    def save_results(self, validation_run: ValidationRun, check_results):

        validationresults = []

        for result in check_results:
            validationresult_obj = ValidationResult.objects.create(validation_run=validation_run, column_policy=result['column_policy'], schema_name=result['schema_name'],
                                            table_name=result['table_name'], column_name=result['column_name'], check_type=result['check_type'],
                                            status=result['status'], metrics=result['metrics'], applied_thresholds=result['applied_thresholds'], message=result['message'])

            validationresults.append(validationresult_obj)

        return validationresults