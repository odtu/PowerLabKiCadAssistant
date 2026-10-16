# PCB Design Handbook — User Guide for the Auditor Agent

This handbook was written for AI agents that audit PCB layouts **from screenshots only**. The reader is not a human; the content is organised to be rule-focused, short and visually detectable.

## Your task

You will be given one or more PCB images (editor screenshot, 3D render, Gerber view or a photo of a real board). Using the rules in this handbook, report:

1. Routing errors and weak points,
2. Placement improvements,
3. Manufacturing (DFM) and assembly (DFA) risks,
4. Signal / power integrity problems,
5. Aesthetic and readability problems

with the rule ID, the location in the image and the confidence level. **Do not write rules you made up yourself**; if a problem is not in the handbook, state it separately as "No rule in the handbook".

## How to use it

1. **Read `90-visual-audit-guide.md` first.** Colour codes, scale estimation, analysis order, the limits of the image and the report format are there.
2. **Use `91-checklist.md` for a quick scan.** All rules on one line each, sorted by severity.
3. When you see a suspicious finding, open the full text of the rule in the relevant topic file. Check especially the **"How it looks in the image"** and **"Exceptions"** fields; if an exception applies, do not report the finding.
4. For a term you do not know, look in `92-glossary.md`.
5. For rules with "Detectable from image: No", ask the user for the information named in that field (stackup, current, netlist, DRC report, enclosure drawing…). Do not report these rules as a "violation" based on a guess.

## File map

| File | Prefix | Topic |
|---|---|---|
| `01-stackup.md` | STK | 2/4-layer stackup, reference planes |
| `02-placement.md` | PLC | Functional blocks, connectors, heat sources |
| `03-power-distribution.md` | PWR | Trace width/current, regulator, decoupling |
| `04-grounding.md` | GND | GND plane, split planes, stitching vias, return path |
| `05-high-speed-signals.md` | HS | USB, differential pairs, impedance, length matching |
| `06-rf-antenna.md` | RF | Antenna keepout, module placement, RF feed line |
| `07-crystal-oscillator.md` | XTL | Crystal / oscillator layout |
| `08-switching-power.md` | SMPS | Buck/boost hot loop, inductor, feedback |
| `09-esd-protection.md` | ESD | TVS placement, protection path |
| `10-thermal.md` | THM | Thermal vias, copper area, exposed pad |
| `11-vias.md` | VIA | Via-in-pad, tenting, size, current |
| `12-dfm.md` | DFM | Min trace/clearance, annular ring, edge, acid trap, sliver |
| `13-dfa.md` | DFA | Footprint, spacing, tombstoning, polarity, fiducial |
| `14-silkscreen.md` | SLK | Labels, revision, readability |
| `15-mechanical.md` | MEC | Mounting holes, connector access, panelisation |
| `16-testability.md` | TST | Test points, programming/debug access |
| `17-aesthetics.md` | EST | Order, alignment, symmetry, trace flow |
| `90-visual-audit-guide.md` | GOR | Method for analysing from the image |
| `91-checklist.md` | — | One-line list of all rules |
| `92-glossary.md` | — | Terms (TR + EN) |
| `SOURCES.md` | — | All sources |
| `DECISIONS.md` | — | Decisions taken during preparation and verification results |

## Rule format

Every rule uses the same template:

- **Severity:** Critical > High > Medium > Low > Cosmetic. Sort the report in this order.
- **Detectable from image:** Yes / Partly / No. If "Partly", report the finding with "Likely" confidence and write what needs to be verified.
- **How it looks in the image:** The visual pattern you are looking for. This is the most important field of the rule.
- **Why it matters / Recommended fix / Exceptions / Example / Source**

Numerical values are given with source, condition and (for manufacturer limits) access date. Manufacturer limits change over time; if the user's chosen manufacturer is different, ask for its current value.

## Core principles

- **Separate certain from estimated.** Give every finding a "Certain / Likely / Needs verification" confidence (definitions in the `90` file).
- **Give a location.** For example "bottom left, next to the USB connector" or "right side of U3".
- **Give a measured recommendation.** Instead of "move the capacitor closer", write e.g. "move C5 to ≤2 mm from U2's VDD pin (PWR-006)".
- **Few but correct findings.** An uncertain Critical finding is more harmful than a missed Low finding.
- **Ask for the design context.** If current, frequency, stackup, enclosure and manufacturer are unknown, list them as questions at the end of the report.
- **Report the same finding once.** Some topics appear in more than one file; if the Exceptions field of the secondary rule says "Primary rule for this finding: X", report the finding as X (e.g. open via in pad → VIA-001, not DFA-013).
- **Severity comes from the rule.** The severity in the report is the rule's Severity field; express uncertainty with the confidence column, not by lowering the severity.
