#!/usr/bin/env python3
"""Ablenote – Menu bar app for quick access to all functions."""

import json
import os
import subprocess
import sys

# Hide from Dock
try:
    from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
    NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)
except Exception:
    pass

import rumps

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ABLENOTE_SCRIPT = os.path.join(SCRIPT_DIR, "ablenote.py")
ICON_PATH = os.path.join(SCRIPT_DIR, "icon_menubar.png")
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")


def _load_locale():
    from i18n import load_locale, t
    locale = "en"
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                locale = json.load(f).get("locale", "en")
        except Exception:
            pass
    load_locale(locale)
    return t


class AblenoteApp(rumps.App):
    def __init__(self):
        t = _load_locale()
        super().__init__(
            "Ablenote",
            icon=ICON_PATH if os.path.exists(ICON_PATH) else None,
            template=True,
        )
        self.menu = [
            rumps.MenuItem(t("menu_new_note"), callback=self.new_note),
            None,
            rumps.MenuItem(t("menu_settings"), callback=self.settings),
            None,
        ]

    def new_note(self, _):
        subprocess.Popen([sys.executable, ABLENOTE_SCRIPT])

    def settings(self, _):
        subprocess.Popen([sys.executable, ABLENOTE_SCRIPT, "--setup"])


if __name__ == "__main__":
    AblenoteApp().run()
