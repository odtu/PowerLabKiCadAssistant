---
name: powerlab-visual-review
description: Render the PCB and look at it while working, the METU Power Lab way. Use for any placement or routing work (placing, moving or rotating parts, routing tracks, pours, autorouting, stitching vias, layout clean-up) and whenever the user asks to see, check or review the board. Covers which views to render, when, how to review them against the design rules, and showing them to the user.
---

# Look at the board while you work

Tool results and DRC numbers don't show what a layout looks like:
- loop areas, return paths and decoupling distance
- parts crowding each other, or silkscreen on pads
- tracks that wander or take odd detours

A rendered view shows all of these at a glance. On the lab's ESC3Phase board, rendering and reviewing at every step made the biggest difference to the result. **This is a rule, not an option:** render, look, fix, render again.

## When
- **Before you start:** one baseline view, so you know what's there.
- **After every meaningful step:** a functional block placed, a group of nets routed, pours added or refilled, a PowerLab router run, stitching vias added. Don't batch ten changes and look once at the end.
- **Before you say a placement or routing task is done:** final views, after `refill_zones`.
- **When the user asks for a review:** at least three views: placement, top copper alone, bottom copper alone. Add the 3D top view when parts or silkscreen matter. One combined view isn't enough, because pours hide the tracks.

## How
1. **Save first.** The views are rendered from the saved `.kicad_pcb`, not KiCad's live copy. After live edits call `save_board` (or ask for Ctrl+S).
2. **Render** into the views folder named in the panel instructions. Use numbered names so the series stays in order (`01-placement.png`, `02-route-top.png`, …).
   - **2D:** `get_board_2d_view` with `pcbPath: <board>.kicad_pcb` (the panel's "Board file" path), `responseMode: "file"`, `outputPath: <views>/NN-name.png` and a `layers` list. The default is layer colours on a dark background; keep it.
     - Placement: `["F.Cu", "F.SilkS", "F.Fab", "F.CrtYd", "Edge.Cuts"]` (and the `B.` layers if parts are on the bottom).
     - Top routing: `["F.Cu", "Edge.Cuts"]`.
     - Bottom routing: `["B.Cu", "Edge.Cuts"]`. Copper pours hide tracks in combined views, so check layers one at a time.
     - Both layers together: `["F.Cu", "B.Cu", "Edge.Cuts"]`, for layer changes and crossings.
     - Use `width: 2400` for dense boards.
     - **Close-ups:** add `region: {x, y, size}` (board mm; or `{x0, y0, x1, y1}`) to render one block, e.g. 15–25 mm round an IC. A whole-board view looks fine even when parts are packed pad to pad, so render a close-up of every block you place or route, and look at it.
   - **3D:** `kicad-cli pcb render --side top --output <views>/NN-3d-top.png <board>.kicad_pcb` (and `--side bottom`). Use it for placement, part bodies colliding, connectors facing outward, polarity marks, and missing 3D models.
3. **Look at it** with the Read tool. The panel shows every image you open to the user too, so open the views you want them to see. Usually that's the final one per step, not every attempt.
4. **Review it against the design rules** (`powerlab-pcb-design-rules`), and write down what you see in one or two short lines, e.g. "C5 is 4 mm from U1's VDD pin, move it closer":
   - **Placement (§3.2):**
     - every part where its connections are shortest, packed as tightly as assembly allows; passives on the other side under their pins where that's shorter; blocks that talk to each other stacked on the two sides. Distances in the rules are targets: closer is better, a little further is fine when closer would push other parts away
     - decoupling caps right at their IC pins, smallest value closest
     - crystal at the MCU
     - power, analog and digital sections apart, with power flowing one way
     - connectors at the edge, facing out
     - polarized parts aligned; rotations at 0/90/180/270 on a rectangular board, following the circle on a round one
     - **passives placed by their connections (§3.2):** each beside the pin it serves, rows in pin order, pads facing their connections, chains in signal order, decap supply pad to the VDD pin and GND pad to its GND. In the close-up, follow every airwire: one that crosses another inside a block, or runs past a part to reach its pin, means a 180° turn or a swap. Measure with `get_ratsnest` / `estimate_airwire_lengths`.
     - assembly spacing and keep-outs (§3.2): **measure with `check_part_spacing`**, never judge them from a view; the lab's parts have no courtyard, so DRC reports nothing. Pass `minGap` 0.5 for machine assembly (1.0 hand soldering, per `design-requirements.md`) and the requirement keep-outs as `keepouts` (both sides unless the requirement allows one; `allow` for the parts the requirement lets inside, e.g. `["R", "C"]`). Every pair, keep-out hit and through-pad hit it lists is a finding.
     - room between parts for the tracks and vias that must pass there (a bus, the escape from a fine-pitch IC); routing can't make room that placement didn't leave
     - silkscreen readable, not on pads (checked last: fit the labels after the placement, never move parts for them)
   - **Routing (§3.3–3.5):**
     - every power pad in its copper area; high-current paths short and wide
     - small gate-drive and switching loops, return path directly beside or below
     - switching tracks not on the same layer as the high-current copper beside them
     - no tracks under inductors or transformers
     - fast signals on one layer, without vias where possible
     - no 90° corners, no acute angles, no detours or stubs
     - clocks short, and none crosses a split in the plane below
     - vias doubled on power layer changes
     - pours not chopped into islands, stitching where planes need it
5. **Fix what you found, then render again.** Repeat until the view looks like something you would send to a reviewer. If a fix needs a decision (moving a connector, changing layers), show the view and ask.

## Report
End with the final views open (Read), plus a short list: what you checked, what you changed after looking, and what the user should still review by eye.

At the end of a placement or routing task, go on with `powerlab-design-review`: it reviews the whole board against the lab rules and the review handbook, fixes what it can in rounds, and writes the final review that the panel shows and saves as a PDF.
