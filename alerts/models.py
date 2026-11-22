from django.db import models
from django.utils import timezone

from validations.models import ValidationResult, ValidationRun


class Alert(models.Model):
    validation_run = models.ForeignKey(ValidationRun, on_delete=models.PROTECT)
    validation_result = models.ForeignKey(ValidationResult, on_delete=models.SET_NULL, null=True, blank=True)

    class AlertType(models.TextChoices):
        ROW_COUNT = "ROW_COUNT", "Row count"
        COLUMN_TYPE = "COLUMN_TYPE", "Column type"
        VALUE_OVERLAP = "VALUE_OVERLAP", "Value overlap"
        STATISTICAL = "STATISTICAL", "Statistical"
        MISSING_POLICY = "MISSING_POLICY", "Missing policy"
        K_ANONYMITY = "K_ANONYMITY", "K_anonymity"

    alert_type = models.CharField(max_length=250, choices=AlertType.choices, verbose_name="Riasztás típusa")

    class SeverityType(models.TextChoices):
        INFO = "INFO", "Info"
        WARNING = "WARNING", "Warning"
        CRITICAL = "CRITICAL", "Critical"

    severity = models.CharField(max_length=250, choices=SeverityType.choices, default=SeverityType.INFO, verbose_name="Súlyosság")
    schema_name = models.CharField(max_length=250, verbose_name="Séma neve")
    table_name = models.CharField(max_length=250, verbose_name="Tábla neve")
    column_name = models.CharField(max_length=250, verbose_name="Oszlop neve")
    message = models.TextField(max_length=255, verbose_name="Üzenet")
    is_resolved = models.BooleanField(default=False, verbose_name="Megoldva")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Létrehozás ideje")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Megoldás ideje")

    def resolve(self):
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save()
