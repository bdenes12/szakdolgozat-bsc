import os

import psycopg2
from django.db import IntegrityError
from psycopg2 import sql

from .models import AnonFunction, ColumnPolicy, DataCategory, MaskingStrategy, PolicySuggestion
from .suggestion_rules import match_rule


class PolicyService:
    def get_active_policies(self, environment):
        return ColumnPolicy.objects.filter(is_active=True, target_environment=environment).select_related(
            "masking_strategy", "data_category"
        )

    def find_missing_policies(self, prod_dsn, environment):
        conn_prod = None

        missing_policies = []

        try:
            if not prod_dsn:
                raise ValueError("Hiányzik a PRODUCTION_DSN")

            conn_prod = psycopg2.connect(prod_dsn)
            with conn_prod:
                with conn_prod.cursor() as cur:
                    cur.execute(
                        sql.SQL(
                            "SELECT table_schema, table_name, column_name FROM information_schema.columns WHERE table_schema = 'public'"
                        )
                    )

                    all_column_names = cur.fetchall()

                    cur.execute(
                        sql.SQL(
                            "SELECT kcu.table_schema, kcu.table_name, kcu.column_name "
                            "FROM information_schema.table_constraints tc "
                            "JOIN information_schema.key_column_usage kcu "
                            "ON tc.constraint_name = kcu.constraint_name "
                            "AND tc.table_schema = kcu.table_schema "
                            "WHERE tc.table_schema = 'public' "
                            "AND tc.constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY')"
                        )
                    )

                    pk_columns = set(cur.fetchall())

            active_policies = []
            policies = self.get_active_policies(environment)

            for policy in policies:
                active_policies.append((policy.schema_name, policy.table_name, policy.column_name))

            missing_policies = list(set(all_column_names) - set(active_policies) - pk_columns)

        finally:
            if conn_prod:
                conn_prod.close()

        return environment, missing_policies


class SuggestionService:
    def get_column_metadata(self, prod_dsn):
        conn_prod = None

        column_metadata = {}

        try:
            conn_prod = psycopg2.connect(prod_dsn)

            with conn_prod:
                with conn_prod.cursor() as cur:
                    cur.execute(
                        sql.SQL(
                            "SELECT table_schema, table_name, column_name, data_type FROM information_schema.columns WHERE table_schema = 'public' "
                        )
                    )
                    column_metadata = {
                        (row[0], row[1], row[2]): {"data_type": row[3], "is_pk": False, "is_fk": False}
                        for row in cur.fetchall()
                    }

                    cur.execute(
                        sql.SQL(
                            "SELECT kcu.table_schema, kcu.table_name, kcu.column_name, tc.constraint_type "
                            "FROM information_schema.table_constraints tc "
                            "JOIN information_schema.key_column_usage kcu "
                            "ON tc.constraint_name = kcu.constraint_name "
                            "AND tc.table_schema = kcu.table_schema "
                            "WHERE tc.table_schema = 'public' "
                            "AND tc.constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY')"
                        )
                    )

                    for row in cur.fetchall():
                        key = (row[0], row[1], row[2])

                        if row[3] == "PRIMARY KEY":
                            column_metadata[key]["is_pk"] = True
                        else:
                            column_metadata[key]["is_fk"] = True

        finally:
            if conn_prod:
                conn_prod.close()

        return column_metadata

    def suggest_for_column(self, column_name, data_type, is_pk, is_fk):
        if is_pk:
            suggest = ("TECHNICAL", None, [], "pk")
        elif is_fk:
            suggest = ("TECHNICAL", None, [], "fk")
        else:
            suggest = match_rule(column_name, data_type)

        return suggest

    def resolve_strategy(self, anon_fn_name, params):
        if anon_fn_name is None:
            return None

        strategy = MaskingStrategy.objects.filter(anon_function__name=anon_fn_name, parameters=params).first()

        if strategy:
            return strategy

        try:
            anon_function = AnonFunction.objects.get(name=anon_fn_name)
            if not params:
                name = anon_fn_name
            else:
                name = f"{anon_fn_name}_{params[0]}"

            strategy, created = MaskingStrategy.objects.get_or_create(
                name=name,
                defaults={
                    "description": "Automatikus javaslatból létrehozva",
                    "parameters": params,
                    "anon_function": anon_function,
                },
            )

            return strategy

        except AnonFunction.DoesNotExist:
            raise RuntimeError(f"Seed-hiba: Az '{anon_fn_name}' nevű AnonFunction nem található az adatbázisban. ")

    def generate_suggestions(self):
        prod_dsn = os.getenv("PRODUCTION_DSN")

        if not prod_dsn:
            raise ValueError("Hiányzik a PRODUCTION_DSN")

        _, missing = PolicyService().find_missing_policies(prod_dsn, ColumnPolicy.EnvironmentTypes.DEVELOPMENT)

        metadata = self.get_column_metadata(prod_dsn)

        existing = set(PolicySuggestion.objects.values_list("schema_name", "table_name", "column_name"))

        created = 0

        for schema, table, column in missing:
            key = (schema, table, column)

            if key in existing:
                continue

            value = metadata.get(key)

            if value is None:
                continue

            category_name, anon_fn, params, reason = self.suggest_for_column(
                column, value["data_type"], value["is_pk"], value["is_fk"]
            )

            category = DataCategory.objects.get(name=category_name)

            strategy = self.resolve_strategy(anon_fn, params)

            if anon_fn:
                reason = f"{reason}; fn={anon_fn}"

            PolicySuggestion.objects.create(
                schema_name=schema,
                table_name=table,
                column_name=column,
                data_type=value["data_type"],
                is_pk=value["is_pk"],
                is_fk=value["is_fk"],
                reason=reason,
                suggested_category=category,
                suggested_strategy=strategy,
                status=PolicySuggestion.SuggestionStatus.PENDING,
            )

            created += 1

        return created

    def accept_suggestion(self, queryset):
        skipped = 0
        ok = 0

        for policy_suggestion in queryset:
            if policy_suggestion.status != PolicySuggestion.SuggestionStatus.PENDING:
                skipped += 1
                continue

            if policy_suggestion.suggested_category is None:
                skipped += 1
                continue

            if policy_suggestion.suggested_strategy is None and policy_suggestion.suggested_category.name != "TECHNICAL":
                skipped += 1
                continue

            try:
                ColumnPolicy.objects.create(
                    schema_name=policy_suggestion.schema_name,
                    table_name=policy_suggestion.table_name,
                    column_name=policy_suggestion.column_name,
                    target_environment=ColumnPolicy.EnvironmentTypes.DEVELOPMENT,
                    masking_policy="",
                    data_category=policy_suggestion.suggested_category,
                    masking_strategy=policy_suggestion.suggested_strategy,
                    quality_checks={"value_overlap": True},
                    is_active=True,
                )
            except IntegrityError:
                skipped += 1
                continue

            policy_suggestion.status = PolicySuggestion.SuggestionStatus.ACCEPTED
            policy_suggestion.save()
            ok += 1

        return ok, skipped
