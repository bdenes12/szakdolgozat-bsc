from django.db import models

# Create your models here.

class PipelineRun(models.Model):

    class RunStatuses(models.TextChoices):
        RUNNING = "RUNNING", "Running"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    status = models.CharField(max_length=250, choices=RunStatuses.choices)
    started_at = models.DateTimeField(auto_now_add=True) # létrehozáskor létrejön a dátum, és ha a sort updatelnénk ez akkor sem változik meg
    finished_at = models.DateField(null=True, blank=True)
    error_message = models.TextField(blank=True)
