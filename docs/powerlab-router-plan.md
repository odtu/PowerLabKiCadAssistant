# PowerLab router: design plan

Status: milestones 0–4 done (results in §12–16). The router isn't a tool yet: its code is in the MCP patch (`python/commands/powerlab_router/`), and `tools/router_bench.py` runs it. Phase 1 (pad-centre entry and shortcuts in `clean_up_routing`) is on hold.

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

## 12. Milestone 0 results (2026-10-15)

**What was built:**
- `grid.py`: rasterising, numpy + Pillow.
- `search.py`: A* with 45° turns, `min_run` between bends, entry lanes as starts and goals, through vias. No pcbnew.
- `model.py`: obstacles from net-class clearances, entry lanes, the grid path snapped exactly onto the pads' axes, an exact pcbnew check, the result as tracks and vias.
- `tools/router_bench.py`: the benchmark. `tools/render_copper.py`: copper views without pours.

**Test:** TestPCB (2 layers, 30 × 55 mm, ESP32 module, USB-C, QFN USB-UART). The 33 Default-class nets were stripped, 52 connections. Power, USB and GND copper stayed. Routed in order of net length, without rip-up. Freerouting + `clean_up_routing` routed the same stripped board.

| | PowerLab router, 0.1 mm grid | PowerLab router, 0.05 mm grid | Freerouting + clean-up |
|---|---|---|---|
| Connections routed | 42 of 52 | 43 of 52 | 51 of 52 |
| Time | 37 s (search 32 s, grids 4 s) | 172 s | 69 s (50 s + 18 s) |
| New DRC errors | 1 (starved thermal) | 0 | 26: 17 clearance, 3 shorts, 3 hole clearance, 1 crossing, 2 starved thermal |
| Pad entry | every track straight into the pad centre | same | header pads entered at 45°; unlocked power tracks reshaped |

On the 27 nets both finished: 394.5 mm against 365.0 mm (+8%), 18 vias against 12, 240 segments against 166.

**Decisions:**
- **Grid:** 0.1 mm. The 0.05 mm grid is 5× slower for one more connection. Exact checks cover the rest:
  - entry lanes are checked against the real shapes;
  - after each connection, the copper is checked exactly. On a clearance error it is routed again with 0.05 mm extra margin, then 0.1 mm. That removed all 3 clearance errors the grid's rounding had caused.
- **Speed:** plain Python is enough for 2-layer boards. The slowest connection took 5 s (430k nodes). Failed searches need a node limit, so they give up fast.
- **Lanes under a part:** allowed, at an extra cost. The ESP32 module's edge pads can only be left under the module. Fine-pitch pins still leave straight out only.
- **"Outward":** measured from the footprint's body centre, not the average of its pads. A USB-C receptacle's pins sit at its back.

**What failed, and the fix:**
- **6 connections:** pins boxed in by nets routed earlier. → Rip-up (milestone 2), and route the most constrained connections first.
- **4 connections at the USB-C and the QFN:** their lanes are squeezed by the copper that stayed, and the grid errs by about a cell there. → Rip-up, and "most constrained first".
- **Small zigzags** where a path joins a pad's lane (2-cell minimum run). → The shortcut pass (4.7).
- **1 starved thermal:** a new track took a GND pad's thermal spokes. → A cost near pour-net pads' spokes (milestone 3).

**Tried and dropped for now:**
- **Longer straight runs and dearer turns** (`min_run` 5, turn 1.0 mm): slower, more vias, more pins boxed in.
- **Reserving other pins' escape lanes** (cost 2 mm per cell): one more connection, but 3.7× slower, mostly in hopeless searches. Try again with node limits and rip-up.

**Added to milestone 1:**
- **Custom rules:** read the board's `.kicad_dru`. TestPCB relaxes pad clearance to 0.15 mm at U3 and J1, and KiCad's DRC engine isn't available from Python. Start with clearance rules by footprint, net class and item type; list the rules the router doesn't understand in the report.
- **Node limit** per search.
- **"Most constrained first"** inside a group.
- **Incremental grid updates** instead of rebuilding the grids for each net.
- **KiCad 10 Python:** use `board.Delete()`, not `board.Remove()` (crashes), and `PCB_VIA.GetWidth(layer)`.

## 13. Milestone 1 results (2026-10-15)

**What was built:**
- `rules.py`: the board's `.kicad_dru` clearance rules, parsed and evaluated in Python. It covers `Type`, `NetName`, `NetClass`, `Width`, `memberOfFootprint` (with wildcards), `hasNetclass`, `isPlated`, `existsOnLayer`, `&&`, `||`, `!` and `(layer ...)`. The last matching rule wins, as in KiCad.
  - A term it doesn't know (e.g. `intersectsArea`) makes the rule "maybe". Such a rule is applied only where it makes the clearance larger, and is listed in the report.
  - It reads the lab's rule files (TestPCB, ESC3Phase, EncoderSignal). Only ESC3Phase's `intersectsArea` rule comes out as not understood.
- **Clearances everywhere follow those rules:** the grids, the exact checks and the lanes. Edge and hole clearance come from the board constraints, not fixed numbers.
- **Incremental grids:** one raster per net and layer for each "key" (net class, track width, via size), plus a count of nets per cell. A net's obstacles are the cells another net covers. Accepted copper is stamped in, and nothing is rebuilt.
- **Node limit:** 1M nodes per search by default. A search that hits it gives up, without trying a bigger window.
- **Groups:** `groups.py` sorts nets into the lab order of §5, which can be overridden per net. `router.py` routes group by group and reports routed/left per group.
- **Lanes:** each lane tries several exit lengths, the preferred one and longer first, then shorter ones down to one track width beyond the pad. A USB-C pin had free space only 0.2–0.4 mm beyond its tip.
- **Tests:** rules (precedence, layer clause, wildcards, "maybe" terms) and groups.

**TestPCB, same benchmark as milestone 0:**

| Setting | Routed | Time | New DRC errors | Track, vias |
|---|---|---|---|---|
| M0: length order, rebuilt grids, 600k-node search without limit stop | 42 of 52 | 37 s | 1 (starved thermal) | 402 mm, 18 |
| M1: most constrained first | 42 | 40 s | 0 | 389 mm, 21 |
| M1: most constrained first + reserved lanes of waiting pins | 42 | 32–39 s | 2 starved thermal | 391 mm, 17 |
| M1: length order | 43 | 47 s | 0 | 371 mm, 14 |
| M1: length order + reserved lanes | 43 | 70 s | 1 starved thermal | 379 mm, 16 |
| **M1 default: length order, 1M-node limit** | **44** | 74 s | **0** | 410 mm, 15 |
| Freerouting + `clean_up_routing` | 51 | 69 s | 26 (17 clearance, 3 shorts) | — |

**What this showed:**
- **Most constrained first doesn't pay on this board.** Length order routes as many or more, with shorter tracks and fewer vias. Lane counts at the start don't predict which pins get boxed in later.
- **Reserving waiting pins' lanes doesn't help either.** Most connections can't get around the reserved lanes and go through them anyway. Both stay as options (`order`, `reserve`) to try again with rip-up. The default is length order without reservation.
- **The node limit** trades time for connections: 600k nodes gives 43, 1M gives 44, 1.5M gives 44.
- **One hopeless search** (`J1.A5`, its lane leads into a pocket next to a via) still costs 13 s. Milestone 2 should notice an enclosed lane exit before searching.
- **What's left is rip-up work.**
  - 5 ESP32 module pins: the channel between the module and the 2.54 mm headers is full.
  - 2 QFN pins.
  - 1 USB-C pin.

  Every one is "no lane" or "no path" after other nets took the space. Next is milestone 2: rip-up and reroute, then the shortcut pass.

## 14. Milestone 2 results (2026-10-15)

**What was built:**
- **Rip-up and reroute** (`router.py`), when a connection finds no way:
  - It searches again with the router's copper of the same or later groups passable at a cost: 1 mm per cell, `SOFT`.
  - It rips up the connections whose copper the new way touches, takes the way, and queues those connections again.
  - Never ripped up: copper of earlier groups, the board's own copper, and a net that also has copper that may not be ripped.
  - Limits: a connection is ripped up at most 3 times and rips others up at most 3 times, with 2 rip-ups per connection overall.
  - Cells fought over get a growing history cost (PathFinder).
  - If the rip-up search finds a way that touches no copper at all, it is kept as it is. The normal grid had been too pessimistic at a pin.
- **Grids:** the board's own copper and the router's are kept apart (`model.py`), so the router's copper of chosen nets can be "soft" for that search. A grid created mid-run, e.g. for a margin retry, knows which copper is the router's.
- **Shortcut pass** (`finish.py`), after routing:
  - It takes the farthest straight or straight + 45° jump that is clear, if it is shorter or as long with fewer corners. A staircase of 45° and 90° steps is as long as one dogleg.
  - Lanes and vias stay. Every corner still turns by 45° at most.
- **Fail fast:**
  - A flood fill notices lanes that open into a closed pocket.
  - The node limit grows with the connection's length: 100k + 40k per mm, at most 1M. A 2 mm connection that needs a million nodes won't find a way. `J1.A5` now gives up in 1.4 s instead of 12 s.
- **Board edge:**
  - The exact checks include it now.
  - The grid's "inside the board" mask shrinks one more cell. Pillow's fill erred outward, and a via landed at 0.45 mm from the edge (minimum 0.5).
- **Thermal spokes:** cells in front of pour-net pads' spokes cost 2 mm per cell, so new tracks keep clear of them.
- **Via cost:** 4 mm of track by default (was 2).
- **Tests:**
  - shortcut;
  - pocket check;
  - penalties;
  - an end-to-end route of a small board: around another net's pad, ends at both pad centres, 45° turns only. It builds the package from the patch.

**TestPCB, same benchmark:**

| | Routed | Time | New DRC errors | Track | Vias |
|---|---|---|---|---|---|
| M1 default | 44 of 52 | 74 s | 0 | 410 mm | 15 |
| M2, via cost 2 | 51 | 168 s | 2 starved thermal | 555 mm | 36 |
| **M2 default, via cost 4** | **51** | **121 s** | 2 starved thermal | 557 mm | 33 |
| M2, via cost 8 | 50 | 125 s | 1 starved thermal | 520 mm | 24 |
| Freerouting + `clean_up_routing` | 51 | 69 s | 26: 17 clearance, 3 shorts, 3 hole clearance, 1 crossing, 2 starved thermal | 503 mm | 15 |

- **Rip-up** ran 12 times and moved 15 connections. It untangled the ESP32 fan-out to the headers, where several pins had been boxed in.
- **The shortcut pass** changed 43 connections: 80 corners fewer, 4.4 mm shorter.
- **Left:** `J1.A5`, the USB-C pin whose only lane leads into a pocket next to a `USB_DP` via. That via is the board's own copper, so nothing may rip it up.

**What this showed:**
- **Completion now matches Freerouting** on TestPCB, with no clearance errors, against Freerouting's 26 DRC errors including 3 shorts.
- **Still behind Freerouting** on:
  - time: 121 s against 69 s;
  - length: about 10% more;
  - vias: 33 against 15.

  Rip-up and history costs push connections onto the other layer. A dearer via trades completion for vias.
- **The 2 starved thermals** are GND pads in pockets of the pour that new tracks cut off from the rest. That is pour integrity, not spokes. The autoroute skill already gives such a pad a via after the zone fill (§3.3). Teaching the router to keep pours whole goes to milestone 3.

**Next (milestone 3), besides the lab costs already planned:**
- keep pours in one piece (cost for cutting a pour-net region off);
- fewer vias, e.g. a rip-up search that may not add vias first;
- speed: incremental lane counts, a coarse corridor search before the 0.1 mm one.

## 15. Milestone 3 results (2026-10-16)

**Goal, from the maintainer:** routing quality counts more than run time (a minute or two is fine), and the lab rules come first. The hand-routed TestPCB was given as an example to learn from, not to copy.

**What the hand routing does well:** `tools/route_quality.py` (new) measured it. It is not the shortest: 625 mm of signal track. Its strength is the GND pours:
- **Top pour:** 91% in one piece.
- **Bottom pour:** 94% in one piece.

How it gets there:
- **Top layer:** only short fan-outs, with a via right at the pin.
- **Bottom layer:** the long runs, packed together in parallel bundles.

Milestone 2 left the top pour at 86% and the bottom at 83%; Freerouting leaves the top at 85%.

**What was built:**
- `costs.py`: the lab rules as per-cell search costs.
  - **Pours stay whole (§3.3):** a cell costs more the farther it is from copper or the board edge, so tracks hug pads, edges and each other.
  - **Thermal spokes** of pour-net pads stay clear.
  - **No tracks under inductors, transformers or chokes** (§3.4), on any layer. The courtyard is grown by 0.3 mm, and the part's own nets are exempt.
  - **Escape room:** 1.5 mm in front of fine-pitch pins (§3.4).
  - **Switching nets and clocks** keep off layers with a power pour there (§3.4).
  - **Clocks:** 3W from other tracks, and off the board edge (§3.4).
  - **Vias:** half price near the connection's own pins (escape vias), 3× on clocks and switching nets (§3.4, §3.5).
- **Pour checks** (`router.py`), measured on a grid of the pour net's own zone clearance and minimum width. It matches KiCad's fill: the largest-piece share is within 1–2%.
  - **Per connection:** if a connection cuts a pour into pieces, it is routed again with the cut cells expensive. The better of the two ways is kept.
  - **After routing:** a repair pass takes out the "walls" (every connection whose copper touches two pieces of a pour), checks that the pour joins, and puts them back one by one. Any that splits it again is rerouted. It is all or nothing per wall: if a connection would be lost or the pour doesn't improve, the wall goes back exactly as it was.
- **Found and fixed on the way:**
  - The shortcut pass only checked clearance, so it straightened tracks back under an inductor. It now uses the search costs.
  - The search widened its window only when it found no way at all, so a way around an inductor outside the first window was never seen. A way much dearer than its length now also tries the next window.
  - A run ending at a via was not moved onto the pad's axis with it, which gave 47–55° corners at off-grid pins. The whole run moves now, via included.
  - Two bugs in the first wall repair could put tracks on top of each other (up to 30 shorts). The repair is now all or nothing.
- **Speed:**
  - The search's heuristic is computed once per window. It had been 410 of 1020 s.
  - The pour measure is cached until the copper changes.
  - `Costs.weight` allows a weighted A*.
- **Tools and tests:**
  - `tools/route_quality.py`: the quality report.
  - The benchmark takes `LAYERS` and `WEIGHT`.
  - New test: a track goes around an inductor, not under it.

**TestPCB.** Pour cells: largest piece share, area in mm², number of pieces.

| | Hand-routed | M2 | **M3 default** | Freerouting |
|---|---|---|---|---|
| Connections routed (of 52) | 52 | 51 | 50 | 51 |
| New DRC errors | — | 2 starved thermal | **0** | 26 |
| Signal length | 625 mm | 557 mm | 602 mm | 503 mm |
| Vias | 23 | 33 | 41 | 15 |
| Track ends off pad centre / at an angle | 12 / 11 | 2 / 1 | 2 / 1 | 22 / 37 |
| Sharp corners (> 45° turn) | 2 | 0 | 0 | 0 |
| Top GND pour | 91%, 808, 5 | 86%, 668, 8 | **93%, 818, 7** | 85%, 675, 14 |
| Bottom GND pour | 94%, 949, 3 | 83%, 958, 3 | **94%, 911, 4** | 100%, 1110, 1 |

**Time:** 458 s with three runs in parallel (863 s before the heuristic fix).

**Tried:**
- **Layer weights:** top 1.3× or 2× with bottom 1×, to copy the hand routing's "long runs on the bottom". The top pour came out larger but cut in two (58%). The default stays top 1×, bottom 1.2×.
- **Weighted A\*:** 1.2 and 1.5 are faster, but cut a pour (58–62%). The default stays 1.0.

**What this showed, and what's next:**
- **Pours now match the hand routing, with no DRC errors.** But the result is fragile: a small change in costs or search weight cuts a pour in two. The wall repair rarely helps in the end (4 walls tried, 0 kept), and the per-connection check does most of the work. Next: make pour integrity part of the search itself, not checks afterwards, so it doesn't depend on order and luck.
- **Fan-outs are untidy:** small hooks and doglegs between the ESP32 module and the left header, where the hand routing has short, even stubs. The quality report doesn't measure that yet. Next: a fan-out pattern (stub, then via or bend, the same for a whole pin row), and a "tidiness" measure.
- **More vias than by hand** (41 against 23), and 2 connections left (`J1.A5` in its pocket, `ESP_TXD0`).
- **Speed:** several minutes per board, against a target of 1–2. The search dominates: the costs make it explore more.
- **Open question for the maintainers:** §3.4 says to keep bottom-layer tracks short on 2-layer boards. The hand-routed example puts long runs on the bottom in bundles and keeps the top for short fan-outs, and that is what keeps the pours whole. Should §3.4 say that instead?

## 16. Milestone 4: route like hand drawing (2026-10-16)

**Why:** the maintainer's verdict on milestone 3 was that it looks like trash, and that the router should think the way a person draws a board.

**What makes hand routing look right:** `tools/route_quality.py` doesn't show it, so the hand-routed TestPCB was taken apart connection by connection. Gaps are measured between parallel long runs.

| | Hand-routed | Milestone 3 |
|---|---|---|
| Segments per net (median) | 6 | 10 |
| Segments shorter than 0.5 mm (jogs, hooks) | 10 | 86 |
| Gap to the neighbouring parallel track | 0.40 mm in 31 of 64 (one track pitch), else the pin pitch (1.27 / 2.54) | 0.6, 0.5, 0.49, 0.8, 0.42… (irregular) |

So a person draws:
- few, long, straight segments;
- parallel tracks side by side at exactly one pitch;
- a group of pins between two parts (a bus) as a group.

The search did none of that. Measured: in 42 of 84 runs a clean shape fitted, but the search's own way scored cheaper. It wove through the lab costs to collect small savings, because a bend cost only 0.4 mm.

**What was built:**
- **Dearer bends:** a bend costs 1.5 mm in the search (`Costs.turn`; it was 0.4).
- **Hand-drawn shapes** (`patterns.py`): every run of the search's way is redrawn as the simplest shape that fits:
  - straight, one bend, or a Z of up to three 45° bends;
  - scored by length, the lab costs, 1.5 mm per bend and 1.5 mm per jog under 0.5 mm.
- **Slivers** (§3.3): next to other copper, a track either hugs it at the clearance or stands far enough off for the pour to fill the gap (two zone clearances plus its minimum width). In between costs the most, so tracks don't leave unpourable strips.
- **Buses** (`router.py`): 3 or more connections between the same two parts are routed together, in the order of their pins along the row, before the other connections.
- **River routing of a bus** (`bus.py`), for two parallel pin rows such as a module and a header:
  - each track leaves its pin straight, bends 45°, runs in the channel between the rows, bends 45° and enters the other pin straight;
  - tracks going down take their slots from the far row inward, one pitch apart, so no stub crosses another's run; tracks going up are the mirror image;
  - a track whose slot is taken by copper steps along the channel until it fits;
  - a bend may start just past a pad's edge, as long as the exact clearance check accepts it (as by hand).
- **Fan-out with escape vias:** the pins that don't fit on the shared layer get:
  - a straight stub to an escape via;
  - all vias in one column beside the pin row. Both sides and four distances are tried, and the one that places the most wins.
  - a river on the other layer from the via column into the far row.
- **Round pads** have no axis: they can be entered straight to the centre in eight directions, not four. A bus track may end with a level run just beside the pin's row and a 45° step into the pin, to pass under copper on that row (as by hand at J2.9).

**TestPCB, full board (same benchmark).** Pour cells: largest piece share, area in mm², pieces.

| | Hand-routed | Milestone 3 | **Milestone 4** | Freerouting |
|---|---|---|---|---|
| Routed (of 52) / new DRC errors | 52 / — | 50 / 0 | **50 / 0** | 51 / 26 |
| Segments | 248 | 409 | **304** | 231 |
| Short jogs (< 0.5 mm) | 10 | 86 | **44** | 46 |
| Corners | 174 | 297 | **201** | 168 |
| Vias | 23 | 41 | **32** | 15 |
| Parallel runs exactly 0.4 mm apart | 31 | under 5 | **18** | 4 |
| Top GND pour | 91%, 808, 5 | 93%, 818, 7 | **98%, 843, 3** | 85%, 675, 14 |
| Bottom GND pour | 94%, 949, 3 | 94%, 911, 4 | **98%, 976, 2** | 100%, 1110, 1 |
| Time | — | about 7 min | **223 s** | 69 s |

19 of the 52 connections go in as buses: the two module-to-header fan-outs. On the left side:
- the four pins whose header pins are near go on top in one river, exactly where the hand routing has them;
- the next four go through an escape-via column and a bottom bundle;
- the rest go to the search.

The 6 entries "at an angle" are 45° entries into round header pins, on purpose.

**What's still worse than by hand:**
- **Connections that aren't a bus** still come from the search with long diagonals and an occasional hook. Example: the USB-UART chip's lines to the module and the header.
- **Bus pins that neither river fits** (`IO27`, `IO12`, `IO13` on the left) go to the search too.
- **One segment is off by 1.6°**: `ESP_EN`, where a straight run joins two off-grid pins. A 0.05 mm skew.
- **2 connections are still left**, as before.

**Next:**
- shapes for the non-bus connections: whole-connection patterns (L/Z between the two pins and their escape vias) before the search, the way the bus river works;
- a "step-in" for rivers, where a track moves to the slot freed by the one before (the hand routing does that);
- a tidiness measure in `route_quality.py`: parallel runs at pitch, bends aligned.

