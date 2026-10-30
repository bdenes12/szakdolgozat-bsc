from django.core.management.base import BaseCommand

from policies.anon_functions import ANON_FUNCTIONS
from policies.models import AnonFunction, ColumnPolicy, DataCategory, MaskingStrategy


def qc(overlap, mean=None, std=None, ks=None, entropy=None, k_anon=None):
    return {
        "value_overlap": overlap,
        "k_anonymity": {"enabled": k_anon is not None, "min_k": k_anon},
        "statistical": {
            "mean": {"enabled": mean is not None, "max_rel_error": mean},
            "std": {"enabled": std is not None, "max_rel_error": std},
            "ks": {
                "enabled": ks is not None,
                "max_statistic": ks[0] if ks else None,
                "min_pvalue": ks[1] if ks else None,
            },
            "entropy": {"enabled": entropy is not None, "max_rel_error": entropy},
        },
    }


STRATEGIES = {
    "fake_first_name": ("fake_first_name", [], "Hamis keresztnév, paraméter nélkül."),
    "partial_email": ("partial_email", [], "Részleges e-mail maszk."),
    "noise_15": ("noise", [0.15], "Numerikus zaj, 15%. Több összegoszlopra is rátehető."),
    "fake_city": ("fake_city", [], "Hamis városnév, paraméter nélkül."),
    "fake_postcode": ("fake_postcode", [], "Hamis irányítószám, paraméter nélkül."),
    "fake_last_name": ("fake_last_name", [], "Hamis vezetéknév, paraméter nélkül."),
    "dummy_name": ("dummy_name", [], "Dummy név, paraméter nélkül."),
    "dummy_phone": ("dummy_phone_number", [], "Dummy telefonszám, paraméter nélkül."),
    "hash_id": ("hash", [], "Hash, paraméter nélkül."),
    "date_noise_1y": ("dnoise", ["365 days"], "Dátum zaj, 1 év intervallummal."),
    "noise_50": ("noise", [0.5], "Numerikus zaj, 50%. Több összegoszlopra is rátehető."),
    "partial_account": ("partial", [2, "****", 2], "Részleges maszk."),
    "generalize_decade": ("generalize_daterange", ["decade"], "Dátum évtizedre bontás."),
    "partial_postcode": ("partial", [4, "**", 0], "Részleges irányítószám, [4, '**', 0]."),
}


SCENARIOS = {
    "alap": [
        ("public", "patients", "gender", "DIRECT", None, qc(True, k_anon=5), "DEVELOPMENT", ""),
        ("public", "patients", "email", "DIRECT", "partial_email", qc(True), "DEVELOPMENT", ""),
        ("public", "patients", "first_name", "DIRECT", "fake_first_name", qc(True), "DEVELOPMENT", ""),
        ("public", "patients", "birth_date", "QUASI", "date_noise_1y", qc(False, k_anon=5), "DEVELOPMENT", ""),
        (
            "public",
            "patient_addresses",
            "postal_code",
            "QUASI",
            "fake_postcode",
            qc(False, k_anon=5),
            "DEVELOPMENT",
            "",
        ),
        (
            "public",
            "invoices",
            "paid_amount",
            "SENSITIVE",
            "noise_15",
            qc(False, mean=0.0001, std=0.25, ks=(0.20, 0.05)),
            "DEVELOPMENT",
            "",
        ),
        (
            "public",
            "invoices",
            "total_amount",
            "SENSITIVE",
            "noise_15",
            qc(False, mean=0.20, std=0.25, ks=(0.20, 0.05)),
            "DEVELOPMENT",
            "",
        ),
        ("public", "patients", "email", "DIRECT", "partial_email", qc(True), "STAGING", "SUPPORT"),
        (
            "public",
            "patient_addresses",
            "city",
            "QUASI",
            "fake_city",
            qc(True, entropy=0.40),
            "DEVELOPMENT",
            "",
        ),
    ],
    "hibatlan": [
        ("public", "patients", "national_health_id", "DIRECT", "hash_id", qc(True), "DEVELOPMENT", ""),
        ("public", "patients", "email", "DIRECT", "partial_email", qc(True), "DEVELOPMENT", ""),
        ("public", "patients", "phone_number", "DIRECT", "dummy_phone", qc(True), "DEVELOPMENT", ""),
        ("public", "patients", "first_name", "QUASI", "fake_first_name", qc(True), "DEVELOPMENT", ""),
        ("public", "patients", "last_name", "QUASI", "fake_last_name", qc(True), "DEVELOPMENT", ""),
        ("public", "patients", "mother_name", "QUASI", "dummy_name", qc(True), "DEVELOPMENT", ""),
        ("public", "patients", "birth_date", "QUASI", "date_noise_1y", qc(False), "DEVELOPMENT", ""),
        ("public", "patients", "gender", "TECHNICAL", None, qc(False), "DEVELOPMENT", ""),
        ("public", "patients", "created_at", "TECHNICAL", None, qc(False), "DEVELOPMENT", ""),
        (
            "public",
            "invoices",
            "total_amount",
            "SENSITIVE",
            "noise_15",
            qc(False, mean=0.05, std=0.25, ks=(0.20, 0)),
            "DEVELOPMENT",
            "",
        ),
        (
            "public",
            "invoices",
            "paid_amount",
            "SENSITIVE",
            "noise_15",
            qc(False, mean=0.05, std=0.25, ks=(0.20, 0)),
            "DEVELOPMENT",
            "",
        ),
        (
            "public",
            "invoices",
            "bank_account_number",
            "DIRECT",
            "partial_account",
            qc(True),
            "DEVELOPMENT",
            "",
        ),
        ("public", "invoices", "issued_at", "TECHNICAL", None, qc(False), "DEVELOPMENT", ""),
        ("public", "invoices", "payment_status", "TECHNICAL", None, qc(False), "DEVELOPMENT", ""),
    ],
    "szivargas": [
        ("public", "patients", "national_health_id", "DIRECT", None, qc(True), "DEVELOPMENT", ""),
        ("public", "patients", "email", "DIRECT", None, qc(True), "DEVELOPMENT", ""),
        ("public", "patients", "first_name", "DIRECT", "fake_first_name", qc(True), "DEVELOPMENT", ""),
    ],
    "szigoru_stat": [
        (
            "public",
            "invoices",
            "total_amount",
            "SENSITIVE",
            "noise_50",
            qc(False, mean=0.01, std=0.05, ks=(0.05, 0)),
            "DEVELOPMENT",
            "",
        ),
        (
            "public",
            "invoices",
            "paid_amount",
            "SENSITIVE",
            "noise_15",
            qc(False, mean=0.001, std=0.01),
            "DEVELOPMENT",
            "",
        ),
        (
            "public",
            "lab_results",
            "value_numeric",
            "SENSITIVE",
            "noise_15",
            qc(False, std=0.01, ks=(0.01, 0)),
            "DEVELOPMENT",
            "",
        ),
    ],
    "hianyos": [],
    "staging": [
        ("public", "patients", "gender", "DIRECT", None, qc(True), "DEVELOPMENT", ""),
        ("public", "patients", "email", "DIRECT", "partial_email", qc(True), "DEVELOPMENT", ""),
        ("public", "patients", "first_name", "DIRECT", "fake_first_name", qc(True), "DEVELOPMENT", ""),
        (
            "public",
            "invoices",
            "paid_amount",
            "SENSITIVE",
            "noise_15",
            qc(False, mean=0.001, std=0.25, ks=(0.20, 0.05)),
            "DEVELOPMENT",
            "",
        ),
        (
            "public",
            "invoices",
            "total_amount",
            "SENSITIVE",
            "noise_15",
            qc(False, mean=0.20, std=0.25, ks=(0.20, 0.05)),
            "DEVELOPMENT",
            "",
        ),
        ("public", "patients", "email", "DIRECT", "partial_email", qc(True), "STAGING", "SUPPORT"),
        (
            "public",
            "patient_addresses",
            "city",
            "QUASI",
            "fake_city",
            qc(True, entropy=0.40),
            "DEVELOPMENT",
            "",
        ),
        ("public", "patients", "first_name", "DIRECT", "fake_first_name", qc(True), "STAGING", "ANALYTICS"),
        ("public", "invoices", "paid_amount", "SENSITIVE", "noise_15", qc(False), "STAGING", "ANALYTICS"),
    ],
    "analytics": [
        ("public", "patients", "gender", "DIRECT", None, qc(True, k_anon=5), "DEVELOPMENT", ""),
        ("public", "patients", "email", "DIRECT", "partial_email", qc(True), "DEVELOPMENT", ""),
        ("public", "patients", "first_name", "DIRECT", "fake_first_name", qc(True), "DEVELOPMENT", ""),
        ("public", "patients", "birth_date", "QUASI", "date_noise_1y", qc(False, k_anon=5), "DEVELOPMENT", ""),
        (
            "public",
            "patient_addresses",
            "postal_code",
            "QUASI",
            "fake_postcode",
            qc(False, k_anon=5),
            "DEVELOPMENT",
            "",
        ),
        (
            "public",
            "invoices",
            "paid_amount",
            "SENSITIVE",
            "noise_15",
            qc(False, mean=0.0001, std=0.25, ks=(0.20, 0.05)),
            "DEVELOPMENT",
            "",
        ),
        (
            "public",
            "invoices",
            "total_amount",
            "SENSITIVE",
            "noise_15",
            qc(False, mean=0.20, std=0.25, ks=(0.20, 0.05)),
            "DEVELOPMENT",
            "",
        ),
        ("public", "patients", "email", "DIRECT", "partial_email", qc(True), "STAGING", "SUPPORT"),
        (
            "public",
            "patient_addresses",
            "city",
            "QUASI",
            "fake_city",
            qc(True, entropy=0.40),
            "DEVELOPMENT",
            "",
        ),
        ("public", "patients", "patient_id", "TECHNICAL", None, qc(False), "STAGING", "ANALYTICS"),
        ("public", "patients", "birth_date", "QUASI", "generalize_decade", qc(False, k_anon=5), "STAGING", "ANALYTICS"),
        ("public", "patients", "gender", "QUASI", None, qc(False, k_anon=5), "STAGING", "ANALYTICS"),
        ("public", "patient_addresses", "patient_id", "TECHNICAL", None, qc(False), "STAGING", "ANALYTICS"),
        (
            "public",
            "patient_addresses",
            "postal_code",
            "QUASI",
            "partial_postcode",
            qc(False, k_anon=5),
            "STAGING",
            "ANALYTICS",
        ),
        ("public", "encounters", "encounter_id", "TECHNICAL", None, qc(False), "STAGING", "ANALYTICS"),
        ("public", "encounters", "patient_id", "TECHNICAL", None, qc(False), "STAGING", "ANALYTICS"),
        ("public", "diagnoses", "encounter_id", "TECHNICAL", None, qc(False), "STAGING", "ANALYTICS"),
        ("public", "diagnoses", "icd_code", "SENSITIVE", None, qc(False), "STAGING", "ANALYTICS"),
        ("public", "diagnoses", "severity", "SENSITIVE", None, qc(False), "STAGING", "ANALYTICS"),
    ],
}


class Command(BaseCommand):
    help = "Kezdő adatvédelmi kategóriák, maszkolási stratégiák és oszlop szabályok. Későbbiekben ezzel hozunk létre állandó szabályt egy állapot teszteléséhez."

    def _setup(self):
        categories = {
            "DIRECT": DataCategory.objects.get_or_create(
                name="DIRECT_IDENTIFIER",
                defaults={
                    "description": "Közvetlen azonosító",
                    "maximum_overlap": 0,
                    "is_active": True,
                },
            )[0],
            "QUASI": DataCategory.objects.get_or_create(
                name="QUASI_IDENTIFIER",
                defaults={
                    "description": "Kvázi azonosító",
                    "maximum_overlap": 10,
                    "is_active": True,
                },
            )[0],
            "SENSITIVE": DataCategory.objects.get_or_create(
                name="SENSITIVE",
                defaults={
                    "description": "Érzékeny azonosító",
                    "maximum_overlap": 30,
                    "is_active": True,
                },
            )[0],
            "TECHNICAL": DataCategory.objects.get_or_create(
                name="TECHNICAL",
                defaults={
                    "description": "Technikai azonosító",
                    "maximum_overlap": 100,
                    "is_active": True,
                },
            )[0],
        }

        for key, spec in ANON_FUNCTIONS.items():
            AnonFunction.objects.get_or_create(
                name=key,
                defaults={
                    "function": spec["anon_function"],
                    "is_column_name_parameter": spec["is_column_name_parameter"],
                    "description": spec["description"],
                },
            )

        strategies = {}
        for name, (function_name, parameters, description) in STRATEGIES.items():
            strategies[name], _ = MaskingStrategy.objects.get_or_create(
                name=name,
                defaults={
                    "description": description,
                    "parameters": parameters,
                    "anon_function": AnonFunction.objects.get(name=function_name),
                },
            )

        return categories, strategies

    def add_arguments(self, parser):
        parser.add_argument(
            "--scenario",
            type=str,
            choices=["alap", "hibatlan", "szivargas", "szigoru_stat", "hianyos", "staging", "analytics"],
            default="alap",
            help="A betöltendő policy-szcenárió neve az alábbiak valamelyike lehet: alap, hibatlan, szivargas, szigoru_stat, hianyos, staging, analytics",
        )

    def handle(self, *args, **options):
        ColumnPolicy.objects.all().delete()

        categories, strategies = self._setup()

        policy_number = 0
        scenario = options["scenario"]

        for schema, table, column, category, strategy, checks, environment, role in SCENARIOS[scenario]:
            ColumnPolicy.objects.create(
                schema_name=schema,
                table_name=table,
                column_name=column,
                target_environment=environment,
                masking_policy=role,
                data_category=categories[category],
                masking_strategy=strategies[strategy] if strategy else None,
                quality_checks=checks,
                is_active=True,
            )
            policy_number += 1

        self.stdout.write(self.style.SUCCESS(f"{scenario}: {policy_number} policy létrehozva"))
