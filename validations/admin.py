from django.contrib import admin

from .models import ValidationResult, ValidationRun


@admin.register(ValidationRun)
class ValidationRunAdmin(admin.ModelAdmin):
    list_display = ["status", "started_at", "finished_at", "error_message"]
    list_filter = ["status", "started_at", "finished_at"]
    list_select_related = ["pipeline_run"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ValidationResult)
class ValidationResultAdmin(admin.ModelAdmin):
    list_display = ["table_name", "column_name", "check_type", "status", "message"]
    list_filter = ["table_name", "status", "check_type"]
    list_select_related = ["validation_run", "column_policy"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
