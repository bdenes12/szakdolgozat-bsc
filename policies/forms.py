from django import forms
from .models import ColumnPolicy

class ColumnPolicyForm(forms.ModelForm):
    value_overlap = forms.BooleanField(required=False, initial=True, label='Értékátfedés vizsgálat')

    statistical_mean = forms.BooleanField(required=False, initial=False, label='Átlag')
    statistical_std = forms.BooleanField(required=False, initial=False, label='Szórás')
    statistical_ks = forms.BooleanField(required=False, initial=False, label='Kolmogorov-Smirnov (eloszlás)')
    statistical_entropy = forms.BooleanField(required=False, initial=False, label='Shannon-entrópia')

    max_mean_rel_error = forms.DecimalField(required=False, max_digits=4, decimal_places=2, label="Átlag - max. relatív eltérés (0.20 = 20%)")
    max_std_rel_error = forms.DecimalField(required=False, max_digits=4, decimal_places=2, label="Szórás - max. relatív eltérés (0.25 = 25%)")
    max_ks_statistic = forms.DecimalField(required=False, max_digits=4, decimal_places=2, label="KS - max. távolság (0 = azonos, 1 = teljesen más)")
    min_ks_pvalue = forms.DecimalField(required=False, max_digits=4, decimal_places=2, label="KS - min. p-érték (pl. 0.05)")
    max_entropy_rel_error = forms.DecimalField(required=False, max_digits=4, decimal_places=2, label="Entrópia - max. relatív eltérés (0.40 = 40%)")

    class Meta:
        model = ColumnPolicy
        exclude = ['quality_checks']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        qc = {}
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

        if mean_enabled and max_mean_rel_error is None:
            raise forms.ValidationError("Ha az átlag statisztika engedélyezve van, meg kell adni a maximális relatív hibát!")

        if std_enabled and max_std_rel_error is None:
            raise forms.ValidationError("Ha a szórás statisztika engedélyezve van, meg kell adni a maximális relatív hibát!")

        if ks_enabled and (max_ks_statistic is None or min_ks_pvalue is None):
            raise forms.ValidationError("Ha a KS statisztika engedélyezve van, meg kell adni p értéket és a KS-távolságot!")

        if entropy_enabled and max_entropy_rel_error is None:
            raise forms.ValidationError("Ha az entropy statisztika engedélyezve van, meg kell adni a maximális relatív hibát!")

        return cleaned_data


    def save(self, commit = True):
        policy = super().save(commit=False)

        policy.quality_checks = {
            "value_overlap": self.cleaned_data.get("value_overlap", True),
            "statistical": {
                "mean": {"enabled": self.cleaned_data.get("statistical_mean"), "max_rel_error": float(self.cleaned_data.get("max_mean_rel_error")) if self.cleaned_data.get("max_mean_rel_error") is not None else None },
                "std": {"enabled": self.cleaned_data.get("statistical_std"), "max_rel_error": float(self.cleaned_data.get("max_std_rel_error")) if self.cleaned_data.get("max_std_rel_error") is not None else None },
                "ks": {"enabled": self.cleaned_data.get("statistical_ks"), "max_statistic": float(self.cleaned_data.get("max_ks_statistic")) if self.cleaned_data.get("max_ks_statistic") is not None else None , "min_pvalue": float(self.cleaned_data.get("min_ks_pvalue")) if self.cleaned_data.get("min_ks_pvalue") is not None else None },
                "entropy": {"enabled": self.cleaned_data.get("statistical_entropy"), "max_rel_error": float(self.cleaned_data.get("max_entropy_rel_error")) if self.cleaned_data.get("max_entropy_rel_error") is not None else None }
            }
        }

        if commit:
            policy.save()

        return policy
    