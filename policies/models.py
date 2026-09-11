from django.db import models

# Create your models here.

class DataCategory(models.Model):
    name = models.CharField(unique=True)
    description = models.TextField(blank=True)
    maximum_overlap = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)

class MaskingStrategy(models.Model):
    name = models.CharField(unique=True)
    description = models.TextField(blank=True)
    parameters = models.JSONField(default=dict)
    anon_function = models.CharField(max_length=250)