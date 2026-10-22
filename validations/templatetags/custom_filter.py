from django import template

register = template.Library()


@register.filter
def translate_key(key, labels_dict):
    return labels_dict.get(key, key)
