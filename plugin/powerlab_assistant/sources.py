"""Where the panel gets its KiCad context from.

KiCadSource serves both editors from the one standalone panel, talking to KiCad over its
IPC API (Preferences > Plugins > Enable KiCad API).
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
        return "KiCad isn't running. Start KiCad and open the schematic or the board, then try again."
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


EDITOR_TITLES = {"pcb": "PCB Editor", "schematic": "Schematic Editor"}
EDITOR_NAMES = {"pcb": "PCB editor", "schematic": "schematic editor"}


def schematic_files(project_dir):
    return glob.glob(os.path.join(project_dir, "*.kicad_sch")) if project_dir else []


class KiCadSource:
    """Both editors, for the one panel: the toolbar button in either shows or hides it.

    The board and its selected footprints come from KiCad's API. KiCad 10's schematic API only
    reports which schematic is open (no selection, save or revert): the schematic selection is
    read by running the editor's Edit > Copy and parsing the clipboard, which is then restored,
    and save/revert go through its menu."""

    suggestions = [
        ("Create a symbol + footprint library for…", "Create a symbol and footprint library for "),
        ("Run ERC and summarize violations", "Run ERC on this schematic and summarize the violations"),
        ("Run DRC and summarize violations", "Run DRC on this board and summarize the violations"),
        ("Check the selected parts", "Check the selected parts against their datasheets"),
        ("Autoroute the remaining nets", "Autoroute the remaining nets with Freerouting"),
        ("Export Gerbers for PCBWay", "Export Gerbers and drill files for PCBWay"),
    ]

    def __init__(self, editor="schematic"):
        self.editor = editor  # the editor the user worked in last ("pcb" or "schematic")
        self.token = None  # first connect: the token KiCad put in the launch environment
        self.down_until = 0.0
        self.connect()
        self.clip_seq = clipboard_sequence()  # ignore whatever was copied before the panel opened
        self.selected = []  # in the schematic editor

    def connect(self):
        from kipy import KiCad

        # Short timeout: these calls run on the panel's GUI thread.
        self.kicad = KiCad(client_name=f"powerlab-assistant-{os.getpid()}", kicad_token=self.token, timeout_ms=600)


    def call(self, fn):
        """Run fn(kicad). After a KiCad restart the connection and its launch token are
        stale, so reconnect once with a fresh one; while KiCad is unreachable, fail fast
        for a few seconds instead of stalling the panel on every poll. KiCad's own errors
        (e.g. an editor that isn't open) are passed on as they are."""
        from kipy.errors import ApiError

        if time.time() < self.down_until:
            raise ConnectionError("KiCad is not reachable")
        try:
            return fn(self.kicad)
        except ApiError:
            raise
        except Exception:
            self.token = ""
            self.connect()
            try:
                return fn(self.kicad)
            except ApiError:
                raise
            except Exception:
                self.down_until = time.time() + 5
                raise

    def open_document(self, doc_type):
        """(file name, project folder or "") of the open document of that type, or None.
        KiCad answers "no handler" while that editor is closed."""
        from kipy.errors import ApiError

        try:
            docs = self.call(lambda k: k.get_open_documents(doc_type))
        except ApiError:
            return None
        if not docs:
            return None
        # Despite the name, board_filename holds the .kicad_sch file name for a schematic.
        return docs[0].board_filename, docs[0].project.path

    def board_selection(self):
        """References of the footprints selected in the PCB editor."""
        from kipy.board_types import FootprintInstance
        from kipy.errors import ApiError

        try:
            items = self.call(lambda k: k.get_board().get_selection())
        except ApiError:
            return []
        return sorted(i.reference_field.text.value for i in items if isinstance(i, FootprintInstance))

    def track_editor(self):
        """The editor the user is in: the KiCad editor window that last had the focus."""
        title = kicad_window.foreground_title()
        for editor, kind in EDITOR_TITLES.items():
            if title.endswith(kind):
                self.editor = editor

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

        self.track_editor()
        board = self.open_document(DocumentType.DOCTYPE_PCB)
        sch = self.open_document(DocumentType.DOCTYPE_SCHEMATIC)
        if not board and not sch:
            return Snapshot(os.path.expanduser("~"), ["No schematic or board open"],
                            "You were launched from KiCad, but no schematic or board is open.",
                            "No schematic or board open")
        project_dir = (board or sch)[1] or (self.project_dir(sch[0]) if sch else None) or ""
        stem = os.path.splitext((board or sch)[0])[0]
        board_path = os.path.join(project_dir, board[0] if board else stem + ".kicad_pcb")
        sch_path = os.path.join(project_dir, sch[0] if sch else stem + ".kicad_sch")
        footprints = self.board_selection() if board else []
        sheet = ""
        if sch:
            self.poll_clipboard()
            hwnd = kicad_window.find_editor()
            sheet = kicad_window.current_sheet(hwnd) if hwnd else ""

        if self.editor == "pcb" and board or not sch:
            chips, selected = [board[0]], footprints
        else:
            chips, selected = [f"Sheet: {sheet.split('/')[-1]}" if sheet else sch[0]], \
                [p.split(" (")[0] for p in self.selected]
        if selected:
            chips.append("Selected: " + short_list(selected))

        context = ["You were launched from KiCad. This one panel serves both the PCB editor and "
                   "the schematic editor."]
        if project_dir:
            context.append(f"KiCad project folder: {project_dir}")
            if sch or os.path.isfile(sch_path):
                context.append(f"Root schematic: {sch_path}")
            if board or os.path.isfile(board_path):
                context.append(f"Board file: {board_path}")
        context += [
            "Use the kicad MCP tools to inspect or edit the schematic, the board and libraries. "
            "Schematic edits are written to the .kicad_sch files. Board tools edit the open board "
            "live in the PCB editor.",
            "The message state says which editor the user is working in, which editors are open, "
            "the sheet shown in the schematic editor and what is selected in each editor (the "
            "schematic selection is read via the editor's Edit > Copy).",
            library_context(),
        ]
        state = [f"The user is working in the {EDITOR_NAMES[self.editor]}."]
        if board:
            state += [f"PCB editor: board {board[0]}",
                      "Selected footprints in the PCB editor: " + (", ".join(footprints) or "none")]
        else:
            state.append("PCB editor: not open")
        if sch:
            state += [f"Schematic editor: root {sch[0]}, showing sheet {sheet or 'unknown'}",
                      "Selected in the schematic editor: " + (", ".join(self.selected) or "nothing")]
        else:
            state.append("Schematic editor: not open")
        watch = schematic_files(project_dir) + ([board_path] if project_dir and os.path.isfile(board_path) else [])
        return Snapshot(
            cwd=project_dir or os.path.expanduser("~"),
            chips=chips,
            context="\n".join(filter(None, context)),
            state="\n".join(state),
            watch=watch,
        )

    # ---- driving the schematic editor window (no API for these in KiCad 10) ----

    def schematic_open(self):
        return bool(kicad_window.find_editor())

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
