from abc import ABC, abstractmethod
from collections import defaultdict

import numpy as np
import psycopg2
from psycopg2 import sql
from scipy.stats import ks_2samp

from validations.models import ValidationResult

COMPATIBLE_TYPES = {
    "integer": {"integer", "bigint"},
    "smallint": {"smallint", "integer", "bigint"},
    "bigint": {"integer", "bigint"},
    "character varying": {"character varying", "text"},
    "text": {"character varying", "text"},
    "date": {"date", "timestamp without time zone"},
    "timestamp without time zone": {"timestamp without time zone", "timestamp with time zone"},
}
# Az ETL folyamat során a PyArrow backend bizonyos típuskonverziókat végez (pl. integer -> bigint), amelyeket a validáció elfogadható megfeleltetésként kezel, mivel funkcionálisan kompatibilisek.


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
                    cur.execute(
                        sql.SQL(
                            "SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
                        )
                    )

                    table_names = cur.fetchall()

        finally:
            if conn_prod:
                conn_prod.close()

        return table_names

    def _quality_checks(self, policy):
        raw = policy.quality_checks

        if isinstance(raw, dict):
            return raw

        return {}

    def _stat_spec(self, policy):
        spec = self._quality_checks(policy).get("statistical")

        if isinstance(spec, dict):
            return spec

        return None

    def _threshold(self, spec_part, key, default):
        if spec_part is None:
            return default

        value = spec_part.get(key)

        if value is None:
            return default

        return value

    @abstractmethod
    def execute(self):
        pass


class RowCountCheck(BaseCheck):
    def _count(self, dsn, schema, table):
        conn = None

        try:
            conn = psycopg2.connect(dsn)
            with conn, conn.cursor() as cur:
                cur.execute(
                    sql.SQL("SELECT COUNT(*) FROM {schema}.{table_name}").format(
                        schema=sql.Identifier(schema), table_name=sql.Identifier(table)
                    )
                )
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

            results.append(
                {
                    "schema_name": schema_name,
                    "table_name": table_name,
                    "column_name": "",
                    "check_type": ValidationResult.CheckTypes.ROW_COUNT,
                    "status": ValidationResult.ValidationResultStatuses.PASS
                    if prod_table_count == staging_table_count == dev_table_count
                    else ValidationResult.ValidationResultStatuses.FAIL,
                    "metrics": {
                        "prod_table_count": prod_table_count,
                        "staging_table_count": staging_table_count,
                        "dev_table_count": dev_table_count,
                    },
                    "applied_thresholds": {},
                    "message": "A sorok száma egyezik"
                    if prod_table_count == staging_table_count == dev_table_count
                    else "A sorok száma nem egyezik",
                    "column_policy": None,
                }
            )

        return results


class ColumnTypeCheck(BaseCheck):
    def _column_types(self, dsn, schema, table):
        conn = None

        types = {}

        try:
            conn = psycopg2.connect(dsn)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        sql.SQL(
                            "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = {table_name} AND table_schema = {schema} AND column_name NOT LIKE '_dlt%' "
                        ).format(table_name=sql.Literal(table), schema=sql.Literal(schema))
                    )

                    types[table] = {row[0]: row[1] for row in cur.fetchall() if not row[0].startswith("_dlt")}
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
                staging_type = staging_types.get(table_name, {}).get(column_name)
                dev_type = dev_types.get(table_name, {}).get(column_name)

                compatible_set = COMPATIBLE_TYPES.get(prod_type, {prod_type})
                is_compatible_staging = (prod_type == staging_type) or (staging_type in compatible_set)
                is_compatible_dev = (prod_type == dev_type) or (dev_type in compatible_set)

                results.append(
                    {
                        "schema_name": schema_name,
                        "table_name": table_name,
                        "column_name": column_name,
                        "check_type": ValidationResult.CheckTypes.COLUMN_TYPE,
                        "status": ValidationResult.ValidationResultStatuses.PASS
                        if is_compatible_staging and is_compatible_dev
                        else ValidationResult.ValidationResultStatuses.FAIL,
                        "metrics": {
                            "prod_type": prod_type,
                            "staging_type": staging_type,
                            "dev_type": dev_type,
                        },
                        "applied_thresholds": {},
                        "message": "Kompatibilis oszloptípusok"
                        if is_compatible_staging and is_compatible_dev
                        else "Nem kompatibilis típusok",
                        "column_policy": None,
                    }
                )

        return results


class ValueOverlapCheck(BaseCheck):
    def _column_values(self, dsn, schema, table, column):
        conn = None

        result = set()

        try:
            conn = psycopg2.connect(dsn)
            with conn, conn.cursor() as cur:
                cur.execute(
                    sql.SQL("SELECT {column_name} FROM {schema}.{table_name}").format(
                        column_name=sql.Identifier(column),
                        schema=sql.Identifier(schema),
                        table_name=sql.Identifier(table),
                    )
                )

                result = {row[0] for row in cur.fetchall() if row[0] is not None}

            return result

        finally:
            if conn:
                conn.close()

    def _calculate_overlap(self, prod_values, dev_values):
        if not prod_values:
            return None

        leaks = prod_values.intersection(dev_values)
        leaks_count = len(leaks)

        overlap_ratio = round((leaks_count / len(prod_values)) * 100, 3)

        return {
            "leaks_count": leaks_count,
            "overlap_ratio": overlap_ratio,
            "prod_distinct_count": len(prod_values),
            "dev_distinct_count": len(dev_values),
        }

    def execute(self):
        results = []

        for policy in self.policies:
            if self._quality_checks(policy).get("value_overlap", True) is False:
                continue

            prod_col_values = self._column_values(
                self.prod_dsn, policy.schema_name, policy.table_name, policy.column_name
            )
            dev_col_values = self._column_values(
                self.dev_dsn, policy.schema_name, policy.table_name, policy.column_name
            )

            metrics = self._calculate_overlap(prod_col_values, dev_col_values)

            if metrics is None:
                continue

            if policy.data_category is None:
                continue
            else:
                threshold = float(policy.data_category.maximum_overlap)

            results.append(
                {
                    "schema_name": policy.schema_name,
                    "table_name": policy.table_name,
                    "column_name": policy.column_name,
                    "check_type": ValidationResult.CheckTypes.VALUE_OVERLAP,
                    "status": ValidationResult.ValidationResultStatuses.PASS
                    if metrics["overlap_ratio"] <= threshold
                    else ValidationResult.ValidationResultStatuses.FAIL,
                    "metrics": metrics,
                    "applied_thresholds": {"maximum_overlap": threshold},
                    "message": "Az átfedés a megengedett határon belül"
                    if metrics["overlap_ratio"] <= threshold
                    else f"Az átfedés {metrics['overlap_ratio']}% (megengedett: {threshold}%)",
                    "column_policy": policy,
                }
            )

        return results


class StatisticalQualityCheck(BaseCheck):
    def _column_numeric_values(self, dsn, schema, table, column):
        conn = None

        result = []

        numeric_types = ["smallint", "integer", "bigint", "numeric", "decimal", "real", "double precision"]

        try:
            conn = psycopg2.connect(dsn)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        sql.SQL(
                            "SELECT data_type FROM information_schema.columns WHERE table_name = {table_name} AND table_schema = {schema} AND column_name = {column_name} "
                        ).format(
                            table_name=sql.Literal(table), schema=sql.Literal(schema), column_name=sql.Literal(column)
                        )
                    )

                    row = cur.fetchone()
                    if not row:
                        return []
                    column_type = row[0]

                    if column_type in numeric_types:
                        cur.execute(
                            sql.SQL("SELECT {column_name} FROM {schema}.{table_name}").format(
                                column_name=sql.Identifier(column),
                                schema=sql.Identifier(schema),
                                table_name=sql.Identifier(table),
                            )
                        )

                        result = [float(row[0]) for row in cur.fetchall() if row[0] is not None]

            return result

        finally:
            if conn:
                conn.close()

    def _value_counts(self, dsn, schema, table, column):
        result = []

        conn = None

        try:
            conn = psycopg2.connect(dsn)

            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        sql.SQL(
                            "SELECT {column_name}, COUNT(*) FROM {schema}.{table_name} WHERE {column_name} IS NOT NULL GROUP BY {column_name}"
                        ).format(
                            column_name=sql.Identifier(column),
                            schema=sql.Identifier(schema),
                            table_name=sql.Identifier(table),
                        )
                    )

                    result = [row[1] for row in cur.fetchall()]

            return result

        finally:
            if conn:
                conn.close()

    def _histogram_metrics(self, prod_values, dev_values):
        if len(prod_values) < 2 or len(dev_values) < 2:
            return None

        merged_list = [*prod_values, *dev_values]
        min_value = min(merged_list)
        max_value = max(merged_list)

        if min_value == max_value:
            return None

        prod_counts, bin_edges = np.histogram(prod_values, bins=10, range=(min_value, max_value))
        dev_counts, _ = np.histogram(dev_values, bins=10, range=(min_value, max_value))

        labels = []
        for i in range(len(bin_edges) - 1):
            labels.append(f"{round(bin_edges[i], 2)} - {round(bin_edges[i + 1], 2)}")

        return {"prod_histogram": prod_counts.tolist(), "dev_histogram": dev_counts.tolist(), "labels": labels}

    def _compare_means(self, prod_values, dev_values):
        np_prod_values = np.array(prod_values)
        np_dev_values = np.array(dev_values)

        if not prod_values or not dev_values:
            mean_rel_error = None
            prod_mean = None
            dev_mean = None
        else:
            prod_mean = float(np.mean(np_prod_values))
            dev_mean = float(np.mean(np_dev_values))

            if prod_mean != 0:
                mean_rel_error = float(abs(dev_mean - prod_mean) / abs(prod_mean))
            else:
                mean_rel_error = None

        return {"prod_mean": prod_mean, "dev_mean": dev_mean, "mean_rel_error": mean_rel_error}

    def _compare_standard_deviations(self, prod_values, dev_values):
        np_prod_values = np.array(prod_values)
        np_dev_values = np.array(dev_values)

        if not prod_values or not dev_values:
            std_rel_error = None
            prod_std = None
            dev_std = None
        else:
            prod_std = float(np.std(np_prod_values, ddof=0))
            dev_std = float(np.std(np_dev_values, ddof=0))
            if prod_std != 0:
                std_rel_error = float(abs(dev_std - prod_std) / abs(prod_std))
            else:
                std_rel_error = None

        return {"prod_std": prod_std, "dev_std": dev_std, "std_rel_error": std_rel_error}

    def _compare_distributions(self, prod_values, dev_values):
        if len(prod_values) < 2 or len(dev_values) < 2:
            ks_statistic = None
            ks_pvalue = None

        else:
            result = ks_2samp(prod_values, dev_values)
            ks_statistic = float(result.statistic)
            ks_pvalue = float(result.pvalue)

        return {"ks_statistic": ks_statistic, "ks_pvalue": ks_pvalue}

    def _calculate_entropy(self, value_counts):
        if not value_counts:
            return 0.0

        np_value_counts = np.array(value_counts, dtype=float)
        value_counts_sum = np.sum(np_value_counts)

        if value_counts_sum == 0:
            return 0.0

        p = np_value_counts / value_counts_sum

        p_non_zero = p[p > 0]

        entropy = -np.sum(p_non_zero * np.log2(p_non_zero))

        return float(entropy)

    def execute(self):
        results = []

        for policy in self.policies:
            spec = self._stat_spec(policy)

            if spec is None:
                continue

            mean_enabled = spec.get("mean", {}).get("enabled")
            std_enabled = spec.get("std", {}).get("enabled")
            ks_enabled = spec.get("ks", {}).get("enabled")
            entropy_enabled = spec.get("entropy", {}).get("enabled")

            if mean_enabled != True and std_enabled != True and ks_enabled != True and entropy_enabled != True:
                continue

            metrics = {}
            applied_thresholds = {}
            failed = []

            prod = []
            dev = []

            schema = policy.schema_name
            table = policy.table_name
            column = policy.column_name

            if mean_enabled == True or std_enabled == True or ks_enabled == True:
                prod = self._column_numeric_values(self.prod_dsn, schema, table, column)
                dev = self._column_numeric_values(self.dev_dsn, schema, table, column)
                metrics["prod_len"] = len(prod)
                metrics["dev_len"] = len(dev)

            if mean_enabled:
                max_mean_rel_error = self._threshold(spec.get("mean"), "max_rel_error", 0.20)
                applied_thresholds["max_mean_rel_error"] = max_mean_rel_error

                if prod and dev:
                    mean = self._compare_means(prod, dev)
                    mean_rel_error = mean["mean_rel_error"]
                    if mean_rel_error is not None:
                        metrics.update(mean)
                        if mean_rel_error > max_mean_rel_error:
                            failed.append(f"Átlag relatív eltérése {mean_rel_error:.3g} (max. {max_mean_rel_error})")

            if std_enabled:
                max_std_rel_error = self._threshold(spec.get("std"), "max_rel_error", 0.25)
                applied_thresholds["max_std_rel_error"] = max_std_rel_error

                if prod and dev:
                    std = self._compare_standard_deviations(prod, dev)
                    std_rel_error = std["std_rel_error"]
                    if std_rel_error is not None:
                        metrics.update(std)
                        if std_rel_error > max_std_rel_error:
                            failed.append(f"Szórás relatív eltérése {std_rel_error:.3g} (max. {max_std_rel_error})")

            if ks_enabled:
                max_statistic = self._threshold(spec.get("ks"), "max_statistic", 0.20)
                min_pvalue = self._threshold(spec.get("ks"), "min_pvalue", 0.05)

                applied_thresholds["max_statistic"] = max_statistic
                applied_thresholds["min_pvalue"] = min_pvalue

                if len(prod) >= 2 and len(dev) >= 2:
                    distributions = self._compare_distributions(prod, dev)
                    ks_statistic = distributions["ks_statistic"]
                    ks_pvalue = distributions["ks_pvalue"]

                    if ks_statistic is not None:
                        metrics.update(distributions)
                        if ks_statistic > max_statistic:
                            failed.append(f"KS-távolság {ks_statistic:.3g} (max. {max_statistic})")
                        if ks_pvalue < min_pvalue:
                            failed.append(f"KS p-érték {ks_pvalue:.3g} (min. {min_pvalue})")

            if entropy_enabled:
                prod_counts = self._value_counts(self.prod_dsn, schema, table, column)
                prod_entropy = self._calculate_entropy(prod_counts)

                dev_counts = self._value_counts(self.dev_dsn, schema, table, column)
                dev_entropy = self._calculate_entropy(dev_counts)

                max_entropy_rel_error = self._threshold(spec.get("entropy"), "max_rel_error", 0.40)
                applied_thresholds["max_entropy_rel_error"] = max_entropy_rel_error

                metrics["prod_entropy"] = prod_entropy
                metrics["dev_entropy"] = dev_entropy

                if prod_entropy != 0:
                    entropy_rel_error = abs(dev_entropy - prod_entropy) / abs(prod_entropy)
                    metrics["entropy_rel_error"] = entropy_rel_error

                    if entropy_rel_error > max_entropy_rel_error:
                        failed.append(
                            f"Entrópia relatív eltérése {entropy_rel_error:.3g} (max. {max_entropy_rel_error})"
                        )

            if (
                "mean_rel_error" not in metrics
                and "std_rel_error" not in metrics
                and "ks_statistic" not in metrics
                and "entropy_rel_error" not in metrics
            ):
                continue

            histogram_metrics = self._histogram_metrics(prod, dev)
            metrics.update(histogram_metrics or {})

            results.append(
                {
                    "schema_name": policy.schema_name,
                    "table_name": policy.table_name,
                    "column_name": policy.column_name,
                    "check_type": ValidationResult.CheckTypes.STATISTICAL,
                    "status": ValidationResult.ValidationResultStatuses.PASS
                    if not failed
                    else ValidationResult.ValidationResultStatuses.FAIL,
                    "metrics": metrics,
                    "applied_thresholds": applied_thresholds,
                    "message": "; ".join(failed) if failed else "A statisztikai eltérések a határon belül",
                    "column_policy": policy,
                }
            )

        return results


class KAnonymityCheck(BaseCheck):
    def __init__(
        self,
        prod_dsn: str,
        staging_dsn: str,
        dev_dsn: str,
        policies,
        target_dsn: str,
        target_schema: str,
        target_label: str,
        fail_status: str,
    ):
        super().__init__(prod_dsn, staging_dsn, dev_dsn, policies)
        self.target_dsn = target_dsn
        self.target_schema = target_schema
        self.target_label = target_label
        self.fail_status = fail_status

    def _quasi_groups(self):
        k_anonymity_by_tables = {}

        for policy in self.policies:
            k_anonymity = self._quality_checks(policy).get("k_anonymity") or {}
            k_enabled = k_anonymity.get("enabled")

            if k_enabled:
                table = policy.table_name
                column = policy.column_name

                current_k = k_anonymity.get("min_k")

                if table not in k_anonymity_by_tables:
                    k_anonymity_by_tables[table] = {"columns": [], "min_k": 0}

                if column not in k_anonymity_by_tables[table]["columns"]:
                    k_anonymity_by_tables[table]["columns"].append(column)

                k_anonymity_by_tables[table]["min_k"] = max(k_anonymity_by_tables[table]["min_k"], current_k or 5)

        return k_anonymity_by_tables

    def _class_sizes(self, dsn, schema, table, columns):
        result = []

        conn = None

        try:
            conn = psycopg2.connect(dsn)

            with conn:
                with conn.cursor() as cur:
                    sql_columns = [sql.Identifier(column) for column in columns]

                    cur.execute(
                        sql.SQL(
                            "SELECT {column_names}, COUNT(*) AS size FROM {schema}.{table_name} GROUP BY {column_names} ORDER BY size"
                        ).format(
                            column_names=sql.SQL(", ").join(sql_columns),
                            schema=sql.Identifier(schema),
                            table_name=sql.Identifier(table),
                        )
                    )

                    result = [row[-1] for row in cur.fetchall()]

            return result

        finally:
            if conn:
                conn.close()

    def _k_metrics(self, sizes, min_k):
        result = {}

        if not sizes:
            return None

        k = min(sizes)
        n_classes = len(sizes)
        n_rows = sum(sizes)
        unique_ratio = sizes.count(1) / n_rows
        below_k_ratio = sum([size for size in sizes if size < min_k]) / n_rows

        result = {
            "k": k,
            "n_classes": n_classes,
            "n_rows": n_rows,
            "unique_ratio": unique_ratio,
            "below_k_ratio": below_k_ratio,
        }

        return result

    def execute(self):
        results = []

        k_anonymity_by_tables = self._quasi_groups()

        if not k_anonymity_by_tables:
            return results

        for table_name, data in k_anonymity_by_tables.items():
            prod_sizes = self._class_sizes(self.prod_dsn, "public", table_name, data["columns"])
            target_sizes = self._class_sizes(self.target_dsn, self.target_schema, table_name, data["columns"])

            if not prod_sizes or not target_sizes:
                continue

            prod_k_metrics = self._k_metrics(prod_sizes, data["min_k"])
            target_k_metrics = self._k_metrics(target_sizes, data["min_k"])

            status = (
                ValidationResult.ValidationResultStatuses.PASS
                if target_k_metrics["k"] >= data["min_k"]
                else self.fail_status
            )

            message = (
                f"A k-anonimitás teljesül (k={target_k_metrics['k']}, min_k={data['min_k']})"
                if status == ValidationResult.ValidationResultStatuses.PASS
                else f"A k-anonimitás sérül: k={target_k_metrics['k']} (min_k={data['min_k']})"
            )

            results.append(
                {
                    "schema_name": "public",
                    "table_name": table_name,
                    "column_name": ", ".join(data["columns"]),
                    "check_type": ValidationResult.CheckTypes.K_ANONYMITY,
                    "status": status,
                    "applied_thresholds": {"min_k": data["min_k"]},
                    "metrics": {
                        "target": self.target_label,
                        "prod_k": prod_k_metrics["k"],
                        "prod_n_classes": prod_k_metrics["n_classes"],
                        "prod_unique_ratio": prod_k_metrics["unique_ratio"],
                        "prod_below_k_ratio": prod_k_metrics["below_k_ratio"],
                        "k": target_k_metrics["k"],
                        "n_classes": target_k_metrics["n_classes"],
                        "unique_ratio": target_k_metrics["unique_ratio"],
                        "below_k_ratio": target_k_metrics["below_k_ratio"],
                    },
                    "column_policy": None,
                    "message": message,
                }
            )

        return results
