from django.db import models


class DataCategory(models.Model):
    name = models.CharField(max_length=250, unique=True)
    description = models.TextField(blank=True)
    maximum_overlap = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Data categories"

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

    class Meta:
        verbose_name_plural = "Masking strategies"

    def __str__(self):
        return f"{self.name} - {self.description}"


class ColumnPolicy(models.Model):
    schema_name = models.CharField(max_length=250)
    table_name = models.CharField(max_length=250)
    column_name = models.CharField(max_length=250)

    class EnvironmentTypes(models.TextChoices):
        STAGING = "STAGING", "Staging"
        DEVELOPMENT = "DEVELOPMENT", "Development"

    target_environment = models.CharField(
        max_length=250, choices=EnvironmentTypes.choices, default=EnvironmentTypes.STAGING
    )

    class UserTypes(models.TextChoices):
        SUPPORT = "SUPPORT", "Support"
        ANALYTICS = "ANALYTICS", "Analytics"

    masking_policy = models.CharField(max_length=50, choices=UserTypes.choices, blank=True, default="", verbose_name="Maszkolt szerepkör")
    data_category = models.ForeignKey(DataCategory, null=True, blank=True, on_delete=models.PROTECT)
    masking_strategy = models.ForeignKey(MaskingStrategy, null=True, blank=True, on_delete=models.PROTECT)
    quality_checks = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True, verbose_name="Aktív")

    class Meta:
        verbose_name_plural = "Column policies"
        constraints = [
            models.UniqueConstraint(
                fields=["schema_name", "table_name", "column_name", "target_environment", "masking_policy"],
                name="unique_policy",
            )
        ]

    def __str__(self):
        return f"{self.schema_name}.{self.table_name}.{self.column_name} [{self.target_environment}]"


class PolicySuggestion(models.Model):
    schema_name = models.CharField(max_length=250)
    table_name = models.CharField(max_length=250)
    column_name = models.CharField(max_length=250)
    data_type = models.CharField(max_length=250, blank=True)
    is_pk = models.BooleanField(default=False)
    is_fk = models.BooleanField(default=False)
    reason = models.CharField(max_length=250, blank=True)
    suggested_category = models.ForeignKey(DataCategory, on_delete=models.PROTECT)
    suggested_strategy = models.ForeignKey(MaskingStrategy, on_delete=models.SET_NULL, null=True, blank=True)

    class SuggestionStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    status = models.CharField(max_length=50, choices=SuggestionStatus.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["schema_name", "table_name", "column_name"], name="unique_policy_suggestion"
            )
        ]

    def __str__(self):
        return f"{self.schema_name}.{self.table_name}.{self.column_name} [{self.status}]"
