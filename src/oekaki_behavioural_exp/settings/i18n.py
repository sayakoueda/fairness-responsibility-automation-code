"""UI text localization (i18n).

Locale files live at ``src/oekaki_behavioural_exp/settings/messages_{locale}.yaml``.
The active locale is selected via the ``OEKAKI_LOCALE`` environment
variable (default: ``en``).

Usage::

    import i18n
    label = i18n.t("scene_q_time")             # plain key lookup
    label = i18n.t("format_seconds").format(7) # works with format strings too

If a key is missing, the fallback chain is:
    1. requested locale -> 2. default locale (``en``) -> 3. the key itself
The third step makes missing keys easy to spot in the UI.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

DEFAULT_LOCALE = "en"
LOCALE = os.environ.get("OEKAKI_LOCALE", DEFAULT_LOCALE).lower()

_HERE = Path(__file__).resolve().parent


def _load_yaml(locale: str) -> Dict[str, str]:
    """Load the YAML file for ``locale`` as a dict. Return an empty dict
    if the file is missing or cannot be parsed.
    """
    path = _HERE / f"messages_{locale}.yaml"
    if not path.exists():
        return {}
    try:
        import yaml  # type: ignore
    except ImportError:
        return {}
    try:
        with open(path, "rt", encoding="utf-8") as fp:
            data = yaml.safe_load(fp)
        if not isinstance(data, dict):
            return {}
        # Coerce all values to str so a stray None / number does not
        # crash callers that do `.format()` on the returned value.
        return {str(k): str(v) for k, v in data.items()}
    except Exception:
        return {}


_PRIMARY: Dict[str, str] = _load_yaml(LOCALE)
_FALLBACK: Dict[str, str] = (
    _load_yaml(DEFAULT_LOCALE) if LOCALE != DEFAULT_LOCALE else _PRIMARY
)


def t(key: str) -> str:
    """Return the localized UI string for ``key``.

    Lookup order:
    1. The locale selected via ``OEKAKI_LOCALE``.
    2. The default locale (``en``).
    3. The raw key itself (so missing translations show up clearly).
    """
    if key in _PRIMARY:
        return _PRIMARY[key]
    if key in _FALLBACK:
        return _FALLBACK[key]
    return key


def available_locales() -> list[str]:
    """List the locale codes for which a ``messages_{locale}.yaml`` file
    exists in this directory.
    """
    locales = []
    for p in _HERE.glob("messages_*.yaml"):
        name = p.stem  # messages_xx
        if name.startswith("messages_"):
            locales.append(name[len("messages_"):])
    return sorted(locales)
