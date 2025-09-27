from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def script_name():
    return getattr(settings, "FORCE_SCRIPT_NAME", "")
