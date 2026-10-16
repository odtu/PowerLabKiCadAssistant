# 14 — Silkscreen (SLK)

The silkscreen (print/legend) layer is not electrical, but it is the board's "user manual" for assembly, inspection, debugging and field maintenance. Most rules in this section can be checked directly from a screenshot; for size checks, use a known dimension in the image (e.g. 2.54 mm header pitch, 0603 pad length ≈ 1.6 mm) as a ruler. Whether polarity marks are required for assembly belongs to DFA, and the distance of copper from the board edge belongs to DFM; here only silkscreen visibility is covered.

### [SLK-001] Silkscreen on a pad, an exposed via or a mask opening

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** White (or the chosen silk colour) lines/text passing over copper-coloured pads, exposed (not tented) via rings or test pads; silk and pad layers overlapping in the 2D view. If cut/missing letters appear on a pad in the 3D render, the manufacturer has already clipped the silk. In KiCad DRC, the "Silkscreen clipped by solder mask" warning corresponds to this.
- **Why it matters:** Ink on a pad reduces solderability; because the manufacturer clips the silk from the mask opening at the CAM stage, the text becomes illegible.
- **Recommended fix:** Keep the silk at least 0.15 mm from the pad edge (JLCPCB pad–silk clearance 0.15 mm, accessed 2026-10); at least 6 mil (0.15 mm) on dense packages such as BGA. Shift the label off the pad, shorten the footprint silk.
- **Exceptions:** Silk may be printed over vias fully covered (tented) by mask (Atlas PCB: 0 mm allowed).
- **Example:** Link: https://forum.kicad.info/t/warning-silkscreen-clipped-by-solder-mask/46445 — Visible error: "clipped by solder mask" warning caused by silk running onto a pad.
- **Source:** [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [Top ten tips for nailing your PCB silkscreen design (EE World)](https://www.eeworldonline.com/top-ten-tips-for-nailing-your-pcb-silkscreen-design/), [Atlas PCB – Silkscreen legend design](https://atlaspcb.com/blog/pcb-silkscreen-legend-design)

### [SLK-002] Text height or line width below the manufacturer limit

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** Labels clearly smaller than the neighbouring 0402/0603 pads; if the letter height is less than ~40% of the 2.54 mm header pitch (≈1 mm), or the letters look like solid blobs/illegible lines in the 3D render, they may be below the limit. For an exact measurement, ask the user for the Gerber/DRC value.
- **Why it matters:** Text below the limit is either not printed or the ink spreads and the letters merge; the label is useless for assembly and repair.
- **Recommended fix:** JLCPCB: height ≥ 1.0 mm, line ≥ 0.15 mm, width/height 1:6. PCBWay standard: height ≥ 0.8 mm, line ≥ 0.15 mm, 1:5 (both accessed 2026-10). Safe value suitable for both manufacturers: 1.0 mm / 0.15 mm.
- **Exceptions:** On a very dense board, labels can be moved to the assembly drawing (Fab layer); in that case no size rule is needed on the silk, but the assembly drawing must be delivered.
- **Example:** —
- **Source:** [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [PCBWay PCB Capabilities](https://www.pcbway.com/capabilities.html)

### [SLK-003] Reference labels in more than two reading directions

- **Severity:** Low
- **Detectable from image:** Yes
- **How it looks in the image:** Upside-down (180°) text on the same side, vertical text read both from the left and from the right (90° and 270° mixed), or labels slanted at 45°. In the correct state all text reads either left to right or bottom to top.
- **Why it matters:** The technician has to keep rotating the board; confusions such as "6/9" or "U1/IN" read upside down cause assembly and debugging errors.
- **Recommended fix:** Use only two directions: left to right (0°) and bottom to top (90°). For a horizontal part put the label to its left, for a vertical part below it.
- **Exceptions:** If the board's operating position is known (e.g. panel-mounted, a board viewed from one direction only), a single direction may be preferred; some sources recommend all labels be horizontal — both approaches are compatible with "at most two directions".
- **Example:** —
- **Source:** [Top ten tips for nailing your PCB silkscreen design (EE World)](https://www.eeworldonline.com/top-ten-tips-for-nailing-your-pcb-silkscreen-design/), [Atlas PCB – Silkscreen legend design](https://atlaspcb.com/blog/pcb-silkscreen-legend-design)

### [SLK-004] Reference label hidden under the component body

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** In the 2D view the label is inside the footprint's body outline/courtyard, between the pads; in the 3D render the label is not visible, or only part of it sticks out from the edge of the part.
- **Why it matters:** After assembly the label is covered and is useless for repair and inspection; under low parts such as 0201/0402/QFN, the ink thickness can lift the part and cause a reflow defect.
- **Recommended fix:** Place the label outside the body, within ~2 mm of the part, so that it is clear which part it belongs to. If there is no room, move the label to the Fab/assembly drawing.
- **Exceptions:** On large THT parts (e.g. electrolytic capacitor) an under-body label guides assembly; however, legibility after assembly is not expected.
- **Example:** Link: https://eevblog.com/forum/blog/eevblog-1334-mystery-dumpster-teardown — Visible error: the forum criticizes carelessly placed labels for making debugging harder (from the search-result summary of the content; image not verified).
- **Source:** [PCB Silkscreen: Consider your Stakeholders (Boulder Engineering)](https://www.boulderes.com/resource-library/pcb-silkscreen-know-your-audience-0), [Top ten tips for nailing your PCB silkscreen design (EE World)](https://www.eeworldonline.com/top-ten-tips-for-nailing-your-pcb-silkscreen-design/), [How to Make Your PCB Layout AOI and X-Ray Friendly (Altium)](https://resources.altium.com/p/optimize-pcb-layout-for-aoi-x-ray)

### [SLK-005] Ambiguous which part a label belongs to

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** A label at equal distance from two parts; the label orientation does not match the orientation of the nearby part; in a row of passives the label order differs from the part order (parts in R7 R5 R6 order under the text R5 R6 R7).
- **Why it matters:** The wrong part gets replaced/measured; a wrong value gets fitted during assembly.
- **Recommended fix:** Move the label to the position closest to its own part and clearly away from the others. In dense areas, give the labels as a group and point to the part with an arrow/line, or put an ordered list next to the row.
- **Exceptions:** —
- **Example:** —
- **Source:** [Top ten tips for nailing your PCB silkscreen design (EE World)](https://www.eeworldonline.com/top-ten-tips-for-nailing-your-pcb-silkscreen-design/), [PCB Silkscreen Guidelines (Altium)](https://resources.altium.com/p/your-guide-pcb-silkscreen)

### [SLK-006] Polarity / pin-1 mark not visible after assembly

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** No cathode bar, "+", dot or "1" on diodes, LEDs, tantalum/electrolytic capacitors, ICs and connectors; or the mark is only inside the body outline (disappears under the part in the 3D render). On low-profile ICs the pin-1 dot must be outside the body.
- **Why it matters:** A reverse-fitted polarized part breaks or burns the circuit; after assembly, reverse fitting cannot be noticed in visual inspection.
- **Recommended fix:** Place the mark outside the body outline, next to the pin-1/cathode pad (Atlas PCB: dot diameter 0.5–1.0 mm). On long-lead parts use a line along the pad, on chip parts use silk wrapping the pin-1/cathode side. Rotate the polarized parts in the same functional block to the same orientation.
- **Exceptions:** On packages whose leads are under the body, such as BGA/QFN/DFN, leaving a gap in the body outline at the pin-1 corner may be considered sufficient according to IPC-7351 convention. For polarity rules from the assembly point of view see DFA. Primary rule for this finding: DFA-002; report it as DFA-002.
- **Example:** —
- **Source:** [PCB Libraries Forum – IPC-7351 pin 1 / polarity marking](https://www.pcblibraries.com/forum/topic1530.html), [Atlas PCB – Silkscreen legend design](https://atlaspcb.com/blog/pcb-silkscreen-legend-design), [Top ten tips for nailing your PCB silkscreen design (EE World)](https://www.eeworldonline.com/top-ten-tips-for-nailing-your-pcb-silkscreen-design/)

### [SLK-007] No pin number / signal name / power polarity on connectors

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** No text such as "1", "GND", "VIN", "+/−", "TX/RX" next to pin headers, terminal blocks, programming and power input connectors; only a reference such as "J3".
- **Why it matters:** A cable can be connected backwards, the power input can be fed with reverse polarity; in the field, connections cannot be made without the schematic.
- **Recommended fix:** Number at least the first and last pins; write the signal name of every pin on power and debug connectors; on terminal blocks give the wire colour/signal name and the mating direction (KEY/arrow).
- **Exceptions:** On connectors whose pinout is mechanically keyed and that mate in only one direction (e.g. latching JST), a signal name is still recommended but a pin number may be enough.
- **Example:** —
- **Source:** [PCB Silkscreen Guidelines (Altium)](https://resources.altium.com/p/your-guide-pcb-silkscreen), [Atlas PCB – Silkscreen legend design](https://atlaspcb.com/blog/pcb-silkscreen-legend-design), [PCB Silkscreen: Consider your Stakeholders (Boulder Engineering)](https://www.boulderes.com/resource-library/pcb-silkscreen-know-your-audience-0)

### [SLK-008] No board name, revision and date

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** No project/board name, revision such as "Rev A"/"v1.1", or date code (e.g. "2026-10", YYWW) visible on either side of the board; or the revision is only on a copper layer and too small to read.
- **Why it matters:** When more than one revision is in circulation, it cannot be told which board belongs to which schematic/Gerber set; failure analysis and boards returned from the field cannot be traced.
- **Recommended fix:** Write a single line "BOARDNAME Rev X YYYY-MM" at a fixed place near the edge; put the revision right next to the part number; leave at least 10 × 3 mm of free space for the manufacturer's date code (Atlas PCB).
- **Exceptions:** Information that changes per board, such as a serial number, is given with a label/laser/QR, not with silk.
- **Example:** —
- **Source:** [Top ten tips for nailing your PCB silkscreen design (EE World)](https://www.eeworldonline.com/top-ten-tips-for-nailing-your-pcb-silkscreen-design/), [Atlas PCB – Silkscreen legend design](https://atlaspcb.com/blog/pcb-silkscreen-legend-design), [What Is Silkscreen on PCB? (Best Technology)](https://www.bestpcbs.com/blog/2026/05/what-is-silkscreen-on-pcb-clear-marking-for-better-assembly/)

### [SLK-009] Logo or decorative graphic does not follow the rules

- **Severity:** Low
- **Detectable from image:** Partly
- **How it looks in the image:** The logo runs over vias or pads; fine detail lines are clearly thinner than the surrounding 0.15 mm text lines; the logo covers component labels/polarity marks or draws more attention than them.
- **Why it matters:** Lines below the limit are not printed or come out blurred; a logo running onto a pad creates the SLK-001 problem; it overshadows functional marks.
- **Recommended fix:** Include the logo in the silk Gerber, put it in a free area, keep its thinnest line ≥ 0.15 mm (JLCPCB/PCBWay, accessed 2026-10) and apply the pad/via clearance rule.
- **Exceptions:** Logos made in copper or mask are subject not to the silk rule but to the DFM copper/mask rules (see DFM).
- **Example:** —
- **Source:** [Atlas PCB – Silkscreen legend design](https://atlaspcb.com/blog/pcb-silkscreen-legend-design), [PCB Silkscreen Guidelines (Altium)](https://resources.altium.com/p/your-guide-pcb-silkscreen)

### [SLK-010] No label (TP number / net name) on test points

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** There are round pads with open mask or test rings, but no text such as "TP3", "3V3", "GND" next to them; or the text is on the pad.
- **Why it matters:** Which net you are putting the probe on cannot be told without opening the schematic; ink on the pad increases contact resistance.
- **Recommended fix:** Write the TP number and, if possible, the net name next to (not on) every test point; on power rails also write the voltage (e.g. "TP1 3V3"). Atlas PCB recommends a 0.8 mm height for test point labels; this is below JLCPCB's 1.0 mm limit — use 1.0 mm at JLCPCB.
- **Exceptions:** On production boards with hundreds of TPs intended only for a fixture (bed-of-nails), the net name can be given in the assembly/test documentation. For test point design see TST.
- **Example:** —
- **Source:** [Maximizing Circuit Reliability with PCB Test Points and Smart DFT (JLCPCB)](https://jlcpcb.com/blog/pcb-test-points-and-smart-dft), [PCB Silkscreen: Consider your Stakeholders (Boulder Engineering)](https://www.boulderes.com/resource-library/pcb-silkscreen-know-your-audience-0), [Atlas PCB – Silkscreen legend design](https://atlaspcb.com/blog/pcb-silkscreen-legend-design)

### [SLK-011] Silk line between the pads of a small two-pin part or under a low-profile package

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** A line passing between the two pads of a 0402/0603 resistor-capacitor; a full rectangular silk frame under a QFN/DFN/LGA, lying between the pads.
- **Why it matters:** The ink thickness lifts the small part off the pad and impairs solder wetting; a line between pads can increase the risk of solder bridges.
- **Recommended fix:** Keep the body outline outside the pads; on chip parts use only short side lines parallel to the pads, or no lines at all.
- **Exceptions:** On large THT parts an under-body frame is not a problem.
- **Example:** —
- **Source:** [Top ten tips for nailing your PCB silkscreen design (EE World)](https://www.eeworldonline.com/top-ten-tips-for-nailing-your-pcb-silkscreen-design/), [PCB Silkscreen: Consider your Stakeholders (Boulder Engineering)](https://www.boulderes.com/resource-library/pcb-silkscreen-know-your-audience-0)

### [SLK-012] Bottom-side silkscreen text not mirrored

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** In the top view (flip off), the bottom-side (B.SilkS) text reads normally. In the correct state, bottom-side text looks like a mirror image when viewed from the top, and reads normally when the board is flipped (flip/bottom 3D view). If the text is reversed in the bottom 3D render, the error is certain.
- **Why it matters:** All text on the bottom side of the manufactured board is printed reversed; labels are illegible and the board looks amateurish.
- **Recommended fix:** Enable the "mirrored/justify mirror" property on bottom-side text; do the check in the bottom 3D render. After flipping a footprint, check that the bottom silk positions do not overlap pads (see SLK-001).
- **Exceptions:** —
- **Example:** Link: https://forum.kicad.info/t/back-layer-silkscreen-reference-designators-reversed/53339 — Visible error: bottom-layer reference labels coming out reversed (from the title; from the search-result summary of the content).
- **Source:** [KiCad GitLab issue #18235 (text mirroring behaviour)](https://gitlab.com/kicad/code/kicad/-/issues/18235), [KiCad Forum – Silkscreen/fab layer confusion](https://forum.kicad.info/t/silkscreen-fab-layer-confusion/52521), [KiCad Forum – Back Layer Silkscreen Reference Designators Reversed](https://forum.kicad.info/t/back-layer-silkscreen-reference-designators-reversed/53339)

### [SLK-013] Manufacturer mark (order/serial no., barcode) location unclear or an old placeholder left

- **Severity:** Low
- **Detectable from image:** Yes
- **How it looks in the image:** Old order-number placeholder text such as "JLCJLCJLCJLC" in the silkscreen; or a purposeless filled silk square on a visible surface (front side, next to the logo). If a manufacturer mark was requested but its location is not indicated, no mark appears in the image; ask the user about the order option.
- **Why it matters:** If no location is specified, the manufacturer places its mark in a free area itself; on a visible side it can spoil the aesthetics, or be illegible near traces/holes. JLCPCB (2026-05 update) no longer adds a mark by default; the old placeholder text gets printed as unnecessary silk.
- **Recommended fix:** If no mark is wanted, remove the placeholder text. If a barcode/serial number is wanted, select "Specify Position" at JLCPCB and place a filled square of barcode size (5×5, 8×8 or 10×10 mm) on the silk layer, or a 2×10 mm filled square for the number only; place it away from traces, holes and other silk, preferably on a large mask area over copper (JLCPCB, accessed 2026-10). For other manufacturers ask about the current option.
- **Exceptions:** If a serial number is mandatory for product traceability, having it on the visible side is intentional.
- **Example:** Link: https://forum.kicad.info/t/pcb-review-request/40027 — Visible error: "JLCJLCJLC" text in an open area on the bottom side; a commenter suggested hiding it under the module.
- **Source:** [JLCPCB Help — How to mark on PCB?](https://jlcpcb.com/help/article/how-to-mark-on-pcb)
