"""Build demo copies of the real panel.html with scripted events, for the README screenshots.

Usage (KiCad's Python, from the repo root):
    python tools/make_readme_screenshots.py <folder with board.png>
It writes start.html, chat.html and attach.html next to board.png. Screenshot each one with
headless Edge at 400x780 (--force-dark-mode --force-device-scale-factor=2), then put the three
side by side into docs/images/panel-overview.png. board.png is a get_board_2d_view render of a
public board; never use a private design."""
import base64, json, os, sys

HERE = os.path.abspath(sys.argv[1])
PANEL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "plugin", "powerlab_assistant", "panel.html")
html = open(PANEL, encoding="utf-8").read()
board = "data:image/png;base64," + base64.b64encode(open(os.path.join(HERE, "board.png"), "rb").read()).decode()

MODELS = [{"id": "claude-opus-5-5", "label": "Opus 5.5", "short": "Opus 5.5", "hint": ""}]
SUGGESTIONS = [
    ("Create a symbol + footprint library for…", ""),
    ("Run DRC and summarize violations", ""),
    ("Check selected footprints", ""),
    ("Autoroute the remaining nets", ""),
    ("Export Gerbers for PCBWay", ""),
]

start = [
    {"kind": "models", "current": "claude-opus-5-5", "items": MODELS},
    {"kind": "suggestions", "items": [{"label": l, "text": t} for l, t in SUGGESTIONS]},
    {"kind": "context", "items": ["Voltage_Sensor_Card.kicad_pcb", "Selected: U1, C3"]},
    {"kind": "library", "configured": True, "vars_ok": True, "behind": 3, "ok": True, "changes": []},
    {"kind": "usage", "text": "5h 12% · context 0%", "tip": ""},
]

tools = [
    ("t1", "Skill", "powerlab-pcb-design-rules"),
    ("t2", "Skill", "powerlab-visual-review"),
    ("t3", "Get design rules", ""),
    ("t4", "Autoroute", "pourNets: GND"),
    ("t5", "Refill zones", ""),
    ("t6", "Run drc", ""),
    ("t7", "Get board 2d view", "03-route.png"),
]
chat = [
    {"kind": "models", "current": "claude-opus-5-5", "items": MODELS},
    {"kind": "context", "items": ["Voltage_Sensor_Card.kicad_pcb"]},
    {"kind": "user", "text": "Route the remaining signal nets and show me the result", "files": []},
] + [{"kind": "tool", "id": i, "name": n, "detail": d} for i, n, d in tools] \
  + [{"kind": "tool_done", "id": i, "error": False} for i, _, _ in tools] + [
    {"kind": "image", "src": board, "name": "03-route.png", "path": ""},
    {"kind": "text", "text": (
        "Routed all **29 nets**; GND connects through the pours. "
        "DRC: **0 errors** after refill. Use **File → Revert** to load it.")},
    {"kind": "meta", "text": "2m 41s · 21 steps · Opus 5.5 · high effort"},
    {"kind": "attachments", "items": []},
    {"kind": "usage", "text": "5h 23% · context 9%", "tip": ""},
]

attach = [
    {"kind": "models", "current": "claude-opus-5-5", "items": MODELS},
    {"kind": "context", "items": ["Voltage_Sensor_Card.kicad_pcb", "Selected: U2"]},
    {"kind": "user", "text": "Does U2's footprint match this datasheet page?", "files": ["opamp-datasheet.pdf"]},
    {"kind": "tool", "id": "a1", "name": "Read", "detail": "opamp-datasheet.pdf"},
    {"kind": "tool", "id": "a2", "name": "Get component pads", "detail": "U2"},
    {"kind": "tool_done", "id": "a1", "error": False},
    {"kind": "tool_done", "id": "a2", "error": False},
    {"kind": "text", "text": (
        "The pad layout matches the SOIC-8 drawing on page 31: 1.27 mm pitch, 5.4 mm row spacing.\n\n"
        "One difference: the datasheet recommends **1.55 mm** long pads, and the footprint has 1.5 mm. "
        "That's fine for reflow; check it if you hand-solder.")},
    {"kind": "meta", "text": "34s · 4 steps · Opus 5.5 · high effort"},
    {"kind": "attachments", "items": ["front-photo.jpg"]},
    {"kind": "usage", "text": "5h 25% · context 4%", "tip": ""},
]


def build(name, events, typed=""):
    script = ("<style>html,body{width:400px!important;height:780px!important;}</style><script>window.addEventListener('load',()=>{"
              f"for (const e of {json.dumps(events)}) app.event(e);"
              f"input.value={json.dumps(typed)}; autosize(); updateSend();"
              "document.querySelectorAll('.ti.run').forEach(t=>t.remove());"
              "log.scrollTop=0;});</script>")
    out = os.path.join(HERE, name + ".html")
    open(out, "w", encoding="utf-8").write(html.replace("</body>", script + "</body>"))
    return out


build("start", start, "")
build("chat", chat, "")
build("attach", attach, "Is the silkscreen readable in this photo?")
print("built")
