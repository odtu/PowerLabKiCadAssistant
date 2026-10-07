"""Where the panel gets its KiCad context from.

PcbSource runs inside the PCB editor and reads the board through pcbnew.
SchematicSource runs in the standalone panel and talks to KiCad over its IPC API
(Preferences > Plugins > Enable KiCad API).
"""

import ctypes
import glob
import json
import os
import re
import time
from dataclasses import dataclass, field

from .library import library_context

if os.name == "nt":
    from . import kicad_window
else:  # the panel only runs on Windows; this keeps the module importable for tests on Linux CI
    kicad_window = None
from .pcb import board_state, build_context


@dataclass
class Snapshot:
    cwd: str
    chips: list
    context: str  # static facts, sent as an appended system prompt
    state: str  # live selection, attached to each message
    watch: list = field(default_factory=list)  # files whose on-disk changes need a reload


def unreachable_hint(processes):
    """Why KiCad's API may not answer, from [(pid, has_visible_window)] of kicad.exe (issue #7).

    A KiCad that got stuck while closing keeps running without a window and holds KiCad's
    API connection, so the KiCad the user is working in can't open its own."""
    stale = [pid for pid, visible in processes if not visible]
    if len(processes) > 1 and stale:
        return (f"KiCad isn't answering because another KiCad is still running in the background "
                f"without a window (process {', '.join(map(str, stale))}) and is holding KiCad's "
                "connection. End it in Task Manager > Details > kicad.exe (that process ID), "
                "then restart KiCad.")
    if not processes:
        return "KiCad isn't running. Start KiCad and open the schematic, then try again."
    return ("Can't reach KiCad. Turn on Preferences > Plugins > Enable KiCad API, then restart "
            "KiCad and reopen the panel.")


def unreachable_chip(processes):
    """The same diagnosis as unreachable_hint, short enough for the status chip."""
    stale = [pid for pid, visible in processes if not visible]
    if len(processes) > 1 and stale:
        return f"Not connected: a stuck background KiCad (process {stale[0]}) is blocking it"
    if not processes:
        return "Not connected: KiCad isn't running"
    return "Not connected to KiCad (is its API server on?)"


def short_list(names, limit=6):
    return ", ".join(names[:limit]) + (f" +{len(names) - limit}" if len(names) > limit else "")


class PcbSource:
    editor = "pcb"
    suggestions = [
        ("Create a symbol + footprint library for…", "Create a symbol and footprint library for "),
        ("Run DRC and summarize violations", "Run DRC on this board and summarize the violations"),
        ("Check selected footprints", "Check the selected footprints against their datasheets"),
        ("Autoroute the remaining nets", "Autoroute the remaining nets with Freerouting"),
        ("Export Gerbers for PCBWay", "Export Gerbers and drill files for PCBWay"),
    ]
    can_reload = False
    changed_note = ("Board changed on disk. Use File → Revert in KiCad to load it "
                    "(unsaved KiCad edits will be lost).")

    def snapshot(self):
        board_path, selected = board_state()
        chips = [os.path.basename(board_path)] if board_path else ["No board saved yet"]
        if selected:
            chips.append("Selected: " + short_list(selected))
        state = "Selected footprints: " + (", ".join(selected) if selected else "none")
        if board_path:
            state = f"Open board: {board_path}\n" + state
        return Snapshot(
            cwd=os.path.dirname(board_path) if board_path else os.path.expanduser("~"),
            chips=chips,
            context="\n".join(filter(None, [build_context(board_path, selected), library_context()])),
            state=state,
            watch=[board_path] if board_path else [],
        )

    def kicad_version(self):
        import pcbnew

        return pcbnew.GetBuildVersion()


def clipboard_sequence():
    return ctypes.windll.user32.GetClipboardSequenceNumber()


def read_clipboard_text():
    import wx

    if not wx.TheClipboard.Open():
        return ""
    try:
        data = wx.TextDataObject()
        return data.GetText() if wx.TheClipboard.GetData(data) else ""
    finally:
        wx.TheClipboard.Close()


def parse_selection(text):
    """Symbols and labels in a KiCad schematic clipboard copy (power symbols skipped)."""
    parts = []
    for block in re.split(r"\n\s*\(symbol\s*\n?\s*\(lib_id", text)[1:]:
        ref = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
        value = re.search(r'\(property\s+"Value"\s+"([^"]+)"', block)
        if ref and not ref.group(1).startswith("#"):
            parts.append(f"{ref.group(1)} ({value.group(1)})" if value else ref.group(1))
    labels = re.findall(r'\((?:label|global_label|hierarchical_label)\s+"([^"]+)"', text)
    sheets = re.findall(r'\(property\s+"Sheetname"\s+"([^"]+)"', text)
    return parts + [f"label {l}" for l in labels] + [f"sheet {s}" for s in sheets]


def is_kicad_schematic(text):
    return "(lib_id" in text or "(label" in text or "(wire" in text or "(kicad_sch" in text


class SchematicSource:
    """KiCad 10's schematic API only reports which schematic is open (no selection,
    save or revert). The selection is read by running the editor's Edit > Copy and
    parsing the clipboard, which is then restored; save/revert go through its menu."""

    editor = "schematic"
    suggestions = [
        ("Create a symbol + footprint library for…", "Create a symbol and footprint library for "),
        ("Run ERC and summarize violations", "Run ERC on this schematic and summarize the violations"),
        ("Check the selected parts", "Check the selected parts against their datasheets"),
        ("Export the schematic as PDF", "Export the schematic as a PDF"),
    ]
    can_reload = True
    changed_note = ("Claude changed the schematic, but you have unsaved edits in KiCad, so it "
                    "wasn't reloaded automatically. Reloading drops those edits.")

    def __init__(self):
        self.token = None  # first connect: the token KiCad put in the launch environment
        self.down_until = 0.0
        self.connect()
        self.clip_seq = clipboard_sequence()  # ignore whatever was copied before the panel opened
        self.selected = []

    def connect(self):
        from kipy import KiCad

        # Short timeout: these calls run on the panel's GUI thread.
        self.kicad = KiCad(client_name=f"powerlab-assistant-{os.getpid()}", kicad_token=self.token, timeout_ms=600)

    def call(self, fn):
        """Run fn(kicad). After a KiCad restart the connection and its launch token are
        stale, so reconnect once with a fresh one; while KiCad is unreachable, fail fast
        for a few seconds instead of stalling the panel on every poll."""
        if time.time() < self.down_until:
            raise ConnectionError("KiCad is not reachable")
        try:
            return fn(self.kicad)
        except Exception:
            self.token = ""
            self.connect()
            try:
                return fn(self.kicad)
            except Exception:
                self.down_until = time.time() + 5
                raise

    def project_dir(self, sch_name):
        """The API doesn't say where the schematic lives; KiCad's recent-projects list does."""
        try:
            with open(os.path.join(os.environ["APPDATA"], "kicad", "10.0", "kicad.json"), encoding="utf-8") as f:
                history = json.load(f).get("system", {}).get("file_history", [])
        except (OSError, ValueError, KeyError):
            return None
        for pro in history:
            folder = os.path.dirname(pro)
            if os.path.isfile(os.path.join(folder, sch_name)):
                return folder
        return None

    def poll_clipboard(self):
        """A manual Ctrl+C in the schematic also counts as pointing at parts."""
        seq = clipboard_sequence()
        if seq == self.clip_seq:
            return
        self.clip_seq = seq
        text = read_clipboard_text()
        if is_kicad_schematic(text):
            self.selected = parse_selection(text)

    def capture_selection(self, owner, done):
        """Read the editor's current selection: Edit > Copy, parse the clipboard, then put
        the user's clipboard back. `owner` is a window of this process; calls done()."""
        import wx

        hwnd = kicad_window.find_editor()
        if not hwnd:
            done()
            return
        saved = kicad_window.save_clipboard()
        before = clipboard_sequence()
        if not kicad_window.menu_command(hwnd, "Edit", "Copy"):
            done()
            return
        deadline = time.time() + 1.0

        def check():
            if clipboard_sequence() != before:
                text = read_clipboard_text()
                self.selected = parse_selection(text) if is_kicad_schematic(text) else []
                kicad_window.restore_clipboard(saved, owner)
                self.clip_seq = clipboard_sequence()  # our restore isn't a user copy
                done()
            elif time.time() < deadline:
                wx.CallLater(40, check)
            else:
                self.selected = []  # nothing selected: Copy left the clipboard alone
                done()

        wx.CallLater(40, check)

    def snapshot(self):
        from kipy.proto.common.types.base_types_pb2 import DocumentType

        docs = self.call(lambda k: k.get_open_documents(DocumentType.DOCTYPE_SCHEMATIC))
        if not docs:
            return Snapshot(os.path.expanduser("~"), ["No schematic open"],
                            "You were launched from KiCad, but no schematic is open.", "No schematic open")
        sch_name = docs[0].board_filename  # despite the name, this holds the .kicad_sch file name
        project_dir = self.project_dir(sch_name)
        self.poll_clipboard()
        editor = kicad_window.find_editor()
        sheet = kicad_window.current_sheet(editor) if editor else ""

        chips = [f"Sheet: {sheet.split('/')[-1]}" if sheet else sch_name]
        if self.selected:
            chips.append("Selected: " + short_list([p.split(" (")[0] for p in self.selected]))
        context = [
            "You were launched from KiCad's schematic editor.",
            f"Root schematic: {os.path.join(project_dir, sch_name) if project_dir else sch_name}",
            "Use the kicad MCP tools to inspect or edit the schematic and libraries. Schematic "
            "edits are written to the .kicad_sch files. The panel makes sure the schematic is "
            "saved before each message and reloads it in KiCad after you change a sheet, so "
            "don't tell the user to save or revert.",
            "The message state lists the sheet shown in the schematic editor and the items "
            "selected there when the message was sent (read via the editor's Edit > Copy).",
        ]
        if project_dir:
            context.insert(1, f"KiCad project folder: {project_dir}")
        context.append(library_context())
        selected = ", ".join(self.selected) if self.selected else "nothing"
        return Snapshot(
            cwd=project_dir or os.path.expanduser("~"),
            chips=chips,
            context="\n".join(filter(None, context)),
            state=(f"Schematic editor: root {sch_name}, showing sheet {sheet or 'unknown'}\n"
                   f"Selected in the schematic editor: {selected}"),
            watch=glob.glob(os.path.join(project_dir, "*.kicad_sch")) if project_dir else [],
        )

    # ---- driving the editor window (no API for these in KiCad 10) ----------

    def unsaved(self):
        hwnd = kicad_window.find_editor()
        return bool(hwnd and kicad_window.is_dirty(hwnd))

    def save(self):
        hwnd = kicad_window.find_editor()
        return bool(hwnd and kicad_window.menu_command(hwnd, "File", "Save"))

    def reload(self, done):
        """File > Revert in the editor, then confirm KiCad's dialog. Calls done(ok)."""
        import wx

        hwnd = kicad_window.find_editor()
        if not hwnd or not kicad_window.menu_command(hwnd, "File", "Revert"):
            done(False)
            return
        pid, tries = kicad_window.window_pid(hwnd), [0]

        def confirm():
            if kicad_window.click_dialog_button(pid, {"Revert"}):
                done(True)
            elif tries[0] < 30:
                tries[0] += 1
                wx.CallLater(100, confirm)
            else:
                done(False)

        wx.CallLater(150, confirm)

    def kicad_version(self):
        try:
            return str(self.call(lambda k: k.get_version()))
        except Exception:
            return ""

    def unreachable_reason(self):
        return unreachable_hint(kicad_window.kicad_processes())

    def unreachable_status(self):
        return unreachable_chip(kicad_window.kicad_processes())

    def process_summary(self):
        """For problem reports: how many kicad.exe run, and how many have no window."""
        procs = kicad_window.kicad_processes()
        return f"{len(procs)} running, {sum(1 for _, visible in procs if not visible)} without a window"

    def alive(self):
        try:
            self.call(lambda k: k.ping())
            return True
        except Exception:
            return False
