from django.core.management.base import BaseCommand
from policies.models import DataCategory, AnonFunction, MaskingStrategy, ColumnPolicy
from policies.anon_functions import ANON_FUNCTIONS

class Command(BaseCommand):

    help = "Kezdő adatvédelmi kategóriák, maszkolási stratégiák és oszlop szabályok. Későbbiekben ezzel hozunk létre állandó szabályt egy állapot teszteléséhez."
    
    def _qc(self, overlap, mean=None, std=None, ks=None, entropy=None):
        return {
        "value_overlap": overlap,
        "statistical": {
            "mean": {"enabled": mean is not None, "max_rel_error": mean},
            "std": {"enabled": std is not None, "max_rel_error": std},
            "ks": {"enabled": ks is not None, "max_statistic": ks[0] if ks else None, "min_pvalue": ks[1] if ks else None},
            "entropy": {"enabled": entropy is not None, "max_rel_error": entropy},
        },
    }

    def handle(self, *args, **options):

        ColumnPolicy.objects.all().delete()

        data_category_direct, _ = DataCategory.objects.get_or_create(
            name="DIRECT_IDENTIFIER",
            defaults={"description": "Közvetlen azonosító", "maximum_overlap": 0, "is_active": True}
        )

        data_category_quasi, _ = DataCategory.objects.get_or_create(
            name="QUASI_IDENTIFIER",
            defaults={"description": "Kvázi azonosító", "maximum_overlap": 10, "is_active": True}
        )

        data_category_sensitive, _ = DataCategory.objects.get_or_create(
            name="SENSITIVE",
            defaults={"description": "Érzékeny azonosító", "maximum_overlap": 30, "is_active": True}
        )

        data_category_technical, _ = DataCategory.objects.get_or_create(
            name="TECHNICAL",
            defaults={"description": "Technikai azonosító", "maximum_overlap": 100, "is_active": True}
        )

        for key, spec in ANON_FUNCTIONS.items():
            AnonFunction.objects.get_or_create(
                name=key,
                defaults={"function": spec['anon_function'], "is_column_name_parameter": spec['is_column_name_parameter'], "description": spec['description']}
            )

        fn_fake_first_name = AnonFunction.objects.get(name="fake_first_name")
        fn_partial_email = AnonFunction.objects.get(name="partial_email")
        fn_noise = AnonFunction.objects.get(name="noise")
        fn_fake_city = AnonFunction.objects.get(name="fake_city")

        strategy_fake_first_name, _ = MaskingStrategy.objects.get_or_create(
            name="fake_first_name",
            defaults={
                "description": "Hamis keresztnév, paraméter nélkül.",
                "parameters": [],
                "anon_function": fn_fake_first_name,
            },
        )
        strategy_partial_email, _ = MaskingStrategy.objects.get_or_create(
            name="partial_email",
            defaults={
                "description": "Részleges e-mail maszk.",
                "parameters": [],
                "anon_function": fn_partial_email,
            },
        )
        strategy_noise_15, _ = MaskingStrategy.objects.get_or_create(
            name="noise_15",
            defaults={
                "description": "Numerikus zaj, 15%. Több összegoszlopra is rátehető.",
                "parameters": [0.15],
                "anon_function": fn_noise,
            },
        )
        strategy_fake_city, _ = MaskingStrategy.objects.get_or_create(
            name="fake_city",
            defaults={
                "description": "Hamis városnév.",
                "parameters": [],
                "anon_function": fn_fake_city,
            },
        )

        ColumnPolicy.objects.get_or_create(
            schema_name="public",
            table_name="patients",
            column_name="gender",
            target_environment="DEVELOPMENT",
            masking_policy="",
            defaults={
                "data_category": data_category_direct,
                "masking_strategy": None,
                "quality_checks": self._qc(True),
                "is_active": True,
            },
        )

        ColumnPolicy.objects.get_or_create(
            schema_name="public",
            table_name="patients",
            column_name="email",
            target_environment="DEVELOPMENT",
            masking_policy="",
            defaults={
                "data_category": data_category_direct,
                "masking_strategy": strategy_partial_email,
                "quality_checks": self._qc(True),
                "is_active": True,
            },
        )

        ColumnPolicy.objects.get_or_create(
            schema_name="public",
            table_name="patients",
            column_name="first_name",
            target_environment="DEVELOPMENT",
            masking_policy="",
            defaults={
                "data_category": data_category_direct,
                "masking_strategy": strategy_fake_first_name,
                "quality_checks": self._qc(True),
                "is_active": True,
            },
        )

        ColumnPolicy.objects.get_or_create(
            schema_name="public",
            table_name="invoices",
            column_name="paid_amount",
            target_environment="DEVELOPMENT",
            masking_policy="",
            defaults={
                "data_category": data_category_sensitive,
                "masking_strategy": strategy_noise_15,
                "quality_checks": self._qc(False, mean=0.001, std=0.25, ks=(0.20, 0.05)),
                "is_active": True,
            },
        )

        ColumnPolicy.objects.get_or_create(
            schema_name="public",
            table_name="invoices",
            column_name="total_amount",
            target_environment="DEVELOPMENT",
            masking_policy="",
            defaults={
                "data_category": data_category_sensitive,
                "masking_strategy": strategy_noise_15,
                "quality_checks": self._qc(False, mean=0.20, std=0.25, ks=(0.20, 0.05)),
                "is_active": True,
            },
        )

        ColumnPolicy.objects.get_or_create(
            schema_name="public",
            table_name="patients",
            column_name="email",
            target_environment="STAGING",
            masking_policy="SUPPORT",
            defaults={
                "data_category": data_category_direct,
                "masking_strategy": strategy_partial_email,
                "quality_checks": self._qc(True),
                "is_active": True,
            },
        )

        ColumnPolicy.objects.get_or_create(
            schema_name="public",
            table_name="patient_addresses",
            column_name="city",
            target_environment="DEVELOPMENT",
            masking_policy="",
            defaults={
                "data_category": data_category_quasi,
                "masking_strategy": strategy_fake_city,
                "quality_checks": self._qc(True, entropy=0.40),
                "is_active": True,
            },
        )
    

