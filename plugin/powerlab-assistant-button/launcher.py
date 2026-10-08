"""Schematic editor toolbar action: show/hide the PowerLab Assistant panel (the same one
the PCB editor's button uses), starting it if it isn't running.

KiCad runs this in the plugin's own Python environment, which has no wx, so the
panel itself is started on KiCad's bundled Python (scripting/plugins/powerlab_assistant).
"""

import json
import os
import socket
import subprocess
import sys
import time

PORT = 47615  # this file is a copy of powerlab_assistant/launch.py for the schematic editor
# This file lives in <KiCad documents>/10.0/plugins/<this plugin>/
VERSION_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTING = os.path.join(VERSION_DIR, "scripting", "plugins")
PACKAGE = os.path.join(SCRIPTING, "powerlab_assistant")
CONFIG = os.path.join(os.environ.get("APPDATA", ""), "PowerLabKiCadAssistant", "config.json")


def code_stamp():
    """Same as powerlab_assistant/launch.py: lets an outdated panel know to quit."""
    return str(int(max(os.path.getmtime(os.path.join(PACKAGE, f))
                       for f in os.listdir(PACKAGE) if f.endswith((".py", ".html")))))


def toggle_running_panel():
    """True if a current panel handled the click; False if one must be started."""
    try:
        with socket.create_connection(("127.0.0.1", PORT), timeout=0.5) as conn:
            conn.sendall(f"toggle {code_stamp()} schematic".encode())
            conn.settimeout(2)
            reply = conn.recv(16)
    except OSError:
        return False
    if reply == b"restart":  # the running panel is older than the code; it is quitting
        time.sleep(1)
        return False
    return True


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


def start_panel():
    exe = kicad_python()
    env = dict(os.environ)  # keeps KICAD_API_SOCKET / KICAD_API_TOKEN from KiCad
    env.pop("PYTHONHOME", None)
    env["POWERLAB_ASSISTANT_STANDALONE"] = "1"
    env["POWERLAB_ASSISTANT_EDITOR"] = "schematic"
    # KiCad's Python ignores PYTHONPATH, so put the package on the path in code.
    bootstrap = (f"import sys; sys.path.insert(0, {SCRIPTING!r}); "
                 "from powerlab_assistant.standalone import main; main()")
    subprocess.Popen(
        [exe, "-c", bootstrap],
        env=env, cwd=os.path.expanduser("~"),
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
    )


if __name__ == "__main__":
    if not toggle_running_panel():
        start_panel()
