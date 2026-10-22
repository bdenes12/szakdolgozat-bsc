from django import template

register = template.Library()


@register.filter
def translate_key(key, labels_dict):
    return labels_dict.get(key, key)

@register.filter
def round_value(value):
    if isinstance(value, float):
        return round(value, 3) if abs(value) >= 0.001 or value == 0 else f"{value:.1e}"
    
    return value
