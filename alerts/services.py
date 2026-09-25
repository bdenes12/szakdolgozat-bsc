from validations.models import ValidationResult
from .models import Alert

ALERT_TYPES = {
    ValidationResult.CheckTypes.COLUMN_TYPE: Alert.AlertType.COLUMN_TYPE,
    ValidationResult.CheckTypes.ROW_COUNT: Alert.AlertType.ROW_COUNT,
    ValidationResult.CheckTypes.VALUE_OVERLAP: Alert.AlertType.VALUE_OVERLAP,
    ValidationResult.CheckTypes.STATISTICAL: Alert.AlertType.STATISTICAL
}

class AlertService:

    def create_alerts(self, validation_run, results):

        for validation_result in results:
            if validation_result.status == ValidationResult.ValidationResultStatuses.FAIL:
                Alert.objects.create(validation_run=validation_run, validation_result=validation_result, alert_type=ALERT_TYPES.get(validation_result.check_type),
                                     severity=Alert.SeverityType.CRITICAL, schema_name=validation_result.schema_name, table_name=validation_result.table_name,
                                     column_name=validation_result.column_name, message=validation_result.message)