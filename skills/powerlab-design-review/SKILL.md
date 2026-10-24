---
name: powerlab-design-review
description: Review a KiCad PCB layout, fix what can be fixed, and repeat until it is clean, then write the final design review that the panel shows and saves as a PDF, the METU Power Lab way. Use at the end of every placement, routing or autorouting task (a block or more placed, nets routed, pours or stitching added), and whenever the user asks to review, check, audit or critique the board or layout, asks whether it is ready to order or manufacture, or asks for a design review, review report or review PDF. Covers DRC, rendered views, the lab rules and the 233-rule review handbook, sorting findings into "fix it" and "needs the user", the fix-and-recheck loop and when to stop, and the report format.
---

# Review the board, fix it, repeat

After you place or route a board, check your own work like a reviewer would, fix what you can, and check again. Stop only when nothing is left that you can fix on your own. Then write one final review for the user: what was fixed, what is still open, and what needs them.

## When
- **At the end of every placement or routing task** you did in the panel: a functional block or more placed, nets routed, a PowerLab router run, pours or stitching vias added. Run it before you say the task is done. Skip it after a single small edit (one part moved, one track added), unless the user asks.
- **Whenever the user asks** for a review, a check, or whether the board is ready to order.

Say in one line that you're starting the review, e.g. "Layout done. Reviewing it now: DRC, views, lab rules and the review handbook."

## Before the first round
1. Load `powerlab-pcb-design-rules` (lab rules §1–§3 and the handbook in its `handbook/` folder) and `powerlab-visual-review`, if they aren't loaded yet.
2. If the project has `design-requirements.md`, read it: currents, voltages, enclosure, fab, layers. Anything a rule needs that it doesn't say (e.g. phase current for track widths) is a question for the user, not a guess.
3. **Is KiCad's board up to date?** If a tool changed the `.kicad_pcb` file itself in this task (e.g. `clean_up_routing`, or `powerlab_route` while KiCad didn't have the board open) and the user hasn't used File → Revert since, stop and ask them to. Your fixes go to KiCad's live board, and saving it would overwrite the file with the old copy.
4. Save the board (`save_board`). kicad-cli and the renders read the saved `.kicad_pcb`, not KiCad's live copy. Save again after every group of fixes.
5. Pick the rules that apply to this board from `handbook/91-checklist.md`, rule by rule, from the board's parts and nets, not by section title. A rule is out only when the board has nothing it is about: HS-009 without USB-C, HS-016 without HDMI or MIPI, RF without a radio module, antenna or RF connector, SMPS without a switching converter. HS isn't only USB, Ethernet and HDMI: it also covers CAN, RS-485 and encoder pairs, SPI, clocks and other fast edges (HS-001, HS-011 to HS-014), which most lab boards have. Don't announce the rules you leave out in the chat; list them under "Not checked" in the review, with the reason (e.g. "RF: no radio or antenna on the board").

## One round
1. **DRC.** One plain command:
   `kicad-cli pcb drc --severity-all --all-track-errors --schematic-parity --refill-zones --format json -o <views>\drc-NN.json <board>.kicad_pcb`
   (`<views>` is the views folder named in the panel instructions; NN is the round). Read the report with Read or Grep. Every error is a finding. Judge the warnings: some are real problems (silkscreen on pads), some are accepted (a footprint that differs from the library on purpose).
2. **Placement, measured.** `check_part_spacing` with `minGap` for the assembly method (0.5 mm machine, 1.0 mm hand, from `design-requirements.md`), the keep-out areas as `keepouts` (both sides unless the requirement allows one), and `edgeGap` when the requirements give an edge distance. The lab's parts have no courtyard, so DRC can't see crowding: this tool is the check. Every pair closer than the rule, every keep-out hit and every part on the other side's through pads is a finding. Then the connections (design rules §3.2): `get_ratsnest` / `estimate_airwire_lengths` and the block close-ups; a passive turned the wrong way, out of pin order or in another part's place is a finding, and so is a part whose connections would be much shorter somewhere else (on the other side too).
   - **Distances are targets** (design rules, "How to apply"): a decap at 3 mm where the rule says about 2.5 mm, because closer would push other parts away, is a Low finding at most, worded as "closer is better", not a failure.
   - **Check the requirements before you call it a finding:** parts the requirements allow inside a keep-out (e.g. passives under an encoder ring) and part angles that follow a round board (§3.2) are fine. Pass only the parts the area keeps out: `allow` on the keep-out lists the reference prefixes allowed inside (e.g. `["R", "C"]`).
3. **Routing, measured.** `check_routing`: every off-angle segment, corner sharper than 45°, kink, detour (same-net pads joined the long way round), off-centre pad entry and solid GND pour it lists is a finding. Fix them like DRC errors: redraw the run 45°-only and straight into the pads (`delete_trace`, then `route_trace` with waypoints or `route_pad_to_pad`), set GND pours to thermal reliefs (`edit_zone` with `padConnection: "thermal"`). A detour that's deliberate (a gate-drive loop kept round a via row, a bus kept together) is fine: say why in the review.
4. **Views.** Render and look at them as `powerlab-visual-review` says: placement, each copper layer on its own, and the 3D top (bottom too if parts are there). Then a close-up (`region`) of every block: crowding, pad entries and odd routing only show close up. Numbered names in the views folder.
5. **Check.** Go block by block (power input, each converter, MCU, connectors, …) and write one short line per block as you go. For every rule that could apply:
   - **Measure, don't estimate.** Distances with `get_pad_position` / `get_component_pads`, widths and layers with `query_traces`, pours with `query_zones`, unrouted nets with `get_ratsnest`. The handbook's "estimate from the image" advice is for screenshots; you have the board.
   - Read the rule's **Exceptions** before you call something a finding.
   - Check the lab's final list (design rules §3.7) and `design-requirements.md` too.
6. **Sort every finding** into one of two groups:
   - **Fix it:** the fix is clear, local, within the lab rules and the requirements, and the kicad tools can do it. For example: move or rotate a part that isn't locked (a decoupling cap closer to its pin), add or widen a track, add vias on a power layer change, add stitching vias, refill zones, move silkscreen text off a pad, add the board info text, fix a net class, put a plated mounting hole on the net the requirements give (`edit_component` with `padNets: {"*": "GND"}`).
   - **Needs the user:**
     - it needs information you don't have (current, voltage, enclosure, fab or cost choice);
     - it needs a decision: moving a connector, mounting hole, locked part or anything the user placed on purpose; changing the outline, layer count or stackup; changing the schematic, a part or a footprint; anything with a surcharge;
     - the tools can't do it (see below);
     - you tried to fix it twice and it didn't work.
7. **Fix** the "fix it" findings, highest severity first, one block at a time. Silkscreen and label fixes come last, after the placement and routing fixes. After each group: save, run the DRC again, and render the area you changed.
   - If a fix adds DRC errors or makes something else worse, undo it (move the part back) and move the finding to "needs the user".
   - Keep a log for the report: round, rule, where, what you changed (with numbers, e.g. "C5 moved from 4.2 mm to 1.1 mm of U2 pin 7").

**When a tool can't do it.** Some edits don't reach KiCad's live board: a tool says it worked, but the next DRC or render shows no change. Changing an existing track in place (`modify_trace`) is the usual case; delete it with `delete_trace` and route it again instead. Board-outline lines are deleted with `list_graphics` + `delete_graphic`, or all at once with `clear_board_outline`. If a tool still shows no change, don't retry. Put it under "needs the user" with exact steps for KiCad, e.g. "Delete the 0.25 mm track from U3 pin 4 to the via at (106.2, 124.0) on B.Cu".

## When to stop
After a round with fixes, start another round. Stop when one of these is true:
- **Nothing left to fix:** the round found no "fix it" findings. Everything open needs the user, or nothing is open.
- **No progress:** a round's fixes removed no findings, or a finding came back after you fixed it. Move those findings to "needs the user".
- **Five rounds:** write the review with what's left and say the user can ask you to continue.

Never write the final review while DRC shows errors you could fix. Never stop a round silently: if you stop, the review says why.

## The final review
1. **Final views** in `design-review\images\` in the project folder (the panel puts the review there; it isn't a temp folder). Same views as a round, after the last fixes and a zone refill:
   - 2D: `get_board_2d_view` with `pcbPath: <board>.kicad_pcb` (the panel's "Board file" path), `responseMode: "file"`, `outputPath: <project>\design-review\images\NN-name.png`.
   - 3D: `kicad-cli pcb render --side top --output design-review\images\NN-3d-top.png <board>.kicad_pcb`.
   - Names: `01-placement.png`, `02-top.png`, `03-bottom.png` (inner layers next), then the 3D views.
2. **Write `design-review\design-review.md`** in the project folder with the Write tool, in the format below. Replace an older one.
   - The panel turns it into `design-review.pdf` next to it and shows the whole review in the chat after your reply. Don't make the PDF yourself and don't open it.
   - In a terminal session (not the panel) there is no PDF: tell the user where the `.md` file is.
3. **Reply in a few lines:** the verdict, the counts, and the "needs you" items as a short numbered list, with the same `kicad:` links. The full review shows under your reply, so don't repeat it. If a "needs you" item has clear options, end with a `<choices>` block.

### Format

Keep to this structure. The panel and the PDF understand headings, `-` lists, numbered lists, tables, **bold**, `code`, links and images on a line of their own. Leave out a section or a severity heading that has nothing in it.

```markdown
# Design review: <board file name, without .kicad_pcb>

2026-10-15 · PowerLab KiCad Assistant · 3 review rounds

## Summary
- **Board:** 100 × 90 mm, 4 layers (F.Cu power and signal, In1.Cu GND, In2.Cu GND and signal, B.Cu GND and signal), 84 parts, 61 nets
- **DRC** (kicad-cli, zones refilled, all track errors, schematic parity): 0 errors, 2 warnings, 0 unconnected
- **Result:** 7 findings fixed in 3 rounds. 2 need you. Still open: 1 High, 2 Medium.
- **Verdict:** Ready to order after the 2 items under "Needs you".

## Needs you
| # | Rule | Where | Finding | What to do |
|---|---|---|---|---|
| N1 | RF-006 | [Top edge, J1](kicad:refs=J1) | J1 is 1.9 mm from the antenna keepout; at least 10 mm is needed. | Move J1 to the top left next to SW1, or accept a shorter Wi-Fi range. |

## Open findings
### High
| # | Rule | Where | Finding | Confidence | Fix |
|---|---|---|---|---|---|
| F1 | SMPS-006 | [Middle left, under L1](kicad:refs=L1&net=BUCK_PG) | BUCK_PG (In2.Cu, 0.2 mm) runs under the inductor L1. | Certain | Route it outside L1's body (x 7.8–14.1, y 32.0–40.5 mm). |

## Fixed during the review
| Round | Rule | Where | Change |
|---|---|---|---|
| 1 | PWR-006 | [U2, right side](kicad:refs=U2,C5) | C5 moved from 4.2 mm to 1.1 mm of U2 pin 7. |

## Checked and fine
- In1.Cu is a continuous GND plane under all signals (STK-002, GND-001).
- Antenna at the board edge, no copper under it (RF-001, RF-002).

## Not checked
- Phase current is unknown, so the phase pour widths weren't checked (PWR-001).

## Views
![Placement](images/01-placement.png)
![Top copper](images/02-top.png)
![Bottom copper](images/03-bottom.png)
![3D top](images/05-3d-top.png)
```

### Rules for the report
- **Severity** comes from the rule (handbook) or, for lab rules (`§3.4`), from how much it matters. Order: Critical, High, Medium, Low, Cosmetic. Show doubt in the confidence (Certain / Likely / Needs verification), not by lowering the severity.
- **Number** open findings F1, F2, … and "needs you" items N1, N2, …, across the whole report.
- **Where:** a place on the board in words plus the reference designators ("top right, between U6 and Q2"), and coordinates when that helps.
- **Make every "Where" a `kicad:` link,** so a click in the panel selects that place in KiCad and zooms to it (the schematic editor follows by cross-probing). Point at what the finding is about:
  - parts: `[top right, U6 → Q2](kicad:refs=U6,Q2)`
  - a net (its tracks, vias and pads, highlighted): `[GLC gate track](kicad:net=GLC)`
  - parts and a net: `[under L1](kicad:refs=L1&net=BUCK_PG)`
  - a place with no part on it, in mm in board coordinates as KiCad shows them: `kicad:area=x1,y1,x2,y2`, or `kicad:at=x,y` for what lies within 2.5 mm of a point
  - In net names, write `(`, `)`, `&`, `,`, `%` and spaces as `%28`, `%29`, `%26`, `%2C`, `%25` and `%20`: `kicad:net=Net-%28U1-Pad3%29`.
  - Use the board's real references and net names, and check them: a link to something not on the board only shows "Not found".
- **Measured numbers** in findings and fixes, with the limit they break.
- **Each problem once,** under its primary rule.
- **Verdict:** one of "Ready to order", "Ready to order after the items under Needs you", or "Not ready: <the main reason>". "Ready to order" needs 0 DRC errors, no open Critical or High findings, and nothing under "Needs you".
- Images use paths relative to the report (`images/…`), each on a line of its own.
