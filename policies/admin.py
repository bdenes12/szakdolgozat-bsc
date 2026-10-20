from django.contrib import admin
from .models import DataCategory, AnonFunction, MaskingStrategy, ColumnPolicy, PolicySuggestion
from .forms import ColumnPolicyForm
from .services import SuggestionService

from admin_extra_buttons.api import ExtraButtonsMixin, button

admin.site.register(AnonFunction)

@admin.register(DataCategory)
class DataCategoryAdmin(admin.ModelAdmin):
    list_display = ["__str__", "maximum_overlap"]

@admin.register(MaskingStrategy)
class MaskingStrategyAdmin(admin.ModelAdmin):
    list_display = ["__str__", "parameters"]

@admin.action(description="Policy aktiválása")
def activate(modeladmin, request, queryset):
    queryset.update(is_active=True)

@admin.action(description="Policy deaktiválása")
def deactive(modeladmin, request, queryset):
    queryset.update(is_active=False)

@admin.register(ColumnPolicy)
class ColumnPolicyAdmin(ExtraButtonsMixin, admin.ModelAdmin):
    list_display = ["__str__", "is_active"]
    list_filter = ["is_active", ]
    list_select_related = ["data_category", "masking_strategy"]
    form = ColumnPolicyForm
    fields = ["schema_name", "table_name", "column_name", "target_environment", "data_category", "masking_strategy", "masking_policy", "is_active",  
              "value_overlap", ("statistical_mean", "max_mean_rel_error"), ("statistical_std", "max_std_rel_error"), 
              ("statistical_ks", "max_ks_statistic", "min_ks_pvalue"), ("statistical_entropy", "max_entropy_rel_error")]
    actions = [activate, deactive]

    @button(
        html_attrs={'style': 'background-color: #417690; color: white;'}
    )
    def generate_suggestion(self, request):
        try:
            n = SuggestionService().generate_suggestions()
            self.message_user(request, f"{n} új javaslat sikeresen generálva.")
        except Exception:
            self.message_user(request, "Javaslatgenerálás sikertelen, lásd logs/app.log", level="ERROR")

@admin.action(description="Javaslat elutasítása")
def reject_suggestion(modeladmin, request, queryset):
    queryset.filter(status=PolicySuggestion.SuggestionStatus.PENDING).update(status=PolicySuggestion.SuggestionStatus.REJECTED)

@admin.action(description="Javaslat elfogadása")
def accept_suggestion(modeladmin, request, queryset):
    ok, skipped = SuggestionService().accept_suggestion(queryset)
    modeladmin.message_user(request, f"{ok}db javaslat elfogadva, {skipped}db javaslat kihagyva!")

@admin.register(PolicySuggestion)
class PolicySuggestionAdmin(admin.ModelAdmin):
    list_display = ["__str__", "reason", "suggested_category", "suggested_strategy"]
    list_filter = ["status", "suggested_category"]
    list_select_related = ["suggested_category", "suggested_strategy"]
    readonly_fields = ["schema_name", "table_name", "column_name", "data_type", "is_pk", "is_fk", "reason", "status", "created_at"]
    actions = [reject_suggestion, accept_suggestion]

