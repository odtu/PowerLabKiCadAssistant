# 04 — Grounding (GND)

At high frequency (from a few kHz upwards according to Altium; Olney: "at high frequencies") the return current follows the lowest-inductance path, i.e. the plane region directly beneath the signal trace; most grounding errors are an interruption or lengthening of this path. This section covers GND plane continuity, slots, split planes, stitching vias, pour islands and analog/digital grounding. Rules are ordered roughly by severity; the auditor should first clarify the layer roles (see STK-001).

### [GND-001] Reference GND plane chopped into pieces by traces

- **Severity:** Critical
- **Detectable from image:** Yes
- **How it looks in the image:** On the GND layer (usually B.Cu on 2 layers) the pour is split into many separate polygons by the dark clearance strips around long traces; the polygons connect to each other only through narrow necks or not at all. The plane looks like "puzzle pieces". In a good example the pour is a single piece with only small, scattered via holes in it.
- **Why it matters:** In a chopped plane the return current does not flow beneath the trace but detours through the narrow passages between the pieces; loop area, inductance, radiation and crosstalk increase. A pour being surrounded by pads and traces does not make it a real plane.
- **Recommended fix:** Move the traces on the GND layer to a signal layer; keep unavoidable bridging traces short and do not route fast signals over them. Leave several wide connections and stitching vias between the pieces.
- **Exceptions:** Intentional partitioning/isolation (see GND-005, GND-006).
- **Example:** —
- **Source:** [Sierra Circuits forum — Ground Plane Strategy for a 2-Layer PCB](https://sierraconnect.protoexpress.com/t/ground-plane-strategy-for-a-2-layer-pcb-from-an-emi-emc-perspective/3630), [Altium — Understanding Ground Planes in Your Two-Layer PCB](https://resources.altium.com/pcb-design-blog/understanding-ground-planes-in-your-two-layer-pcb), [JLCPCB — Ground Plane and Power Plane Guide](https://jlcpcb.com/blog/circuit-board-ground-plane-and-power-plane-guide-2026)

### [GND-002] Signal trace crosses a slot/gap in the reference plane

- **Severity:** Critical
- **Detectable from image:** Yes (signal and GND layer images must be overlaid)
- **How it looks in the image:** A trace on one layer crosses, perpendicularly or at an angle, a dark gap line in the adjacent GND layer (slot, split boundary, cut, large hole, connector cutout). When both layers are shown at once in KiCad, the trace passes over a strip where the lower layer's colour is interrupted.
- **Why it matters:** The return current is forced to detour around the slot; the large loop produces radiation, extra inductance/ringing, delay and crosstalk into nearby signals. According to Olney, in some cases the current travels all the way back to the power supply.
- **Recommended fix:** Reroute the trace so it does not cross the slot, or close the slot. If unavoidable, leave a bridge joining the planes at the crossing point (see GND-006), or, for planes at different potentials, place a ≤1 µF stitching capacitor as close as possible to the crossing (TI SPRAAR7J).
- **Exceptions:** Differential, optically or transformer-isolated crossings (TI SLYT512); DC/very slow signals.
- **Example:** Link: [TI SLYT512, Figures 1–3](https://www.ti.com/lit/pdf/SLYT512) — Visible: Figures 1–2 traces crossing the split (wrong), Figure 3 all traces passing over the bridge (correct).
- **Source:** [TI SLYT512 — Grounding in mixed-signal systems demystified, Part 2](https://www.ti.com/lit/pdf/SLYT512), [Barry Olney — Split Planes in Multilayer PCBs](https://www.icd.com.au/articles/Split_Planes_PCBD-Mar2015.pdf), [TI SPRAAR7J — reference plane guidelines](https://www.ti.com/document-viewer/lit/html/SPRAAR7J/GUID-AD6D2D54-84AC-47F5-A2ED-87883A148A25)

### [GND-003] Long "bridge" trace on a plane layer creates a slot

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** On an inner GND layer (or B.Cu on 2 layers) a single trace running through the pour, together with its dark clearance, looks like a long, thin slot in the plane. The longer the trace and the more parallel it is to traces on other layers, the greater the risk.
- **Why it matters:** A trace inside the plane behaves like a slot; every signal passing over it falls into the GND-002 error. JLCPCB requires that high-speed traces never cross plane gaps and slots.
- **Recommended fix:** Move the trace to a signal layer. If it cannot be moved, keep the bridge as short as possible (a few mm), orient it perpendicular to the signal traces above it and do not run it beneath fast/sensitive signals; add GND vias close to both ends of the bridge.
- **Exceptions:** Board corner/edge areas that no signal crosses.
- **Example:** —
- **Source:** [JLCPCB — Ground Plane and Power Plane Guide](https://jlcpcb.com/blog/circuit-board-ground-plane-and-power-plane-guide-2026), [Barry Olney — Split Planes in Multilayer PCBs](https://www.icd.com.au/articles/Split_Planes_PCBD-Mar2015.pdf)

### [GND-004] Row of aligned vias/antipads creates a slot in the plane

- **Severity:** High
- **Detectable from image:** Yes (inner layer image needed)
- **How it looks in the image:** On an inner GND layer the clearance (antipad) circles of a connector pin row, BGA escape vias or vias lined up in a straight line touch each other and form a continuous dark strip; no copper bridge (web) is left between the circles. Traces passing over this strip have the same problem as GND-002.
- **Why it matters:** TI states that aligned vias block the return current path like "logs in a river" and that vias should be placed staggered. Merged antipads are in practice a plane slot.
- **Recommended fix:** Arrange the vias in a zigzag (staggered) pattern; leave enough spacing for a copper bridge to remain between antipads (for minimum copper width see DFM). If no plane bridge remains in connector arrays, route the traces perpendicular to the array, not parallel to it.
- **Exceptions:** Via rows in areas that no signal crosses.
- **Example:** Link: [TI SNLA426, Figure 20-1 / 20-2](https://www.ti.com/lit/an/snla426/snla426.pdf) — Visible: staggered vias (correct) and aligned vias (wrong).
- **Source:** [TI SNLA426 — High-Speed PCB Layout for PCIe Gen 5, Section 20](https://www.ti.com/lit/an/snla426/snla426.pdf)

### [GND-005] Unjustified AGND/DGND plane split

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** The GND layer is divided by a thin gap line into two (or more) separate polygons; the polygons carry different net names (e.g. AGND/DGND, GNDA/GND) and join at a single point, through a ferrite bead, 0 Ω resistor or net-tie.
- **Why it matters:** ADI (RAQ 63) states that in most cases a split does more harm than good and increases the inductance of the return current; TI and Olney also recommend a single plane + partitioning. Every trace crossing the split forms a large loop and a dipole antenna.
- **Recommended fix:** Use a single, continuous GND plane; place analog and digital circuits in separate regions in XY (partitioning, see GND-008). Remove the existing split or at least apply GND-006.
- **Exceptions:** When the form factor does not allow good partitioning (ADI); very high-resolution applications such as ≥20-bit delta-sigma ADCs (TI SLYT512 weigh-scale example); cases where the datasheet explicitly requires a split and its own evaluation board does so; galvanic isolation (the gap under the isolator is mandatory, see ESD/isolation).
- **Example:** Link: [TI SLYT512, Figure 4](https://www.ti.com/lit/pdf/SLYT512) — Visible: (a) split plane, (b) partitioned single plane.
- **Source:** [ADI Analog Dialogue RAQ 63 (search result only)](https://www.analog.com/en/resources/analog-dialogue/raqs/raq-issue-63.html), [TI SLYT512](https://www.ti.com/lit/pdf/SLYT512), [Barry Olney — Split Planes in Multilayer PCBs](https://www.icd.com.au/articles/Split_Planes_PCBD-Mar2015.pdf), [Autodesk — summary of Ott's partitioning approach](https://www.autodesk.com/products/fusion-360/blog/everyday-app-note-successfully-design-mixed-signal-pcb-partitioning/)

### [GND-006] Split plane has no bridge, or traces cross outside the bridge

- **Severity:** Critical
- **Detectable from image:** Yes
- **How it looks in the image:** The two GND polygons join only at the power supply side (e.g. at the input connector) or not at all; analog↔digital traces cross the split line at different points, away from the bridge. In a correct design there is a single, wide copper bridge across the split line and all crossing traces run directly over that bridge.
- **Why it matters:** If the planes join only at the source, the return current travels all the way to the source; two planes at different RF potentials form an effective dipole antenna (TI SLYT512).
- **Recommended fix:** Join the planes at a single point (usually under the mixed-signal IC) with a wide bridge and route all crossing traces over that bridge. On boards with multiple ADCs, TI recommends joining the planes solidly under all converters.
- **Exceptions:** Regions separated by isolated power/communication (isolator, optocoupler, transformer) contain no bridge.
- **Example:** Link: [TI SLYT512, Figures 2 and 3](https://www.ti.com/lit/pdf/SLYT512) — Visible: Figure 2 planes joined only at the source (wrong), Figure 3 bridge (correct).
- **Source:** [TI SLYT512](https://www.ti.com/lit/pdf/SLYT512)

### [GND-007] Wrong AGND–DGND connection of a mixed-signal IC (ADC/DAC)

- **Severity:** High
- **Detectable from image:** Partly (footprint/schematic information needed for pin names)
- **How it looks in the image:** The ADC's AGND and DGND pins go to different pours via long traces; there is a ferrite bead or resistor footprint between them; the IC sits far from the partition boundary, entirely inside the digital or analog region.
- **Why it matters:** According to ADI, the DGND pin should be joined to AGND next to the package, at the same potential and with the lowest impedance; any extra impedance in between carries digital noise into the analog reference.
- **Recommended fix:** Connect the AGND and DGND pins directly to the single GND plane under the IC with the shortest connection; do not put a ferrite/resistor between them. Place the IC on the analog–digital region boundary; if there is a split plane, the star point should be directly under the IC (TI: minimum trace length, no vias).
- **Exceptions:** Systems with many ADCs on different boards (TI SLYT512 multicard system section); specific datasheet instructions.
- **Example:** Link: [TI SLYT512, Figure 6](https://www.ti.com/lit/pdf/SLYT512) — Visible: correct arrangement with the star point directly under the converter.
- **Source:** [ADI RAQ 9 — Grounding Converters (search result only)](https://www.analog.com/en/analog-dialogue/raqs/raq-issue-9.html), [ADI MT-031 — Grounding Data Converters (search result only)](https://wcm-cce.cldnet.analog.com/media/en/training-seminars/tutorials/mt-031.pdf), [TI SLYT512](https://www.ti.com/lit/pdf/SLYT512)

### [GND-008] Broken partitioning discipline: digital trace runs through the analog region (or vice versa)

- **Severity:** High
- **Detectable from image:** Partly (which region is analog must be known)
- **How it looks in the image:** A clock, SPI, PWM or bus trace on any layer runs through the analog region (op-amp, reference, sensor input, ADC analog side); or an analog input trace wanders in the digital region (next to the MCU, SMPS). When all layers are shown overlaid, both kinds of traces share the same area.
- **Why it matters:** With partitioning, digital return currents stay beneath their traces and do not enter the analog region; but this only holds if the trace stays in its own region. According to TI, the only problem is traces routed into the wrong region.
- **Recommended fix:** Route each signal type within its own region on all layers; define a "route fence" if needed. Keep oscillators and SMPSs ≥10 mm away from critical signals (Olney).
- **Exceptions:** In multilayer stackups with a continuous GND plane between the analog and digital layers, overlap between layers is less critical.
- **Example:** Link: [TI SLYT512, Figure 5](https://www.ti.com/lit/pdf/SLYT512) — Visible: digital trace spilling into the analog region and its return current. [Olney, Figure 1](https://www.icd.com.au/articles/Split_Planes_PCBD-Mar2015.pdf) — route fence example.
- **Source:** [TI SLYT512](https://www.ti.com/lit/pdf/SLYT512), [Barry Olney — Split Planes in Multilayer PCBs](https://www.icd.com.au/articles/Split_Planes_PCBD-Mar2015.pdf), [Autodesk — summary of Ott's partitioning](https://www.autodesk.com/products/fusion-360/blog/everyday-app-note-successfully-design-mixed-signal-pcb-partitioning/)

### [GND-009] No return (GND) via next to a signal that changes layers

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** A fast signal (clock, USB, Ethernet, SPI, RF) changes layers through a via, but there is no GND via near the via (within ≈1–5 mm). In a differential pair the GND vias are on one side only, not symmetric.
- **Why it matters:** When the signal changes reference plane, the return current must change plane too; without a nearby GND via the current detours through a distant via, the loop grows and the impedance becomes discontinuous.
- **Recommended fix:** If both reference planes are GND, place a GND via close to the signal via (TI SNLA426, PCIe Gen5: centre-to-centre ≤50 mil ≈1.27 mm; TI SPRAAR7J: ≤200 mil ≈5 mm, the closer the better), symmetric in a differential pair. If the references are at different potentials (GND↔PWR), use a stitching capacitor close to the transition.
- **Exceptions:** DC and slow signals; transitions between two layers referenced to the same GND plane (e.g. stripline to stripline on the same plane).
- **Example:** —
- **Source:** [TI SNLA426 Section 19](https://www.ti.com/document-viewer/lit/html/SNLA426/GUID-1AE18886-EA7A-45F0-9BA7-15EAE462B587), [TI SPRAAR7J](https://www.ti.com/document-viewer/lit/html/SPRAAR7J/GUID-AD6D2D54-84AC-47F5-A2ED-87883A148A25), [JLCPCB — Ground Plane and Power Plane Guide](https://jlcpcb.com/blog/circuit-board-ground-plane-and-power-plane-guide-2026)

### [GND-010] GND pours on different layers connected by too few stitching vias

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** A large GND pour on the top layer is connected to the bottom plane by only a few vias (e.g. one every few cm); large pour areas have no vias at all. In a good example the vias form a regular grid/fence across the pour, evenly spaced.
- **Why it matters:** A sparsely connected pour stays at different potentials at different points; via spacings can form resonant structures and increase crosstalk (Altium/Peterson). For shielding, the spacing must be much smaller than half a wavelength.
- **Recommended fix:** Choose a spacing of ≤λ/20 of the highest frequency of interest. In the dielectric λ = c / (f·√Dk); for FR-4 (Dk≈4.4) and 1 GHz, λ/20 ≈ 7 mm. On digital boards use the knee frequency (≈0.35/t_rise) instead of f. Add the vias after signal and power routing is finished.
- **Exceptions:** Sources calculate the wavelength differently (free space ↔ in dielectric, ≈2× difference); the in-dielectric value is the conservative one. On low-frequency/DC boards they serve only mechanical/thermal purposes.
- **Example:** —
- **Source:** [Altium — Copper Pour and Stitching: Do You Need Them?](https://resources.altium.com/p/copper-pour-and-stitching-do-you-need-them-pcb-layout), [Atlas PCB — Ground Plane Stitching Via](https://atlaspcb.com/blog/pcb-ground-plane-stitching-via), [RF Essentials — Via stitching and shielding effectiveness](https://rfessentials.com/rf-knowledge-base/what-is-the-effect-of-via-stitching-on-the-shielding-effectiveness-of-a-ground-p/), [TI SNLA426 (0.35/t_r bandwidth)](https://www.ti.com/lit/an/snla426/snla426.pdf)

### [GND-011] No GND via row along the board edge and connectors

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** Top and bottom GND pours extend to the board edge but there are no vias along the edge; or there is a GND pour around external connectors but it is not connected to the inner plane by vias. In a good example a regularly spaced via row ("via fence") is visible along the board edge.
- **Why it matters:** Unconnected pours at the edge can radiate from the edge; JLCPCB lists along the edge, next to connectors and around noisy circuits as priority locations for stitching vias.
- **Recommended fix:** Add a via row along the edge and around connectors with the λ/20 spacing from GND-010; for the distance between edge and via see DFM.
- **Exceptions:** Antenna area and isolation barriers (see RF). RF "via fence" details are in the RF section.
- **Example:** —
- **Source:** [JLCPCB — Ground Plane and Power Plane Guide](https://jlcpcb.com/blog/circuit-board-ground-plane-and-power-plane-guide-2026), [Atlas PCB — Ground Plane Stitching Via](https://atlaspcb.com/blog/pcb-ground-plane-stitching-via)

### [GND-012] Floating (unconnected) copper island

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** On a pour layer, small/medium copper pieces completely surrounded by clearance, with no via or pad connection inside; usually between IC pins, between traces or in a board corner. Reported in KiCad DRC as an "Isolated copper fill" warning.
- **Why it matters:** Unconnected copper can act as an antenna and pick up or radiate EMI; Altium/Peterson recommend that a pour always be grounded and that DRC flag floating conductors.
- **Recommended fix:** Connect the island to the plane with at least one (preferably two) GND vias or remove it (KiCad zone setting "Remove islands: Always" or minimum island area; Altium "Remove Dead Copper"). Rerun DRC after filling.
- **Exceptions:** Intentional copper balancing (copper thieving) areas — these are placed by the manufacturer (see DFM).
- **Example:** —
- **Source:** [Altium — Copper Pour and Stitching](https://resources.altium.com/p/copper-pour-and-stitching-do-you-need-them-pcb-layout), [KiCad 8 PCB Editor — Zones / DRC](https://docs.kicad.org/8.0/en/pcbnew/pcbnew.html)

### [GND-013] Thin GND pour arm connected at one point only (dangling finger) or narrow neck

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** The GND pour extends between two traces as a long, thin tongue and is connected at one end only (no via at its tip); or a large pour region is connected to the main plane through a thin neck.
- **Why it matters:** Thin pour arms can behave like a "guard trace" and increase crosstalk (Altium/Peterson), and an arm not connected at its tip forms a resonant stub. A narrow neck is a bottleneck for that region's return current.
- **Recommended fix:** Remove thin arms (KiCad: minimum pour width/island setting) or place GND vias at both their base and tip; connect large regions to the main plane with several wide connections and vias.
- **Exceptions:** Very short arms (shorter than λ/20 at the frequency of interest) are insignificant.
- **Example:** —
- **Source:** [Altium — Copper Pour and Stitching](https://resources.altium.com/p/copper-pour-and-stitching-do-you-need-them-pcb-layout), [JLCPCB — Ground Plane and Power Plane Guide](https://jlcpcb.com/blog/circuit-board-ground-plane-and-power-plane-guide-2026)

### [GND-014] Noisy/high-current return path runs beneath a sensitive circuit (common impedance)

- **Severity:** High
- **Detectable from image:** Partly (current path is inferred from placement)
- **How it looks in the image:** The power input connector is at one end of the board and the load (motor driver, SMPS, LED driver, relay) at the other; an ADC, reference or sensitive op-amp is placed in the GND plane region between them. When the high current's source→load→source path is drawn, it passes beneath the sensitive circuit.
- **Why it matters:** Large current flowing through the common plane impedance creates a voltage drop in the sensitive circuit's "ground". TI recommends that power enter at the digital section of the board and be filtered from there into the analog section, so that noisy currents never visit the analog region.
- **Recommended fix:** Base the placement on current paths: power input → high-current/noisy section → digital → analog order; keep the sensitive circuit outside the large current loop. If needed, provide a separate, wide pour path for the power return (see PWR, SMPS).
- **Exceptions:** On low-current (≪100 mA) boards the effect is usually small; still, evaluate it against the measurement sensitivity.
- **Example:** Link: [TI SLYT512, Figure 7](https://www.ti.com/lit/pdf/SLYT512) — Visible: placement where power enters at the digital section and is fed through a filter to the analog section.
- **Source:** [TI SLYT512](https://www.ti.com/lit/pdf/SLYT512), [Barry Olney — Split Planes in Multilayer PCBs](https://www.icd.com.au/articles/Split_Planes_PCBD-Mar2015.pdf)

### [GND-015] GND pins connected to the plane by a long trace or a single shared via

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** A trace leaving an IC or capacitor GND pad runs a few mm, merges with the GND traces of other parts and reaches a single via; or the GND pad is connected to the plane only through thin thermal relief spokes and a distant via.
- **Why it matters:** Every extra mm of trace adds inductance (content linked from the JLCPCB guide: ≈1 nH/mm); a shared via passes the return current of several circuits through the same impedance.
- **Recommended fix:** Give each GND pad its own via, adjacent to the pad, with the trace between them as short as possible (sources give no fixed mm limit; each mm adds ≈1 nH); on 2 layers drop a via directly from the GND pin to the bottom plane (Altium). For decoupling capacitor placement see PWR.
- **Exceptions:** THT pads to be hand-soldered may need thermal relief (see DFA/THM); in low-frequency circuits the effect is small.
- **Example:** —
- **Source:** [Altium — Understanding Ground Planes in Your Two-Layer PCB](https://resources.altium.com/pcb-design-blog/understanding-ground-planes-in-your-two-layer-pcb), [JLCPCB — Ground Plane and Power Plane Guide](https://jlcpcb.com/blog/circuit-board-ground-plane-and-power-plane-guide-2026)

### [GND-016] Too few GND pins in a board-to-board connector

- **Severity:** Medium
- **Detectable from image:** Partly (pin assignments must be verified from net names/schematic)
- **How it looks in the image:** On a multi-pin connector linking the board to another board/cable, only one or two pins are connected to the GND pour (with thermal relief or directly); fast signal pins are lined up side by side, far from any GND pin.
- **Why it matters:** All return current between boards passes through a few GND pins; loop area and common impedance grow. TI recommends dedicating at least 30–40% of connector pins to GND.
- **Recommended fix:** Make 30–40% of the pins GND and distribute fast signals between/next to GND pins; connect the GND pins to the plane with their own vias.
- **Exceptions:** Connectors carrying only DC power or very slow signals (current capacity must still be checked, see PWR).
- **Example:** —
- **Source:** [TI SLYT512 — Multicard mixed-signal systems](https://www.ti.com/lit/pdf/SLYT512)
