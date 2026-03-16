from functools import lru_cache
from pathlib import Path

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


@lru_cache(maxsize=16)
def _read_static_file(relative_path):
    asset_path = Path(settings.BASE_DIR) / "static" / relative_path
    return asset_path.read_text(encoding="utf-8")


@register.simple_tag
def inline_css(relative_path):
    try:
        return mark_safe(_read_static_file(relative_path))
    except OSError:
        return ""
