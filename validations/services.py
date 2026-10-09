import os
from django.template.loader import render_to_string
from collections import defaultdict
from pipelines.models import PipelineRun
from policies.services import PolicyService
from policies.models import ColumnPolicy
from alerts.services import AlertService
from alerts.models import Alert
from validations.checks import RowCountCheck, ColumnTypeCheck, ValueOverlapCheck, StatisticalQualityCheck
from validations.models import ValidationRun, ValidationResult, ValidationReport


class ValidationService:         

    def run_validation(self, pipeline_run: PipelineRun):

        validation_run_obj = ValidationRun.objects.create(pipeline_run=pipeline_run, status=ValidationRun.ValidationRunStatuses.RUNNING)

        try:
            check_results = self.execute_checks()
            save_results = self.save_results(validation_run_obj, check_results)
            
            AlertService().create_alerts(validation_run_obj, save_results)
            
            environment, missing_policies = PolicyService().find_missing_policies(os.getenv("PRODUCTION_DSN"), ColumnPolicy.EnvironmentTypes.DEVELOPMENT)
            AlertService().create_missing_policy_alerts(validation_run_obj, missing_policies, environment)

            self.generate_report(validation_run_obj)

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

    def risk_level(self, results):

        has_fail = False
        has_missing_policy_alert = False

        for result in results:
            if result.check_type == ValidationResult.CheckTypes.VALUE_OVERLAP and result.status == ValidationResult.ValidationResultStatuses.FAIL:
                return "MAGAS"

            if result.check_type in (ValidationResult.CheckTypes.STATISTICAL, ValidationResult.CheckTypes.ROW_COUNT, ValidationResult.CheckTypes.COLUMN_TYPE) and result.status == ValidationResult.ValidationResultStatuses.FAIL:
                return "KÖZEPES"

            if result.status == ValidationResult.ValidationResultStatuses.FAIL:
                has_fail = True

            if Alert.AlertType.MISSING_POLICY == Alert.objects.filter(validation_result=result).values_list("alert_type", flat=True).first():
                has_missing_policy_alert = True

        if has_fail and has_missing_policy_alert:
            return "ALACSONY"

        return "NINCS"

    def generate_report(self, validation_run: ValidationRun):
        
        pipeline = validation_run.pipeline_run
        results = ValidationResult.objects.filter(validation_run=validation_run)
        alerts = Alert.objects.filter(validation_run=validation_run)

        pass_count = results.filter(status=ValidationResult.ValidationResultStatuses.PASS).count()
        fail_count = results.filter(status=ValidationResult.ValidationResultStatuses.FAIL).count()
        alert_count = alerts.count()

        fail_row_count = results.filter(status=ValidationResult.ValidationResultStatuses.FAIL, check_type=ValidationResult.CheckTypes.ROW_COUNT).count()
        fail_column_type = results.filter(status=ValidationResult.ValidationResultStatuses.FAIL, check_type=ValidationResult.CheckTypes.COLUMN_TYPE).count()
        fail_value_overlap = results.filter(status=ValidationResult.ValidationResultStatuses.FAIL, check_type=ValidationResult.CheckTypes.VALUE_OVERLAP).count()
        fail_statistical = results.filter(status=ValidationResult.ValidationResultStatuses.FAIL, check_type=ValidationResult.CheckTypes.STATISTICAL).count()

        grouped_results = defaultdict(list)
        grouped_alerts = defaultdict(list)

        for result in results:
            grouped_results[(result.schema_name, result.table_name)].append(result)

        for alert in alerts:
            grouped_alerts[(alert.schema_name, alert.table_name)].append(alert)

        tables = []

        for schema_table, result_list in grouped_results.items():
            tables.append({
                "schema_name": schema_table[0],
                "table_name": schema_table[1],
                "risk": self.risk_level(result_list),
                "results": result_list,
            })

        for table in tables:
            table["alerts"] = []
            for schema_table, alert_list in grouped_alerts.items(): 
                if table["schema_name"] == schema_table[0] and table["table_name"] == schema_table[1]:
                    table["alerts"] = alert_list
                    break

        context = {
            "pipeline": pipeline,
            "validation_run": validation_run,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "alert_count": alert_count,
            "fail_row_count": fail_row_count,
            "fail_column_type": fail_column_type,
            "fail_value_overlap": fail_value_overlap,
            "fail_statistical": fail_statistical,
            "tables": tables
        }

        html = render_to_string("validations/report.html", context)

        return ValidationReport.objects.create(validation_run=validation_run, html_content=html)

        