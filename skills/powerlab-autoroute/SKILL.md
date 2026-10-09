---
name: powerlab-autoroute
description: Autoroute a KiCad PCB with Freerouting 2.4.1 (Java 25) through the kicad MCP tools, the METU Power Lab way. Use when the user asks to autoroute, auto-route, route the board/remaining nets/signals automatically, or run Freerouting. Covers setting the lab design rules and net classes first, protecting hand-routed power and gate-drive nets, best-of-N runs, DRC and rule checks afterwards, and reporting what is left.
---

# Autorouting with Freerouting

Freerouting is good at the many small signal connections and bad at power electronics judgement. Use it to finish a board, not to design the critical paths.

**The lab design rules come first.** Before anything else, load the `powerlab-pcb-design-rules` skill. Every width, clearance, via and routing-order decision below comes from it: §2.6 for constraints and net classes, §3.3 for routing, §3.4 for vias, §3.5 for pours. Freerouting only routes as well as the rules it is given. With the default net class it routes everything as thin signal tracks, and the result is useless for a power board.

## 0. Is Freerouting the right tool for this board?
Check with `get_board_info` / `query_zones` / `get_ratsnest` before promising anything.
- **Good fit:** a board where most signal nets are still unrouted and copper pours are few, or are only GND on inner plane layers. A 2-layer board with 62 footprints and 29 nets routed completely in about 5 s.
- **Poor fit, so say so before running:** a dense board that is already mostly routed and has many copper pours on the outer layers (e.g. VBUS, phase and switch-node pours on F.Cu). Freerouting reads each zone's whole outline as a solid plane, so it starts out with hundreds of false clearance violations. On a 4-layer ESC board with 11 pour nets on F.Cu, rerouting just 4 small nets did not finish in 5 minutes. For a board like that, recommend KiCad's interactive router (`X`, with walkaround/shove) for the remaining nets instead, and only run Freerouting if the user still wants to try with a long timeout.

## 1. Check the setup first
Call the `check_freerouting` tool.
- It must find **Java 25** and the Freerouting jar. Freerouting 2.4.1 is built for Java 25 and fails with `UnsupportedClassVersionError` on older Java.
- In the PowerLab Assistant panel both are preinstalled and found automatically. If the check fails, stop and tell the user to run `install.ps1 -Update` from the PowerLab KiCad Assistant folder, then restart KiCad. Don't try to install Java or Freerouting yourself.

## 2. Set the rules (design rules §2)
Ask for whatever you can't read from the board, and don't guess currents or voltages.
- **Copper weight and layer count:** confirm them, because they change every limit (§2.0–2.2). The default is 2 layers and 1 oz.
- **Board constraints (§2.6):** check them with `get_design_rules`. For 1 oz copper they should be the values below.
  - If they differ and the board is open in KiCad, `set_design_rules` can't change them: KiCad's API has no design-rule calls, and KiCad overwrites the file when it saves. Ask the user to set them in **Board Setup → Design Rules → Constraints**, save, and tell you to continue.
  - Use `set_design_rules` only when KiCad doesn't have the board open.
  - The values:
    - minimum clearance 0.15 mm, minimum track 0.15 mm, minimum connection 0.15 mm. These are the PCBWay standard-price floor; the net classes below set the 0.2 mm lab default. Freerouting's fanout narrows escape tracks to 0.15 mm between fine-pitch pads (e.g. ESP32, USB-C), which the rules allow.
    - via 0.6 mm, through hole 0.3 mm, annular ring 0.15 mm
    - copper to hole 0.25 mm, copper to edge 0.5 mm, hole to hole 0.4 mm
    - no micro or blind vias
- **Net classes (§2.6):** Freerouting reads the project's net classes, so these decide its widths, clearances and vias. Create them with `create_netclass` (its `nets` list) or `assign_net_to_class`. Both take net names, not patterns, so list the nets with `get_nets_list` and pick the ones matching the §1.6 patterns `*GND*`, `+*`, `-*`, `VBUS*`:

  | Class | Track | Clearance | Via drill / pad |
  |---|---|---|---|
  | Default | 0.2 mm | 0.2 mm | 0.3 / 0.6 mm |
  | Power, GND | width for the current, at least 0.5 mm | 0.3 mm | 0.4 / 0.8 mm |
  | HV (> 50 V) | width for the current | from the §3.3 voltage table | 0.4 / 0.8 mm |

  - **Power widths:** ask the user for each rail's current, then size the track from the §3.3 table. On 1 oz outer copper that is 0.3 mm for 1 A, 0.8 mm for 2 A and 1.4 mm for 3 A. Above about 3 A the net belongs in a pour, not a track.
  - **Never route a power net at the default width.**
  - **Freerouting 2.4.1 ignores the net-class width.** It writes every net to the session at the default width, even when the DSN carries the Power class with 0.5 mm (seen on a 4-layer board, issue #21). Don't leave the rails to it:
    - route them first, at the class width (step 3);
    - after any run, check every power track (step 5).
- **Schematic `LAYOUT:` notes:** collect them, because they are requirements too (§1.7). Typical ones are hot loops, Kelvin connections and impedance.

## 3. Make sure the board is ready (design rules §3.1–3.2)
Before routing, confirm with the user, or check with the kicad tools:
- **Saved:** the board is saved in KiCad. Routing writes the `.kicad_pcb` file, so unsaved KiCad edits would be lost.
- **Outline and placement:** a closed board outline exists on Edge.Cuts and every footprint is inside it. Placement decides the result far more than router settings. Check the §3.2 points before routing; bad placement can't be fixed by the router. **Render a placement view first** (`powerlab-visual-review`), look at it, and fix the placement before routing:
  - decoupling caps right at their IC pins
  - crystals at the MCU
  - analog, digital and power sections apart
  - assembly spacing
- **Route in the §3.3 order, and only the last step is for Freerouting:**
  1. **High-current paths:** pours or hand-routed wide tracks. This covers power input and output, switch nodes, half-bridge and DC-bus loops.
  2. **Clocks and gate-drive loops:** driver → gate → source return. Keep them short with a small loop.
  3. **Differential pairs.**
  4. **Sensitive analog:** current-sense and Kelvin connections, references, ADC inputs.
  5. **Everything else:** Freerouting.

  Steps 1–4 must be routed by hand and locked first. KiCad exports locked tracks as protected, so Freerouting keeps them. If they aren't done, say so and recommend doing them first. Only autoroute them if the user explicitly insists, and warn that loop area, current capacity and return paths won't be considered.
  - The **power rails** belong to step 1 even when they carry little current.
    - Make them copper areas (pours) wherever they fit (design rules §3.3).
    - Where a pour doesn't fit, use tracks at the Power class width (≥ 0.5 mm).
    - Lock them before running Freerouting.
  - KiCad's session import clears the locked flag. Lock the hand-routed copper again after every `autoroute` run.
- **Fan out the pour nets first (design rules §3.3, issue #21):** the pours connect the GND pads. Don't give every GND pad a via; that only clutters the board and blocks routing.
  - **Decoupling caps:** a via to the GND plane right at each cap's GND pad.
  - **Fine-pitch IC GND pins:** a pin next to a GND exposed pad joins the exposed pad straight across the gap. Other fine-pitch GND pins neck down to a via just outside the pin row.
  - Keep about 1.5 mm in front of every fine-pitch pin free of these vias, so the signal pins can still escape.
  - Lock the fan-out.
  - **After routing and the zone fill:** a GND pad the pour can't reach shows up as unconnected in DRC. Give only that pad a via. GND never needs a track between pads.
- **Pours first (§3.1, §3.5):** never let Freerouting draw GND as tracks.
  - **Check for existing pours first** with `query_zones`. Never add a second pour for the same net on a layer that already has one: overlapping same-net zones give DRC "zones intersect" errors. To change an existing pour, ask the user.
  - If the board has no GND pour, create one before routing with `add_copper_pour` (layer, net and clearance; leave out `outline` to cover the whole board outline), on the bottom layer and also on the top. On 4 layers, use the inner GND plane layer. Do the same for any power net the user wants as a pour (above ~3 A).
  - Then route with `pourNets` set to those nets, e.g. `pourNets: ["GND"]`. Freerouting leaves them out, routes on all layers, and keeps their existing tracks. The pours are refilled around the new tracks afterwards.
  - **Check the fan-out survived:** Freerouting 2.4.1 can drop the fixed vias of a plane net and route other nets straight over them.
    - After the run, any `shorting_items` or `clearance` error between a signal and a GND via or stub means this happened.
    - Undo (File → Revert) and tell the user. Those nets need keepouts over the fan-out copper, or routing by hand around the fan-out.
  - **A 4-layer board's GND plane layer stays a plane.** If tracks land on the plane layer (e.g. In1.Cu), the plane was routed over: undo and say so.
- **3D models:** check that the footprints still have their 3D models (`get_component_properties` or the 3D viewer). If they are missing, tell the user to run **Tools → Update Footprints from Library** with **Reset 3D models** ticked. It restores them without moving the parts.

## 4. Route
- **Load the saved board:** `autoroute` reads the `.kicad_pcb` file, not KiCad's live copy. After live edits (placement, new pours), save first (`save_board`, or ask the user to press Ctrl+S), then call `open_board` with the board path so the router sees them. Also call `open_board` if `autoroute` says "No board is loaded". On large boards it can take over 30 s and time out once; retry once.
- **Baseline DRC:** run `run_drc` once before routing, so new errors can be told apart from old ones.
- **Estimate the run time:** check the ratsnest (`get_ratsnest`) and tell the user how many connections are open. Freerouting 2.4.1 needs seconds for a small 2-layer board, about 2 minutes for a 2-layer ESP32 board with ~85 nets, and several minutes per attempt for a dense 4-layer one.
- **Timeout:** set `timeout` from that estimate. Allow 600 s per attempt for dense boards and 900 s for very dense ones; the 300 s default is often too short.
- **Best-of-N:** for a first run, use `attempts: 1` with the default `maxPasses` (20). Only use `attempts: 3` (or 5 for dense boards) when the user wants the most complete result and accepts the extra time; each attempt varies the max passes and the most complete result is kept.
- **Pour nets:** always pass `pourNets` for the nets that have pours (step 3).
- **Priority nets:** put signal nets that must be completed (e.g. MCU control, communication) in `targetNets`.
- **If it times out:** say so plainly. Nothing is imported and the board is unchanged. Offer a longer timeout, routing more nets by hand first, or adding the missing pours.

## 5. Check the result against the rules (§3.3–3.7)
- **Refill zones:** run `refill_zones`.
- **Look at it** (`powerlab-visual-review`): save, then render top copper, bottom copper and both layers together. Review them for detours, 90° corners, long or looping power and gate-drive paths, and pours chopped into islands. Fix what you see and render again before reporting.
- **Pour-net pads:** in the DRC's unconnected items, find pads of the pour nets that the pour can't reach, e.g. a GND pad boxed in by tracks. Add a via next to each one (`add_via`, 0.4/0.8 mm), connected with a short track, so it reaches the bottom pour. Then refill again.
- **DRC:** run `run_drc` and compare it with the baseline. The goal is **0 new errors**. Track-width or clearance errors mean the net classes don't match the board constraints; fix the rules and re-route rather than hiding the errors.
- **Corners:** Freerouting routes at 45° but still leaves some 90° corners. On a test board it left 26. The rules forbid them (§3.3). Find them with `query_traces`: two segments of the same net and layer meeting at 90° or less, including where two widths meet. List them for the user, who can fix them with the interactive router or by dragging the corner with `D`.
- **Paths and pad connections (§3.3, issue #21):**
  - Look for tracks that detour or staircase.
  - Look for tracks that touch a pad's edge or clip its corner instead of entering straight and ending at the pad centre.
  - Look for pour slivers or islands between a track and a pad's clearance ring (refill first).
  - Report these and fix them with the interactive router (`X` with walkaround), or by dragging the last segment straight into the pad centre.
  - Remove dangling stubs (DRC `track_dangling`).
- **GND tracks:** list the GND tracks (`query_traces`). Every one must be a short pad-to-via stub. A GND track from pad to pad means a pad was routed instead of being fanned out to the plane: replace it with a via at the pad.
- **Widths and vias on power nets:**
  - check every power and GND track against its class width (`query_traces`). Freerouting routes them at the default width (step 2).
    - Widen every segment that has room.
    - A narrower section is only allowed right at a pin that forces it.
    - List the rest for the user.
  - no track below the board minimum: Freerouting necks down to 0.10–0.12 mm at fine-pitch pins (DRC `track_width`)
  - at least 2 vias at each power layer change, 0.4 mm drill (§3.4)
  - no vias in SMD pads except thermal pads
- **Pours and stitching:** after the pours are filled, save the board (Ctrl+S, or `save_board`), then add GND stitching vias every ~5 mm with `add_gnd_stitching_vias` (`strategies: ["grid", "in_zones"]`, `viaSize: 0.8`, `viaDrill: 0.4`; §3.4). With KiCad open, it plans on the saved file and places the vias live, keeping the board's largest net-class clearance. Remove copper islands or stitch them to GND (§3.5).
- **High-speed:** no clock or fast signal crosses a gap in its reference plane (§3.3).
- **Unrouted nets:** report what is still unrouted (`get_ratsnest`). Name the nets and suggest finishing them by hand.
- **Optional:** render the top and bottom with `kicad-cli pcb render` so the user can look at the result.

## 6. Tell the user
- **How it went:** say how many nets were routed and how many are left, plus the DRC result compared with the baseline and the rule checks from step 5.
- **Reload:** the board file changed, so the user must use **File → Revert** in KiCad to see it (unsaved edits are lost; that's why step 3 asks them to save).
- **Finish:** suggest teardrops (Edit → Edit Teardrops, §3.3) once routing is final.
- **Review:** remind them that autorouted power-electronics boards need a human review against the §3.7 checklist before ordering. That includes loop areas, return paths, track widths on high-current nets, and via counts on power paths.
