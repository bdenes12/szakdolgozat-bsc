import psycopg2
import os
from psycopg2 import sql
from itertools import groupby
from policies.models import ColumnPolicy
from policies.services import PolicyService
from config.logger import setup_logger

logger = setup_logger("anonymization", console=False)

def build_mask_expression(policy_obj: ColumnPolicy):

    column_name = policy_obj.column_name
    parameters_list = policy_obj.masking_strategy.parameters
    anon_function = policy_obj.masking_strategy.anon_function.function
    is_column_name_parameter = policy_obj.masking_strategy.anon_function.is_column_name_parameter

    if not anon_function or "." not in anon_function:
        raise ValueError(f"Hibás AnonFunction.function: {anon_function}")
    
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

    elif not is_column_name_parameter and parameters_list:
        for parameter in parameters_list:
            anon_func_args.append(sql.Literal(parameter))

        mark_exp = sql.SQL("{}.{}({})").format(schema, name, sql.SQL(", ").join(anon_func_args))

    else:

        mark_exp = sql.SQL("{}.{}()").format(schema, name)

    return mark_exp  

    
def apply_staging_labels():
    
    active_policies = PolicyService().get_active_policies(environment=ColumnPolicy.EnvironmentTypes.STAGING).order_by('table_name')

    conn_staging = None

    try:
        dsn_staging = os.getenv("STAGING_DSN")
        if not dsn_staging:
            raise ValueError("Hiányzik a STAGING_DSN")
        
        conn_staging = psycopg2.connect(dsn_staging)

        skipped = 0
        applied = 0

        with conn_staging:
            with conn_staging.cursor() as cur:

                cur.execute(sql.SQL("" \
                    "SELECT n.nspname, c.relname, a.attname, s.provider " \
                    "FROM pg_seclabel s " \
                    "JOIN pg_class c ON s.objoid = c.oid AND s.classoid = 'pg_class'::regclass " \
                    "JOIN pg_namespace n ON c.relnamespace = n.oid " \
                    "JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = s.objsubid " \
                    "WHERE s.provider IN ('support', 'analytics') AND a.attnum > 0"
                ))

                active_labels = cur.fetchall()

                for label in active_labels:
                    cur.execute(sql.SQL("SECURITY LABEL FOR {provider} ON COLUMN {schema_name}.{table_name}.{column_name} IS NULL").format(
                        schema_name = sql.Identifier(label[0]),
                        table_name = sql.Identifier(label[1]),
                        column_name = sql.Identifier(label[2]),
                        provider = sql.Identifier(label[3])
                    ))
                
                for policy in active_policies:
                    
                    if policy.masking_strategy is None:
                        skipped += 1
                        continue

                    mask_exp = build_mask_expression(policy).as_string(cur)

                    label = "MASKED WITH FUNCTION " + mask_exp

                    if not policy.masking_policy:
                        skipped += 1
                        continue

                    cur.execute(sql.SQL("SECURITY LABEL FOR {masking_policy} ON COLUMN {schema_name}.{table_name}.{column_name} is {label} ").format(
                        masking_policy = sql.Identifier(policy.masking_policy.lower()),
                        schema_name = sql.Identifier(policy.schema_name),
                        table_name = sql.Identifier(policy.table_name),
                        column_name = sql.Identifier(policy.column_name),
                        label = sql.Literal(label)
                    ))

                    applied += 1

                logger.info(f"STAGING címkék: {applied} felrakva")

    finally:
        if conn_staging:
            conn_staging.close()



def apply_policies():

    active_policies = PolicyService().get_active_policies(environment=ColumnPolicy.EnvironmentTypes.DEVELOPMENT).order_by('table_name')

    active_policies_by_tables = {}
    columns = []

    conn_staging = None

    applied = 0
    skipped = 0

    try:
        dsn_staging = os.getenv("STAGING_DSN")
        if not dsn_staging:
            raise ValueError("Hiányzik a STAGING_DSN")
        
        conn_staging = psycopg2.connect(dsn_staging)

        with conn_staging:
            with conn_staging.cursor() as cur_staging:

                for table_name, policy in groupby(active_policies, key = lambda x: x.table_name):
                    active_policies_by_tables[table_name] = list(policy)

                cur_staging.execute(sql.SQL("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' AND table_name NOT LIKE '_dlt_%'"))
                table_names = [row[0] for row in cur_staging.fetchall()]

                for table_name in table_names:
                    policies = active_policies_by_tables.get(table_name, [])

                    cur_staging.execute(sql.SQL("SELECT column_name FROM information_schema.columns WHERE table_name = {table_name} AND table_schema = 'public' ").format(
                         table_name = sql.Literal(table_name)
                    ))

                    columns = [sql.Identifier(row[0]) for row in cur_staging.fetchall()]

                    for policy in policies:
                        
                        if policy.masking_strategy is None:
                            skipped += 1
                            continue
                        
                        if sql.Identifier(policy.column_name) in columns:
                            index = columns.index(sql.Identifier(policy.column_name))
                            mask_exp = build_mask_expression(policy)
                            columns[index] = sql.SQL("{} AS {}").format(
                                mask_exp,
                                sql.Identifier(policy.column_name)
                            )
                            applied += 1

                    cur_staging.execute(sql.SQL("DROP VIEW IF EXISTS dev_export.{table_name}").format(
                        table_name = sql.Identifier(table_name)
                    ))
                    
                    cur_staging.execute(sql.SQL("CREATE OR REPLACE VIEW dev_export.{table_name} AS SELECT {} FROM public.{table_name}").format(
                        sql.SQL(', ').join(columns),
                        table_name = sql.Identifier(table_name)))

                logger.info(f"DEV nézetek: {applied} oszlop maszkolva")

    finally:
        if conn_staging:
            conn_staging.close()

