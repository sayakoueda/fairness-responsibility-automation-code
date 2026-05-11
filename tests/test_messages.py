"""Tests for the i18n layer (i18n.py + messages_*.yaml).

Checks:
- both ja and en YAMLs load.
- every key is defined in both languages (no missing-on-one-side keys).
- t() resolves in the order: requested locale -> fallback -> raw key.
- format strings can be fed to str.format().
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PKG_DIR = REPO_ROOT / "src" / "oekaki_behavioural_exp" / "settings"


def _load(locale: str) -> dict:
    p = PKG_DIR / f"messages_{locale}.yaml"
    with open(p, "rt", encoding="utf-8") as fp:
        data = yaml.safe_load(fp)
    assert isinstance(data, dict), f"{p} should be a dict"
    return data


@pytest.fixture(scope="module")
def messages_ja() -> dict:
    return _load("ja")


@pytest.fixture(scope="module")
def messages_en() -> dict:
    return _load("en")


def test_ja_and_en_have_same_keys(messages_ja, messages_en):
    """The key set of ja and en must match exactly."""
    ja_keys = set(messages_ja.keys())
    en_keys = set(messages_en.keys())
    only_in_ja = ja_keys - en_keys
    only_in_en = en_keys - ja_keys
    assert not only_in_ja, f"keys only in ja: {sorted(only_in_ja)}"
    assert not only_in_en, f"keys only in en: {sorted(only_in_en)}"


def test_all_values_are_non_empty_strings(messages_ja, messages_en):
    for d, name in [(messages_ja, "ja"), (messages_en, "en")]:
        for k, v in d.items():
            assert isinstance(v, str) and v, f"{name}.{k} should be non-empty string, got {v!r}"


def test_format_strings_have_compatible_placeholders(messages_ja, messages_en):
    """format_* keys contain format specs like {:>2d}; both languages must have the same number of '{' braces."""
    for k in messages_ja:
        if not k.startswith("format_"):
            continue
        ja_braces = messages_ja[k].count("{")
        en_braces = messages_en[k].count("{")
        assert ja_braces == en_braces, f"{k}: ja has {ja_braces} '{{' vs en {en_braces}"


def test_t_returns_key_when_missing(monkeypatch):
    """Missing keys come back as the literal key string (so bugs surface quickly)."""
    import oekaki_behavioural_exp  # noqa: F401  (trigger sys.path hook)
    import i18n
    assert i18n.t("__no_such_key__") == "__no_such_key__"


def test_t_falls_back_to_default_locale(monkeypatch):
    """When the requested locale does not exist, t() falls back to the default (en) values."""
    monkeypatch.setenv("OEKAKI_LOCALE", "xx")  # non-existent locale
    import oekaki_behavioural_exp  # noqa: F401
    import i18n
    importlib.reload(i18n)
    assert i18n.LOCALE == "xx"
    assert i18n.DEFAULT_LOCALE == "en"
    # Must match the en value.
    en = _load("en")
    sample_key = "scene_q_time"
    assert i18n.t(sample_key) == en[sample_key]
    # cleanup
    monkeypatch.delenv("OEKAKI_LOCALE")
    importlib.reload(i18n)


def test_t_uses_ja_when_locale_is_ja(monkeypatch):
    monkeypatch.setenv("OEKAKI_LOCALE", "ja")
    import oekaki_behavioural_exp  # noqa: F401
    import i18n
    importlib.reload(i18n)
    ja = _load("ja")
    sample_key = "scene_q_time"
    assert i18n.t(sample_key) == ja[sample_key]
    monkeypatch.delenv("OEKAKI_LOCALE")
    importlib.reload(i18n)


def test_default_locale_is_en():
    import oekaki_behavioural_exp  # noqa: F401
    import i18n
    importlib.reload(i18n)
    assert i18n.DEFAULT_LOCALE == "en"
    en = _load("en")
    sample_key = "scene_q_time"
    assert i18n.t(sample_key) == en[sample_key]
