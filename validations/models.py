from django.db import models
from django.utils import timezone

from pipelines.models import PipelineRun
from policies.models import ColumnPolicy


class ValidationRun(models.Model):
    pipeline_run = models.ForeignKey(PipelineRun, on_delete=models.PROTECT)

    class ValidationRunStatuses(models.TextChoices):
        RUNNING = "RUNNING", "Running"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    status = models.CharField(max_length=250, choices=ValidationRunStatuses.choices)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    def mark_completed(self):
        self.status = self.ValidationRunStatuses.COMPLETED
        self.finished_at = timezone.now()
        self.save()

    def mark_failed(self, err_message):
        self.status = self.ValidationRunStatuses.FAILED
        self.finished_at = timezone.now()
        self.error_message = err_message
        self.save()


class ValidationResult(models.Model):
    validation_run = models.ForeignKey(ValidationRun, on_delete=models.CASCADE)
    column_policy = models.ForeignKey(ColumnPolicy, on_delete=models.SET_NULL, null=True, blank=True)
    schema_name = models.CharField(max_length=250)
    table_name = models.CharField(max_length=250)
    column_name = models.CharField(max_length=250)

    class CheckTypes(models.TextChoices):
        ROW_COUNT = "ROW_COUNT", "Row_count"
        COLUMN_TYPE = "COLUMN_TYPE", "Column_type"
        VALUE_OVERLAP = "VALUE_OVERLAP", "Value_overlap"
        STATISTICAL = "STATISTICAL", "Statistical"
        K_ANONYMITY = "K_ANONYMITY", "K_anonymity"

    check_type = models.CharField(max_length=250, choices=CheckTypes.choices)

    class ValidationResultStatuses(models.TextChoices):
        PASS = "PASS", "Pass"
        WARNING = "WARNING", "Warning"
        FAIL = "FAIL", "Fail"

    status = models.CharField(max_length=250, choices=ValidationResultStatuses.choices)
    metrics = models.JSONField(default=dict)
    applied_thresholds = models.JSONField(default=dict)
    message = models.TextField(blank=True)


class ValidationReport(models.Model):
    validation_run = models.ForeignKey(ValidationRun, on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)
    html_content = models.TextField(blank=True)
