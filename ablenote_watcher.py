#!/usr/bin/env python3
"""Ablenote Watcher – Starts/stops the menu bar app with Ableton."""

import os
import signal
import subprocess
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MENU_SCRIPT = os.path.join(SCRIPT_DIR, "ablenote_menu.py")
STATE_FILE = os.path.expanduser("~/.ablenote_state.json")
CHECK_INTERVAL = 5


def is_ableton_running():
    try:
        if os.path.exists(STATE_FILE):
            age = time.time() - os.path.getmtime(STATE_FILE)
            return age < 30
    except Exception:
        pass
    return False


def is_menu_running():
    try:
        result = subprocess.run(
            ["pgrep", "-f", "ablenote_menu.py"],
            capture_output=True, text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def start_menu():
    try:
        subprocess.Popen(
            [sys.executable, MENU_SCRIPT],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        sys.stderr.write(f"Ablenote Watcher: failed to start menu – {e}\n")


def stop_menu():
    try:
        subprocess.run(["pkill", "-f", "ablenote_menu.py"], capture_output=True)
    except Exception:
        pass


def main():
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    while True:
        try:
            ableton = is_ableton_running()
            menu = is_menu_running()

            if ableton and not menu:
                start_menu()
            elif not ableton and menu:
                stop_menu()
        except Exception as e:
            sys.stderr.write(f"Ablenote Watcher: error – {e}\n")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
