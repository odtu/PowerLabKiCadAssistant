"""The PowerLab Assistant panel, one window for both the PCB and the schematic editor.

Started by the toolbar button in either editor (see launch.py), running on KiCad's own
Python so it has wx and WebView. Only one copy runs: a second launch just toggles the panel
through a local socket, or, if the plugin code changed since this copy started, asks it to
quit so a fresh one runs.
"""

import ctypes
import os
import socket
import threading
import time

import wx

from .common import INSTALL_HELP, find_claude
from .launch import PORT, code_stamp
from .panel import ClaudePanel
from .sources import EDITOR_TITLES, KiCadSource

STAMP = code_stamp()


def listen():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for _ in range(20):  # an outdated copy may still be releasing the port
        try:
            srv.bind(("127.0.0.1", PORT))
            break
        except OSError:
            time.sleep(0.25)
    else:
        raise OSError(f"port {PORT} is busy")
    srv.listen(1)
    return srv


def serve(srv, on_toggle, on_outdated):
    def loop():
        while True:
            conn, _ = srv.accept()
            with conn:
                parts = conn.recv(64).split()
                if not parts or parts[0] != b"toggle":
                    continue
                if len(parts) > 1 and parts[1].decode() != STAMP:
                    conn.sendall(b"restart")
                    wx.CallAfter(on_outdated)
                else:
                    conn.sendall(b"ok")
                    editor = parts[2].decode() if len(parts) > 2 else ""
                    wx.CallAfter(on_toggle, editor if editor in EDITOR_TITLES else "schematic")

    threading.Thread(target=loop, daemon=True).start()


def main():
    try:  # match KiCad: per-monitor DPI aware, so window coordinates aren't rescaled
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        pass
    app = wx.App(False)
    claude = find_claude()
    if not claude:
        wx.MessageBox(INSTALL_HELP, "PowerLab Assistant", wx.OK | wx.ICON_WARNING)
        return
    try:
        editor = os.environ.get("POWERLAB_ASSISTANT_EDITOR", "")
        source = KiCadSource(editor if editor in EDITOR_TITLES else "schematic")
        srv = listen()
    except Exception as exc:
        wx.MessageBox(f"Could not start the panel:\n{exc}", "PowerLab Assistant", wx.OK | wx.ICON_WARNING)
        return

    panel = ClaudePanel(claude, source)

    def quit_panel():
        panel.save_chat()
        if panel.proc:
            panel.proc.terminate()
        srv.close()
        app.ExitMainLoop()

    def toggle(editor):
        if panel.IsShown():
            panel.Hide()
        else:
            source.editor = editor  # the button's editor, until the user clicks into the other one
            panel.present()

    # Closing the window hides it; the process lives until KiCad goes away.
    serve(srv, toggle, quit_panel)
    panel.present()

    misses = [0]

    def watchdog():
        misses[0] = 0 if source.alive() else misses[0] + 1
        if misses[0] >= 3:
            quit_panel()

    keepalive = wx.Timer()
    keepalive.Bind(wx.EVT_TIMER, lambda evt: watchdog())
    keepalive.Start(5000)
    app.MainLoop()


if __name__ == "__main__":
    main()
