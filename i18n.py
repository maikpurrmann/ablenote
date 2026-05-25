#!/usr/bin/env python3
"""Minimal i18n module — loads UI strings from JSON locale files."""

import json
import os

LOCALES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locales")
_strings = {}


def load_locale(locale="en"):
    global _strings
    path = os.path.join(LOCALES_DIR, f"{locale}.json")
    if not os.path.exists(path):
        path = os.path.join(LOCALES_DIR, "en.json")
    with open(path, encoding="utf-8") as f:
        _strings = json.load(f)


def t(key, **kwargs):
    """Get translated string. Use keyword args for placeholders."""
    text = _strings.get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text
