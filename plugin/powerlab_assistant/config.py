"""Per-user settings. Everything here stays on this computer.

config.json  - written by install.ps1 (library clone path, extra work folders, MCP path)
settings.json - panel preferences (chosen model, accepted notice version)

Both live in %APPDATA%\\PowerLabKiCadAssistant. Nothing in this folder is ever sent
anywhere by the panel.
"""

import json
import os
import sys

VERSION = "0.1.0"
REPORT_REPO = "odtu/PowerLabKiCadAssistant"  # public repo that receives bug reports
LIBRARY_REPO = "odtu/PowerLabKiCadLibraries"
NOTICE_VERSION = 1  # bump when the AI/privacy notice changes, so users see it again

CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "PowerLabKiCadAssistant")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
SETTINGS_PATH = os.path.join(CONFIG_DIR, "settings.json")


def _load(path):
    try:
        with open(path, encoding="utf-8-sig") as f:  # install.ps1 (PowerShell 5.1) writes a BOM
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass  # preferences are a convenience; the panel works without them


def config():
    return _load(CONFIG_PATH)


def settings():
    return _load(SETTINGS_PATH)


def save_settings(data):
    _save(SETTINGS_PATH, data)


def library_path():
    """The user's git clone of PowerLabKiCadLibraries, if the installer set one up."""
    path = config().get("library_path", "")
    return path if path and os.path.isdir(path) else ""


def work_dirs():
    """Folders Claude may work in besides the current project (library clone + user extras)."""
    dirs = [library_path()] + list(config().get("extra_dirs", []))
    return [d for d in dirs if d and os.path.isdir(d)]


def mcp_path():
    return config().get("mcp_path", "")


def kicad_bin():
    """KiCad's bin folder (python, kicad-cli). Inside KiCad that's where Python runs from."""
    candidates = [config().get("kicad_bin", ""), os.path.dirname(sys.executable),
                  r"C:\Program Files\KiCad\10.0\bin"]
    for folder in candidates:
        if folder and os.path.isfile(os.path.join(folder, "kicad-cli.exe")):
            return folder
    return ""
