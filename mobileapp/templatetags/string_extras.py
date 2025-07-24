from django import template

register = template.Library()

@register.filter
def concat(val1, val2):
    return str(val1) + str(val2)
