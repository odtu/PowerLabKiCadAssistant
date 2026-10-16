# 17 — Aesthetics (EST)

A board that looks "pretty" does not necessarily work better: if all design rules are met, an autorouted board works no worse than a "neat" hand-routed one ([Siemens – The myth of the pretty design](https://blogs.sw.siemens.com/electronic-systems-design/2014/08/13/the-myth-of-the-pretty-design/)). On the other hand, order speeds up assembly, automated optical inspection (AOI), debugging and review, and some "aesthetic" rules have a real electrical or manufacturing reason behind them. In this section each rule states explicitly whether its reason is purely visual (Severity: **Cosmetic**) or concrete; the auditor must not report purely cosmetic findings as errors, but separate them as "suggestions".

### [EST-001] 90° trace corners

- **Severity:** Cosmetic
- **Detectable from image:** Yes
- **How it looks in the image:** Corners where traces turn at a right angle (L-shaped); a sharp corner instead of a 45° chamfer or an arc.
- **Why it matters:** On typical digital/power boards the electrical effect is too small to measure: a 125 ps TDR pulse did not detect the right-angle corner on 5–10 mil traces; according to LearnEMC, the claim that a 90° corner causes radiation is a myth. The signal integrity effect only becomes meaningful at > 50 Gbps (LearnEMC) / above ~70 GHz bandwidth (Altium). Most teams still prefer 45° for readability and consistency.
- **Recommended fix:** Not needed. If the team standard is 45°, use 45° for consistency; on very high-speed/RF lines use arcs or chamfers (see HS, RF).
- **Exceptions:** In high-power RF circuits with thousands of volts a sharp corner can create a corona risk; multi-GHz lines and wide traces are more sensitive.
- **Example:** —
- **Source:** [EMC Design Myths (LearnEMC)](https://www.learnemc.com/emc-design-myths), [Slaying the PCB 90° Right-Angle Bend Dragon (Altium)](https://resources.altium.com/p/slaying-900-right-angle-bend-dragon), [PCB Routing Angle Myths: 45° vs 90° (Altium)](https://resources.altium.com/pcb-design-blog/pcb-routing-angle-myths-45-degree-angle-versus-90-degree-angle)

### [EST-002] Acute-angle (< 90°) trace junctions and "acid traps"

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** Points where a trace enters a pad or another trace in a V shape at an angle smaller than 90°; a thin wedge of copper/gap between two traces.
- **Why it matters:** This is a manufacturing rule, not an aesthetic one: etchant can collect in acute corners and over-etch the copper. According to Altium, modern low-viscosity etchants have greatly reduced the risk, but it still recommends keeping the "Acute Angle" rule; LearnEMC calls the etching problem "not really" an issue. The risk is higher on thin traces.
- **Recommended fix:** Connect traces to pads and to each other at 90° or 45°; at T junctions use a perpendicular entry or a teardrop.
- **Exceptions:** If the fabricator's DFM report sees no problem, it is practically irrelevant on wide traces. Primary rule for this finding: DFM-008; report it as DFM-008.
- **Example:** —
- **Source:** [8 Common DFM Problems PCB Design Rules Catch Before Fab (Altium)](https://resources.altium.com/p/common-dfm-problems), [EMC Design Myths (LearnEMC)](https://www.learnemc.com/emc-design-myths)

### [EST-003] Irregular spacing and zigzags in parallel trace bundles

- **Severity:** Cosmetic
- **Detectable from image:** Yes
- **How it looks in the image:** In a bus/trace group running in the same direction, the gap between traces changes from place to place, traces jump over each other, there are unnecessary zigzags and bends; the bundle spreads out and gathers again here and there.
- **Why it matters:** It is mostly a matter of looks and reviewability: a tidy bundle makes signal tracing and rework easier. On the electrical side, crosstalk depends on spacing relative to the trace height above the reference plane, not on trace width (according to LearnEMC the "3W rule" alone is misleading; it is a good approximation in thin-dielectric stackups, see HS-011); so irregular but sufficient spacing is not an electrical error.
- **Recommended fix:** Route the bundle with constant spacing and common bend points; on sensitive lines set the spacing according to the layer height (see HS).
- **Exceptions:** Length-matching meanders (serpentine) are intentional and do not count as irregularity.
- **Example:** —
- **Source:** [EMC Design Myths (LearnEMC)](https://www.learnemc.com/emc-design-myths), [Aesthetic PCB Design Tips For Improved Functionality (Hackaday / Phil's Lab)](https://hackaday.com/2022/11/29/aesthetic-pcb-design-tips-for-improved-functionality/)

### [EST-004] Passives not in rows/a grid, mixed orientations

- **Severity:** Low
- **Detectable from image:** Yes
- **How it looks in the image:** Resistors/capacitors with the same function are scattered at random angles and on offset axes; polarized parts (diode, tantalum) in the same block face different directions; very low parts are squeezed right next to tall parts.
- **Why it matters:** There are real reasons beyond looks: polarized parts facing the same direction make AOI programming easier and make a reversed part instantly obvious to the human eye; tall–low adjacency creates shadows for the AOI camera; a regular grid makes pick-and-place and reflow easier.
- **Recommended fix:** Line up passives of the same type on a common axis and rotate them the same way; turn polarized parts the same way within a block; leave enough spacing for the AOI camera. Electrical requirements (e.g. the decoupling capacitor placed closest to the pin) always come before alignment.
- **Exceptions:** Signal/power requirements may force a part to an angle other than a multiple of 90° (Cadence).
- **Example:** —
- **Source:** [How to Make Your PCB Layout AOI and X-Ray Friendly (Altium)](https://resources.altium.com/p/optimize-pcb-layout-for-aoi-x-ray), [PCB Component Orientation Considerations (Cadence)](https://resources.pcb.cadence.com/blog/2021-pcb-component-orientation-considerations-for-optimum-part-placement), [Aesthetic PCB Design Tips (Hackaday / Phil's Lab)](https://hackaday.com/2022/11/29/aesthetic-pcb-design-tips-for-improved-functionality/)

### [EST-005] Repeated channels (phases, channels, half bridges) laid out differently from each other

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** The three legs of a three-phase bridge, multi-channel measurement inputs or identical drivers are drawn on the board with different part placement, different trace lengths and different via counts; one channel is tidy, another is scattered.
- **Why it matters:** Symmetry here is not aesthetic: matching between channels (gate-drive loop inductance, delay, offset) depends on identical placement and routing; different channels behave differently. Identical channels also speed up debugging.
- **Recommended fix:** Complete one channel and copy it to the others (Altium "Copy Room Formats"/multi-channel design; equivalent replication tools in KiCad); after copying, check the length/skew difference between channels.
- **Exceptions:** A mechanical constraint (connector position) may break the symmetry; in that case it is enough that the critical loops (see SMPS) stay equivalent.
- **Example:** —
- **Source:** [Multi-Channel Design with a Flat Project (Altium)](https://resources.altium.com/p/multi-channel-design-with-a-flat-project), [PCB Layout Replication (Altium Docs)](https://www.altium.com/documentation/altium-designer/pcb-layout-replication)

### [EST-006] Unnecessary vias and roundabout paths

- **Severity:** Low
- **Detectable from image:** Yes
- **How it looks in the image:** A trace changes layer twice over a short distance (via–short trace–via); a trace detours around a part where it could go straight with no obstacle; clusters of vias on a net with no visible reason.
- **Why it matters:** It is partly aesthetic, but every layer change adds inductance (example of ~1.2 nH for a full-length signal via in a 63 mil board, SigCon) and disrupts the return current path; on high-speed lines it is recommended not to change layers (TI). Each via and detour also adds manufacturing and review burden.
- **Recommended fix:** Remove unnecessary layer transitions; at a necessary transition place a GND return via next to the signal via (see VIA, HS).
- **Exceptions:** GND stitching vias, thermal vias and intentional length matching do not count as unnecessary.
- **Example:** —
- **Source:** [Via Inductance (SigCon, Howard Johnson)](https://www.sigcon.com/Pubs/news/6_04.htm), [High-speed layout guidelines – via discontinuity (TI SLLA284)](https://ti.com/document-viewer/lit/html/SLLA284G/GUID-B9B310F5-9021-45EE-8935-8E219F9D693D)

### [EST-007] Inconsistent trace widths within the same net class

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** A power trace suddenly narrows at one point (a neck) and then widens again; traces of the same kind of signal have randomly different widths; power and signal traces are so similar in width that they cannot be told apart. Without the netlist, infer which trace carries power from the parts (inductor, MOSFET, connector).
- **Why it matters:** A neck sets the current capacity at its narrowest point and causes heating/voltage drop; inconsistency usually indicates that the board was routed without net class rules defined.
- **Recommended fix:** Before routing, define net classes (Power, Signal, etc.) and width rules; size power traces for the current (see PWR) and keep any forced narrowing at the pad entry short.
- **Exceptions:** A short neck-down to enter a fine-pitch IC pad is normal; if the same net carries different currents in different areas, different widths are legitimate.
- **Example:** —
- **Source:** [Customizing Performance-Based Electrical Design Rules in Altium Designer (Altium)](https://resources.altium.com/p/customizing-electrical-performance-based-design-rules-altium-designer), [Routing Rule Types (Altium Docs)](https://www.altium.com/documentation/altium-designer/pcb/design-rule-types/routing?version=24)

### [EST-008] Unconnected ratsnest (airwire) left over

- **Severity:** Critical
- **Detectable from image:** Partly
- **How it looks in the image:** In an editor screenshot, thin straight lines without width that ignore layers run between pads (usually white/grey in KiCad) — they cross straight over everything and never make corners. The ratsnest is not visible in a 3D render or in Gerbers; so in a render a "missing connection" can only be suspected when no trace reaches a pad at all. Ask the user for the DRC "unconnected items" count.
- **Why it matters:** Every unconnected ratsnest line is an open circuit on the manufactured board; the board does not work.
- **Recommended fix:** Route the whole ratsnest or connect it with a pour (zone), refill the pours, and verify in DRC that the unconnected item count is 0.
- **Exceptions:** Deliberately separated net-ties/intentionally unconnected pads (NC) do not produce ratsnest lines; if they do, it is a netlist error.
- **Example:** —
- **Source:** [KiCad Forum – Easy way to find unrouted traces?](https://forum.kicad.info/t/easy-way-to-find-unrouted-traces/5061/), [8 Common DFM Problems PCB Design Rules Catch Before Fab (Altium)](https://resources.altium.com/p/common-dfm-problems)

### [EST-009] Dangling trace ends and dead-end trace segments

- **Severity:** Low
- **Detectable from image:** Yes
- **How it looks in the image:** A trace segment that ends without reaching a pad, via or another trace; a "tail" leaving a pad and stopping after a few mm; a trace with a free end inside a pour of the same net (KiCad does not warn about this in DRC).
- **Why it matters:** It is usually editing leftover; it clutters the view and can hide a real missing connection; in KiCad DRC it appears as a "Track has unconnected end" warning. For the electrical effects of an open-ended stub on high-speed/RF lines see HS and RF (not separately verified with a source in this section).
- **Recommended fix:** Delete leftover segments (KiCad: Tools → Cleanup Tracks and Vias); clear the dangling warnings in DRC, and check ends inside pours by hand.
- **Exceptions:** Intentional stubs (RF matching stub, test point branch, pad left for a future option) are fine if documented.
- **Example:** Link: https://forum.kicad.info/t/6-0-rc1-track-has-unconnected-end/32080 — Visible error: "track has unconnected end" warnings caused by short trace leftovers hidden on a pad.
- **Source:** [KiCad Forum – Track has unconnected end](https://forum.kicad.info/t/6-0-rc1-track-has-unconnected-end/32080), [KiCad GitLab issue #10539 (dangling track cleanup)](https://gitlab.com/kicad/code/kicad/-/issues/10539)

### [EST-010] Slivers, necks and isolated islands at pour edges

- **Severity:** Low
- **Detectable from image:** Yes
- **How it looks in the image:** Thin "finger"-shaped copper strips reaching in between pads; narrow necks connecting two areas of a pour; isolated copper islands surrounded by clearance and not connected by any via; jagged/irregular pour edges.
- **Why it matters:** There is a manufacturing reason beyond looks: thin strips (slivers) can break off during fabrication and cause a short elsewhere, and can cause failures on some boards even if they pass DRC; unconnected islands misrepresent the pour's current path (for the EMC effect see GND); a narrow neck reduces the pour's current-carrying capacity.
- **Recommended fix:** Set the pour's minimum width (sliver) setting to at least the fabricator's min. trace width, remove isolated islands or connect them with vias, widen narrow necks or bridge them with extra vias (see GND, DFM).
- **Exceptions:** Deliberately separated copper areas (isolation zone, heat-spreader island) are fine if documented. Primary rule for isolated islands: GND-012; for slivers: DFM-009; use this rule only for irregular pour edges.
- **Example:** —
- **Source:** [8 Common DFM Problems PCB Design Rules Catch Before Fab (Altium)](https://resources.altium.com/p/common-dfm-problems), [Preventing Top DFM Errors in Your PCB Design (Altium)](https://resources.altium.com/p/preventing-top-dfm-errors-your-pcb-design)
