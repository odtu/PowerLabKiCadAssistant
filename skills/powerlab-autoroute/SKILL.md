---
name: powerlab-autoroute
description: Autoroute a KiCad PCB with Freerouting 2.4.1 (Java 25) through the kicad MCP tools, the METU Power Lab way. Use when the user asks to autoroute, auto-route, route the board/remaining nets/signals automatically, or run Freerouting. Covers prerequisites, protecting hand-routed power and gate-drive nets, best-of-N runs, DRC afterwards, and reporting what is left.
---

# Autorouting with Freerouting

Freerouting is good at the many small signal connections and bad at power electronics judgement. Use it to finish a board, not to design the critical paths.

## 0. Is Freerouting the right tool for this board?
Check with `get_board_info` / `query_zones` / `get_ratsnest` before promising anything.
- **Good fit:** a board where most signal nets are still unrouted and copper pours are few, or are only GND on inner plane layers. A 2-layer board with 62 footprints and 29 nets routed completely in about 5 s.
- **Poor fit, so say so before running:** a dense board that is already mostly routed and has many copper pours on the outer layers (e.g. VBUS, phase and switch-node pours on F.Cu). Freerouting reads each zone's whole outline as a solid plane, so it starts out with hundreds of false clearance violations. On a 4-layer ESC board with 11 pour nets on F.Cu, rerouting just 4 small nets did not finish in 5 minutes. For a board like that, recommend KiCad's interactive router (`X`, with walkaround/shove) for the remaining nets instead, and only run Freerouting if the user still wants to try with a long timeout.

## 1. Check the setup first
Call the `check_freerouting` tool.
- It must find **Java 25** and the Freerouting jar. Freerouting 2.4.1 is built for Java 25 and fails with `UnsupportedClassVersionError` on older Java.
- In the PowerLab Assistant panel both are preinstalled and found automatically. If the check fails, stop and tell the user to run `install.ps1 -Update` from the PowerLab KiCad Assistant folder, then restart KiCad. Don't try to install Java or Freerouting yourself.

## 2. Make sure the board is ready (ask, don't assume)
Before routing, confirm with the user, or check with the kicad tools:
- **Saved:** the board is saved in KiCad. Routing writes the `.kicad_pcb` file, so unsaved KiCad edits would be lost.
- **Outline:** a closed board outline exists on Edge.Cuts, and every footprint is placed inside it. Placement decides the result far more than router settings.
- **Net classes:** these hold the track widths and clearances. Freerouting uses them, so set them before routing, from the lab's design rules or the user's values. High-current nets need wide tracks: never let them route at the default width.
- **Critical nets are already routed by hand and locked:** power input and output, switch nodes, half-bridge and DC-bus loops, gate-drive loops (driver → gate → source return), current-sense and Kelvin connections, and differential pairs. KiCad exports locked tracks as protected, so Freerouting keeps them. If they aren't routed yet, say so and recommend routing them first. Only autoroute them if the user explicitly insists, and warn that loop area and current capacity won't be considered.
- **Planes:** copper pours (e.g. GND planes) aren't routed by Freerouting. If GND/power should be a pour, it must exist before routing; otherwise Freerouting routes the whole net as tracks, which is slow and wrong for power boards. Refill zones after routing. A Freerouting warning that a plane layer "has no conduction areas" means that pour is missing.

## 3. Route
- **Load the board:** if `autoroute` says "No board is loaded", call `open_board` with the board path first. On large boards it can take over 30 s and time out once; retry once.
- **Estimate the run time first:** check the ratsnest (`get_ratsnest`) and tell the user how many connections are open. Freerouting 2.4.1 needs seconds for a small 2-layer board, but several minutes per attempt for a dense one: a 4-layer, 95-net board with ~230 open connections took over 3 minutes for its first passes.
- **Timeout:** set `timeout` from that estimate. Allow 600 s per attempt for dense boards and 900 s for very dense ones; the 300 s default is often too short.
- **Best-of-N:** for a first run, use `attempts: 1` with the default `maxPasses` (20). Only use `attempts: 3` (or 5 for dense boards) when the user wants the most complete result and accepts the extra time; each attempt varies the max passes and the most complete result is kept.
- **Priority nets:** put important signal nets that must be completed (e.g. gate drive, current sense, MCU control) in `targetNets`.
- **If it times out:** say so plainly. Nothing is imported and the board is unchanged. Offer a longer timeout, routing more of the critical nets by hand first, or adding the missing pours.

## 4. Check the result
- **Refill zones:** run `refill_zones` if the board has copper pours.
- **DRC:** run `run_drc` and summarise the errors by type. Compare against the DRC from before routing where you can, so only the new errors are blamed on the router. Clearance, track-width or short-circuit errors after autorouting usually mean the net-class rules don't match the board's design rules; report them, don't hide them.
- **Unrouted nets:** report what is still unrouted (ratsnest / `get_ratsnest`). Name the nets and suggest finishing them by hand.
- **Optional:** render the top and bottom with `kicad-cli pcb render` so the user can look at the result.

## 5. Tell the user
- **How it went:** say how many nets were routed and how many are left, plus the DRC result.
- **Reload:** the board file changed, so the user must use **File → Revert** in KiCad to see it (unsaved edits are lost; that's why step 2 asks them to save).
- **Review:** remind them that autorouted power-electronics boards need a human review. Check loop areas, return paths, track widths on high-current nets, and via counts on power paths before ordering.
