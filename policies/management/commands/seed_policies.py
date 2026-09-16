from django.core.management.base import BaseCommand

from policies.models import DataCategory, MaskingStrategy, ColumnPolicy

class Command(BaseCommand):

    help = "Kezdő adatvédelmi kategóriák, maszkolási stratégiák és oszlop szabályok. Későbbiekben ezzel hozunk létre állandó szabályt egy állapot teszteléséhez."

    def handle(self, *args, **options):
        data_category_direct, created = DataCategory.objects.get_or_create(
                name="DIRECT_IDENTIFIER",
                defaults={"description": "Közvetlen azonosító", "maximum_overlap": 0, "is_active": True}
        )

        data_category_quasi, created = DataCategory.objects.get_or_create(
                name="QUASI_IDENTIFIER",
                defaults={"description": "Kvázi azonosító", "maximum_overlap": 10, "is_active": True}
        )

        data_category_sensitive, created = DataCategory.objects.get_or_create(
                name="SENSITIVE",
                defaults={"description": "Érzékeny azonosító", "maximum_overlap": 30, "is_active": True}
        )

        data_category_technical, created = DataCategory.objects.get_or_create(
                name="TECHNICAL",
                defaults={"description": "Technikai azonosító", "maximum_overlap": 100, "is_active": True}
        )

        masking_strategy_fake_first_name, created = MaskingStrategy.objects.get_or_create(
            name="fake_first_name",
            defaults={"description": "Hamis vezetéknév", "parameters": [], "anon_function":"anon.fake_first_name"}
        )

        masking_strategy_partial_email, created = MaskingStrategy.objects.get_or_create(
            name="partial_email",
            defaults={"description": "Részleges email", "parameters": [], "anon_function":"anon.partial_email"}
        )

        masking_strategy_noise_amount, created = MaskingStrategy.objects.get_or_create(
            name="noise_amount",
            defaults={"description": "Összeg zajosítás", "parameters": {"paid_amount": 0.15}, "anon_function":"anon.noise"}
        )

        ColumnPolicy.objects.get_or_create(
            schema_name="public",
            table_name="invoices",
            column_name="paid_amount",
            target_environment="DEVELOPMENT",
            defaults={
                "data_category": data_category_sensitive,
                "masking_strategy": masking_strategy_noise_amount,
                "quality_checks": [],
                "is_active": True
            }
        )

        ColumnPolicy.objects.get_or_create(
            schema_name="public",
            table_name="practitioners",
            column_name="first_name",
            target_environment="DEVELOPMENT",
            defaults={
                "data_category": data_category_quasi,
                "masking_strategy": masking_strategy_fake_first_name,
                "quality_checks": [],
                "is_active": True
            }
        )

        ColumnPolicy.objects.get_or_create(
            schema_name="public",
            table_name="practitioners",
            column_name="email",
            target_environment="DEVELOPMENT",
            defaults={
                "data_category": data_category_direct,
                "masking_strategy": masking_strategy_partial_email,
                "quality_checks": [],
                "is_active": True
            }
        )
    

