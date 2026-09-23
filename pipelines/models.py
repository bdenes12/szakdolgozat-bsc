from django.utils import timezone
from django.db import models

class PipelineRun(models.Model):

    class RunStatuses(models.TextChoices):
        RUNNING = "RUNNING", "Running"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    status = models.CharField(max_length=250, choices=RunStatuses.choices)
    started_at = models.DateTimeField(auto_now_add=True) # létrehozáskor létrejön a dátum, és ha a sort updatelnénk ez akkor sem változik meg
    finished_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    def mark_completed(self):
        self.status=self.RunStatuses.COMPLETED
        self.finished_at=timezone.now()
        self.save()

    def mark_failed(self, err_message):
        self.status=self.RunStatuses.FAILED
        self.finished_at=timezone.now()
        self.error_message=err_message
        self.save()