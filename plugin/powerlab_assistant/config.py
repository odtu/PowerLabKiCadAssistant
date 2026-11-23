"""Per-user settings. Everything here stays on this computer.

config.json  - written by install.ps1 (library clone path, extra work folders, MCP path)
settings.json - panel preferences (chosen model, effort, accepted notice version)

Both live in %APPDATA%\\PowerLabKiCadAssistant (Windows) or ~/Library/Application Support/
PowerLabKiCadAssistant (macOS). Nothing in this folder is ever sent anywhere by the panel.
"""

import json
import os
import sys

VERSION = "1.5.0"  # bump with every release (see CLAUDE.md > Releasing)
REPORT_REPO = "odtu/PowerLabKiCadAssistant"  # public repo that receives bug reports
LIBRARY_REPO = "odtu/PowerLabKiCadLibraries"
NOTICE_VERSION = 1  # bump when the AI/privacy notice changes, so users see it again

IS_WINDOWS = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"


def _user_dir(windows_var):
    """The per-user folder for app data: %APPDATA% / %LOCALAPPDATA% on Windows,
    ~/Library/Application Support on macOS, $XDG_CONFIG_HOME (~/.config) elsewhere."""
    if IS_MAC:
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    if IS_WINDOWS or os.environ.get(windows_var):
        return os.environ.get(windows_var, os.path.expanduser("~"))
    return os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")


CONFIG_DIR = os.path.join(_user_dir("APPDATA"), "PowerLabKiCadAssistant")
# Where the installer puts the KiCad MCP server and numba (%LOCALAPPDATA% on Windows).
LOCAL_DIR = os.path.join(_user_dir("LOCALAPPDATA"), "PowerLabKiCadAssistant")
# KiCad 10's own settings (kicad_common.json, kicad.json, library tables).
if IS_MAC:
    KICAD_CONFIG = os.path.join(os.path.expanduser("~"), "Library", "Preferences", "kicad", "10.0")
else:
    KICAD_CONFIG = os.path.join(_user_dir("APPDATA"), "kicad", "10.0")
EXE = ".exe" if IS_WINDOWS else ""
MAC_APP = "/Applications/KiCad/KiCad.app"
MAC_PYTHON = "Contents/Frameworks/Python.framework/Versions/Current/bin/python3"
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


def source_path():
    """The folder install.ps1 ran from (a git clone, if updates can be pulled)."""
    return config().get("source_path", "")


def _app_of(path):
    """macOS: the KiCad.app a path lies in (KiCad's Python is inside the app), or ""."""
    marker = ".app" + os.sep + "Contents" + os.sep
    return path[:path.index(marker) + 4] if marker in path else ""


def _apps():
    """KiCad.apps to look in: the one this Python is in (directly, or as the base of the venv
    KiCad makes for a plugin), then the usual place."""
    return [_app_of(sys.executable), _app_of(sys.base_prefix + os.sep), MAC_APP]


def kicad_bin():
    """KiCad's folder with kicad-cli: bin\\ on Windows (Python is there too), KiCad.app's
    Contents/MacOS on macOS. Inside KiCad, found from where Python runs."""
    if IS_MAC:
        candidates = [config().get("kicad_bin", "")] + [
            os.path.join(app, "Contents", "MacOS") for app in _apps() if app]
    else:  # base_prefix: KiCad's Python when this runs in the venv KiCad made for a plugin
        candidates = [config().get("kicad_bin", ""), os.path.dirname(sys.executable),
                      sys.base_prefix, r"C:\Program Files\KiCad\10.0\bin"]
    for folder in candidates:
        if folder and os.path.isfile(os.path.join(folder, "kicad-cli" + EXE)):
            return folder
    return ""


def kicad_python(gui=False):
    """KiCad 10's own Python (it has wx and pcbnew), or "". gui: Windows' pythonw.exe, which
    opens no console; on macOS the framework's python3 runs GUI programs as it is."""
    if IS_MAC:
        apps = [_app_of(kicad_bin() + os.sep)] + _apps()
        candidates = [config().get("kicad_python", "")] + [os.path.join(a, *MAC_PYTHON.split("/")) for a in apps if a]
    else:
        folder = kicad_bin()
        candidates = [os.path.join(folder, "pythonw.exe" if gui else "python.exe")] if folder else []
    for exe in candidates:
        if exe and os.path.isfile(exe):
            return exe
    return ""
