from django.contrib import admin
from .models import DataCategory, AnonFunction, MaskingStrategy, ColumnPolicy

# Register your models here.

#admin.site.register(DataCategory)
#admin.site.register(MaskingStrategy)
admin.site.register(AnonFunction)

@admin.register(DataCategory)
class DataCategoryAdmin(admin.ModelAdmin):
    list_display = ["__str__", "maximum_overlap"]

@admin.register(MaskingStrategy)
class MaskingStrategyAdmin(admin.ModelAdmin):
    list_display = ["__str__", "parameters"]

@admin.register(ColumnPolicy)
class ColumnPolicyAdmin(admin.ModelAdmin):
    list_display = ["__str__", "is_active"]
    list_filter = ["is_active", ]
    list_select_related = ["data_category", "masking_strategy"]

@admin.action(description="Activate policy")
def activate(modeladmin, request, queryset):
    queryset.update(is_active=True)

@admin.action(description="Deactivate policy")
def deactive(modeladmin, request, queryset):
    queryset.update(is_active=False)