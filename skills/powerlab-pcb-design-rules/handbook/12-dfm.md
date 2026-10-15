# 12 — Manufacturability / DFM (DFM)

This section covers the geometric rules that decide whether the bare board can be manufactured by the fab **without problems and without surcharges**: trace/spacing, holes, annular rings, edge clearance, solder mask, acid traps, slivers, slots and half-holes (castellations). Numeric limits depend on the manufacturer and the price class; below, each value is given separately for **JLCPCB** and **PCBWay** (the standard price class used by METU PowerLab), accessed 2026-10. When measuring from a screenshot, use known body/pitch values as a reference scale: 0603 body 1.6×0.8 mm, 0402 body 1.0×0.5 mm, SOIC pitch 1.27 mm, pin header pitch 2.54 mm, QFN pitch usually 0.5 mm (verify from the package drawing).

> Scale hint (for all rules): Divide the pixel width of the gap you want to measure in the image by the pixel width of a known item at the same zoom, and multiply by that item's mm value. E.g. if the distance between two adjacent SOIC pin centres is 64 px, 1 px ≈ 0.02 mm; a 6 px gap is ≈ 0.12 mm. This estimate carries ±1–2 px error; mark borderline values as "Needs verification with the DRC report".

### [DFM-001] Trace width / trace spacing below the manufacturer limit

- **Severity:** Critical
- **Detectable from image:** Partly
- **How it looks in the image:** Thin, hair-like traces; especially traces passing between the pads of a fine-pitch IC, or an almost invisible gap between two traces. If a trace passes between two pads of a 0.5 mm pitch QFN, since the pad is ≈0.25–0.28 mm the remaining space for trace + 2×spacing is ≈0.25 mm; this physically drops below 0.1/0.1 mm (the 0.5 mm pitch example in the JLCPCB BGA guide). Compare the trace width with the SOIC pitch (1.27 mm): a trace thinner than ~1/8 of the pitch is below ≈0.15 mm.
- **Why it matters:** A trace below the limit breaks when over-etched (open circuit), and a narrow gap leaves a short when under-etched; if the limit is exceeded the manufacturer either rejects the order or moves it to a more expensive class.
- **Recommended fix:** JLCPCB standard, 2026-10: 1–2 layers 1 oz ≥0.10/0.10 mm, 2 oz ≥0.16/0.16 mm. PCBWay standard price, 2026-10: absolute min 0.10/0.10 mm but ≥0.15/0.15 mm (6/6 mil) is recommended for cost; 2 oz outer layer "normal" process 7/8 mil. PowerLab default for 1 oz is 0.20/0.20 mm; 0.15 mm only locally at fine-pitch pad escapes.
- **Exceptions:** In the BGA fan-out area, JLCPCB allows 3 mil (0.076 mm) locally on multilayer boards — this needs a surcharge/special class. With heavy copper (≥2 oz) the limits grow.
- **Example:** Link: https://jlcpcb.com/help/article/bga-design-guidelines---pcb-layout-recommendations-for-bga-packages — Visible error: on a 0.5 mm pitch BGA only 0.25 mm of space remains where 0.27 mm is needed to pass a trace between two pads (unmanufacturable example).
- **Source:** [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [PCBWay PCB Capabilities](https://www.pcbway.com/capabilities.html), [PCBWay PCB Manufacturing Tolerances](https://www.pcbway.com/pcb_prototype/PCB_Manufacturing_tolerances.html), [PowerLab PCB_DESIGN_RULES](https://github.com/odtu/Powerlab/blob/master/KiCAD/PCB_DESIGN_RULES.md)

### [DFM-002] Hole diameter below the price-class limit / aspect ratio exceeded

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** The inner hole of the vias (black/dark circle in the render) looks very small relative to the via pad. Compare the via pad with the 0603 body width (0.8 mm): if the pad is ≈0.6 mm and the hole is half of the pad, it is ≈0.3 mm (borderline). If the hole looks smaller than one third of the pad diameter, it is ≈0.2 mm or less → suspected surcharge. Ask for the drill table (drill report) for the exact value.
- **Why it matters:** Small drill bits break and plating is not uniform; on a 1.6 mm board a small hole increases the aspect ratio and weakens the barrel plating.
- **Recommended fix:** PCBWay standard price, 2026-10: ≥0.3 mm (below 0.3 mm and above 6.3 mm carry a surcharge; absolute min 0.15–0.2 mm), aspect ratio ≤8 (normal). JLCPCB standard, 2026-10: min 0.15 mm (preferred ≥0.2 mm), via pad ≥0.1 mm (preferably 0.15 mm) larger than the hole. PowerLab: signal via 0.3/0.6 mm, power via 0.4/0.8 mm.
- **Exceptions:** Boards with HDI/microvias where the surcharge is knowingly accepted; on thin boards below 1 mm JLCPCB goes down to 0.1 mm (ENIG/OSP).
- **Example:** —
- **Source:** [PCBWay PCB Manufacturing Tolerances](https://www.pcbway.com/pcb_prototype/PCB_Manufacturing_tolerances.html), [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [PCBWay PCB Capabilities](https://www.pcbway.com/capabilities.html)

### [DFM-003] Insufficient annular ring / hole breakout risk

- **Severity:** Critical
- **Detectable from image:** Partly
- **How it looks in the image:** The copper ring left between the hole and the outer edge of the pad is very thin — the hole almost fills the pad; or the hole is not centred in the pad but shifted towards one edge (footprint error). Ring width = (pad diameter − hole diameter)/2; 0.6 mm pad + 0.3 mm hole → 0.15 mm. On a THT pad, suspect it if the ring is thinner than ~1/4 of the hole diameter. The risk increases if the trace enters the pad where the ring is thinnest.
- **Why it matters:** Because of drill position tolerance the hole can run outside the pad (breakout); if the junction with the trace is cut the connection breaks, and if this happens on an inner layer it cannot be repaired.
- **Recommended fix:** PCBWay standard, 2026-10: via ring min 0.15 mm (6 mil); "normal" process outer layer via 5/7/8 mil, component hole 10/12/14 mil (1/2/3 oz). JLCPCB standard, 2026-10: 2 layers 1 oz recommended 0.25 mm, absolute min 0.18 mm; 2 oz 0.254 mm. Sierra Circuits: min 4 mil, wider if possible; add teardrops on narrow rings (see DFM-019).
- **Exceptions:** In IPC Class 1/2, partial breakout is acceptable (as long as the minimum ring is kept); in Class 3 it is not (JLCPCB annular ring article). For electrically parallel multiple vias such as thermal via arrays, losing a single via is not critical.
- **Example:** —
- **Source:** [PCBWay PCB Capabilities](https://www.pcbway.com/capabilities.html), [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [Preventing Top DFM Errors in Your PCB Design (Altium/Sierra)](https://resources.altium.com/p/preventing-top-dfm-errors-your-pcb-design), [Understanding the Importance of Annular Rings in PCB Design (JLCPCB)](https://jlcpcb.com/blog/annular-rings)

### [DFM-004] Copper too close to the routed board edge

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** A copper pour, trace or pad touches the board outline (Edge.Cuts, usually a yellow/grey line), or only a very thin dark strip remains between them. Scale: if the edge–copper gap is clearly smaller than one 0603 body width (0.8 mm), it may be below the PowerLab default (0.5 mm); if the gap is less than one third of the 0603 width (≈0.25 mm), it is at the manufacturer limit. Pour edges should run parallel to the board edge at an equal distance.
- **Why it matters:** The routing tool tears the copper/leaves burrs, and exposed copper remains at the edge; on inner layers, copper exposed at the edge becomes a path for interlayer shorts or corrosion.
- **Recommended fix:** JLCPCB standard, 2026-10: ≥0.2 mm (routed edge). PCBWay standard, 2026-10: normal 0.3 mm, minimum 0.25 mm. Sierra Circuits: outer layer 0.010" (0.25 mm), inner layer 0.015" (0.38 mm). PowerLab default: 0.5 mm. Check the pour's "edge clearance" setting.
- **Exceptions:** Intentional edge plating, castellated holes (DFM-018) and RF edge shielding — these are surcharged options and must be stated in the order notes.
- **Example:** —
- **Source:** [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [PCBWay PCB Manufacturing Tolerances](https://www.pcbway.com/pcb_prototype/PCB_Manufacturing_tolerances.html), [Preventing Top DFM Errors in Your PCB Design (Altium/Sierra)](https://resources.altium.com/p/preventing-top-dfm-errors-your-pcb-design)

### [DFM-005] Copper close to the V-score line

- **Severity:** High
- **Detectable from image:** Partly (Yes if a panel image is available)
- **How it looks in the image:** In a panel image, a straight line (V-score) between boards with no gap, and pour/trace/pad closer than 1 mm to this line. In a single-board image, if there is a straight-edged rectangular board + a "V-cut" panel note, evaluate the edge copper distance by the V-score rule. Scale: 1 mm ≈ ~60% of one 0603 body length (1.6 mm).
- **Why it matters:** The V-blade cuts ~1/3 of the board from each side and the edge is stressed during break-off; nearby copper gets cut or cracks, and on an inner layer this can cause a short.
- **Recommended fix:** JLCPCB standard, 2026-10: copper–V-score ≥0.4 mm; board ≥0.6 mm for V-scoring. PCBWay, 2026-10: V-score line–copper min 0.35 mm, remaining thickness ≥0.25 mm, board 0.6–2.4 mm. PowerLab default: 1.0 mm. If there are stress-sensitive parts such as ceramic capacitors at the edge, keep them even farther away (see MEC).
- **Exceptions:** Panels separated with mouse bites (tab-routing) — in that case DFM-004 applies. The panelization decision itself falls under MEC.
- **Example:** —
- **Source:** [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [PCBWay PCB Manufacturing Tolerances](https://www.pcbway.com/pcb_prototype/PCB_Manufacturing_tolerances.html), [PCBWay PCB Capabilities](https://www.pcbway.com/capabilities.html)

### [DFM-006] Insufficient hole-to-hole spacing

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** The edges of two holes (via or THT) almost touch each other; in thermal via arrays the via pads overlap or there is no mask left between them. Scale: if the edge-to-edge gap of adjacent vias is smaller than half of a via hole (≈0.3 mm), it is close to the PCBWay via limit (0.28 mm).
- **Why it matters:** The thin material between close holes breaks/cracks during drilling; during plating the two holes can merge (a short if they are on different nets).
- **Recommended fix:** PCBWay "normal" process, 2026-10: between vias ≤0.45 mm ≥11 mil (0.28 mm), between component holes ≥16 mil (0.41 mm). JLCPCB standard, 2026-10: via hole-to-hole 0.2 mm, pad hole-to-hole 0.45 mm. PowerLab default: via 0.4 mm, component 0.5 mm. For thermal via pitch see THM (TI: ~1.0 mm pitch).
- **Exceptions:** Holes on the same net cause no electrical problem even if they merge, but the mechanical problem remains; if an intentional merge is needed, use a slot (DFM-017).
- **Example:** —
- **Source:** [PCBWay PCB Capabilities](https://www.pcbway.com/capabilities.html), [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities)

### [DFM-007] Insufficient drill-to-copper clearance

- **Severity:** High
- **Detectable from image:** Partly (No for inner layers)
- **How it looks in the image:** A trace or pour belonging to a different net passes very close to the edge of a hole (via, THT, NPTH mounting hole); there is no clearance cut out of the pour around an NPTH mounting hole, or it is very narrow. Inner layers can only be seen in per-layer renders; otherwise ask the user for inner-layer images or the DRC report.
- **Why it matters:** Because of drill wander and plating tolerance, the hole barrel can touch nearby copper; on an inner layer this creates a short that cannot be repaired.
- **Recommended fix:** JLCPCB standard, 2026-10: via hole–trace 0.2 mm, PTH–trace min 0.28 mm (recommended 0.35 mm), NPTH–trace 0.2 mm, inner layer via hole–copper 0.2 mm. PCBWay, 2026-10: NPTH–copper normal 0.2 mm (min 0.15 mm); inner layer isolation ring 4L 7 mil, 6L 8 mil. Sierra Circuits: ≥8 mil, the hole diameter is measured with the drill diameter, not the finished diameter. PowerLab default: copper–hole 0.25 mm.
- **Exceptions:** Thermal connections (spokes) to the same net are not subject to this rule.
- **Example:** —
- **Source:** [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [PCBWay PCB Manufacturing Tolerances](https://www.pcbway.com/pcb_prototype/PCB_Manufacturing_tolerances.html), [Preventing Top DFM Errors in Your PCB Design (Altium/Sierra)](https://resources.altium.com/p/preventing-top-dfm-errors-your-pcb-design)

### [DFM-008] Acid trap: acute-angle trace junction or almost-enclosed copper pocket

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** Two traces joining at an angle narrower than 90° (a sharp "V"); a trace entering a pad tangentially at a very shallow angle; small gap pockets between a pour and a trace/pad with a narrow mouth and a wide interior. The real risk is not the sharp angle itself but the small enclosed area where etchant can collect — even if the angle is 45°, a narrow notch next to a pad is risky.
- **Why it matters:** Etchant left in the pocket eats away too much copper and can cause the trace to narrow or break. Some manufacturers hold that the risk has decreased in modern processes (see DECISIONS.md), but the rule is kept because it is cheap and easy to apply.
- **Recommended fix:** Make trace junctions at 45° or wider angles, run the trace straight into the pad along its axis; fill or widen narrow pockets with pour; enable the "acute angle" check in the design tool and check the manufacturer's DFM report. PowerLab: 45° corners, no 90° and no acute angles.
- **Exceptions:** Junctions rounded with arcs and teardrop fills do not create acid traps.
- **Example:** Link: https://community.sparkfun.com/t/another-pcb-design-noob-new-thread-for-new-board/16280 — Visible error: acute angles at trace junctions; commenters warn about acid traps.
- **Source:** [4 less obvious PCB DFM violations (Siemens)](https://blogs.sw.siemens.com/electronic-systems-design/2020/03/16/4-less-obvious-pcb-dfm-violations/), [Preventing Top DFM Errors in Your PCB Design (Altium/Sierra)](https://resources.altium.com/p/preventing-top-dfm-errors-your-pcb-design), [PowerLab PCB_DESIGN_RULES](https://github.com/odtu/Powerlab/blob/master/KiCAD/PCB_DESIGN_RULES.md)

### [DFM-009] Copper sliver

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** Very thin, long, pointed copper pieces ("splinters") left after the pour is filled, between a trace and a pad's clearance ring, between the clearances of two close vias, or at the edge of the pour. A pour piece clearly thinner than the trace itself and several times longer than its width is a sliver. It usually forms when the trace enters the pad from an edge/at an angle rather than from the centre.
- **Why it matters:** A thin piece of copper or photoresist can break off during processing, stick somewhere else and cause a short; also, a narrow strip does not etch uniformly.
- **Recommended fix:** Set the pour's minimum width to at least the manufacturer's minimum trace width (PCBWay standard ≥0.15 mm, JLCPCB ≥0.10 mm, 2026-10) so that pieces below it are not filled; the Altium/Sierra article recommends removing gaps/slivers below 3 mil. Run the trace into the pad along its axis, at the centre (PowerLab §3.4); if needed, add a local keepout to remove the sliver.
- **Exceptions:** Intentionally thin thermal spokes are not slivers.
- **Example:** —
- **Source:** [Preventing Top DFM Errors in Your PCB Design (Altium/Sierra)](https://resources.altium.com/p/preventing-top-dfm-errors-your-pcb-design), [PowerLab PCB_DESIGN_RULES](https://github.com/odtu/Powerlab/blob/master/KiCAD/PCB_DESIGN_RULES.md), [Pulsonix copper check rules](https://pulsonix.com/docs/technology/idh_technology_copper_check_rules)

### [DFM-010] Unconnected copper island (island / dead copper)

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** A copper piece inside a pour that appears not to be connected to any via, trace or pad (completely surrounded by clearance). Without the netlist it is not certain that it is unconnected — if no via is visible under it and it touches no pad, mark it as a "possible island".
- **Why it matters:** Floating copper can pick up and radiate noise like an antenna; very small islands can break off like slivers (DFM-009). Islands left intentionally for copper balance are harmless (DFM-015).
- **Recommended fix:** Either connect the island to GND with a stitching via or remove it (KiCad: "Remove islands: Always" in the zone settings). Define a minimum island area threshold.
- **Exceptions:** Intentional copper balancing (thieving) patterns; intentional floating structures in RF (see RF). Primary rule for this finding: GND-012; report it as GND-012.
- **Example:** —
- **Source:** [Thermal relief connection to zone incomplete — KiCad forum](https://forum.kicad.info/t/thermal-relief-connection-to-zone-incomplete/62623), [Pulsonix copper check rules](https://pulsonix.com/docs/technology/idh_technology_copper_check_rules)

### [DFM-011] Starved thermal and plane bottleneck in a hole array

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** Only one or none of the thermal spokes of a pad connected to a pour reaches the pour; the spokes are cut off by the clearance of a nearby trace/via. Also, the clearance rings of dense via/hole arrays (connector, thermal array) merge and reduce the copper feeding the inside of the plane to a few thin bridges. Requires per-layer renders; ask for them if inner layers are not visible.
- **Why it matters:** A single-spoke thermal heats up/drops voltage at high current and carries a risk of an open connection; the thin bridges in a hole array can break with small misregistration and isolate the inner part of the plane.
- **Recommended fix:** Do not disable the "minimum thermal relief spoke count" DRC in KiCad (default 2); rotate the spokes by 45° or move the obstructing trace; use a solid connection on power pads (PWR/THM). In hole arrays, open up the hole spacing enough to leave plane copper between the clearances.
- **Exceptions:** Signal pads that will not be hand-soldered and do not carry current; DRC false positives (reported in KiCad 7 for adjacent edge spokes).
- **Example:** Link: https://forum.kicad.info/t/thermal-relief-connection-to-zone-incomplete-layer-in1-cu-5-spokes-connected-to-isolated-island/66037 — Visible error: thermal spokes on an inner layer connected to an isolated island.
- **Source:** [4 less obvious PCB DFM violations (Siemens)](https://blogs.sw.siemens.com/electronic-systems-design/2020/03/16/4-less-obvious-pcb-dfm-violations/), [Thermal relief connection to zone incomplete — KiCad forum](https://forum.kicad.info/t/thermal-relief-connection-to-zone-incomplete/62623), [KiCad issue 15568](https://gitlab.com/kicad/code/kicad/-/issues/15568)

### [DFM-012] No solder mask bridge (dam) between pads, or below the manufacturer limit

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** The pad row of a fine-pitch IC (SOIC, TSSOP, QFN) is inside a single, combined mask opening (no mask colour between the pads, exposed copper/tin colour is continuous). In a mask layer render, the width of the mask strip between pads = pad gap − 2×mask expansion. With 0.5 mm pitch, 0.25–0.28 mm pads and 0.05 mm expansion, the remaining bridge is ≈0.12 mm — borderline.
- **Why it matters:** The mask bridge limits solder flowing from pad to pad and escaping onto traces; the manufacturer silently removes a bridge below the limit (gang opening), and thin bridges can break off and leave loose pieces on the board.
- **Recommended fix:** JLCPCB standard, 2026-10: 1 oz green/red/yellow/blue/purple 0.10 mm, black/white 0.13 mm; 2 oz 0.20 mm. PCBWay "normal", 2026-10: <2 oz green 4 mil (0.10 mm), black/other 4.5 mil, ≥2 oz 5 mil. PowerLab: green 0.10 mm. If the bridge cannot be achieved, TI's recommendation: at 0.5 mm pitch reduce the pad width to ≤0.28 mm, or shrink it according to the manufacturer's mask tolerance.
- **Exceptions:** At 0.5 mm pitch and below, an intentional "gang" opening can be acceptable with a thin stencil and a good process (TI SLUA271: ≤0.05 mm clearance around the pad group at 0.5 mm pitch). In that case, note the decision.
- **Example:** Link: https://forum.kicad.info/t/how-bad-is-having-no-mask-between-smd-pads/43923 — Visible error: no mask left between fine-pitch pads, discussion of mask slivers breaking off. Link: https://eevblog.com/forum/eda/solder-mask-bridge-between-qfn-pads-how-important/msg2403045 — no bridge between QFN pads (discussion of it as an intentional choice).
- **Source:** [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [PCBWay PCB Capabilities](https://www.pcbway.com/capabilities.html), [TI SLUA271 QFN/SON PCB Attachment](https://edgeworker.ti.com/lit/pdf/slua271)

### [DFM-013] Solder mask opening (expansion) wrongly sized

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** The mask opening is much larger than the pad (a wide ring of exposed copper around the pad, a nearby trace is also exposed) or smaller than the pad (mask overlaps the pad; it has become "solder mask defined"). In a render, the opening usually appears as a ring slightly lighter in colour than the pad; if the ring is larger than ~20% of the pad width, suspect excessive expansion.
- **Why it matters:** Excessive expansion exposes the neighbouring trace (solder bridge) and eliminates the bridge in DFM-012; zero/negative expansion covers part of the pad when the mask shifts and reduces the solderable area.
- **Recommended fix:** PCBWay "normal", 2026-10: opening ≥2 mil (0.05 mm). JLCPCB, 2026-10: opening 1:1 to the pad (the manufacturer applies its own compensation) and opening to neighbouring trace ≥0.09 mm. TI SLUA271: NSMD opening 0.1–0.14 mm larger than the pad in total. PowerLab: 0.05 mm. Follow the manufacturer's design rule; do not expand twice (CAD + manufacturer).
- **Exceptions:** Intentional SMD (solder-mask-defined) pad choice for BGA; fiducials (DFA-007: opening 2× diameter).
- **Example:** —
- **Source:** [PCBWay PCB Capabilities](https://www.pcbway.com/capabilities.html), [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [TI SLUA271 QFN/SON PCB Attachment](https://edgeworker.ti.com/lit/pdf/slua271)

### [DFM-014] Silkscreen on a pad or exposed copper

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** A white (or black) line/text passes over an SMD pad, a THT ring or a mask opening; a footprint outline line cuts across pads; a reference designator sits on a via or pad. This rule only covers the manufacturing/soldering aspect — legibility and placement are in SLK.
- **Why it matters:** Ink on a pad degrades solderability; manufacturers handle it differently (silently clip it, put the order on hold, print it as is). JLCPCB support replies have reported that it clips silkscreen on pads, but do not rely on this.
- **Recommended fix:** JLCPCB, 2026-10: pad–silkscreen ≥0.15 mm. PowerLab: ≥0.1 mm. PCBWay does not publish a number; apply the same value. Fix the footprint (so it does not repeat in every project); enable the silk–pad clearance DRC in KiCad.
- **Exceptions:** Silkscreen over copper covered by mask (pour, tented via) is not a problem. Primary rule for this finding: SLK-001; report it as SLK-001.
- **Example:** Link: https://forum.kicad.info/t/jlcpcb-silkscreen-overlap/58557 — Visible error: JLCPCB DFM tool warning about silkscreen too close to a pad; the fix was correcting the footprint.
- **Source:** [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [Dealing with silkscreen over solder mask — KiCad forum](https://forum.kicad.info/t/dealing-with-silkscreen-over-solder-mask/46011), [PowerLab PCB_DESIGN_RULES](https://github.com/odtu/Powerlab/blob/master/KiCAD/PCB_DESIGN_RULES.md)

### [DFM-015] Unbalanced copper distribution (copper balance)

- **Severity:** Low
- **Detectable from image:** Partly
- **How it looks in the image:** One side (or layer) is almost entirely filled with pour while the symmetric opposite layer is almost empty; or one half of the board has dense copper and the other half is empty. Put the top and bottom layer renders side by side and compare the copper-covered area ratio by eye (40–60% is the ideal range).
- **Why it matters:** Copper and FR-4 expand differently; an unbalanced distribution leads to bow/twist after lamination and reflow, as well as variation in plating thickness and trace width.
- **Recommended fix:** Fill empty areas with pour or an unconnected dot pattern (thieving). JLCPCB article, 2026-10: density difference between mirror layers within 15–20% (citing IPC-6012 — standard text not verified), layer density target 40–60%; thieving dots 20–40 mil diameter, 50–80 mil pitch; ≥3W away from impedance-controlled lines.
- **Exceptions:** On 2-layer, non-thin (1.6 mm) prototype boards the effect is usually small; thieving is not placed near RF/impedance lines.
- **Example:** —
- **Source:** [Copper Balancing in PCBs (JLCPCB)](https://jlcpcb.com/blog/pcb-copper-balancing), [Balanced copper distribution and copper weight in PCBs (Sierra)](https://www.protoexpress.com/blog/balanced-copper-distribution-and-copper-weight-in-pcbs/), [What is copper thieving in PCBs (Sierra)](https://www.protoexpress.com/kb/what-is-copper-thieving-in-pcbs/)

### [DFM-016] Plated (PTH) / non-plated (NPTH) hole distinction wrong

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** A hole without a copper ring (only a dark circle) is NPTH; a hole with a ring is PTH. Signs of an error: a mounting hole has no ring but a GND connection around it is expected; a connector locating-pin hole has a ring and is very close to a signal trace; no pour clearance around an NPTH; NPTH too small (<0.5 mm).
- **Why it matters:** The wrong type leads to a lost body/chassis connection or an unwanted short; NPTH and PTH are drilled with different tolerances (important for press-fit pins).
- **Recommended fix:** JLCPCB standard, 2026-10: NPTH min 0.5 mm, NPTH–trace 0.2 mm. PCBWay, 2026-10: NPTH tolerance ±0.05 mm, PTH ±0.08 mm; NPTH–copper normal 0.2 mm. Eurocircuits: min ring 0.30 mm on a connected NPTH. Follow the recommended hole type in the datasheet; supply the NPTHs in a separate drill file. For the choice of mounting hole type see MEC.
- **Exceptions:** If the datasheet explicitly says "plated or non-plated", both are acceptable.
- **Example:** —
- **Source:** [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [PCBWay PCB Manufacturing Tolerances](https://www.pcbway.com/pcb_prototype/PCB_Manufacturing_tolerances.html), [Eurocircuits PCB Classification](https://www.eurocircuits.com/pcb-design-guidelines/classification/)

### [DFM-017] Slot (oval hole) outside the manufacturer limit or wrongly defined

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** Oval pads of parts such as a DC jack, power connector or relay; the slot width is very narrow relative to the pad (like a thin line), or the slot length is shorter than 2 times its width. If the slot is drawn only on Edge.Cuts or a user layer instead of the drill layer, the manufacturer may not see it (a copper pad appears in the render instead of a hole).
- **Why it matters:** Narrow slots require a small router bit and their plating suffers; a slot defined on the wrong layer is never drilled and the part cannot be fitted.
- **Recommended fix:** JLCPCB standard, 2026-10: plated slot min 0.5 mm (2 layers) / 0.35 mm (multilayer), non-plated slot min 1.0 mm. PCBWay "normal", 2026-10: plated ≥0.5 mm, non-plated ≥0.8 mm, length/width ≥2. PowerLab: plated ≥0.6 mm, non-plated ≥1.0 mm. Define the slot in the footprint as an oval hole (drill).
- **Exceptions:** Cut-outs that are part of the board outline (Edge.Cuts) are outline, not slots; they fall under MEC.
- **Example:** —
- **Source:** [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [PCBWay PCB Capabilities](https://www.pcbway.com/capabilities.html), [PowerLab PCB_DESIGN_RULES](https://github.com/odtu/Powerlab/blob/master/KiCAD/PCB_DESIGN_RULES.md)

### [DFM-018] Half-hole (castellated) dimensions out of limits or not ordered

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** Plated holes centred on the board edge, with half of them outside the board (module-type board). Check: hole diameter (≈ the half-circle opening along the edge), gap between adjacent hole edges, and distance to the board corner. Scale: 0.5 mm diameter ≈ one 0402 body width; if the hole centres are on a 1.27 mm pitch, compare with the SOIC pitch.
- **Why it matters:** Half-holes need a special two-step drill + rout process; with a very small hole or a narrow gap the plating tears and pads lift. If not selected in the order form, the standard process cuts away the plating at the edge.
- **Recommended fix:** PCBWay "normal", 2026-10: diameter ≥0.5 mm, edge-to-edge ≥0.3 mm (the tolerances page says min 0.6 mm — a contradiction, see DECISIONS.md); a surcharged option. JLCPCB, 2026-10: capabilities page diameter ≥0.5 mm, between holes ≥0.5 mm, to the board corner ≥1 mm; design blog diameter ≥0.6 mm, spacing ≥0.6 mm, ring 0.25 mm (min 0.18). Safest: diameter ≥0.6 mm, edge-to-edge ≥0.6 mm. There must be a pad + mask opening on both sides.
- **Exceptions:** —
- **Example:** —
- **Source:** [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [Castellated PCBs: Introduction and Design Requirements (JLCPCB)](https://jlcpcb.com/blog/142-castellated-pcbs-introduction-and-design-requirements), [PCBWay PCB Capabilities](https://www.pcbway.com/capabilities.html), [PCBWay PCB Manufacturing Tolerances](https://www.pcbway.com/pcb_prototype/PCB_Manufacturing_tolerances.html)

### [DFM-019] Missing teardrop on a narrow ring/thin trace

- **Severity:** Low
- **Detectable from image:** Yes
- **How it looks in the image:** Places where a thin trace (≤0.25 mm) enters a small via or THT pad with a sharp "T" junction; with a teardrop, the trace widens towards the pad in a drop shape. Mark thin trace + small-ring via combinations that have no drop.
- **Why it matters:** A teardrop prevents the trace–pad junction from breaking when the drill wanders (it enlarges the effective ring) and strengthens the junction against mechanical/thermal stress; it is considered mandatory on flex boards.
- **Recommended fix:** Enable teardrops on pad and via connections (KiCad: Edit → Edit Teardrops; it is free). Sierra Circuits: recommended on traces <20 mil; with traces ≥10 mil and a similar ring the need drops noticeably; on traces <6 mil it gives extra assurance. Rerun DRC after adding them (teardrops can cause clearance errors).
- **Exceptions:** Wide power traces and pads with large rings; on RF/high-speed lines it is a designer decision due to the impedance effect (see HS/RF).
- **Example:** —
- **Source:** [Use of Teardrops in PCB Design (Sierra Connect)](https://sierraconnect.protoexpress.com/t/use-of-teardrops-in-pcb-design/2781), [PCB Teardrops (Labcenter)](https://www.labcenter.com/blog/pcb-teardrops/), [PowerLab PCB_DESIGN_RULES](https://github.com/odtu/Powerlab/blob/master/KiCAD/PCB_DESIGN_RULES.md)

### [DFM-020] Wide trace entering a small/NSMD pad (no neck-down)

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** A trace wider than or equal to the pad width enters a small SMD pad (0402/0603, QFN lead) directly; because the trace overlaps with its full width rather than from the side of the pad, the pad looks "elongated". Criterion: mark it if the part of the trace exposed by the mask is wider than 2/3 of the pad width.
- **Why it matters:** A wide exposed trace draws solder away from the pad (wicking), changes the geometry of the solder surface and contributes to tombstoning on small passives (DFA-006); an abrupt width change at the mask edge can lead to trace cracking.
- **Recommended fix:** TI (LMG3622 datasheet, 2026-10): a trace connected to an NSMD pad must be narrower than 2/3 of the pad width until it goes under the mask; under the mask the width is free. Neck down the wide power trace a short distance from the pad or enlarge the pad; Altium's "SMD Neck-Down" rule checks this ratio.
- **Exceptions:** Power pads and power parts with large pads (current capacity takes priority, see PWR); there are also designers who report using wide traces in practice without problems (see DECISIONS.md).
- **Example:** —
- **Source:** [TI LMG3622 datasheet — 8.4.1.1 Solder-Joint Stress Relief](https://www.ti.com/document-viewer/LMG3622/datasheet/GUID-F43232EE-8176-4A62-AFFA-1DE030FFB851), [SMT - SMD Neck-Down (Altium)](https://www.altium.com/documentation/altium-designer/pcb-smt-rule-smd-neck-down), [PCB Libraries forum: neck-down discussion](https://www.pcblibraries.com/forum/printer_friendly_posts.asp?TID=2025)
