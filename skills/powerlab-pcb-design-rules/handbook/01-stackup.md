# 01 — Stackup (STK)

The layer stackup determines which plane carries the return current of every signal; a wrong layer assignment cannot be fixed later by routing. This section contains the rules for reference planes, layer assignment and plane spacing on 2- and 4-layer boards. If the auditor cannot work out the layer count and the role of each layer from the screenshot, it must first ask the user for them (see STK-001).

### [STK-001] Layer count and layer roles unknown

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** In KiCad the copper layers are listed in the Appearance panel as `F.Cu`, `B.Cu` and the inner layers `In1.Cu`, `In2.Cu` …; if the panel is not in the image, the layer name cannot be known. Colours depend on the theme (the F.Cu/B.Cu colours have changed between versions), so do not guess the layer from its colour. If only two copper colours are visible, the board may have 2 layers, but the inner layers may also be hidden.
- **Why it matters:** Without knowing the order of the GND, PWR and signal layers, none of the return path, plane slot and via rules can be assessed correctly.
- **Recommended fix:** Before starting the review the auditor should ask the user for: the layer count, the role of each layer (SIG/GND/PWR), the total thickness and dielectric thicknesses (the manufacturer's stackup), a separate screenshot of each layer and an image with the Appearance panel visible.
- **Exceptions:** If the layer names are clearly written in the board's 3D/Gerber image, no extra information is needed.
- **Example:** —
- **Source:** [KiCad 8 PCB Editor documentation](https://docs.kicad.org/8.0/en/pcbnew/pcbnew.html), [JLCPCB — Circuit Board Ground Plane and Power Plane Guide](https://jlcpcb.com/blog/circuit-board-ground-plane-and-power-plane-guide-2026)

### [STK-002] No reference (GND) plane adjacent to a signal layer

- **Severity:** Critical
- **Detectable from image:** Partly (the layer order must be known, see STK-001)
- **How it looks in the image:** The layer directly below/above the layer carrying the signal traces is either full of other signal traces, made of fragmented pours, or has no copper at all. On 4+ layers, a stackup table in which two signal layers (e.g. SIG–SIG) follow each other is also this error.
- **Why it matters:** High-frequency return current flows in the nearest plane directly below the trace; if there is no nearby plane, the loop area grows and radiation and crosstalk increase.
- **Recommended fix:** Every signal and power layer should have at least one GND reference layer adjacent to it (Altium recommendation). 4 layers: SIG–GND–GND–SIG or SIG–GND–PWR–SIG; 6 layers: SIG–GND–SIG–PWR–GND–SIG.
- **Exceptions:** On a 2-layer board this can only be achieved by leaving the bottom layer largely as GND (see STK-003).
- **Example:** —
- **Source:** [Altium — PCB Stackup Basics](https://resources.altium.com/p/pcb-stackup-basics), [Barry Olney — Split Planes in Multilayer PCBs (PCB Design Magazine, 2015)](https://www.icd.com.au/articles/Split_Planes_PCBD-Mar2015.pdf)

### [STK-003] Bottom layer not kept as GND on a 2-layer board

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** In the B.Cu image the GND pour is cut into many pieces by long traces and looks like a "patchwork"; or there is no pour on the bottom layer at all and both layers are densely routed. In a good example the bottom layer is an almost uninterrupted single-colour area with only short (a few mm) bridge traces on it.
- **Why it matters:** On a 2-layer board the only reference plane is the bottom layer; splitting it lengthens the return path of every top-layer signal (see GND-001).
- **Recommended fix:** Dedicate the bottom layer to GND and do the routing on the top layer; keep the unavoidable crossings short and away from under fast signals. Fill the empty areas on top with GND and connect them to the bottom with stitching vias. If GND cannot be provided for all signals, move to 4 layers.
- **Exceptions:** On very low-frequency/DC boards (e.g. only relays, LEDs) the effect is small; it should still be applied if there will be EMC testing.
- **Example:** —
- **Source:** [Altium — Understanding Ground Planes in Your Two-Layer PCB](https://resources.altium.com/pcb-design-blog/understanding-ground-planes-in-your-two-layer-pcb), [Sierra Circuits forum — Ground Plane Strategy for a 2-Layer PCB](https://sierraconnect.protoexpress.com/t/ground-plane-strategy-for-a-2-layer-pcb-from-an-emi-emc-perspective/3630), [JLCPCB — Ground Plane and Power Plane Guide](https://jlcpcb.com/blog/circuit-board-ground-plane-and-power-plane-guide-2026)

### [STK-004] 4-layer stackup choice does not fit the application

- **Severity:** Medium
- **Detectable from image:** Partly (inner layer images needed)
- **How it looks in the image:** Inspect the In1 and In2 images. In SIG–GND–PWR–SIG, In2 consists of polygons split into more than one power rail; in SIG–GND–GND–SIG both inner layers are a single GND pour and power is carried on the outer layers with wide pours/traces.
- **Why it matters:** In SIG–GND–PWR–SIG the bottom-layer signals reference the PWR plane, and the return current of a signal that changes layer has to pass from GND to PWR. In SIG–GND–GND–SIG every signal is referenced to GND, but high-current/multi-rail power distribution becomes harder.
- **Recommended fix:** On low-to-medium-current boards with few rails and fast signals, prefer SIG–GND–GND–SIG. On high-current or multi-rail boards use SIG–GND–PWR–SIG (or SIG–GND–PWR–GND); keep critical signals on the top layer (over GND).
- **Exceptions:** Sources disagree on this (the Bogatin/Hartley line argues against a power plane on 4 layers, Altium/Peterson defend a power layer at high current); the decision should be made based on current and rail count.
- **Example:** —
- **Source:** [Altium — SIG/GND/SIG + PWR/GND Stackups](https://resources.altium.com/p/siggndsig-pwrgnd-stackups-will-work-4-layer-pcbs), [Altium — PCB Stackup Basics](https://resources.altium.com/p/pcb-stackup-basics), [JLCPCB — Ground Plane and Power Plane Guide](https://jlcpcb.com/blog/circuit-board-ground-plane-and-power-plane-guide-2026)

### [STK-005] High-speed signal references a power plane or crosses a power plane split

- **Severity:** High
- **Detectable from image:** Partly (layer roles must be known)
- **How it looks in the image:** A clock/USB/SPI trace on B.Cu (in a SIG–GND–PWR–SIG stackup) crosses, perpendicular or parallel, the dark gap line between two different power polygons in the In2 image. When the two layer images are overlaid, the trace passes over the polygon boundary.
- **Why it matters:** At the power split boundary the return current path is cut, and the current detours through a distant decoupling capacitor; radiation, delay and crosstalk increase.
- **Recommended fix:** Move high-speed signals to a GND-referenced layer. If the crossing is unavoidable, place a ≤1 µF "stitching" capacitor across the boundary, as close as possible to the crossing point (TI SPRAAR7J). Avoid overlapping planes that do not reference each other.
- **Exceptions:** Not important for DC or very slow signals (e.g. enable pin, LED).
- **Example:** —
- **Source:** [TI SPRAAR7J — reference plane guidelines](https://www.ti.com/document-viewer/lit/html/SPRAAR7J/GUID-AD6D2D54-84AC-47F5-A2ED-87883A148A25), [TI SNLA426 — High-Speed PCB Layout for PCIe Gen 5, Section 19](https://www.ti.com/document-viewer/lit/html/SNLA426/GUID-1AE18886-EA7A-45F0-9BA7-15EAE462B587)

### [STK-006] PWR–GND plane capacitance relied on in a standard 4-layer stackup

- **Severity:** Medium
- **Detectable from image:** No (stackup table needed)
- **How it looks in the image:** Not visible in the image. Indirect hint: on a SIG–GND–PWR–SIG board there is no local decoupling capacitor next to the IC power pins and the user says "the planes are already a capacitor". The auditor should ask for the manufacturer's stackup (L2–L3 core thickness).
- **Why it matters:** In the JLCPCB 1.6 mm 4-layer (7628) stackup the L1–L2 prepreg is ≈0.2 mm and the L2–L3 core is ≈1.065 mm; no meaningful plane capacitance forms between planes this far apart. The recommendation attributed to Ott is a PWR–GND spacing of 2–3 mil (≈0.05–0.08 mm) for plane capacitance.
- **Recommended fix:** In a standard stackup place a decoupling capacitor close to every IC power pin (see PWR). If plane capacitance is really needed, ask the manufacturer for a custom stackup with a thin dielectric.
- **Exceptions:** Custom 6+ layer stackups in which the PWR–GND pair is separated by thin prepreg.
- **Example:** —
- **Source:** [JLCPCB Help Center — PCB Stackup (accessed 2026-10; search result only)](https://jlcpcb.com/quote/pcbOrderFaq/PCB%20Stackup), [In Compliance Magazine — PCB Layer Stack-Up Considerations for EMC](https://incompliancemag.com/most-important-pcb-layer-stack-up-considerations-that-achieve-optimal-emc-performance/), [Altium — PCB Stackup Basics](https://resources.altium.com/p/pcb-stackup-basics)

### [STK-007] Controlled impedance designed as microstrip on a 2-layer 1.6 mm board

- **Severity:** High
- **Detectable from image:** Partly (board thickness and layer count must be known)
- **How it looks in the image:** On a 2-layer board a USB/Ethernet/RF trace is the same width as the other traces (e.g. 0.2–0.3 mm) and has no GND pour next to it (coplanar GND); a wide empty (dark) area is visible around the trace.
- **Why it matters:** Over ≈1.5 mm of dielectric (εr 4.4) the trace width for a 50 Ω microstrip should be ≈2.8 mm; on 4 layers, over ≈0.2 mm prepreg, the same impedance is ≈0.33 mm (calculated with the IPC-2141 approximate microstrip formula). A thin trace on 2 layers has a very high impedance.
- **Recommended fix:** On 2 layers design impedance-controlled lines as coplanar GND (CPWG): GND pour close to both sides of the trace and dense stitching vias; verify the impedance with the manufacturer's calculator. If this is not practical, move to 4 layers.
- **Exceptions:** If the line length is very short relative to the rise time (electrically short), impedance control may not be needed; see HS.
- **Example:** —
- **Source:** [Altium — Understanding Ground Planes in Your Two-Layer PCB](https://resources.altium.com/pcb-design-blog/understanding-ground-planes-in-your-two-layer-pcb), [JLCPCB PCB Capabilities (7628 Dk 4.4, accessed 2026-10)](https://jlcpcb.com/capabilities/pcb-capabilities)

### [STK-008] Power plane pulled back because of the "20H rule" / auditor demanding 20H

- **Severity:** Low
- **Detectable from image:** Yes
- **How it looks in the image:** The inner PWR plane ends noticeably (a few mm) further in from the board edge than the GND plane; in the PWR layer image there is a wide empty frame around the pour.
- **Why it matters:** The claim that the 20H rule reduces radiation is not supported by measurements; Shim & Hubing measurements and LearnEMC report that the rule can slightly increase radiation. The Altium summary cites a study that reports only a limited benefit (~5 dBµV/m) below ≈300 MHz.
- **Recommended fix:** Do not flag 20H as an error or a requirement. Instead check that the GND plane extends to the edge and that there are stitching vias along the edge (see GND-011). For mechanical/manufacturing pullback see DFM.
- **Exceptions:** If the PWR plane is pulled back because of screw/chassis contact at the edge or a high-voltage clearance, this is legitimate.
- **Example:** —
- **Source:** [LearnEMC — EMC Design Myths](https://learnemc.com/emc-design-myths), [Missouri S&T — 20-H Rule Modeling and Measurements](https://scholarsmine.mst.edu/ele_comeng_facwork/5806), [Altium — The PCB Layout Rules of Thumb Debate](https://resources.altium.com/p/great-pcb-layout-rules-thumb-debate-rages)

### [STK-009] Reference plane layer partly filled or zone not filled

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** In the image of the inner GND layer (or B.Cu on 2 layers) the pour covers only part of the board; on part of the board the layer is completely empty. In KiCad an unfilled zone appears only as an outline with hatched strips at the corners and is empty inside; a filled zone is a solid area in the layer colour.
- **Why it matters:** Signals beyond the point where the pour ends lose their reference plane; a screenshot taken with an unfilled zone misleads the auditor (a plane is assumed to exist, but it is not in the Gerber that will be manufactured).
- **Recommended fix:** Draw the reference plane zone boundary up to the board edge (inset by the manufacturer's edge clearance, see DFM), fill all zones (KiCad: "Fill All Zones", shortcut B) and run DRC in the filled state. The auditor should ask for an image taken with the zones filled.
- **Exceptions:** Intentional copper-free areas such as an antenna keep-out area, isolation barrier or mechanical cut-out (see RF, MEC).
- **Example:** —
- **Source:** [KiCad 8 PCB Editor documentation — Zones](https://docs.kicad.org/8.0/en/pcbnew/pcbnew.html), [Altium — PCB Stackup Basics](https://resources.altium.com/p/pcb-stackup-basics)
