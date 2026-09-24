from validations.models import ValidationResult
from .models import Alert

class AlertService:

    def create_alerts(self, validation_run, results):

        for validation_result in results:
            if validation_result.status == ValidationResult.ValidationResultStatuses.FAIL:
                Alert.objects.create(validation_run=validation_run, validation_result=validation_result, alert_type=Alert.AlertType.HIGH,
                                     severity=Alert.SeverityType.CRITICAL, schema_name=validation_result.schema_name, table_name=validation_result.table_name,
                                     column_name=validation_result.column_name, message=validation_result.message)