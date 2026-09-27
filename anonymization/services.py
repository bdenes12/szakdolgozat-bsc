import psycopg2
import os
from psycopg2 import sql
from itertools import groupby
from policies.models import ColumnPolicy
from policies.services import PolicyService

def build_mask_expression(policy_obj: ColumnPolicy):

    column_name = policy_obj.column_name
    parameters_list = policy_obj.masking_strategy.parameters
    anon_function = policy_obj.masking_strategy.anon_function.function
    is_column_name_parameter = policy_obj.masking_strategy.anon_function.is_column_name_parameter

    schema, name = anon_function.split('.')

    schema = sql.Identifier(schema)
    name = sql.Identifier(name)

    anon_func_args = []
    if is_column_name_parameter:

        mark_exp = sql.SQL("{}.{}({})").format(schema, name, sql.Identifier(column_name))

        anon_func_args.append(sql.Identifier(column_name))

        if parameters_list:
            for parameter in parameters_list:
                anon_func_args.append(sql.Literal(parameter))

            mark_exp = sql.SQL("{}.{}({})").format(schema, name, sql.SQL(", ").join(anon_func_args))

    elif not is_column_name_parameter and not parameters_list:
        for parameter in parameters_list:
            anon_func_args.append(sql.Literal(parameter))

        mark_exp = sql.SQL("{}.{}({})").format(schema, name, sql.SQL(", ").join(anon_func_args))

    else:

        mark_exp = sql.SQL("{}.{}()").format(schema, name)

    return mark_exp            

def apply_policies():

    active_policies = PolicyService().get_active_policies(environment=ColumnPolicy.EnvironmentTypes.DEVELOPMENT).order_by('table_name')

    active_policies_by_tables = {}
    columns = []

    conn_staging = None

    try:
        dsn_staging = os.getenv("STAGING_DSN")
        conn_staging = psycopg2.connect(dsn_staging)

        with conn_staging:
            with conn_staging.cursor() as cur_staging:

                for table_name, policy in groupby(active_policies, key = lambda x: x.table_name):
                    active_policies_by_tables[table_name] = list(policy)

                cur_staging.execute(sql.SQL("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"))
                table_names = [row[0] for row in cur_staging.fetchall()]

                for table_name in table_names:
                    policies = active_policies_by_tables.get(table_name, [])

                #for table_name, policies in active_policies_by_tables.items():
                    cur_staging.execute(sql.SQL("SELECT column_name FROM information_schema.columns WHERE table_name = {table_name} AND table_schema = 'public' ").format(
                         table_name = sql.Literal(table_name)
                    ))

                    columns = [sql.Identifier(row[0]) for row in cur_staging.fetchall()]

                    for policy in policies:
                        if sql.Identifier(policy.column_name) in columns:
                            index = columns.index(sql.Identifier(policy.column_name))
                            mask_exp = build_mask_expression(policy)
                            columns[index] = sql.SQL("{} AS {}").format(
                                mask_exp,
                                sql.Identifier(policy.column_name)
                            )

                    cur_staging.execute(sql.SQL("DROP VIEW IF EXISTS dev_export.{table_name}").format(
                        table_name = sql.Identifier(table_name)
                    ))
                    
                    cur_staging.execute(sql.SQL("CREATE OR REPLACE VIEW dev_export.{table_name} AS SELECT {} FROM public.{table_name}").format(
                        sql.SQL(', ').join(columns),
                        table_name = sql.Identifier(table_name)))
    finally:
        if conn_staging:
            conn_staging.close()

