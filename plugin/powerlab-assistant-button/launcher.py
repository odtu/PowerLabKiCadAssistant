"""Schematic editor toolbar action: show/hide this KiCad's PowerLab Assistant panel (the
same one the PCB editor's button uses), starting it if it isn't running.

KiCad runs this in the plugin's own Python environment, which has no wx, so the
panel itself is started on KiCad's bundled Python (scripting/plugins/powerlab_assistant).
This uses that package's launch.py, which needs no wx.
"""

import os
import sys

# This file lives in <KiCad documents>/10.0/plugins/<this plugin>/
VERSION_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTING = os.path.join(VERSION_DIR, "scripting", "plugins")


def kicad_python():
    """KiCad 10's own Python, which has wx (the installer records where it is)."""
    from powerlab_assistant import config

    python = config.kicad_python(gui=True)
    if config.IS_WINDOWS and python:  # the Windows one must have wx next to it
        if not os.path.isdir(os.path.join(os.path.dirname(python), "Lib", "site-packages", "wx")):
            python = ""
    if not python:
        raise SystemExit("KiCad 10's Python was not found. Run the installer again.")
    return python


if __name__ == "__main__":
    os.environ["POWERLAB_ASSISTANT_STANDALONE"] = "1"  # importing the package mustn't register the PCB button
    sys.path.insert(0, SCRIPTING)
    from powerlab_assistant import kicad_window, launch

    launch.toggle(kicad_python(), "schematic", kicad_window.kicad_ancestor(os.getpid()))
