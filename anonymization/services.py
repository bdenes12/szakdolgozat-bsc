from psycopg2 import sql
from policies.models import ColumnPolicy

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
