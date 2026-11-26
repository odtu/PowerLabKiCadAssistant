"""The powerlab-pcb-design-rules skill, made from the lab's PCB_DESIGN_RULES.md (#119).

    python tools/split_design_rules.py           # write the skill from tools/lab_rules/
    python tools/split_design_rules.py --fetch   # download the lab's latest file first
    python tools/split_design_rules.py --check   # exit 1 if the skill isn't what it gives

The lab's file (odtu/Powerlab, KiCAD/PCB_DESIGN_RULES.md) stays one document; its copy is
tools/lab_rules/PCB_DESIGN_RULES.md. This script applies the panel's edits (EDITS: no lab
branding on other people's boards, the "Designed with" silkscreen text, the §4 handbook
pointer) and splits the result at its "## N." sections, so a session reads only the part
its task needs:

    SKILL.md        the intro, "How to apply", an index of the files below, §4 (handbook)
    schematic.md    §1
    fab-and-drc.md  §2
    layout.md       §3

The § numbers stay the lab's. Joining the parts (`join`) gives the edited file back; the
tests check that against the copy in tools/lab_rules/. Change the rules in the lab's file
(a PR to odtu/Powerlab) or, for panel-only wording, in EDITS here: never in the parts.
"""

import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "tools", "lab_rules", "PCB_DESIGN_RULES.md")
SOURCE_URL = "https://raw.githubusercontent.com/odtu/Powerlab/master/KiCAD/PCB_DESIGN_RULES.md"
SKILL = os.path.join(ROOT, "skills", "powerlab-pcb-design-rules")

BOM = "﻿"
SEP = "\n---\n\n"  # between the "## N." sections
PARTS = (("1", "schematic.md"), ("2", "fab-and-drc.md"), ("3", "layout.md"))
INDEX_HEADING = "## Which file to read"

HANDBOOK = """## 4. Layout review handbook

The `handbook/` folder next to this file holds 233 layout rules, collected from manufacturer application notes, fab capability pages and expert reviews of real boards posted online (EEVblog, KiCad forum and others), with sources. Each rule has an ID such as `SMPS-014`, a severity (Critical > High > Medium > Low > Cosmetic), how it looks on the board, why it matters, the fix, exceptions and sources.

Use it when you place, route or review a board:
- **Quick scan:** `handbook/91-checklist.md` lists every rule on one line, sorted by severity, with its file.
- **Full rule:** open the topic file and read the rule's *How it looks in the image* and *Exceptions*. If an exception applies, it isn't a finding.

| File | Prefix | Topic |
|---|---|---|
| `01-stackup.md` | STK | 2/4-layer stackup, reference planes |
| `02-placement.md` | PLC | Functional blocks, connectors, heat sources |
| `03-power-distribution.md` | PWR | Track width for current, regulators, decoupling |
| `04-grounding.md` | GND | GND plane, splits, stitching vias, return paths |
| `05-high-speed-signals.md` | HS | USB, differential pairs, impedance, length matching |
| `06-rf-antenna.md` | RF | Antenna keepout, module placement, RF feed |
| `07-crystal-oscillator.md` | XTL | Crystals and oscillators |
| `08-switching-power.md` | SMPS | Hot loops, inductors, feedback, gate drive |
| `09-esd-protection.md` | ESD | TVS placement and protection path |
| `10-thermal.md` | THM | Thermal vias, copper area, exposed pads |
| `11-vias.md` | VIA | Via-in-pad, tenting, size, current |
| `12-dfm.md` | DFM | Fab limits, edge clearance, acid traps, slivers |
| `13-dfa.md` | DFA | Footprints, spacing, tombstoning, polarity, fiducials |
| `14-silkscreen.md` | SLK | Labels, revision, readability |
| `15-mechanical.md` | MEC | Mounting holes, connector access, panels |
| `16-testability.md` | TST | Test points, programming and debug access |
| `17-aesthetics.md` | EST | Order, alignment, symmetry, track flow |
| `90-visual-audit-guide.md` | GOR | Reading board images: colours, scale, analysis order, report format |
| `92-glossary.md` | | Terms |
| `SOURCES.md`, `DECISIONS.md` | | Every source; choices made while writing the handbook |

The handbook was written for reviewers who only see a screenshot, so many rules say "ask the user" or "estimate from the image". Here you have the board itself: measure distances, widths and via counts with the kicad tools instead of estimating, and ask only for what the board can't tell you (currents, enclosure, fab, stackup choices).

Cite rules by ID in reviews, e.g. "C5 is 4 mm from U2's VDD pin (PWR-006)". Report each problem once, under its primary rule: when a rule's Exceptions say "Primary rule for this finding: X", use X. The severity is the rule's; express doubt with the confidence (Certain / Likely / Needs verification), not by lowering the severity.
"""

# (what the edit is for, the lab's text, the panel's). Each lab text must occur exactly once.
EDITS = (
    ("skill name and description",
     "name: pcb-design-rules\n"
     "description: METU PowerLab PCB design rules for KiCad work — PCBWay standard-price "
     "(no-surcharge) spec, fab limits and lab default DRC values, schematic rules, and common "
     "PCB layout rules. Use",
     "name: powerlab-pcb-design-rules\n"
     "description: METU PowerLab PCB design rules for KiCad work — PCBWay standard-price "
     "(no-surcharge) spec, fab limits and lab default DRC values, schematic rules, common PCB "
     "layout rules, and a 233-rule layout review handbook (stackup, placement, power, "
     "grounding, high-speed, RF, crystals, switching power, ESD, thermal, vias, DFM, DFA, "
     "silkscreen, mechanical, testability, aesthetics). Use"),
    ("Source line",
     "# PCB Design Rules — METU PowerLab\n\n",
     "# PCB Design Rules — METU PowerLab\n\n"
     "Source: https://github.com/odtu/Powerlab/blob/master/KiCAD/PCB_DESIGN_RULES.md, minus "
     "the lab's drawing sheet, logo, website and QR code: other people's boards don't carry "
     "the lab's branding.\n\n"),
    ("lab rules before the handbook",
     "before setting constraints.\n",
     "before setting constraints.\n"
     "- The lab rules in §1–§3 come first. The review handbook (§4) adds detail where they say "
     "nothing; where the two give different numbers, use the lab's.\n"),
    ("§1.1: no lab drawing sheet",
     "- Every sheet uses the **METU PowerLab drawing sheet**. It carries the lab logo in the "
     "title block.\n"
     "  - Template source: https://github.com/odtu/Powerlab/tree/master/KiCAD "
     "(`METUPowerLab_KiCadSchematicTemplate.kicad_wks`). Take the latest from there; the copy "
     "in this skill's `assets/` folder is an offline fallback.\n"
     "  - Copy it into the project folder and set it with a relative path (Page Settings → "
     "Drawing sheet), so it travels with the project.\n"
     "- The title block uses the text variables `${DESIGNER}`, `${PROJECTNUMBER}` and "
     "`${PROJECT_NAME}`. Define them in Schematic Setup → Project → Text Variables, or the "
     "title block prints the raw `${...}`. Fill in Title, Revision and Date on every sheet.\n",
     "- Keep the drawing sheet the user or project already uses. Don't replace it.\n"
     "- Fill in Title, Revision and Date on every sheet. If the title block uses text "
     "variables (`${...}`), define them in Schematic Setup → Project → Text Variables so they "
     "don't print raw.\n"),
    ("§1.9: no lab drawing sheet",
     "- [ ] A4 + PowerLab drawing sheet on every sheet;",
     "- [ ] A4 on every sheet;"),
    ("§2.6: signal tracks on 2 oz",
     "Signal tracks are 0.15 mm (the Default class); give a signal more",
     "Signal tracks are 0.15 mm (the Default class) on 1 oz; on 2 oz they are 0.2 mm, with the "
     "0.18 mm outer-layer floor kept for neck-downs at fine-pitch pins. Give a signal more"),
    ("§2.6: the kicad MCP sets Board Setup",
     "Put these values in **Board Setup** itself (File → Board Setup → Design Rules → "
     "Constraints and Net Classes), not only in a `.kicad_dru` rule, and check them there "
     "before routing. With the kicad MCP, `set_design_rules` with `preset: \"powerlab\"` sets "
     "them, `create_netclass` the Power and GND classes, and `get_design_rules` shows what the "
     "board holds.",
     "Put these values in **Board Setup** itself (Constraints and Net Classes), not only in a "
     "`.kicad_dru` rule: `set_design_rules` with `preset: \"powerlab\"` sets them, and "
     "`create_netclass` the Power and GND classes. Check them with `get_design_rules` before "
     "routing."),
    ("§3.4: check_routing",
     "- After routing, check the tracks for these (angles, corners, kinks, detours, pad "
     "entries, solid GND pads) and fix them before DRC and the review: DRC passes them. With "
     "the kicad MCP, `check_routing` lists them.",
     "- After routing, run `check_routing` (angles, corners, kinks, detours, pad entries, "
     "solid GND pads) and fix what it lists before DRC and the review."),
    ("§3.6: the panel's text instead of the lab's logo and website",
     "  - organization logos (METU PowerLab)\n"
     "  - website: `power.eee.odtu.edu.tr` / `github.com/odtu`, or a QR code\n",
     "  - the text `Designed with PowerLab KiCad Assistant and Claude`, at least 1.0 mm high, "
     "next to the board info\n"),
    ("§3.6: no lab QR code",
     "  - Make the logo and QR code into footprints with KiCad's Image Converter. The lab QR "
     "code image is `PowerLabQrCode.png` at https://github.com/odtu/Powerlab/tree/master/KiCAD. "
     "Make the QR code at least ~12 mm wide and check that it scans in the 3D viewer render.",
     "  - An organization logo, website or QR code only if the user asks for their own. Make "
     "it into a footprint with KiCad's Image Converter, and check that a QR code scans in the "
     "3D viewer render."),
    ("§3.7: the panel's text",
     "- [ ] Silkscreen clean; board info, logo and website/QR present",
     "- [ ] Silkscreen clean; board info and the \"Designed with PowerLab KiCad Assistant and "
     "Claude\" text present"),
)

TASKS = """The rules are split into files in this skill's folder, next to this file. Read the ones the task needs, and only those:

| Task | Read |
|---|---|
| Schematic: sheets, parts, wiring, net names, net classes and their colours, layout notes, ERC | `schematic.md` (§1) |
| Board setup: copper weight, layers, standard-price spec, fab limits, Board Setup constraints and net classes, DRC | `fab-and-drc.md` (§2) |
| Layout: outline, placement, pours, routing, vias, silkscreen, outputs | `layout.md` (§3), and `fab-and-drc.md` too when the task also sets up the board (net classes, DRC values, track and via sizes) |
| Design review, "is it ready to order?" | all three, and the handbook (§4 below) |

Other skills cite these rules by number (e.g. §3.3 pours, §3.4 routing, §3.5 vias); the number's first digit names the file.
"""


def edit(lab):
    """The lab's file with the panel's edits and the §4 handbook pointer."""
    text = lab.replace("\r\n", "\n")
    for why, old, new in EDITS:
        n = text.count(old)
        if n != 1:
            raise ValueError(f"edit '{why}': the lab's text occurs {n} times, not once; "
                             "update EDITS in tools/split_design_rules.py")
        text = text.replace(old, new)
    return text.rstrip("\n") + "\n" + SEP + HANDBOOK


def sections(text):
    """[head, §1, §2, §3, §4]: the edited file cut at its "## N." headings."""
    pieces = re.split(r"\n---\n\n(?=## \d+\. )", text)
    numbers = [re.match(r"## (\d+)\. ", p).group(1) for p in pieces[1:]]
    if numbers != ["1", "2", "3", "4"]:
        raise ValueError(f"expected sections 1-4 after '---' lines, found {numbers}")
    return pieces


def index(pieces):
    lines = [INDEX_HEADING, "", TASKS]
    for (number, name), piece in zip(PARTS, pieces[1:4]):
        title = piece.split("\n", 1)[0][3:]
        subs = re.findall(r"^### (\d+\.\d+) (.+)$", piece, re.M)
        lines.append(f"- `{name}`: **{title}**. " + "; ".join(f"{n} {t}" for n, t in subs) + ".")
    return "\n".join(lines) + "\n"


def split(text):
    """{file name: content} for the skill folder."""
    pieces = sections(text)
    files = {"SKILL.md": pieces[0] + SEP + index(pieces) + SEP + pieces[4]}
    for (number, name), piece in zip(PARTS, pieces[1:4]):
        files[name] = piece
    return files


def join(files):
    """The edited file back from the skill's files (the index left out)."""
    head, rest = files["SKILL.md"].replace("\r\n", "\n").split(SEP + INDEX_HEADING + "\n", 1)
    handbook = rest.split(SEP, 1)[1]
    parts = [files[name].replace("\r\n", "\n") for _, name in PARTS]
    return SEP.join([head] + parts + [handbook])


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def skill_files():
    return {name: read(os.path.join(SKILL, name)) for name in ["SKILL.md"] + [n for _, n in PARTS]}


def main(argv):
    if "--fetch" in argv:
        with urllib.request.urlopen(SOURCE_URL, timeout=30) as r:
            lab = r.read().decode("utf-8")
        with open(SOURCE, "w", encoding="utf-8", newline="\n") as f:
            f.write(lab.replace("\r\n", "\n"))
        print(f"Downloaded {SOURCE_URL} to {os.path.relpath(SOURCE, ROOT)}")
    files = split(edit(read(SOURCE)))
    if "--check" in argv:
        stale = [n for n, text in files.items()
                 if read(os.path.join(SKILL, n)).replace("\r\n", "\n") != text]
        if stale:
            print("Out of date: " + ", ".join(stale) + ". Run python tools/split_design_rules.py")
            return 1
        print("The skill matches tools/lab_rules/PCB_DESIGN_RULES.md")
        return 0
    for name, text in files.items():
        with open(os.path.join(SKILL, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"{name}: {len(text):,} characters")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
