"""PCB editor side: the toolbar button (a SWIG action plugin) and board context."""

import os

import pcbnew
import wx

from .common import INSTALL_HELP, find_claude


def board_state():
    """Return (board_path, selected footprint refs). Call on the GUI thread."""
    if not wx.FindWindowByName("PcbFrame"):
        return "", []  # PCB editor closed: GetBoard() would point at a freed board
    board = pcbnew.GetBoard()
    if not board:
        return "", []
    selected = sorted(fp.GetReference() for fp in board.GetFootprints() if fp.IsSelected())
    return board.GetFileName(), selected


def build_context(board_path, selected_refs):
    lines = ["You were launched from KiCad's PCB editor."]
    if board_path:
        project_dir = os.path.dirname(board_path)
        stem = os.path.splitext(os.path.basename(board_path))[0]
        lines += [f"KiCad project folder: {project_dir}", f"Board file: {board_path}"]
        for ext, label in ((".kicad_sch", "Root schematic"), (".kicad_pro", "Project file")):
            path = os.path.join(project_dir, stem + ext)
            if os.path.isfile(path):
                lines.append(f"{label}: {path}")
    if selected_refs:
        lines.append("Footprints currently selected in the PCB editor: " + ", ".join(selected_refs))
    lines += [
        "kicad-cli is on PATH: run it by name (`kicad-cli pcb render ...`), never via `&` or its "
        "full path, one command per call; write outputs inside the project folder.",
        "KiCad has this board open: the user must save in KiCad before you read it, and after "
        "you modify the board file, tell them to use File > Revert in KiCad to load your changes.",
    ]
    return "\n".join(lines)


class AssistantButton(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "PowerLab Assistant"
        self.category = "AI"
        self.description = "Show or hide the PowerLab Assistant panel (uses Claude Code)"
        self.show_toolbar_button = True
        here = os.path.dirname(__file__)
        self.icon_file_name = os.path.join(here, "icon.png")
        self.dark_icon_file_name = os.path.join(here, "icon_dark.png")

    def Run(self):
        claude = find_claude()
        if not claude:
            wx.MessageBox(INSTALL_HELP, "PowerLab Assistant", wx.OK | wx.ICON_WARNING)
            return
        from .panel import ClaudePanel

        ClaudePanel.toggle(claude)
