from datetime import timezone

from django.contrib import admin
from .models import PipelineRun

# Register your models here.

# admin.site.register(PipelineRun)

@admin.register(PipelineRun)
class PipelineRunAdmin(admin.ModelAdmin):
    list_display = ["status", "started_at", "finished_at", "error_message"]
    list_filter = ["status", "started_at", "finished_at"]

@admin.action(description="Mark completed")
def mark_completed(modeladmin, request, queryset):
    queryset.update(finished_at=timezone.now())

@admin.action(description="Mark failed")
def mark_failed(modeladmin, request, queryset, message):
    queryset.update(error_message=message)