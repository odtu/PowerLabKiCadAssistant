"""The Start menu and desktop shortcut "PowerLab Assistant": show the panel of the KiCad in
use, from any of its windows.

KiCad 10 has room for plugin buttons only in the schematic and PCB editors, so with just
the project manager, the symbol editor or the footprint editor open there was no way to
open the panel. The shortcut runs this file on KiCad's own pythonw.exe; it picks the KiCad
whose window is frontmost (Windows lists windows front to back) and shows its panel
like the toolbar buttons do (launch.py), but never hides it: from the Start menu the panel
may just be behind other windows.
"""

import os
import sys

os.environ["POWERLAB_ASSISTANT_STANDALONE"] = "1"  # importing the package mustn't register the PCB button
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TITLE = "PowerLab Assistant"
NO_KICAD = "No KiCad window is open. Start KiCad 10 first, then click PowerLab Assistant again."


def pick_kicad(windows, title_of, pid_of, exe_of, editor_titles):
    """(pid, editor) of the KiCad owning the frontmost of `windows` (front to back) that has
    a title, editor from that title ("schematic" when it's no editor's); (0, "") if none."""
    for window in windows:
        title, pid = title_of(window), pid_of(window)
        if not title or exe_of(pid) is None:
            continue
        for editor, kind in editor_titles.items():
            if title.endswith(kind):
                return pid, editor
        return pid, "schematic"
    return 0, ""


def message(text):
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, text, TITLE, 0x30)  # MB_ICONWARNING
    else:
        print(text, file=sys.stderr)


def main():
    from powerlab_assistant import config, kicad_window, launch
    from powerlab_assistant.sources import EDITOR_TITLES

    procs = kicad_window.processes()
    kicad = lambda pid: procs[pid] if pid in procs and procs[pid][1].lower() in kicad_window.KICAD_EXES else None
    pid, editor = pick_kicad(kicad_window.top_windows(), kicad_window.window_text,
                             kicad_window.window_pid, kicad, EDITOR_TITLES)
    if not pid:
        message(NO_KICAD)
        return
    python = config.kicad_python(gui=True) or sys.executable
    if sys.platform == "win32":  # this process was just started by a click: let the panel come forward
        import ctypes

        ctypes.windll.user32.AllowSetForegroundWindow(-1)  # ASFW_ANY
    launch.toggle(python, editor, pid, show=True)


if __name__ == "__main__":
    main()
