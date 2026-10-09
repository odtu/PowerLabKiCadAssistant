"""PCB editor side: the toolbar button (a SWIG action plugin).

It shows or hides the same standalone panel as the schematic editor's button, so both
editors share one panel and one chat.
"""

import os

import pcbnew
import wx

from . import config
from .common import INSTALL_HELP, find_claude


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
        if not find_claude():
            wx.MessageBox(INSTALL_HELP, "PowerLab Assistant", wx.OK | wx.ICON_WARNING)
            return
        python = os.path.join(config.kicad_bin(), "pythonw.exe") if config.kicad_bin() else ""
        if not os.path.isfile(python):
            wx.MessageBox("KiCad 10's Python was not found. Run install.ps1 again.",
                          "PowerLab Assistant", wx.OK | wx.ICON_WARNING)
            return
        from .launch import toggle

        toggle(python, "pcb")
