---
name: powerlab-autoroute
description: Autoroute a KiCad PCB with Freerouting 2.4.1 (Java 25) through the kicad MCP tools, the METU Power Lab way. Use when the user asks to autoroute, auto-route, route the board/remaining nets/signals automatically, or run Freerouting. Covers setting the lab design rules and net classes first, protecting hand-routed power and gate-drive nets, best-of-N runs, DRC and rule checks afterwards, and reporting what is left.
---

# Autorouting with Freerouting

Freerouting is good at the many small signal connections and bad at power electronics judgement. Use it to finish a board, not to design the critical paths.

**The lab design rules come first.** Before anything else, load the `powerlab-pcb-design-rules` skill. Every width, clearance, via and routing-order decision below comes from it: §2.6 for constraints and net classes, §3.3 for pours and high-current copper, §3.4 for routing, §3.5 for vias. Freerouting only routes as well as the rules it is given. With the default net class it routes everything as thin signal tracks, and the result is useless for a power board.

## 0. Is Freerouting the right tool for this board?
Check with `get_board_info` / `query_zones` / `get_ratsnest` before promising anything.
- **Good fit:** a board where most signal nets are still unrouted and copper pours are few, or are only GND on inner plane layers. A 2-layer board with 62 footprints and 29 nets routed completely in about 5 s.
- **Harder, so say so before running:** a dense board with many copper pours on the outer layers (e.g. VBUS, phase and switch-node pours on F.Cu). By default Freerouting reads each zone's whole outline as a solid plane of that net, so it starts out with hundreds of false clearance violations: on a 4-layer ESC board with 11 pour nets on F.Cu, rerouting just 4 small nets did not finish in 5 minutes. Pass those power pours in `keepoutPourNets` (step 3). That makes them keepouts the router goes around, and the same board's 150 open connections then routed in under 7 minutes.
- **Poor fit:** a board that is already mostly routed by hand, with lots of locked copper among the remaining connections. Freerouting 2.4.1 routes over locked tracks and vias as if they weren't there (step 3, "Check for shorts"). For a board like that, recommend KiCad's interactive router (`X`, with walkaround/shove) for the remaining nets instead, and only run Freerouting if the user still wants to try.

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
- **Copper first (§3.3), then route in the §3.4 order. Only the last step is for Freerouting:**
  1. **Power pads and high-current paths:** every power pad gets its copper area first (MOSFET, diode, inductor, shunt, bulk-cap, regulator and power-connector pads). Pours, or hand-routed wide tracks where no pour fits. This covers power input and output, switch nodes, half-bridge and DC-bus loops.
  2. **Gate-drive loops and clocks:** driver → gate → source return, short with a small loop. Keep them off the layer that carries high-current copper in that area, and keep fast signals on one layer, without vias where possible (§3.4).
  3. **Differential pairs.**
  4. **Sensitive analog:** current-sense and Kelvin connections, references, ADC inputs.
  5. **Everything else:** Freerouting.

  Steps 1–4 must be routed by hand and locked first. KiCad exports locked tracks as protected, so Freerouting keeps them. If they aren't done, say so and recommend doing them first. Only autoroute them if the user explicitly insists, and warn that loop area, current capacity and return paths won't be considered.
  - The **power rails** belong to step 1 even when they carry little current.
    - Make them copper areas (pours) wherever they fit (design rules §3.3).
    - Where a pour doesn't fit, use tracks at the Power class width (≥ 0.5 mm).
    - Lock them before running Freerouting.
  - KiCad's session import clears the locked flag. Lock the hand-routed copper again after every `autoroute` run.
- **No GND fan-out before routing (design rules §3.3, issue #21):** the pours connect the GND pads. Never give every GND pad a via up front; that only clutters the board and blocks routing.
  - **Decoupling caps** are the only exception: a via to the GND plane right at each cap's GND pad. Lock these.
  - A fine-pitch IC GND pin next to a GND exposed pad joins the exposed pad straight across the gap, without a via.
  - **After routing and the zone fill:** a GND pad the pour can't reach (boxed in by tracks, or a fine-pitch GND pin) shows up as unconnected in DRC. Give only that pad a via (step 5). GND never needs a track between pads.
- **Pours first (§3.3):** never let Freerouting draw GND as tracks.
  - **Check for existing pours first** with `query_zones`. Never add a second pour for the same net on a layer that already has one: overlapping same-net zones give DRC "zones intersect" errors. To change an existing pour, ask the user.
  - If the board has no GND pour, create one before routing with `add_copper_pour` (layer, net and clearance; leave out `outline` to cover the whole board outline), on the bottom layer and also on the top. On 4 layers, use the inner GND plane layer. Do the same for any power net the user wants as a pour (above ~3 A).
  - Then route with `pourNets` set to those nets, e.g. `pourNets: ["GND"]`. Freerouting leaves them out, routes on all layers, and keeps their existing tracks. The pours are refilled around the new tracks afterwards.
  - **Power pours on the outer layers** (VBUS, phase, switch node, shunt nodes) go in `keepoutPourNets` instead, e.g. `keepoutPourNets: ["+VBUS", "PHASE_A"]`. GND pours stay in `pourNets`.
    - They aren't routed and their tracks are kept, like `pourNets`. In addition, each pour's outline becomes a keepout on its layer, so signals go around the pour instead of cutting it into pieces.
    - The pours must be drawn to their real shape. Pads of other nets inside a pour outline can't be reached.
    - Pads of these nets outside their pour stay unconnected. Connect them by hand first (step 1 of the routing order).
  - **Check for shorts into locked copper:** Freerouting 2.4.1 can route over locked tracks and vias of any net, including the decoupling-cap vias and the hand-routed power and gate-drive copper. Switching the DSN's `fix` to `protect` doesn't help.
    - After the run, any `shorting_items`, `tracks_crossing` or `clearance` error between a new track or via and locked copper means this happened.
    - Undo (File → Revert; after a live run, Edit → Undo, step 4) and tell the user. Those nets need rule areas that keep tracks out over the locked copper, or routing by hand around it.
  - **A 4-layer board's GND plane layer stays a plane.** If tracks land on the plane layer (e.g. In1.Cu), the plane was routed over: undo and say so.
- **3D models:** check that the footprints still have their 3D models (`get_component_properties` or the 3D viewer). If they are missing, tell the user to run **Tools → Update Footprints from Library** with **Reset 3D models** ticked. It restores them without moving the parts.

## 4. Route
- **Load the saved board:** `autoroute` reads the `.kicad_pcb` file, not KiCad's live copy. After live edits (placement, new pours), save first (`save_board`, or ask the user to press Ctrl+S), then call `open_board` with the board path so the router sees them. Also call `open_board` if `autoroute` says "No board is loaded". On large boards it can take over 30 s and time out once; retry once.
- **Baseline DRC:** run `run_drc` once before routing, so new errors can be told apart from old ones.
- **Estimate the run time:** check the ratsnest (`get_ratsnest`) and tell the user how many connections are open. Freerouting 2.4.1 needs seconds for a small 2-layer board, about 2 minutes for a 2-layer ESP32 board with ~85 nets, and several minutes per attempt for a dense 4-layer one.
- **Timeout:** set `timeout` from that estimate. Allow 600 s per attempt for dense boards and 900 s for very dense ones; the 300 s default is often too short.
- **Best-of-N:** for a first run, use `attempts: 1` with the default `maxPasses` (20). Only use `attempts: 3` (or 5 for dense boards) when the user wants the most complete result and accepts the extra time; each attempt varies the max passes and the most complete result is kept.
- **Live:** when the board is open and saved in KiCad's PCB editor and the run is a single attempt, pass `live: true`. Tell the user they can watch the routing appear in KiCad: Freerouting's partial result replaces the previous one every 2 s (`liveInterval`). At the end the result is put into KiCad's board and saved there, so the run itself needs no File → Revert.
  - Existing and locked copper isn't touched. Zones aren't refilled; that's step 5.
  - Each update is one undo step in KiCad. To undo the whole run, use Edit → Undo until the "Freerouting" steps are gone, then save.
  - Not with `attempts` > 1 (refused), not in Docker, and not without KiCad open: use a normal run then.
- **Pour nets:** always pass `pourNets` for GND and `keepoutPourNets` for the outer-layer power pours (step 3).
- **Priority nets:** put signal nets that must be completed (e.g. MCU control, communication) in `targetNets`.
- **If it times out:** say so plainly. Nothing is imported and the board is unchanged. Offer a longer timeout, routing more nets by hand first, or adding the missing pours.

## 5. Check the result against the rules (§3.3–3.7)
- **Clean up first:** run `clean_up_routing` right after `autoroute`. Like `autoroute` it works on the saved file. It:
  - removes the router's zero-length and tiny stubs, and tracks with a free end;
  - widens tracks to their net-class width (Freerouting writes every net at the default width, step 2), halfway where the full width breaks DRC, not at all where that breaks it too;
  - chamfers 90° corners to 45° (§3.4), smaller where a full chamfer breaks DRC.

  Every change that adds copper is checked with kicad-cli DRC, zones refilled, and taken back if it adds an error. Locked tracks are never changed. It takes a few DRC runs: about 30 s on a dense 4-layer board. Its `sharp_corners_left` and `thin_tracks_left` lists are the starting point for the corner and width checks below.
  - **After a live run:** `clean_up_routing` changes the saved file, not KiCad's board. Ask the user to use **File → Revert** right after it, before any other edit or save in KiCad. Nothing is lost: the live run left KiCad's board saved.
- **Refill zones:** run `refill_zones`.
- **Look at it** (`powerlab-visual-review`): save, then render top copper, bottom copper and both layers together. Review them for detours, 90° corners, long or looping power and gate-drive paths, and pours chopped into islands. Fix what you see and render again before reporting.
- **Pour-net pads:** in the DRC's unconnected items, find pads of the pour nets that the pour can't reach, e.g. a GND pad boxed in by tracks. Add a via next to each one (`add_via`, 0.4/0.8 mm), connected with a short track, so it reaches the bottom pour. Then refill again.
- **DRC:** run `run_drc` and compare it with the baseline. The goal is **0 new errors**. Track-width or clearance errors mean the net classes don't match the board constraints; fix the rules and re-route rather than hiding the errors.
- **Corners:** Freerouting routes at 45° but still leaves some 90° corners (26 on a test board), and the rules forbid them (§3.4). `clean_up_routing` chamfers the ones that have room. It skips corners where two widths meet, so a narrow chamfer doesn't neck the wider track. List its `sharp_corners_left` for the user, who can fix them with the interactive router or by dragging the corner with `D`.
- **Paths and pad connections (§3.4, issue #21):**
  - Look for tracks that detour or staircase.
  - Look for tracks that touch a pad's edge or clip its corner instead of entering straight and ending at the pad centre.
  - Look for pour slivers or islands between a track and a pad's clearance ring (refill first).
  - Report these and fix them with the interactive router (`X` with walkaround), or by dragging the last segment straight into the pad centre.
  - Dangling stubs (DRC `track_dangling`) should be gone after `clean_up_routing`; remove any that are left.
- **GND tracks:** list the GND tracks (`query_traces`). Every one must be a short pad-to-via stub. A GND track from pad to pad means a pad was routed instead of reaching the pour: remove it, and if the pad is then unconnected, give it a via.
- **Widths and vias on power nets:**
  - check every power and GND track against its class width (`query_traces`). Freerouting routes them at the default width (step 2); `clean_up_routing` widens every segment that has room.
    - A narrower section is only allowed right at a pin that forces it.
    - List the rest for the user.
  - no track below the board minimum: Freerouting necks down to 0.10–0.12 mm at fine-pitch pins (DRC `track_width`). `clean_up_routing` lists the ones it couldn't widen in `thin_tracks_left`.
  - at least 2 vias at each power layer change, 0.4 mm drill (§3.5)
  - no vias in SMD pads except thermal pads
- **Pours and stitching:** after the pours are filled, save the board (Ctrl+S, or `save_board`), then add GND stitching vias every ~5 mm with `add_gnd_stitching_vias` (`strategies: ["grid", "in_zones"]`, `viaSize: 0.8`, `viaDrill: 0.4`; §3.5). With KiCad open, it plans on the saved file and places the vias live, keeping the board's largest net-class clearance. Remove copper islands or stitch them to GND (§3.3).
- **High-speed:** no clock or fast signal crosses a gap in its reference plane, and none changes layer unless it must (§3.4). Freerouting adds vias freely; list fast signals that got vias.
- **Magnetics and switching (§3.4):** no track runs under an inductor or transformer body, and no gate-drive or other switching track runs on the same layer as the high-current copper beside it. Freerouting doesn't know either rule. List what you find and reroute it by hand. For the next run, the user can draw a rule area (Place → Add Rule Area, keep out tracks) over each magnetic part.
- **Unrouted nets:** report what is still unrouted (`get_ratsnest`). Name the nets and suggest finishing them by hand.
- **Optional:** render the top and bottom with `kicad-cli pcb render` so the user can look at the result.

## 6. Tell the user
- **How it went:** say how many nets were routed and how many are left, plus the DRC result compared with the baseline and the rule checks from step 5.
- **Reload:** after a live run, the routing is already in KiCad and saved; only the reload after `clean_up_routing` (step 5) is needed. After a normal or best-of-N run, or a run without KiCad open, the board file changed, so the user must use **File → Revert** in KiCad to see it (unsaved edits are lost; that's why step 3 asks them to save).
- **Finish:** suggest teardrops (Edit → Edit Teardrops, §3.4) once routing is final.
- **Review:** remind them that autorouted power-electronics boards need a human review against the §3.7 checklist before ordering. That includes loop areas, return paths, track widths on high-current nets, and via counts on power paths. Once they have reverted, offer the design review (`powerlab-design-review`) with a `<choices>` button: it checks the routed board against the lab rules and the review handbook, fixes what it can, and writes a review with a PDF.
