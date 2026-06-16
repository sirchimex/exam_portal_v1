from django import template

register = template.Library()


@register.filter
def dict_value(value, key):
    """Return a dictionary value by key, or empty string if missing."""
    try:
        return value.get(str(key), value.get(key, ''))
    except AttributeError:
        return ''
