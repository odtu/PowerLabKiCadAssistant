"""Schematic editor toolbar action: show/hide this KiCad's PowerLab Assistant panel (the
same one the PCB editor's button uses), starting it if it isn't running.

KiCad runs this in the plugin's own Python environment, which has no wx, so the
panel itself is started on KiCad's bundled Python (scripting/plugins/powerlab_assistant).
This uses that package's launch.py, which needs no wx.
"""

import json
import os
import sys

# This file lives in <KiCad documents>/10.0/plugins/<this plugin>/
VERSION_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTING = os.path.join(VERSION_DIR, "scripting", "plugins")
CONFIG = os.path.join(os.environ.get("APPDATA", ""), "PowerLabKiCadAssistant", "config.json")


def kicad_python():
    try:
        with open(CONFIG, encoding="utf-8-sig") as f:  # written by PowerShell, with a BOM
            configured = json.load(f).get("kicad_bin", "")
    except (OSError, ValueError):
        configured = ""
    for folder in (configured, r"C:\Program Files\KiCad\10.0\bin", sys.base_prefix):
        exe = os.path.join(folder, "pythonw.exe") if folder else ""
        if exe and os.path.isfile(exe) and os.path.isdir(os.path.join(folder, "Lib", "site-packages", "wx")):
            return exe
    raise SystemExit("KiCad 10's Python was not found. Run install.ps1 again.")


if __name__ == "__main__":
    os.environ["POWERLAB_ASSISTANT_STANDALONE"] = "1"  # importing the package mustn't register the PCB button
    sys.path.insert(0, SCRIPTING)
    from powerlab_assistant import kicad_window, launch

    launch.toggle(kicad_python(), "schematic", kicad_window.kicad_ancestor(os.getpid()))
