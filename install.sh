#!/bin/bash
#
# Ablenote Installer
# Installs the Remote Script, Python dependencies, and Dock app.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE="$SCRIPT_DIR/remote_script/Ablenote"
TARGET="$HOME/Music/Ableton/User Library/Remote Scripts/Ablenote"
ABLENOTE_SCRIPT="$SCRIPT_DIR/ablenote.py"

echo ""
echo "=== Ablenote Installer ==="
echo ""

# ── 1. Check Python 3 ────────────────────────────────────────────────────

if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3 is required but not found."
    echo "Install it from https://www.python.org or via Homebrew: brew install python"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo "Found $PYTHON_VERSION"
echo ""

# ── 2. Install Python dependencies ───────────────────────────────────────

echo "Installing Python dependencies..."
pip3 install --quiet rumps 2>/dev/null || pip3 install rumps
echo "  rumps ✓ (menu bar app)"

if pip3 install --quiet Pillow 2>/dev/null || pip3 install Pillow 2>/dev/null; then
    echo "  Pillow ✓ (icon generation)"
else
    echo "  Pillow ✗ (optional – icon generation only)"
fi
echo ""

# ── 3. Install Remote Script ─────────────────────────────────────────────

if [ ! -d "$SOURCE" ]; then
    echo "ERROR: Remote Script not found at:"
    echo "  $SOURCE"
    exit 1
fi

REMOTE_SCRIPTS_DIR="$HOME/Music/Ableton/User Library/Remote Scripts"
if [ ! -d "$REMOTE_SCRIPTS_DIR" ]; then
    echo "Creating Remote Scripts directory..."
    mkdir -p "$REMOTE_SCRIPTS_DIR"
fi

if [ -d "$TARGET" ]; then
    echo "Removing old Ablenote Remote Script..."
    rm -rf "$TARGET"
fi

echo "Installing Remote Script to:"
echo "  $TARGET"
cp -R "$SOURCE" "$TARGET"
echo "  Remote Script ✓"
echo ""

# ── 4. Build Ablenote.app ────────────────────────────────────────────────

APP_PATH="$SCRIPT_DIR/Ablenote.app"
echo "Building Ablenote.app..."
osacompile -o "$APP_PATH" -e "do shell script \"python3 \\\"$ABLENOTE_SCRIPT\\\"\"" 2>/dev/null

if [ -d "$APP_PATH" ]; then
    echo "  Ablenote.app ✓"
    echo "  You can drag it to your Dock for quick access."
else
    echo "  Ablenote.app ✗ (optional – you can still use the hotkey or menu bar)"
fi
echo ""

# ── 5. Copy example config if none exists ─────────────────────────────────

if [ ! -f "$SCRIPT_DIR/config.json" ]; then
    if [ -f "$SCRIPT_DIR/config.example.json" ]; then
        cp "$SCRIPT_DIR/config.example.json" "$SCRIPT_DIR/config.json"
    fi
fi

# ── 6. Offer to run setup ────────────────────────────────────────────────

echo "=== Installation complete! ==="
echo ""
read -p "Run setup now to choose your Obsidian vault folder? [Y/n] " answer
if [[ "$answer" != "n" && "$answer" != "N" ]]; then
    python3 "$ABLENOTE_SCRIPT" --setup
fi

echo ""
echo "=== Next steps ==="
echo ""
echo "1. Restart Ableton Live"
echo "2. Go to: Preferences → Link, Tempo & MIDI"
echo "3. Under 'Control Surface' select 'Ablenote'"
echo "   (Input/Output can be left empty)"
echo ""
echo "4. Optional: Set up a global hotkey"
echo "   Open the macOS Shortcuts app and create a shortcut"
echo "   with the action 'Run Shell Script':"
echo "   python3 \"$ABLENOTE_SCRIPT\""
echo ""
echo "   Then assign a keyboard shortcut (e.g. ⇧⌃N) in:"
echo "   System Settings → Keyboard → Keyboard Shortcuts → App Shortcuts"
echo ""
