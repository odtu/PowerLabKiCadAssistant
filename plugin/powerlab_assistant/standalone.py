"""Standalone PowerLab Assistant panel for the schematic editor.

Started by the toolbar button in the schematic editor (an IPC API
plugin), running on KiCad's own Python so it has wx and WebView. Only one copy
runs: a second launch just toggles the panel through a local socket, or, if the
plugin code changed since this copy started, asks it to quit so a fresh one runs.
"""

import ctypes
import os
import socket
import threading
import time

import wx

from .common import INSTALL_HELP, find_claude
from .panel import ClaudePanel
from .sources import SchematicSource

PORT = 47615  # localhost only; also used by the launcher in the IPC plugin


def code_stamp():
    """Newest modification time of the panel's code; the launcher computes the same."""
    folder = os.path.dirname(os.path.abspath(__file__))
    return str(int(max(os.path.getmtime(os.path.join(folder, f))
                       for f in os.listdir(folder) if f.endswith((".py", ".html")))))


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
                    wx.CallAfter(on_toggle)

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
        source = SchematicSource()
        srv = listen()
    except Exception as exc:
        wx.MessageBox(f"Could not start the panel:\n{exc}", "PowerLab Assistant", wx.OK | wx.ICON_WARNING)
        return

    panel = ClaudePanel(None, claude, source)

    def quit_panel():
        panel.save_chat()
        if panel.proc:
            panel.proc.terminate()
        srv.close()
        app.ExitMainLoop()

    def toggle():
        if panel.IsShown():
            panel.Hide()
        else:
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
