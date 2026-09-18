from django.db import models

# Create your models here.

class DataCategory(models.Model):
    name = models.CharField(max_length=250, unique=True)
    description = models.TextField(blank=True)
    maximum_overlap = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.description}"

class AnonFunction(models.Model):
    name = models.CharField(max_length=250, unique=True)
    function = models.CharField(max_length=250, default="")
    is_column_name_parameter = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.description}"

class MaskingStrategy(models.Model):
    name = models.CharField(max_length=250, unique=True)
    description = models.TextField(blank=True)
    parameters = models.JSONField(default=list, blank=True)
    anon_function = models.ForeignKey(AnonFunction, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.description}"

class ColumnPolicy(models.Model):
    schema_name = models.CharField(max_length=250)
    table_name = models.CharField(max_length=250)
    column_name = models.CharField(max_length=250)

    class EnvironmentTypes(models.TextChoices):
        STAGING = "STAGING", "Staging"
        DEVELOPMENT = "DEVELOPMENT", "Development"

    target_environment = models.CharField(max_length=250, choices=EnvironmentTypes.choices, default=EnvironmentTypes.STAGING)  
    data_category = models.ForeignKey(DataCategory, on_delete=models.PROTECT)
    masking_strategy = models.ForeignKey(MaskingStrategy, on_delete=models.PROTECT)
    quality_checks = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)

    #models.UniqueConstraint(fields=["schema_name", "table_name", "column_name", "target_environment"], name="unique_policy")

    class Meta:
        constraints = [
                models.UniqueConstraint(fields=["schema_name", "table_name", "column_name", "target_environment"], name="unique_policy")
            ]

    def __str__(self):
        return f"{self.schema_name}.{self.table_name}.{self.column_name} [{self.target_environment}]"