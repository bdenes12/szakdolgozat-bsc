import psycopg2
from psycopg2 import sql
from .models import ColumnPolicy

class PolicyService:

    def get_active_policies(self, environment):

        return ColumnPolicy.objects.filter(is_active=True, target_environment=environment).select_related("masking_strategy", "data_category")

    def find_missing_policies(self, prod_dsn, environment):

        conn_prod = None

        missing_policies = []

        try:

            conn_prod = psycopg2.connect(prod_dsn)
            with conn_prod:
                with conn_prod.cursor() as cur:
                    cur.execute(sql.SQL("SELECT table_schema, table_name, column_name FROM information_schema.columns WHERE table_schema = 'public'"))
                    
                    all_column_names = cur.fetchall()

            active_policies = []
            policies = self.get_active_policies(environment)
            
            for policy in policies:
                active_policies.append((policy.schema_name, policy.table_name, policy.column_name))

            missing_policies = list(set(all_column_names) - set(active_policies))
            
        finally:
            if conn_prod:
                conn_prod.close()

        return environment, missing_policies