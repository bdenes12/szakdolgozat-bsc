from django.contrib import admin

from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = [
        "alert_type",
        "severity",
        "schema_name",
        "table_name",
        "column_name",
        "message",
        "is_resolved",
    ]
    list_filter = ["severity", "is_resolved", "created_at"]
    search_fields = ["schema_name", "table_name", "column_name"]
    
    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
