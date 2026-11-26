---
name: powerlab-pcb-design-rules
description: METU PowerLab PCB design rules for KiCad work — PCBWay standard-price (no-surcharge) spec, fab limits and lab default DRC values, schematic rules, common PCB layout rules, and a 233-rule layout review handbook (stackup, placement, power, grounding, high-speed, RF, crystals, switching power, ESD, thermal, vias, DFM, DFA, silkscreen, mechanical, testability, aesthetics). Use whenever designing, reviewing, or editing a schematic or PCB, setting up KiCad board/DRC constraints or net classes, sizing traces/vias/copper, or checking a layout for manufacturability and layout quality.
---

# PCB Design Rules — METU PowerLab

Source: https://github.com/odtu/Powerlab/blob/master/KiCAD/PCB_DESIGN_RULES.md, minus the lab's drawing sheet, logo, website and QR code: other people's boards don't carry the lab's branding.

Target fab: **PCBWay Standard PCB, at standard (no-surcharge) spec**, IPC Class 2.
Sources: https://www.pcbway.com/capabilities.html and the quote form at https://www.pcbway.com/orderonline.aspx (both checked 2026-09-25).

## How to apply these rules

- **Cost comes first.** Every board must fit the standard-price spec in §2.0. Anything outside it adds a surcharge, so ask the user before using it and say which option costs extra.
- Every numeric rule has two columns: **PCBWay min** (the manufacturing limit, already capped at the standard-price spec) and **Lab default** (what to actually use). Design to the lab default. Go below it only locally, only when the part forces it (e.g. fine-pitch pads), and never below the PCBWay min.
- When two rules conflict, the stricter one wins. A project's own `CLAUDE.md` or README can override these; it wins over this file.
- If a design can't meet a rule, don't silently break it. Tell the user which rule, where, and why.
- **Placement distances are targets, not limits.** "Within 2.5 mm", "as close as the layout allows" and the like mean as close as you can. If meeting one would push other parts away from their own pins, go a little further (e.g. 3 mm instead of 2.5 mm) and keep the whole placement short. Fab and assembly limits (§2, "Room for assembly" in §3.2) and keep-out areas stay hard limits.
- Copper weight changes the limits. Always confirm the copper weight (outer and inner) before setting constraints.
- The lab rules in §1–§3 come first. The review handbook (§4) adds detail where they say nothing; where the two give different numbers, use the lab's.

---

## Which file to read

The rules are split into files in this skill's folder, next to this file. Read the ones the task needs, and only those:

| Task | Read |
|---|---|
| Schematic: sheets, parts, wiring, net names, net classes and their colours, layout notes, ERC | `schematic.md` (§1) |
| Board setup: copper weight, layers, standard-price spec, fab limits, Board Setup constraints and net classes, DRC | `fab-and-drc.md` (§2) |
| Layout: outline, placement, pours, routing, vias, silkscreen, outputs | `layout.md` (§3), and `fab-and-drc.md` too when the task also sets up the board (net classes, DRC values, track and via sizes) |
| Design review, "is it ready to order?" | all three, and the handbook (§4 below) |

Other skills cite these rules by number (e.g. §3.3 pours, §3.4 routing, §3.5 vias); the number's first digit names the file.

- `schematic.md`: **1. Schematic rules**. 1.1 Page setup and title block; 1.2 Sheet structure; 1.3 Components: PowerLabKiCadLibraries only; 1.4 Wiring; 1.5 Net naming and power symbols; 1.6 Net classes and power-net styling; 1.7 Layout notes on the schematic; 1.8 Clean text; 1.9 Schematic done-checklist.
- `fab-and-drc.md`: **2. Fab limits and DRC values (PCBWay)**. 2.0 Standard-price spec (default for every board); 2.1 Board; 2.2 Tracks and spacing (per copper weight, "normal process"); 2.3 Drills, vias, annular ring; 2.4 Solder mask and silkscreen; 2.5 Board edge and panelization; 2.6 KiCad setup (Board Setup → Design Rules → Constraints).
- `layout.md`: **3. PCB layout rules**. 3.1 Board setup, outline and fixed parts; 3.2 Placement; 3.3 Copper pours and high-current copper; 3.4 Routing; 3.5 Vias; 3.6 Silkscreen and board information; 3.7 Final checks and outputs.

---

## 4. Layout review handbook

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
