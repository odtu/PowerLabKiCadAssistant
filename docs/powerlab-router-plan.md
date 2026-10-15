# PowerLab router: design plan

Status: plan, nothing built yet. Phase 1 (pad-centre entry and shortcuts in `clean_up_routing`) is on hold.

## 1. Why

Freerouting 2.4.1 finishes boards, but the result breaks the lab rules (design rules §3.3–3.5):
- **Pad entry:** a pad counts as connected as soon as copper touches its edge, so tracks clip pad corners and sides instead of entering straight and ending at the centre.
- **Detours and staircases:** the optimiser shortens tracks, but not to the lab's "shortest path, fewest corners".
- **Widths:** it routes every net at the default width, even when the DSN asks for the Power class (issue #21).
- **No lab judgement:** it can't be told "no tracks under inductors", "switching tracks off the high-current layer", "keep fine-pitch escape lanes free" or "high-speed signals without vias".
- **No order:** it routes every open connection at once in passes, then reshapes everything. In live mode that looks random. The lab order (§3.4) is power → gate drive and clocks → differential pairs → sensitive analog → the rest.

`clean_up_routing` fixes widths, stubs and 90° corners afterwards, but routing well from the start beats repairing afterwards.

## 2. What it is

A kicad MCP tool, `powerlab_route`, that routes the board on the user's computer in KiCad's Python, with the lab rules built into the search.
- **Tokens:** Claude sets up the rules and net classes (as the autoroute skill does today), calls the tool once and reads a short report. Routing costs no tokens. Routing by hand with `route_trace` costs a tool call per segment.
- **Freerouting stays** as the fallback for connections the PowerLab router can't finish, and as the comparison in the benchmark (§9).
- **Dependencies:** none new. KiCad 10's Python has numpy 2.4.2 and Pillow 12.3; it has no scipy or shapely, so the code mustn't need them.

**Not in version 1:** length matching and impedance control, arcs, push-and-shove, blind/buried vias (the lab never uses them), BGA escape, HV creepage beyond the net-class clearance.

## 3. Inputs

- **The board:** the saved `.kicad_pcb`, like `autoroute`. With the board open in KiCad, copper is also shown live (§6).
- **Rules:** net classes from the `.kicad_pro` (width, clearance, via size) and the board constraints. Clearance between two nets is the larger of their classes', like KiCad.
- **Copper that stays:** locked tracks and vias, pours, rule areas (keepouts), NPTH holes, the board edge (0.5 mm, §2.6).
- **Pour nets:** `pourNets` (not routed; the pour connects them) and `keepoutPourNets` (not routed; their pour outline is an obstacle on its layer), as in `autoroute`.
- **Groups:** which nets are power, switching, clocks, differential pairs and sensitive analog (§5). Found automatically, shown to the user by Claude, and corrected through a `groups` parameter.

## 4. How it routes

### 4.1 Board model
- **Grid:** one occupancy grid per copper layer, 0.1 mm pitch, built with numpy and Pillow (as in the lab's `maze_export.py` / `maze.py`). The 0.05 mm grid of `maze.py` is 4× slower and isn't needed: the grid only steers, and exact geometry decides (4.5).
- **Obstacles:** every item of another net is grown by the clearance to the net being routed plus half its track width, so the search only has to treat the track as a line. A second set, grown by the via radius, says where vias may go.
- **Updates:** after each routed connection, its copper is stamped into the grids; after a rip-up, it's erased. Nothing is rebuilt from scratch.

### 4.2 Connections
- For each net, find the copper islands that are already connected: pads, tracks, vias and pour fills that touch, like KiCad's connectivity (the union-find in `maze_export.py`).
- Join the islands with a minimum spanning tree. Each tree edge is one connection to route, between the two nearest pads of the islands.
- Pour nets are skipped. A net that is already complete is skipped.

### 4.3 Order
Groups are routed one after the other in the §3.4 order, and you see each group appear in KiCad:
1. **Power tracks** where no pour fits (Power class, `+*`, `-*`, `VBUS*`), at the class width.
2. **Switching and clocks:** gate drive, PWM, bootstrap, switch-node sense, clocks.
3. **Differential pairs:** in version 1, both lines routed next to each other with the same path shape, no length matching.
4. **Sensitive analog:** current sense, Kelvin, references, ADC inputs.
5. **Everything else.**

Inside a group: connections at fine-pitch parts first (they have the least room), then the shortest first.

### 4.4 Path search
A* over (x, y, layer, direction):
- **Moves:** 8 directions; a turn is 45° at most per step, so 90° corners can't be made. Each turn costs extra, so paths are long straight runs.
- **Vias:** through vias only, at the net class's size. Not inside SMD pads, at least 0.25 mm from a pad edge (§3.5). A layer change on a power net places 2 vias side by side across the current flow.
- **Hard blocks:** clearances, keepouts, `keepoutPourNets` outlines, the board edge, NPTH holes, and on a 4-layer board the GND plane layer.
- **Costs that steer it (the lab rules):**

  | Rule (design rules) | Cost |
  |---|---|
  | Short and direct (§3.4) | length, plus each turn |
  | Few vias; none on high-speed signals (§3.4, §3.5) | via cost, much higher for clocks and switching nets |
  | No tracks under inductors, transformers, chokes (§3.4) | very high inside their courtyards, on every layer |
  | Switching tracks off the high-current layer (§3.4) | high on a layer where that area has a power pour |
  | Fine-pitch escape lanes stay free (§3.4) | high for other nets within ~1.5 mm in front of fine-pitch pins |
  | 3W around clocks; no clocks along the board edge (§3.4) | extra near clock tracks and the edge |
  | No high-speed track over a gap in its reference plane (§3.4) | high where the plane underneath has no copper |
  | Bottom-layer tracks on a 2-layer board stay short (§3.4) | extra per mm on the bottom layer |

  The costs are numbers in one table, so they can be tuned in the benchmark (§9).
- **Search window:** each connection searches a box around its two ends with a margin; the box grows if no path is found. Measured in KiCad's Python: a plain-Python A* with direction states does about 220–270 k steps per second, so a 40 × 40 mm window costs well under a second when it's open and a few seconds when it's crowded.

### 4.5 Pad entry, built in
- Each pad gets **entry lanes:** straight out of the pad along its axis, square to the edge, on the pad's layers. On fine-pitch parts only the outward lane is allowed.
- The search starts and ends on those lanes, and the track runs to the pad centre. Every track then ends straight at the pad centre, and there are no pour slivers next to pads (§3.3, §3.4).
- **Exact check:** the grid path is turned into segments (straight runs merged), their ends are snapped to pad and via centres, and each segment is checked against the real shapes with pcbnew (`TransformShapeToPolygon` / `Collide`, as in `maze_export.py`). A segment that fails is searched again with that spot blocked.

### 4.6 When a connection is blocked
Rip-up and reroute, limited:
- Find what blocks it: the copper of other nets in the way of the cheapest path that ignores routed copper.
- Rip up the blocking connections, but only from the same or a later group. Locked copper and earlier groups are never ripped up, so the lab order holds.
- Route the blocked connection, then the ripped-up ones. Each rip-up raises a "history" cost on the cells involved, so the same fight doesn't repeat (the PathFinder idea).
- Stop after a set number of rounds. What's left is reported, not forced.

### 4.7 Finish
- **Shortcut:** from each point of a run, jump to the farthest later point that a clear straight or straight-plus-45° path reaches (the `track_opt.py` method). This removes the remaining detours and staircases.
- **Corners:** chamfer whatever corner of 90° or less is left, as `clean_up_routing` does.
- **Widths:** already at the class width from the start. A neck-down only happens right at a pin that forces it, and widens again right after.

### 4.8 Check
- Run kicad-cli DRC with zones refilled and `--all-track-errors` before and after, with the `Drc` class from `route_cleanup.py`.
- A connection whose copper adds a DRC error is taken out and listed. The goal is 0 new errors.

## 5. Groups from the board

- **Power:** the Power/GND/HV net classes, plus the §1.6 patterns `+*`, `-*`, `VBUS*`.
- **Switching:** nets on gate-driver output pins, MOSFET gates, `*GATE*`, `*PWM*`, `*BOOT*`, `*SW*`, `*_HO*`/`*_LO*`.
- **Clocks:** `*CLK*`, `*SCK*`, `*XTAL*`, crystal pins.
- **Differential pairs:** KiCad's `_P`/`_N` and `+`/`-` suffix pairs, `USB_D±`, `CAN_H/L`.
- **Sensitive analog:** `*SENSE*`, `*SNS*`, `*ISEN*`, `*REF*`, `*ADC*`, `*AIN*`, nets at shunt pads.

Claude shows the groups to the user before routing, and the user can move nets between them. Names alone aren't enough on every board, so the pin types and part types (driver, MOSFET, shunt, crystal) count too.

## 6. Live display, backup and undo

- **Live:** with the board open in KiCad, each group's copper is pushed into KiCad as it's finished, using `LiveCopper` from `freerouting_live.py` (one commit per update). The user watches power appear first, then switching, and so on. At the end it's saved through KiCad, as in Freerouting's live mode.
- **Backup:** the saved board before the run is kept in `autoroute-backup\`, and `undo_autoroute` puts it back (already built for `autoroute`).

## 7. Tool and report

`powerlab_route` parameters:
- `boardPath`, `pourNets`, `keepoutPourNets`: as in `autoroute`.
- `groups`: changes to the automatic groups.
- `nets`: route only these nets; default all.
- `live`: as in `autoroute`.
- `timeout`: overall limit, default 600 s.
- `ripupRounds`: default 5.

The report, kept short for Claude:
- per group: connections routed and left;
- for every connection left: the net, both ends, and what blocks it (net names and the area, as `kicad:` links the panel can open);
- DRC compared with before, total track length, via count;
- the lab checks: corners of 90° or less (0), tracks not ending at a pad centre (0), tracks under magnetics, switching tracks on a high-current layer, fast signals with vias.

## 8. Code

- **In the MCP patch:** `python/commands/powerlab_router/`, plus the tool in `kicad_interface.py` and `src/tools/freerouting.ts`. It needs the board, kipy and the live code, which live there.
  - `model.py`: board → connections, groups, obstacle shapes (pcbnew).
  - `grid.py`: rasterising and stamping (numpy, Pillow).
  - `search.py`: A*, entry lanes, costs. **No pcbnew**, so it can be tested in the repo's tests without KiCad, and timed.
  - `ripup.py`, `finish.py`, `report.py`.
- **Tests** in `tests/test_assistant.py`, loading the new files from the patch like `test_clean_up_routing` does. They cover a 90° corner that can't happen, straight pad entry, the group order and rip-up that doesn't touch earlier groups, plus one small board routed end to end with DRC.
- **Patch size:** this roughly doubles `patches/kicad-mcp.patch`. If that gets unwieldy, the router can move to its own folder in this repo, with `install.ps1` copying it next to the MCP. Decide at milestone 2.

## 9. Benchmark and when it becomes the default

Boards:
- TestPCB: 2 layers, 33 footprints, 44 nets.
- ESP32 motor driver: 2 layers, about 85 nets.
- EncoderSignal: 4 layers, 154 footprints, 96 nets.

Each one is routed by:
- Freerouting + `clean_up_routing`;
- the PowerLab router;
- the PowerLab router + Freerouting for what's left.

Measure:
- connections routed;
- new DRC errors;
- track length and vias;
- the lab checks from §7;
- run time.

The PowerLab router becomes the skill's default on a board type when it:
- routes at least as many connections as Freerouting, or leaves at most a few that Freerouting then finishes;
- adds 0 new DRC errors;
- passes every lab check;
- finishes within about twice Freerouting's time.

Until then it's opt-in.

## 10. Milestones

0. **Spike:** grid, A* and entry lanes for one net on TestPCB. Time it and render it (`powerlab-visual-review`). Decide the grid pitch.
1. **Core, 2 layers:** connections, groups and order, search with pad entry, exact check, DRC, report. Signal and power tracks, no rip-up.
2. **Finishing:** rip-up and reroute, shortcut and chamfer, live display, backup and undo.
3. **Lab costs:** magnetics, switching off the high-current layer, escape lanes, clocks (3W, edge), plane gaps.
4. **4 layers and power:** inner layers, the GND plane as a block, via pairs on power layer changes, differential pairs routed together.
5. **Benchmark, then the skill:** run §9. Teach `powerlab-autoroute` to use the PowerLab router (opt-in or default, from the results), with Freerouting for leftovers.

Each milestone ends with tests passing, a commit to `test` and rendered views of the benchmark boards.

## 11. Risks and open questions

- **Completion on dense boards:** a router with a fixed order completes less than Freerouting's free-for-all on crowded 4-layer boards. The Freerouting fallback (§2) covers that, and the report says what it couldn't do.
- **Speed:** plain Python is fine for 2-layer boards with search windows. If 4-layer boards are too slow: coarse-then-fine search (1 mm grid for the corridor, 0.1 mm inside it), or later a compiled core, which would need a pinned download in `install.ps1`.
- **Off-grid pads:** pads don't sit on the 0.1 mm grid. Entry lanes start from the pad centre in exact coordinates and join the grid a few cells out; the exact check (4.5) catches what the grid misses.
- **Groups by name:** wrong on boards with unusual names, so the user confirms them (§5).
- **Decisions for the maintainers:**
  - the tool name;
  - whether version 1 is 2-layer only;
  - opt-in or default after the benchmark;
  - keep it in the patch or move it to its own folder (§8).
