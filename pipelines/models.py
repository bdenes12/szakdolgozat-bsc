from django.db import models
from django.urls import reverse
from django.utils import timezone


class PipelineRun(models.Model):
    class RunStatuses(models.TextChoices):
        RUNNING = "RUNNING", "Running"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    status = models.CharField(max_length=250, choices=RunStatuses.choices)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    def mark_completed(self):
        self.status = self.RunStatuses.COMPLETED
        self.finished_at = timezone.now()
        self.save()

    def mark_failed(self, err_message):
        self.status = self.RunStatuses.FAILED
        self.finished_at = timezone.now()
        self.error_message = err_message
        self.save()

    def get_absolute_url(self):
        return reverse("pipelines:pipeline-detail", kwargs={"my_id": self.id})
