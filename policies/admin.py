from django.contrib import admin
from .models import DataCategory, AnonFunction, MaskingStrategy, ColumnPolicy
from .forms import ColumnPolicyForm

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
    form = ColumnPolicyForm
    fields = ["schema_name", "table_name", "column_name", "target_environment", "data_category", "masking_strategy", "is_active",  
              "value_overlap", ("statistical_mean", "max_mean_rel_error"), ("statistical_std", "max_std_rel_error"), 
              ("statistical_ks", "max_ks_statistic", "min_ks_pvalue"), ("statistical_entropy", "max_entropy_rel_error")]


@admin.action(description="Activate policy")
def activate(modeladmin, request, queryset):
    queryset.update(is_active=True)

@admin.action(description="Deactivate policy")
def deactive(modeladmin, request, queryset):
    queryset.update(is_active=False)