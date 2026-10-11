"""Show, hide or start the PowerLab Assistant panel of the KiCad the button was pressed in.

Both editors' toolbar buttons use the same panel, a standalone window on KiCad's own Python
(standalone.py); each KiCad that is open gets its own. Only one copy of the panel program
runs: a click just toggles that KiCad's panel through a local socket, or, if the plugin code
changed since that copy started, asks it to quit so a fresh one runs. The schematic editor's
button (an IPC plugin, plugins/powerlab-assistant/launcher.py) imports this module too.
"""

import os
import socket
import subprocess
import time

from . import instances

PORT = 47615  # localhost only
PACKAGE = os.path.dirname(os.path.abspath(__file__))


def code_stamp():
    """Newest modification time of the panel's code; tells an outdated panel to quit."""
    return str(int(max(os.path.getmtime(os.path.join(PACKAGE, f))
                       for f in os.listdir(PACKAGE) if f.endswith((".py", ".html")))))


def toggle_running_panel(editor, kicad_pid):
    """True if a current panel handled the click; False if one must be started."""
    try:
        with socket.create_connection(("127.0.0.1", PORT), timeout=0.5) as conn:
            conn.sendall(f"toggle {code_stamp()} {editor} {kicad_pid}".encode())
            conn.settimeout(2)
            reply = conn.recv(16)
    except OSError:
        return False
    if reply == b"restart":  # the running panel is older than the code; it is quitting
        time.sleep(1)
        return False
    return True


def start_panel(python, editor, kicad_pid):
    env = dict(os.environ)  # keeps KICAD_API_SOCKET / KICAD_API_TOKEN when KiCad set them
    for var in ("PYTHONHOME", "PYTHONPATH"):
        env.pop(var, None)
    env["POWERLAB_ASSISTANT_STANDALONE"] = "1"
    env["POWERLAB_ASSISTANT_EDITOR"] = editor
    env["POWERLAB_ASSISTANT_KICAD"] = str(kicad_pid)
    # KiCad's Python ignores PYTHONPATH, so put the package on the path in code.
    bootstrap = (f"import sys; sys.path.insert(0, {os.path.dirname(PACKAGE)!r}); "
                 "from powerlab_assistant.standalone import main; main()")
    subprocess.Popen([python, "-c", bootstrap], env=env, cwd=os.path.expanduser("~"),
                     creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)


def toggle(python, editor, kicad_pid):
    """kicad_pid: process id of the KiCad the button is in (0 if unknown)."""
    instances.ensure_placeholder()  # before the user starts another KiCad
    if not toggle_running_panel(editor, kicad_pid):
        start_panel(python, editor, kicad_pid)
