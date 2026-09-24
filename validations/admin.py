from datetime import timezone
from django.contrib import admin
from .models import ValidationRun, ValidationResult

@admin.register(ValidationRun)
class ValidationRunAdmin(admin.ModelAdmin):
    list_display = ["status", "started_at", "finished_at", "error_message"]
    list_filter = ["status", "started_at", "finished_at"]
    list_select_related = ["pipeline_run"]

@admin.register(ValidationResult)
class ValidationResultAdmin(admin.ModelAdmin):
    list_display = ["table_name", "column_name", "check_type", "status", "message"]
    list_filter = ["table_name", "status", "check_type"]
    list_select_related = ["validation_run", "column_policy"]

@admin.action(description="Mark completed")
def mark_completed(modeladmin, request, queryset):
    queryset.update(finished_at=timezone.now())

@admin.action(description="Mark failed")
def mark_failed(modeladmin, request, queryset, message):
    queryset.update(error_message=message)