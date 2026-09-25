from datetime import timezone
from django.contrib import admin
from .models import Alert

@admin.register(Alert)
class StationAdmin(admin.ModelAdmin):
    list_display = ["alert_type", "severity", "schema_name", "table_name", "column_name", "message", "is_resolved"]
    list_filter = ["severity", "is_resolved", "created_at"]
    search_fields = ["schema_name","table_name", "column_name"]

@admin.action(description="Resolve")
def resolve(modeladmin, request, queryset):
    queryset.update(resolved_at=timezone.now())