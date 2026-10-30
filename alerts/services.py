from validations.models import ValidationResult

from .models import Alert

ALERT_TYPES = {
    ValidationResult.CheckTypes.COLUMN_TYPE: Alert.AlertType.COLUMN_TYPE,
    ValidationResult.CheckTypes.ROW_COUNT: Alert.AlertType.ROW_COUNT,
    ValidationResult.CheckTypes.VALUE_OVERLAP: Alert.AlertType.VALUE_OVERLAP,
    ValidationResult.CheckTypes.STATISTICAL: Alert.AlertType.STATISTICAL,
    ValidationResult.CheckTypes.K_ANONYMITY: Alert.AlertType.K_ANONYMITY,
}

SEVERITY_TYPES = {
    ValidationResult.CheckTypes.COLUMN_TYPE: Alert.SeverityType.WARNING,
    ValidationResult.CheckTypes.ROW_COUNT: Alert.SeverityType.WARNING,
    ValidationResult.CheckTypes.VALUE_OVERLAP: Alert.SeverityType.CRITICAL,
    ValidationResult.CheckTypes.STATISTICAL: Alert.SeverityType.WARNING,
    ValidationResult.CheckTypes.K_ANONYMITY: Alert.SeverityType.CRITICAL,
}


class AlertService:
    def create_alerts(self, validation_run, results):
        for validation_result in results:
            if validation_result.status == ValidationResult.ValidationResultStatuses.FAIL:
                Alert.objects.create(
                    validation_run=validation_run,
                    validation_result=validation_result,
                    alert_type=ALERT_TYPES.get(validation_result.check_type),
                    severity=SEVERITY_TYPES.get(validation_result.check_type),
                    schema_name=validation_result.schema_name,
                    table_name=validation_result.table_name,
                    column_name=validation_result.column_name,
                    message=validation_result.message,
                )

    def create_missing_policy_alerts(self, validation_run, missing_policies, environment):
        for schema_name, table_name, column_name in missing_policies:
            Alert.objects.create(
                validation_run=validation_run,
                validation_result=None,
                alert_type=Alert.AlertType.MISSING_POLICY,
                severity=Alert.SeverityType.INFO,
                schema_name=schema_name,
                table_name=table_name,
                column_name=column_name,
                message=f"Nincs {environment} szabály: {schema_name}.{table_name}.{column_name}",
            )
