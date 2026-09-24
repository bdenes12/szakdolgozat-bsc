import psycopg2
from psycopg2 import sql
from validations.models import ValidationResult
from abc import ABC, abstractmethod

COMPATIBLE_TYPES = {
    "integer": {"integer", "bigint"},
    "smallint": {"smallint", "integer", "bigint"},
    "bigint": {"integer", "bigint"},
    "character varying": {"character varying", "text"},
    "text": {"character varying", "text"},
    "date": {"date", "timestamp without time zone"},
    "timestamp without time zone": {"timestamp without time zone", "timestamp with time zone"},
} 
# Az ETL folyamat során a PyArrow backend bizonyos típuskonverziókat végez (pl. integer → bigint), amelyeket a validáció elfogadható megfeleltetésként kezel, mivel funkcionálisan kompatibilisek.

class BaseCheck(ABC):

    def __init__(self, prod_dsn: str, staging_dsn: str, dev_dsn: str, policies):
        self.prod_dsn = prod_dsn
        self.staging_dsn = staging_dsn
        self.dev_dsn = dev_dsn
        self.policies = policies

    def _table_names(self):
    
        conn_prod = None

        table_names = []

        try:
            conn_prod = psycopg2.connect(self.prod_dsn)
            with conn_prod:
                with conn_prod.cursor() as cur:
                    cur.execute(sql.SQL("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"))

                    table_names = cur.fetchall()

        finally:
            if conn_prod:
                conn_prod.close()

        return table_names

    @abstractmethod
    def execute(self):
        pass

class RowCountCheck(BaseCheck):

    def _count(self, dsn, schema, table):

        conn = None

        try:
            conn = psycopg2.connect(dsn)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(sql.SQL("SELECT COUNT(*) FROM {schema}.{table_name}").format(
                        schema=sql.Identifier(schema),
                        table_name=sql.Identifier(table)
                    ))
                    result = cur.fetchone()[0]
        finally:
            if conn:
                conn.close()
            
        return result

    def execute(self):

        results = []

        for schema_name, table_name in self._table_names():
            prod_table_count = self._count(self.prod_dsn, schema_name, table_name)
            staging_table_count = self._count(self.staging_dsn, schema_name, table_name)
            dev_table_count = self._count(self.dev_dsn, schema_name, table_name)

            results.append({
                "schema_name": schema_name,
                "table_name": table_name,
                "column_name": "",
                "check_type": ValidationResult.CheckTypes.ROW_COUNT,
                "status": ValidationResult.ValidationResultStatuses.PASS if prod_table_count == staging_table_count == dev_table_count else ValidationResult.ValidationResultStatuses.FAIL,
                "metrics":{"prod_table_count": prod_table_count, "staging_table_count": staging_table_count, "dev_table_count": dev_table_count},
                "applied_thresholds": {},
                "message": "Row counts match" if prod_table_count == staging_table_count == dev_table_count else "Row counts mismatch",
                "column_policy": None,
            })


        return results

class ColumnTypeCheck(BaseCheck):

    def _column_types(self, dsn, schema, table):

        conn = None

        types = {}

        try:
            conn = psycopg2.connect(dsn)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(sql.SQL("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = {table_name} AND table_schema = {schema} AND column_name NOT LIKE '_dlt%' ").format(
                        table_name = sql.Literal(table),
                        schema = sql.Literal(schema)
                    ))

                    types[table] = {row[0] : row[1] for row in cur.fetchall() if not row[0].startswith("_dlt")}
        finally:
            if conn:
                conn.close()
            
        return types

    def execute(self):

        results = []

        for schema_name, table_name in self._table_names():
            prod_types = self._column_types(self.prod_dsn, schema_name, table_name)
            staging_types = self._column_types(self.staging_dsn, schema_name, table_name)
            dev_types = self._column_types(self.dev_dsn, schema_name, table_name)

            for column_name in prod_types[table_name]:

                prod_type = prod_types[table_name][column_name]
                staging_type = staging_types[table_name][column_name]
                dev_type = dev_types[table_name][column_name]

                compatible_set = COMPATIBLE_TYPES.get(prod_type, {prod_type})
                is_compatible_staging = (prod_type == staging_type) or (staging_type in compatible_set)
                is_compatible_dev = (prod_type == dev_type) or (dev_type in compatible_set)

                results.append({
                    "schema_name": schema_name,
                    "table_name": table_name,
                    "column_name": column_name,
                    "check_type": ValidationResult.CheckTypes.COLUMN_TYPE,
                    "status": ValidationResult.ValidationResultStatuses.PASS if is_compatible_staging and is_compatible_dev else ValidationResult.ValidationResultStatuses.FAIL, 
                    "metrics": {
                        "prod_type": prod_type,
                        "staging_type": staging_type,
                        "dev_type": dev_type,
                    },
                    "applied_thresholds": {},
                    "message": "Column types compatible" if is_compatible_staging and is_compatible_dev else "Column types mismatch",
                    "column_policy": None,
                })

        return results

class ValueOverlapCheck(BaseCheck):

    def _column_values(self, dsn, schema, table, column):

        conn = None

        result = set()

        try:

            conn = psycopg2.connect(dsn)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(sql.SQL("SELECT {column_name} FROM {schema}.{table_name}").format(
                        column_name = sql.Identifier(column),
                        schema = sql.Identifier(schema),
                        table_name = sql.Identifier(table)
                    ))

                    result = {row[0] for row in cur.fetchall() if row[0] is not None}

            return result

        finally:
            if conn:
                conn.close()

    def _calculate_overlap(self, prod_values, dev_values):

        leaks = prod_values.intersection(dev_values)
        leaks_count = len(leaks)

        overlap_ratio = (leaks_count / len(prod_values)) * 100

        return {
            "leaks_count": leaks_count,
            "leaks": leaks, # CSAK TESZTELÉSI CÉLLAL, KÉSŐBB ELVÉTELRE KERÜL
            "overlap_ratio": round(overlap_ratio, 4),
            "prod_distinct_count": len(prod_values),
            "dev_distinct_count": len(dev_values)
        }

    def execute(self):

        results = []

        for policy in self.policies:
            prod_col_values = self._column_values(self.prod_dsn, policy.schema_name, policy.table_name, policy.column_name)
            dev_col_values = self._column_values(self.dev_dsn, policy.schema_name, policy.table_name, policy.column_name)

            metrics = self._calculate_overlap(prod_col_values, dev_col_values)
            threshold = float(policy.data_category.maximum_overlap)

            results.append({
                "schema_name": policy.schema_name,
                "table_name": policy.table_name,
                "column_name": policy.column_name,
                "check_type": ValidationResult.CheckTypes.VALUE_OVERLAP,
                "status": ValidationResult.ValidationResultStatuses.PASS if metrics['overlap_ratio'] <= threshold else ValidationResult.ValidationResultStatuses.FAIL,
                "metrics": metrics,
                "applied_thresholds": {"maximum_pverlap": threshold},
                "message": "The overlap is below the permitted value" if metrics['overlap_ratio'] <= threshold else f"Overlap {metrics['overlap_ratio']} exceeds {threshold}",
                "column_policy": policy,
            })

        return results



        