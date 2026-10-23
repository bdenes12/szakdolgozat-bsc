from django import forms

from .anon_functions import expected_parameters
from .models import ColumnPolicy, MaskingStrategy

PARAMETER_TYPES = {
    "integer": (int,),
    "bigint": (int,),
    "double precision": (int, float),
    "numeric": (int, float),
}


class ColumnPolicyForm(forms.ModelForm):
    value_overlap = forms.BooleanField(required=False, initial=True, label="Értékátfedés vizsgálat")

    statistical_mean = forms.BooleanField(required=False, initial=False, label="Átlag")
    statistical_std = forms.BooleanField(required=False, initial=False, label="Szórás")
    statistical_ks = forms.BooleanField(required=False, initial=False, label="Kolmogorov-Smirnov (eloszlás)")
    statistical_entropy = forms.BooleanField(required=False, initial=False, label="Shannon-entrópia")

    max_mean_rel_error = forms.DecimalField(
        required=False, max_digits=4, decimal_places=4, label="Átlag - max. relatív eltérés (0.20 = 20%)"
    )
    max_std_rel_error = forms.DecimalField(
        required=False, max_digits=4, decimal_places=4, label="Szórás - max. relatív eltérés (0.25 = 25%)"
    )
    max_ks_statistic = forms.DecimalField(
        required=False, max_digits=4, decimal_places=4, label="KS - max. távolság (0 = azonos, 1 = teljesen más)"
    )
    min_ks_pvalue = forms.DecimalField(
        required=False, max_digits=4, decimal_places=4, label="KS - min. p-érték (pl. 0.05)"
    )
    max_entropy_rel_error = forms.DecimalField(
        required=False, max_digits=4, decimal_places=4, label="Entrópia - max. relatív eltérés (0.40 = 40%)"
    )

    class Meta:
        model = ColumnPolicy
        exclude = ["quality_checks"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        qc = {}
        stat = {}
        if self.instance and self.instance.pk:
            raw = self.instance.quality_checks
            if isinstance(raw, dict):
                qc = raw
                stat = qc.get("statistical") or {}
                if not isinstance(stat, dict):
                    stat = {}

        mean = stat.get("mean") or {}
        std = stat.get("std") or {}
        ks = stat.get("ks") or {}
        entropy = stat.get("entropy") or {}

        self.fields["value_overlap"].initial = qc.get("value_overlap", True)

        self.fields["statistical_mean"].initial = mean.get("enabled")
        self.fields["statistical_std"].initial = std.get("enabled")
        self.fields["statistical_ks"].initial = ks.get("enabled")
        self.fields["statistical_entropy"].initial = entropy.get("enabled")

        self.fields["max_mean_rel_error"].initial = mean.get("max_rel_error")
        self.fields["max_std_rel_error"].initial = std.get("max_rel_error")
        self.fields["max_ks_statistic"].initial = ks.get("max_statistic")
        self.fields["min_ks_pvalue"].initial = ks.get("min_pvalue")
        self.fields["max_entropy_rel_error"].initial = entropy.get("max_rel_error")

    def clean(self):
        cleaned_data = super().clean()

        mean_enabled = cleaned_data.get("statistical_mean")
        max_mean_rel_error = cleaned_data.get("max_mean_rel_error")

        std_enabled = cleaned_data.get("statistical_std")
        max_std_rel_error = cleaned_data.get("max_std_rel_error")

        ks_enabled = cleaned_data.get("statistical_ks")
        max_ks_statistic = cleaned_data.get("max_ks_statistic")
        min_ks_pvalue = cleaned_data.get("min_ks_pvalue")

        entropy_enabled = cleaned_data.get("statistical_entropy")
        max_entropy_rel_error = cleaned_data.get("max_entropy_rel_error")

        environment = cleaned_data.get("target_environment")
        role = cleaned_data.get("masking_policy")

        if mean_enabled and max_mean_rel_error is None:
            raise forms.ValidationError(
                "Ha az átlag statisztika engedélyezve van, meg kell adni a maximális relatív hibát!"
            )

        if std_enabled and max_std_rel_error is None:
            raise forms.ValidationError(
                "Ha a szórás statisztika engedélyezve van, meg kell adni a maximális relatív hibát!"
            )

        if ks_enabled and (max_ks_statistic is None or min_ks_pvalue is None):
            raise forms.ValidationError(
                "Ha a KS statisztika engedélyezve van, meg kell adni p értéket és a KS-távolságot!"
            )

        if entropy_enabled and max_entropy_rel_error is None:
            raise forms.ValidationError(
                "Ha az entrópia statisztika engedélyezve van, meg kell adni a maximális relatív hibát!"
            )

        if environment == ColumnPolicy.EnvironmentTypes.DEVELOPMENT and role:
            raise forms.ValidationError(
                "A maszkolt szerepkör mező csak STAGING környezetben adható meg, DEV környezetben nem!"
            )

        if environment == ColumnPolicy.EnvironmentTypes.STAGING and not role:
            raise forms.ValidationError("A maszkolt szerepkör mező STAGING környezetben kötelező, üresen nem hagyható!")

        return cleaned_data

    def save(self, commit=True):
        policy = super().save(commit=False)

        policy.quality_checks = {
            "value_overlap": self.cleaned_data.get("value_overlap", True),
            "statistical": {
                "mean": {
                    "enabled": self.cleaned_data.get("statistical_mean"),
                    "max_rel_error": float(self.cleaned_data.get("max_mean_rel_error"))
                    if self.cleaned_data.get("max_mean_rel_error") is not None
                    else None,
                },
                "std": {
                    "enabled": self.cleaned_data.get("statistical_std"),
                    "max_rel_error": float(self.cleaned_data.get("max_std_rel_error"))
                    if self.cleaned_data.get("max_std_rel_error") is not None
                    else None,
                },
                "ks": {
                    "enabled": self.cleaned_data.get("statistical_ks"),
                    "max_statistic": float(self.cleaned_data.get("max_ks_statistic"))
                    if self.cleaned_data.get("max_ks_statistic") is not None
                    else None,
                    "min_pvalue": float(self.cleaned_data.get("min_ks_pvalue"))
                    if self.cleaned_data.get("min_ks_pvalue") is not None
                    else None,
                },
                "entropy": {
                    "enabled": self.cleaned_data.get("statistical_entropy"),
                    "max_rel_error": float(self.cleaned_data.get("max_entropy_rel_error"))
                    if self.cleaned_data.get("max_entropy_rel_error") is not None
                    else None,
                },
            },
        }

        if commit:
            policy.save()

        return policy


class MaskingStrategyForm(forms.ModelForm):
    class Meta:
        model = MaskingStrategy
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        anon_function = cleaned_data.get("anon_function")
        parameters = cleaned_data.get("parameters")

        if not anon_function:
            return cleaned_data

        if not isinstance(parameters, list):
            self.add_error("parameters", "A paramétereket listaként kell megadni, pl. [0.15].")
            return cleaned_data

        expected_params = expected_parameters(anon_function.name)

        required_params = sum(1 for _, _, required in expected_params if required)
        all_params = len(expected_params)

        if len(parameters) < required_params or len(parameters) > all_params:
            if all_params == 0:
                message = f"A '{anon_function.name}' függvény nem vár paramétert."
            elif required_params == all_params:
                message = f"A '{anon_function.name}' függvény pontosan {all_params} paramétert vár."
            else:
                message = f"A '{anon_function.name}' függvényhez {required_params} és {all_params} közötti számú paraméter adható meg."

            self.add_error("parameters", message)
            return cleaned_data

        for value, (name, data_type, required) in zip(parameters, expected_params):
            if value is None and required:
                self.add_error("parameters", f"A '{name}' paraméter kötelező, nem lehet null.")
                continue

            if isinstance(value, bool):
                self.add_error("parameters", f"A '{name}' paraméter nem lehet logikai érték.")
                continue
            
            if value is not None and not isinstance(value, PARAMETER_TYPES.get(data_type, (str,))):
                self.add_error(
                    "parameters",
                    f"A '{name}' paraméternek '{data_type}' típusnak kell lennie, de a megadott érték: {value} ({type(value).__name__}).",
                )

        return cleaned_data
