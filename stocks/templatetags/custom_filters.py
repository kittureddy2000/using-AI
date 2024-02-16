from django import template
import math


register = template.Library()

@register.filter(name='millions')
def millions(value):
    """Convert an integer to a string representation in millions."""
    try:
        value = float(value)
        return "{:.2f}M".format(value / 1_000_000)
    except (ValueError, TypeError):
        return value

@register.filter
def nan_to_blank(value):
    """Convert NaN values to blank."""
    if value != value:  # This is a way to check for NaN values since NaN != NaN
        return ""
    return value
