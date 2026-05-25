# Ablenote

Quick notes from Ableton Live sessions, saved as Markdown directly into your Obsidian vault.

One hotkey press, type your note, hit Enter — done. Ablenote automatically captures what you're working on (project, track, clip, bar position, tempo) and saves it all as a compact list entry in Obsidian.

> **macOS only** — Ablenote uses native macOS dialogs and Ableton Live's Remote Script API.

## Features

- **One-click notes** — Global hotkey, menu bar icon, or Dock app
- **Auto-context** — Automatically captures project, track, clip, bar position, and tempo
- **Tasks** — Save as Obsidian-compatible checkboxes (`- [ ]`)
- **One file per project** — All notes for "Iter" land in `Iter.md`, regardless of version
- **Version tracking** — Each entry includes the Ableton filename (e.g. `Iter 14 - Master 03`)
- **Menu bar app** — Music note icon appears when Ableton is running, disappears when it closes
- **Autostart** — Menu bar app lifecycle tied to Ableton via background watcher
- **i18n ready** — English by default, German included, easily extendable

## Requirements

- macOS 12+
- Python 3.9+
- Ableton Live 12 (any edition: Intro, Standard, Suite)
- Obsidian (or any Markdown-based note system)

## Quick Start

```bash
git clone https://github.com/maikpurrmann/ablenote.git
cd ablenote
./install.sh
```

The installer will:
1. Install Python dependencies (`rumps`, `Pillow`)
2. Copy the Remote Script to Ableton's User Library
3. Build `Ablenote.app` for the Dock
4. Run the setup dialog to choose your Obsidian vault folder

After installation, restart Ableton Live and activate the Remote Script:
**Preferences → Link, Tempo & MIDI → Control Surface → Ablenote** (Input/Output empty)

## Usage

### Three ways to create a note

1. **Menu bar** — Click the music note icon → "New Note"
2. **Global hotkey** — Set up via macOS Shortcuts (see below)
3. **Dock app** — Click `Ablenote.app` in your Dock

### The note dialog

The dialog shows your current Ableton context and lets you type a note:

```
Project: Iter  |  Track: Piano  |  Clip: Chords Intro

Your note: [                                    ]

[Cancel]  [Task]  [Note]
```

- **Note** — Saves as a regular list entry (`- ...`)
- **Task** — Saves as an Obsidian checkbox (`- [ ] ...`)
- **Cancel** — Discards

### Task mode

Run with `--task` to skip the Note/Task choice and go straight to task input:

```bash
python3 ablenote.py --task
```

## Note Format

Notes are saved as Markdown, one file per project:

```markdown
---
project: "Iter"
created: "2026-03-31"
tags: [ablenote]
---

# Iter Project

- Piano/Chords Intro: Rework these chords (Bar 24, 120 BPM, File: Iter 14 - Master 03, 17:46)
- [ ] Bass: Add more compression (Bar 32, 120 BPM, File: Iter 14 - Master 03, 17:52)
- Drums/Beat v2: Turn down hi-hats (Bar 48, 120 BPM, File: Iter 14 - Master 03, 18:10)
```

Each entry includes: Track/Clip prefix, your note text, bar position, tempo, Ableton filename, and timestamp.

## How It Works

```
Ableton Live 12
└── Remote Script (remote_script/Ablenote/)
    └── Writes every 2 sec → ~/.ablenote_state.json

                ↓
     ~/.ablenote_state.json
       ↓                ↓
 ablenote_watcher.py   ablenote.py
 Checks every 5 sec    ├── Reads Ableton state
 if Ableton is open    ├── Shows macOS dialog
 → starts/stops        ├── Saves Markdown → Obsidian
   menu bar app        └── --setup / --task modes
       ↓                  ↑        ↑         ↑
  Menu bar app       Dock app   Hotkey    Menu bar
 (ablenote_menu.py)
```

1. The **Remote Script** runs inside Ableton and writes session state to a JSON file every 2 seconds
2. The **Watcher** monitors this file and starts/stops the menu bar app when Ableton opens/closes
3. The **Main Script** reads the state, shows a dialog, and saves the note to your Obsidian vault

## Configuration

`config.json` is created during setup. You can also edit it manually:

```json
{
  "vault_base": "/path/to/your/obsidian/vault",
  "folders": {
    "Ablenote": ""
  },
  "default_folder": "Ablenote",
  "locale": "en"
}
```

| Field | Description |
|-------|-------------|
| `vault_base` | Root path to your Obsidian vault (or subfolder) |
| `folders` | Named folders (relative to vault_base). Multiple → user picks at runtime |
| `default_folder` | Which folder to preselect |
| `locale` | UI language: `"en"` (default) or `"de"` |

### Changing the language

Set `"locale": "de"` in `config.json` for German UI. Add your own locale by creating `locales/{code}.json` with the same keys as `locales/en.json`.

## Setting Up the Global Hotkey

1. Open the **Shortcuts** app (macOS built-in)
2. Create a new shortcut
3. Add the action **Run Shell Script** with:
   ```
   python3 "/path/to/ablenote/ablenote.py"
   ```
4. Give it a name (e.g. "Ablenote")
5. Assign a keyboard shortcut in:
   **System Settings → Keyboard → Keyboard Shortcuts → App Shortcuts**
   (Recommended: `⇧⌃N`)

## Uninstall

```bash
# Remove Remote Script
rm -rf ~/Music/Ableton/User\ Library/Remote\ Scripts/Ablenote/

# Remove autostart
launchctl unload ~/Library/LaunchAgents/com.ablenote.menu.plist 2>/dev/null
rm -f ~/Library/LaunchAgents/com.ablenote.menu.plist
rm -f ~/.ablenote_watcher.sh

# Remove state file
rm -f ~/.ablenote_state.json

# Remove the cloned repo
rm -rf /path/to/ablenote
```

## Troubleshooting

**Remote Script not showing up in Ableton**
- Make sure you ran `./install.sh`
- Check that `~/Music/Ableton/User Library/Remote Scripts/Ablenote/` exists
- Restart Ableton Live completely

**Menu bar icon doesn't appear**
- The icon only appears when Ableton is running with the Remote Script active
- Check if the watcher is running: `pgrep -f ablenote_watcher`
- Try enabling autostart: `python3 ablenote.py --setup`

**"Ableton not detected" in dialog**
- The Remote Script might not be activated. Go to Preferences → Link, Tempo & MIDI → Control Surface → Ablenote
- The state file might be stale. Check: `cat ~/.ablenote_state.json`

**Notes not appearing in Obsidian**
- Check your `config.json` — is `vault_base` pointing to the right folder?
- Run `python3 ablenote.py --setup` to reconfigure

## Credits

Built by [Maik Purrmann](https://github.com/maikpurrmann) with [Claude](https://claude.ai).

## License

[MIT](LICENSE)
