---
name: powerlab-autoroute
description: Route a KiCad PCB the METU Power Lab way, by hand with the kicad MCP tools (the PowerLab router is switched off for now). Use when the user asks to route, autoroute or auto-route the board, the remaining nets or some signals, or to run the PowerLab router. Covers setting the lab design rules and net classes first, power pours, GND pours with thermal reliefs, protecting hand-routed power and gate-drive nets, live routing in KiCad, finishing what the router leaves by hand, stitching vias, DRC, and the design review that always follows.
---

# Routing: the PowerLab router or by hand

**The lab design rules come first.** Before anything else, load the `powerlab-pcb-design-rules` skill. Every width, clearance, via and routing-order decision below comes from it: §2.6 for constraints and net classes, §3.3 for pours and high-current copper, §3.4 for routing, §3.5 for vias. A router only routes as well as the rules it is given.

> **The PowerLab router is switched off for now** while it gets more local testing: the panel blocks `powerlab_route` and `powerlab_route_status`. Route by hand. Skip the question in §0 and all of §3, don't offer the router, and if the user asks for it, say it isn't available yet. Where a step below says "the router", you do it by hand. (`undo_autoroute` still undoes an earlier router run.)

## 0. Ask first: by hand or the PowerLab router
Ask this before anything else, as one `<choices>` question, unless the user already said which (skip it while the router is switched off):

```
<choices>
How should I route the board?
- PowerLab router, then I fix its DRC errors by hand (Recommended)
- By hand
</choices>
```

- **PowerLab router (`powerlab_route`):** the lab's own router, on the user's computer in KiCad's Python. It applies the lab rules while it routes:
  - power rails first, at their net-class width, then a copper pour round each rail's tracks (power polygons, §3.3), above the GND pour;
  - GND pours kept whole (§3.3); no tracks under inductors and transformers (§3.4);
  - escape room at fine-pitch pins, escape vias at the pins;
  - keepouts: rule areas, footprint keepouts and the `.kicad_dru` clearance rules;
  - buses between two pin rows as parallel runs; few corners and few vias; pads entered at their centres, straight or at 45° where the pad isn't fine pitch;
  - a net's later tracks join its earlier ones (a T-junction away from the pads) instead of running a second track beside them; overlapping tracks of a net are merged;
  - a second look at tracks that go a long way round;
  - GND stitching vias at the end (§3.5).

  It takes about 10–15 minutes for a 2-layer board with ~50 connections and runs in the background. With the board open in KiCad, the user watches the copper appear.
- **By hand:** you draw every track and via with the kicad tools (`route_pad_to_pad`, `route_trace`, `add_via`), net by net in the §3.4 order. Slower, and costs many tool calls, but every decision is yours. Use it for small boards or when the user wants it.

Freerouting isn't part of the assistant any more. Never offer it.

## 1. Set the rules (design rules §2)
Ask for whatever you can't read from the board, and don't guess currents or voltages.
- **Copper weight and layer count:** confirm them, because they change every limit (§2.0–2.2). The default is 2 layers and 1 oz.
- **Board constraints (§2.6):** check them with `get_design_rules`. For 1 oz copper they should be the values below.
  - If they differ (KiCad's defaults are minimum clearance 0, track 0.2, annular ring 0.1, via 0.5), call `set_design_rules` with `preset: "powerlab"` (`copper: "2oz"` for 2 oz). It writes the constraints, the Default class and the Power/GND classes into the project, and the minimums into the `.kicad_dru`, which DRC reads on every run, so DRC enforces them at once.
  - **With KiCad open**, KiCad 10 only reads the new Board Setup values when it opens the project. Tell the user once: Board Setup shows them the next time they open the project, and pressing OK in Board Setup before then writes the old values back. Don't ask them to close anything. Until then KiCad still routes with its old classes, so pass `width` on every track (0.15 mm signals, the class width for power). Check the files with `get_design_rules`.
  - The values:
    - minimum clearance 0.15 mm, minimum track 0.15 mm, minimum connection 0.15 mm. These are the PCBWay standard-price floor; signals are routed at it too (the Default class below).
    - via 0.6 mm, through hole 0.3 mm, annular ring 0.15 mm
    - copper to hole 0.25 mm, copper to edge 0.5 mm, hole to hole 0.4 mm
    - no micro or blind vias
- **Net classes (§2.6):** the router routes every net at its class's width, clearance and via. Create them with `create_netclass` (its `nets` list) or `assign_net_to_class`. Both take net names, not patterns, so list the nets with `get_nets_list` and pick the ones matching the §1.6 patterns `*GND*`, `+*`, `-*`, `VBUS*`:

  | Class | Track | Clearance | Via drill / pad |
  |---|---|---|---|
  | Default | 0.15 mm | 0.2 mm | 0.3 / 0.6 mm |
  | Power, GND | width for the current, at least 0.5 mm | 0.3 mm | 0.4 / 0.8 mm |
  | HV (> 50 V) | width for the current | from the §3.3 voltage table | 0.4 / 0.8 mm |

  - **Power widths:** ask the user for each rail's current, then size the track from the §3.3 table. On 1 oz outer copper that is 0.3 mm for 1 A, 0.8 mm for 2 A and 1.4 mm for 3 A. Above about 3 A the net belongs in a pour, not a track.
  - **Never route a power net at the default width.**
- **Schematic `LAYOUT:` notes:** collect them, because they are requirements too (§1.7). Typical ones are hot loops, Kelvin connections and impedance.

## 2. Make sure the board is ready (design rules §3.1–3.3)
- **Saved:** the board is saved in KiCad. The router routes the saved `.kicad_pcb`.
- **Outline and placement:** a closed board outline on Edge.Cuts, every footprint inside it. Placement decides the result far more than any router. **Render a placement view first** (`powerlab-visual-review`), look at it, and fix the placement before routing: decoupling caps at their IC pins, crystals at the MCU, analog, digital and power sections apart, assembly spacing. **Run `check_part_spacing`** (with the requirement keep-outs) and fix what it lists first: parts packed pad to pad leave pads no way out, and the router then reports "no free entry lane" for them.
- **Copper first (§3.3), then route in the §3.4 order:**
  1. **Power pads and high-current paths:** every power pad gets its copper area first (MOSFET, diode, inductor, shunt, bulk-cap, regulator and power-connector pads): a pour sized for its current. These are drawn by you, with `add_copper_pour` and an `outline`, before routing.
  2. **Gate-drive loops and clocks:** driver → gate → source return, short with a small loop, off the layer that carries high-current copper there (§3.4). Route these by hand and lock them.
  3. **Differential pairs**, 4. **sensitive analog** (current sense, Kelvin, references): by hand and locked where they matter.
  5. **Everything else:** the PowerLab router (or by hand).

  Locked copper is kept: the router leaves nets with locked copper out and routes around it. Steps 1–4 are routed by hand first on a power board. If they aren't done, say so and recommend doing them first.
- **Power rails (§3.3, "power rails are copper areas, not traces"):** low-current rails (+3V3, +5V, VBUS…) may be left to the PowerLab router: it routes them first at the Power class width and then gives each one a pour round its tracks (`powerPours`, default on). A rail you already routed by hand gets the pour too. Only high-current power rails connect pads solid (`solidPourNets`); everything else uses thermal reliefs, and GND always does.
- **GND (§3.3):** GND is a pour, never tracks.
  - **Check for existing pours first** with `query_zones`. Never add a second pour for the same net on a layer that already has one ("zones intersect" in DRC).
  - If the board has no GND pour, create one before routing with `add_copper_pour` on the bottom layer and on the top (leave out `outline` to cover the whole board; on 4 layers, the inner GND plane layer). **GND pours connect pads with thermal reliefs** (`padConnection: "thermal"`, the default) so the pads can be soldered, **every GND pour and plane, also round high-current GND pads** (give those wider spokes instead). Solid connection (`padConnection: "solid"`) is only for high-current power pours (DC bus, switch node, phase). Check existing GND zones with `query_zones` and set any solid one to thermal with `edit_zone`.
  - **No GND fan-out before routing:** never give every GND pad a via up front. Only decoupling caps get a via at their GND pad now (lock it). A fine-pitch IC GND pin next to a GND exposed pad joins the pad straight across, without a via.
- **3D models:** if footprints lost their 3D models, tell the user to run **Tools → Update Footprints from Library** with **Reset 3D models** ticked.

## 3. Route with the PowerLab router
*Switched off for now: skip this section and route by hand (§4's rules apply to every connection).*

- **Saved board:** with the board open in KiCad, `powerlab_route` refuses to start while KiCad has copper or footprint changes that aren't saved: ask the user to press Ctrl+S, then call it again.
- **Baseline DRC:** run `run_drc` once before routing, so new errors can be told apart from old ones. The report also lists the new DRC errors it found itself.
- **Which nets:** by default every Default-class net (routed from scratch: their unlocked tracks and vias are removed first), plus the nets of other classes that have no tracks yet (e.g. power rails). Nets with locked copper, pour nets and other-class nets that already have tracks are left out; the report lists them under `nets_left_out`. Pass `nets` to route fewer or to route a hand-routed rail again.
  - `pourNets` defaults to `["GND"]`: never routed, the pours connect them.
  - Leave the costs at their defaults unless the user asks: `turnCost` (higher: fewer corners), `viaCost` (higher: fewer vias), `diagonalCost`, `layerCosts` (top first) and `gridPitch` (0.1 mm).
  - `stitchPitch` (default 5 mm, §3.5) sets the GND stitching vias; `0` turns them off.
  - **Layers:** it routes on every copper layer except inner planes (inner layers mostly covered by zones, e.g. a 4-layer board's GND and power planes); vias pass through them. `routeLayers` picks the layers by name.
  - **Time limit:** the routing stops after `timeLimit` minutes (default 15). The connections left are reported with the reason "time limit", and the run still finishes what it has (pours, stitching), so you can finish by hand. On a big board (more than ~100 connections, 4 layers) say so before starting.
- **Run it:** call `powerlab_route`. It returns at once. Tell the user it takes about 10–15 minutes on a 2-layer board with ~50 connections, that with KiCad open they can watch the tracks appear (the pours are unfilled while it routes and refilled at the end), and that they shouldn't edit or save the board until it's done: a board changed during the run isn't overwritten, so the run would be wasted.
- **Wait:** call `powerlab_route_status` (it waits up to `wait` seconds, default 300) until `state` is no longer `running`. Between calls, tell the user the progress (`routed` of `connections`, `per_minute`, `eta_minutes`, `phase`). `cancel: true` stops the run; KiCad's board is put back as it was saved.
  - **Stalled** (`stalled_seconds` in the status: nothing routed for 3 minutes): don't keep waiting silently. Tell the user what it's stuck on (`last`; "no free entry lane" means pads boxed in by the placement) and ask: let it run to its time limit and finish the rest by hand, or cancel and fix the placement first.
- **The result:** when the run is done, `powerlab_route_status` puts it on the board. With KiCad open, the copper goes into KiCad's board, the zones are refilled and the board is saved there (no File → Revert). Without KiCad, the routed board is written to the file. Its report: connections routed and `left` (with the reason), T-junctions, power pours, stitching vias, track length, `new_drc_errors` and time.
- **Undo:** each run keeps the saved board from before it in `autoroute-backup\`; `undo_autoroute` puts it back (once, the last run only; everything done after the run is lost too). With KiCad open it puts the old copper back in KiCad and saves there.

## 4. Finish by hand
The router never forces a connection. Whatever it leaves, and every DRC error it adds, you fix yourself, as a person would:
- **Connections left (`report.left`):** route each one by hand with `route_pad_to_pad` or `route_trace` (and `add_via` where it must change layer), at the net's class width, following §3.4: straight into the pad centre, 45° corners, no detours.
- **Drawing a track by hand** (every connection while the router is off):
  - **Only 0°, 45° and 90°.** Plan the run as straight pieces joined by 45° bends: out of the pad along its axis, a 45° bend, straight on, a 45° bend, straight into the next pad's centre. Never draw a connection as one slanted line between two points that aren't in line, and never join two pieces at 90°: cut every corner at 45°.
  - **One call per run:** pass the bends as waypoints to `route_trace` (or use `route_pad_to_pad`) so the run is drawn in one piece, rather than many short calls whose ends meet at odd angles.
  - **Same-net neighbours directly:** a decoupling cap and its IC pin, two caps in parallel, a bead and its cap: one short straight track pad to pad. Never round the part, out and back, or through a via when the direct track is free.
  - **Buses together:** lines that run side by side (SPI, JTAG, a parallel bus) keep one pitch and bend together. Draw the outer line first and the others parallel to it, so none takes a kink or a different angle.
  - **Signals at 0.15 mm** (the Default class); power at its class width.
  - **Check after each block:** save, run `check_routing` for that block's nets and redraw whatever it lists (off-angle pieces, corners, kinks, detours, off-centre pad entries) before moving on.
- **DRC errors:** run `run_drc` and compare with the baseline. Fix every new error: move or reroute the track, nudge a via. The goal is **0 new errors**. Track-width or clearance errors usually mean the net classes don't match the board constraints: fix the rules and route again rather than hiding the errors.
- **Pour-net pads the pour can't reach** (unconnected in DRC, e.g. a GND pad boxed in by tracks): give that pad a via (0.4/0.8 mm) next to it with a short stub, then refill.
- **Removing copper:** with KiCad open, `delete_trace` deletes in KiCad's board (by `traceUuid` from `query_traces`, by `position`, or every track of a `net`); a point on a via deletes the via. It refuses locked copper. `modify_trace` still doesn't reach KiCad's board: delete and route the track again instead.

## 5. Check the result against the rules (§3.3–3.7)
- **Measure it:** save and run `check_routing` on the whole board. Fix everything it lists; a detour you keep on purpose (a gate-drive loop round a via row) goes in the review with the reason.
- **Look at it** (`powerlab-visual-review`): render top copper, bottom copper and both together. Look for:
  - corners that serve nothing, wiggles round pads, stair-steps, U-turns or loops round a via or pad;
  - two tracks of one net side by side, or on top of each other;
  - tracks that bend just before a pad instead of going straight in (at 45° where the pad isn't fine pitch);
  - power rails without their pour, pours chopped into islands, slivers next to pads.
  Fix what you see and render again before reporting.
- **GND tracks:** list them (`query_traces`). Every one must be a short pad-to-via stub. A GND track from pad to pad means a pad was routed instead of reaching the pour.
- **Power:** every power track at its class width (a neck-down only right at a pin that forces it), at least 2 vias at each power layer change (§3.5), no vias in SMD pads except thermal pads, and every rail inside its pour.
- **Pours and stitching:** after the fill, check the GND pours are whole and the stitching vias are about every 5 mm (more along the edges and round noisy parts, §3.5). Add any that are missing with `add_gnd_stitching_vias` (`viaSize: 0.8`, `viaDrill: 0.4`) and check its list by hand. Remove copper islands or stitch them to GND (§3.3).
- **High-speed, magnetics and switching (§3.4):** no clock or fast signal across a gap in its reference plane or changing layer without need; no track under an inductor or transformer body; no switching track on the layer with the high-current copper beside it.
- **Unrouted nets:** report what is still unrouted (`get_ratsnest`) after your hand routing; it should be nothing.

## 6. Review, then tell the user
- **Always run the design review next, without asking:** load `powerlab-design-review` and follow it: review, fix what you can, check again, and write `design-review\design-review.md`.
- **Then tell the user:** which way the board was routed, connections routed by the router and by hand, DRC against the baseline, the pours and stitching vias, and what the review found. Ask them to look at the board and the review in KiCad, and remind them that a power-electronics board needs a human review against the §3.7 checklist before ordering (loop areas, return paths, high-current widths, via counts on power paths).
- **Finish:** suggest teardrops (Edit → Edit Teardrops, §3.4) once routing is final.
