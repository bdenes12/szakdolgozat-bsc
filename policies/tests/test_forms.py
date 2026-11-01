from unittest.mock import patch

import pytest

from policies.anon_functions import ANON_FUNCTIONS
from policies.forms import ColumnPolicyForm, MaskingStrategyForm
from policies.models import AnonFunction
from policies.services import PolicyService

STRATEGY_CASES = [
    ("noise", "[0.15]", True),
    ("noise", '["abc"]', False),
    ("noise", "[]", False),
    ("noise", "[true]", False),
    ("fake_city", "[1]", False),
    ("partial", '[2, "****", 2]', True),
    ("lorem_ipsum", "[]", True),
]

ROLE_CASES = [
    ("DEVELOPMENT", "", True),
    ("DEVELOPMENT", "SUPPORT", False),
    ("STAGING", "SUPPORT", True),
    ("STAGING", "", False),
]

COLUMN_CASES = [
    ("patients", "email", True),
    ("patients", "city", False),
    ("patient_addresses", "city", True),
    ("nincs_ilyen", "email", False),
]


def _anon_function(name):
    return AnonFunction.objects.create(
        name=name, function=f"anon.{name}", is_column_name_parameter=ANON_FUNCTIONS[name]["is_column_name_parameter"]
    )


def _strategy_form(function, parameters):
    return MaskingStrategyForm(
        data={"name": "teszt", "description": "", "parameters": parameters, "anon_function": function.pk}
    )


def _policy_form(environment, role, table, column):
    return ColumnPolicyForm(
        data={
            "schema_name": "public",
            "table_name": table,
            "column_name": column,
            "target_environment": environment,
            "masking_policy": role,
            "is_active": True,
        }
    )


@pytest.mark.django_db
@pytest.mark.parametrize("function_name, parameters, is_valid", STRATEGY_CASES)
def test_masking_strategy_form_validation(function_name, parameters, is_valid):
    anon_function = _anon_function(function_name)
    form = _strategy_form(anon_function, parameters)

    assert form.is_valid() == is_valid


@pytest.mark.django_db
@pytest.mark.parametrize("environment, role, is_valid", ROLE_CASES)
def test_column_policy_form_validation(environment, role, is_valid, monkeypatch):
    monkeypatch.setenv("PRODUCTION_DSN", "x")
    form = _policy_form(environment, role, "patients", "email")

    with (
        patch.object(
            PolicyService,
            "get_column_metadata",
            return_value={("public", "patients", "email"): {"data_type": "text", "is_pk": False, "is_fk": False}},
        )
    ):
        assert form.is_valid() == is_valid


@pytest.mark.django_db
@pytest.mark.parametrize("table, column, is_valid", COLUMN_CASES)
def test_column_policy_form_column_exists(table, column, is_valid, monkeypatch):
    monkeypatch.setenv("PRODUCTION_DSN", "x")
    form = _policy_form("DEVELOPMENT", "", table, column)

    with patch.object(
        PolicyService,
        "get_column_metadata",
        return_value={
            ("public", "patients", "email"): {"data_type": "text", "is_pk": False, "is_fk": False},
            ("public", "patient_addresses", "city"): {"data_type": "text", "is_pk": False, "is_fk": False},
        },
    ):
        assert form.is_valid() == is_valid