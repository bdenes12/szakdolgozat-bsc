from .models import ColumnPolicy

class PolicyService:

    def get_active_policies(self, environment):

        return ColumnPolicy.objects.filter(is_active=True, target_environment=environment).select_related("masking_strategy", "data_category")