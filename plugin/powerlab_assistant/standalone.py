"""The PowerLab Assistant panels: one window per KiCad, for both its PCB and schematic editor.

Started by the toolbar button in either editor (see launch.py), running on KiCad's own
Python so it has wx and WebView. Only one copy runs: a second launch just toggles the panel
of the KiCad it came from (opening one for a KiCad that has none) through a local socket,
or, if the plugin code changed since this copy started, asks it to quit so a fresh one runs.
"""

import ctypes
import os
import socket
import threading
import time

import wx

from . import instances, kicad_window
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
                    pid = parts[3].decode() if len(parts) > 3 else ""
                    wx.CallAfter(on_toggle, editor if editor in EDITOR_TITLES else "schematic",
                                 int(pid) if pid.isdigit() else 0)

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
    instances.ensure_placeholder()
    panels = {}  # KiCad process id -> its panel

    def open_panel(editor, pid):
        try:
            panel = ClaudePanel(claude, KiCadSource(editor, pid))
        except Exception as exc:
            wx.MessageBox(f"Could not start the panel:\n{exc}", "PowerLab Assistant", wx.OK | wx.ICON_WARNING)
            return False
        panels[pid] = panel
        panel.present()
        return True

    def close_panel(pid):
        panel = panels.pop(pid)
        panel.save_chat()
        if panel.proc:
            panel.proc.terminate()
        panel.Destroy()
        if not panels:
            quit_panel()

    def quit_panel():
        for panel in panels.values():
            panel.save_chat()
            if panel.proc:
                panel.proc.terminate()
        srv.close()
        app.ExitMainLoop()

    def toggle(editor, pid):
        panel = panels.get(pid)
        if not panel:
            open_panel(editor, pid)
        elif panel.IsShown():
            panel.Hide()
        else:
            panel.source.editor = editor  # the button's editor, until the user clicks into the other one
            panel.present()

    try:
        srv = listen()
    except Exception as exc:
        wx.MessageBox(f"Could not start the panel:\n{exc}", "PowerLab Assistant", wx.OK | wx.ICON_WARNING)
        return
    editor = os.environ.get("POWERLAB_ASSISTANT_EDITOR", "")
    pid = os.environ.get("POWERLAB_ASSISTANT_KICAD", "")
    if not open_panel(editor if editor in EDITOR_TITLES else "schematic", int(pid) if pid.isdigit() else 0):
        srv.close()
        return

    # Closing a window hides it; a panel lives until its KiCad goes away, the process
    # until the last one does.
    serve(srv, toggle, quit_panel)

    misses = {}

    def watchdog():
        for pid, panel in list(panels.items()):
            # A known KiCad is gone when its process is; otherwise when it stops answering.
            alive = kicad_window.process_running(pid) if pid else panel.source.alive()
            misses[pid] = 0 if alive else misses.get(pid, 0) + 1
            if misses[pid] >= (1 if pid else 3):
                del misses[pid]
                close_panel(pid)

    keepalive = wx.Timer()
    keepalive.Bind(wx.EVT_TIMER, lambda evt: watchdog())
    keepalive.Start(5000)
    app.MainLoop()


if __name__ == "__main__":
    main()
