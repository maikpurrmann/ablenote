#!/usr/bin/env python3
"""
Ablenote – Quick notes from Ableton Live into Obsidian.

Usage: python3 ablenote.py
       python3 ablenote.py --setup
       python3 ablenote.py --task
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

from i18n import load_locale, t

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
STATE_FILE = os.path.expanduser("~/.ablenote_state.json")
LAUNCH_AGENT = os.path.expanduser("~/Library/LaunchAgents/com.ablenote.menu.plist")


def _init_locale():
    """Load locale from config, default to English."""
    locale = "en"
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                locale = json.load(f).get("locale", "en")
        except Exception:
            pass
    load_locale(locale)


# ---------------------------------------------------------------------------
# AppleScript helpers
# ---------------------------------------------------------------------------

def escape_applescript(text):
    return text.replace("\\", "\\\\").replace('"', '\\"')


def show_notification(title, message):
    subprocess.run([
        "osascript", "-e",
        f'display notification "{escape_applescript(message)}" '
        f'with title "{escape_applescript(title)}"'
    ], capture_output=True)


def choose_from_list(title, prompt, items, default=None):
    items_str = ", ".join(f'"{escape_applescript(i)}"' for i in items)
    default_str = f'default items {{"{escape_applescript(default or items[0])}"}}' if items else ""
    script = f'''
    tell application "System Events"
        activate
        choose from list {{{items_str}}} with title "{escape_applescript(title)}" with prompt "{escape_applescript(prompt)}" {default_str}
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0 or result.stdout.strip() == "false":
        return None
    return result.stdout.strip()


def choose_folder(prompt=None):
    if prompt is None:
        prompt = t("choose_folder_prompt")
    script = f'''
    tell application "System Events"
        activate
        set chosenFolder to choose folder with prompt "{escape_applescript(prompt)}"
        return POSIX path of chosenFolder
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip().rstrip("/")


def show_input_dialog(message, default_answer="", title="Ablenote"):
    msg_escaped = escape_applescript(message).replace("\\n", '" & linefeed & "')
    btn_cancel = escape_applescript(t("btn_cancel"))
    btn_task = escape_applescript(t("btn_task"))
    btn_note = escape_applescript(t("btn_note"))
    script = f'''
    tell application "System Events"
        activate
        set userInput to display dialog "{msg_escaped}" default answer "{escape_applescript(default_answer)}" with title "{escape_applescript(title)}" buttons {{"{btn_cancel}", "{btn_task}", "{btn_note}"}} default button "{btn_note}" with icon note
        return (button returned of userInput) & "|" & (text returned of userInput)
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return None, False
    output = result.stdout.strip()
    if "|" in output:
        button, text = output.split("|", 1)
        return text, button == t("btn_task")
    return output, False


def show_input_dialog_simple(message, default_answer="", title="Ablenote"):
    msg_escaped = escape_applescript(message).replace("\\n", '" & linefeed & "')
    btn_cancel = escape_applescript(t("btn_cancel"))
    btn_save = escape_applescript(t("btn_save"))
    script = f'''
    tell application "System Events"
        activate
        set userInput to display dialog "{msg_escaped}" default answer "{escape_applescript(default_answer)}" with title "{escape_applescript(title)}" buttons {{"{btn_cancel}", "{btn_save}"}} default button "{btn_save}" with icon note
        return text returned of userInput
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def load_config():
    if not os.path.exists(CONFIG_PATH):
        run_setup()
        if not os.path.exists(CONFIG_PATH):
            sys.exit(0)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def is_autostart_enabled():
    return os.path.exists(LAUNCH_AGENT)


def toggle_autostart():
    if is_autostart_enabled():
        subprocess.run(["launchctl", "unload", LAUNCH_AGENT], capture_output=True)
        os.remove(LAUNCH_AGENT)
        subprocess.run(["pkill", "-f", "ablenote_watcher.py"], capture_output=True)
        subprocess.run(["pkill", "-f", "ablenote_menu.py"], capture_output=True)
        show_notification(t("app_title"), t("notification_autostart_off"))
    else:
        watcher_script = os.path.join(SCRIPT_DIR, "ablenote_watcher.py")
        wrapper_path = os.path.expanduser("~/.ablenote_watcher.sh")
        with open(wrapper_path, "w") as wf:
            wf.write(f'#!/bin/bash\nexec /usr/bin/python3 "{watcher_script}"\n')
        os.chmod(wrapper_path, 0o755)
        plist = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ablenote.menu</string>
    <key>ProgramArguments</key>
    <array>
        <string>{wrapper_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>'''
        with open(LAUNCH_AGENT, "w") as f:
            f.write(plist)
        subprocess.run(["launchctl", "load", LAUNCH_AGENT], capture_output=True)
        show_notification(t("app_title"), t("notification_autostart_on"))


def run_setup():
    _init_locale()
    while True:
        current_path = ""
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, encoding="utf-8") as f:
                    existing = json.load(f)
                current_path = existing.get("vault_base", "")
            except Exception:
                pass

        if current_path:
            path_info = t("folder_label", path=current_path)
        else:
            path_info = t("folder_not_set")

        autostart_status = t("on") if is_autostart_enabled() else t("off")
        if is_autostart_enabled():
            autostart_btn = t("btn_autostart_off")
        else:
            autostart_btn = t("btn_autostart_on")

        line1 = escape_applescript(t("setup_description"))
        line2 = escape_applescript(t("setup_detail"))
        line3 = escape_applescript(path_info)
        line4 = escape_applescript(t("autostart_label", status=autostart_status))
        line5 = escape_applescript(t("credits"))
        btn_close = escape_applescript(t("btn_close"))
        btn_autostart = escape_applescript(autostart_btn)
        btn_folder = escape_applescript(t("btn_choose_folder"))

        script = f'''
        tell application "System Events"
            activate
            set msg to "{line1}" & linefeed & linefeed & "{line2}" & linefeed & linefeed & "{line3}" & linefeed & "{line4}" & linefeed & linefeed & "{line5}"
            return button returned of (display dialog msg with title "{escape_applescript(t("setup_title"))}" buttons {{"{btn_close}", "{btn_autostart}", "{btn_folder}"}} default button "{btn_folder}" with icon note)
        end tell
        '''
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if result.returncode != 0:
            return None

        button = result.stdout.strip()

        if button == t("btn_choose_folder"):
            folder = choose_folder(t("choose_folder_setup"))
            if folder:
                folder_name = os.path.basename(folder)
                config = {
                    "vault_base": folder,
                    "folders": {folder_name: ""},
                    "default_folder": folder_name,
                    "locale": "en",
                }
                save_config(config)
                show_notification(t("app_title"), t("notification_folder_set", folder=folder))
            continue

        elif button in (t("btn_autostart_on"), t("btn_autostart_off")):
            toggle_autostart()
            continue

        else:
            return None


# ---------------------------------------------------------------------------
# Ableton state
# ---------------------------------------------------------------------------

def load_ableton_state():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, encoding="utf-8") as f:
                state = json.load(f)
            if time.time() - state.get("timestamp", 0) < 30:
                return state
    except Exception:
        pass
    return None


def get_project_from_window():
    """Fallback: read project name from Ableton window title (any edition)."""
    script = '''
    tell application "System Events"
        set abletonProcs to every process whose name starts with "Ableton Live"
        if (count of abletonProcs) > 0 then
            tell item 1 of abletonProcs
                return name of front window
            end tell
        end if
    end tell
    '''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            title = result.stdout.strip()
            if " - " in title:
                return title.split(" - ")[0].strip()
            return title
    except Exception:
        pass
    return None


def get_ableton_context():
    state = load_ableton_state()
    if state:
        return state
    project = get_project_from_window()
    if project:
        return {"project": project, "_fallback": True}
    return None


# ---------------------------------------------------------------------------
# Save note
# ---------------------------------------------------------------------------

def sanitize_filename(name):
    return "".join(c if c.isalnum() or c in " -_" else "" for c in name).strip()


def extract_project_name(song_name):
    """Extract base project name from Ableton filename.

    'Iter 14 - Master 03' → 'Iter'
    'Iter 01'             → 'Iter'
    'Bond'                → 'Bond'
    """
    if not song_name:
        return "Unknown"
    name = re.sub(r"\s*-\s*Master\s*\d*\s*$", "", song_name, flags=re.IGNORECASE)
    name = re.sub(r"\s+\d+\s*$", "", name)
    return name.strip() or song_name.strip() or "Unknown"


def save_note(config, context, note_text, is_task=False):
    now = datetime.now()
    raw_name = context.get("project", "") if context else ""
    project = extract_project_name(raw_name)

    track = ""
    clip = ""
    tempo = ""
    bar = ""

    if context and not context.get("_fallback"):
        track = context.get("selected_track", "")
        clip = context.get("clip_name", "")
        tempo = context.get("tempo", "")
        bar = context.get("current_bar", "")

    vault_path = config["_resolved_vault_path"]
    os.makedirs(vault_path, exist_ok=True)

    safe_project = sanitize_filename(project)
    filename = f"{safe_project}.md"
    filepath = os.path.join(vault_path, filename)

    if track and clip:
        prefix = f"{track}/{clip}: "
    elif track:
        prefix = f"{track}: "
    elif clip:
        prefix = f"{clip}: "
    else:
        prefix = ""

    meta_parts = []
    if clip and bar:
        meta_parts.append(t("meta_bar", bar=bar))
    if tempo:
        meta_parts.append(f"{int(float(tempo))} BPM")
    if raw_name:
        meta_parts.append(t("meta_file", name=raw_name))
    meta_parts.append(now.strftime("%H:%M"))
    meta = ", ".join(meta_parts)

    if is_task:
        entry = f"- [ ] {prefix}{note_text} ({meta})\n"
    else:
        entry = f"- {prefix}{note_text} ({meta})\n"

    if os.path.exists(filepath):
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(entry)
    else:
        fm_lines = [
            "---",
            f'project: "{project}"',
            f'created: "{now.strftime("%Y-%m-%d")}"',
            "tags: [ablenote]",
            "---",
        ]
        content = "\n".join(fm_lines) + f"\n\n# {project} Project\n\n" + entry
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    return filepath


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def resolve_vault_path(config, folder_name=None):
    base = config["vault_base"]
    folders = config.get("folders", {})

    if folder_name and folder_name in folders:
        return os.path.join(base, folders[folder_name])

    if "vault_path" in config:
        return config["vault_path"]

    default = config.get("default_folder", "")
    if default and default in folders:
        return os.path.join(base, folders[default])

    return base


def main():
    _init_locale()
    config = load_config()
    context = get_ableton_context()

    if context:
        project = extract_project_name(context.get("project", ""))
        info = t("context_project", project=project)
        if not context.get("_fallback"):
            track = context.get("selected_track", "")
            if track:
                info += "  |  " + t("context_track", track=track)
            clip = context.get("clip_name", "")
            if clip:
                info += "  |  " + t("context_clip", clip=clip)
    else:
        project = "Unknown"
        info = t("context_unknown")

    folders = config.get("folders", {})
    folder_name = None
    if len(folders) > 1:
        folder_name = choose_from_list(
            t("dialog_choose_folder_title"),
            f"{info}\n\n{t('dialog_choose_folder_prompt')}",
            list(folders.keys()),
            default=config.get("default_folder")
        )
        if not folder_name:
            return
    elif len(folders) == 1:
        folder_name = list(folders.keys())[0]

    config["_resolved_vault_path"] = resolve_vault_path(config, folder_name)

    force_task = "--task" in sys.argv
    if force_task:
        note_text = show_input_dialog_simple(
            f"{info}\n\n{t('dialog_your_task')}",
            title=f"{t('app_title')} – {t('label_task')}"
        )
        is_task = True
    else:
        note_text, is_task = show_input_dialog(
            f"{info}\n\n{t('dialog_your_note')}",
            title=f"{t('app_title')} – {project}"
        )

    if not note_text:
        return

    filepath = save_note(config, context, note_text, is_task)
    filename = os.path.basename(filepath)
    label = t("label_task") if is_task else t("label_note")
    show_notification(t("app_title"), t("notification_saved", label=label, filename=filename))


if __name__ == "__main__":
    if "--setup" in sys.argv:
        run_setup()
    else:
        main()
