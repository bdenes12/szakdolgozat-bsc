from django.db import models
from validations.models import ValidationRun, ValidationResult

# Create your models here.

class Alert(models.Model):

    validation_run = models.ForeignKey(ValidationRun, on_delete=models.PROTECT)
    validation_result = models.ForeignKey(ValidationResult, on_delete=models.SET_NULL, null=True, blank=True)

    # ezeket majd később átdolgozom, egyelőre maradhatnak
    class AlertType(models.TextChoices):
        HIGH = "HIGH", "High"
        LOW = "LOW", "Low"

    alert_type = models.CharField(max_length=250, choices=AlertType.choices)

    class SeverityType(models.TextChoices):
        INFO = "INFO", "Info"
        WARNING = "WARNING", "Warning"
        CRITICAL = "CRITICAL", "Critical"

    severity = models.CharField(max_length=250, choices=SeverityType.choices, default=SeverityType.INFO)  
    schema_name = models.CharField(max_length=250)
    table_name = models.CharField(max_length=250)
    column_name = models.CharField(max_length=250)
    message = models.TextField(max_length=255)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
