"""Render the toolbar icons from the lab logo embedded in panel.html.

Run with KiCad's Python (it has wx):  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tools\\make_icons.py
"""
import os
import re

import wx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANEL = os.path.join(ROOT, "plugin", "powerlab_assistant")
BUTTON = os.path.join(ROOT, "plugin", "powerlab-assistant-button")

html = open(os.path.join(PANEL, "panel.html"), encoding="utf-8").read()
mark = re.search(r'<div class="brand"><svg[^>]*>(.*?)</svg>', html, re.S).group(1)

app = wx.App(False)
for suffix, ink in (("", "#111111"), ("_dark", "#f2f2f2")):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="210 404 153 152">'
           + mark.replace("currentColor", ink) + "</svg>").encode()
    for size, scale in ((24, ""), (48, "@2x")):
        bmp = wx.BitmapBundle.FromSVG(svg, wx.Size(size, size)).GetBitmap(wx.Size(size, size))
        for folder in (PANEL, BUTTON):
            bmp.SaveFile(os.path.join(folder, f"icon{suffix}{scale}.png"), wx.BITMAP_TYPE_PNG)
print("icons written")
