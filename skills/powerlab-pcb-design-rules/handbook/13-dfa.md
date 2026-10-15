# 13 — Ease of Assembly / DFA (DFA)

This section covers the rules that decide whether the board is assembled without problems in the pick-and-place, reflow, AOI and hand-rework stages: footprint correctness, part spacing, tombstoning, polarity marks, fiducials, edge clearance, shadowing and via-in-pad. Values vary with the manufacturer's assembly service; JLCPCB and PCBWay (used by METU PowerLab) values are given separately, accessed 2026-10. Scale reference: 0603 body 1.6×0.8 mm, 0402 body 1.0×0.5 mm, SOIC pitch 1.27 mm, pin header pitch 2.54 mm.

### [DFA-001] Footprint land pattern does not follow IPC-7351 or the manufacturer recommendation

- **Severity:** Critical
- **Detectable from image:** Partly (datasheet needed)
- **How it looks in the image:** The pads do not extend past the projection of the part's body/leads (no toe extension) or are excessively long; the gap between two pads is very large relative to the body length (for 0603, suspicious if the distance between the pad inner edges is more than half of the body length (1.6 mm)); the pad count/pitch does not match the package; in the 3D render the leads overhang the pads; on a QFN the pads do not extend beyond the package edge at all. For a definite judgement, ask for the recommended land pattern from the datasheet.
- **Why it matters:** Wrong pad geometry leads to missing solder fillets, bridges, tombstoning and the part floating; a footprint error ruins the whole batch and is hard to repair.
- **Recommended fix:** Generate the footprint according to the IPC-7351 density level (A=Most/wide, B=Nominal/default, C=Least/dense). TI SLUA271 (QFN, 2026-10): the pad should extend ≥0.1 mm outward (toe) and 0.05 mm inward (heel) beyond the package lead; pad width ≥0.05 mm wider than the lead width; at 0.5 mm pitch pad ≤0.28 mm. For hand soldering, a variant with longer pads ("handsolder") can be chosen.
- **Exceptions:** A special land pattern given by the manufacturer in the datasheet takes precedence over the IPC calculation.
- **Example:** Link: https://forum.kicad.info/t/questions-about-assembly-and-tombstoning/27659 — Visible error: assembler's report of widespread tombstoning on 0201s due to "oversized pads" and asymmetric copper.
- **Source:** [Features of IPC-7351 standards (Sierra Circuits)](https://www.protoexpress.com/blog/features-of-ipc-7351-standards-to-design-pcb-component-footprint/), [TI SLUA271 QFN/SON PCB Attachment](https://edgeworker.ti.com/lit/pdf/slua271), [IPC-7351B Compliance (Altium)](https://techdocs.altium.com/display/ADOH1/IPC-7351B+Compliance)

### [DFA-002] Polarity / pin-1 mark missing, ambiguous or hidden under the part

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** On a diode, LED, electrolytic/tantalum capacitor or IC footprint, there is no cathode bar, "+"/"−", dot or chamfer in the silkscreen; the mark is only inside the body outline (it will be covered once the part is fitted); the mark points to the wrong pad (e.g. the bar on the anode side of a diode — not certain without the netlist, compare with the symbol/3D). Different marking styles on similar parts on the same board.
- **Why it matters:** The pick-and-place operator and AOI verify orientation from these marks; a reverse-fitted polarized part can burn the board. Post-assembly visual inspection also needs the mark to remain visible.
- **Recommended fix:** On parts with 3+ pads, the mark must indicate pad 1/A1; on diodes/LEDs the cathode, and on capacitors (including tantalum) the negative terminal is marked (Aisler assembly rules). Place the mark outside the part body so it is visible after assembly (Sierra/Altium). IPC-7351 zero orientation: cathode on the left for diodes, pin 1 at top left for ICs.
- **Exceptions:** Parts that can only be fitted one way (e.g. SOT-323) and non-polarized passives. Silkscreen legibility and placement fall under SLK.
- **Example:** —
- **Source:** [Component Orientation and Polarity Rules for Assembly (Aisler)](https://community.aisler.net/t/component-orientation-and-polarity-rules-for-assembly/45), [DFA Guidelines for an Efficient PCB Design (Altium/Sierra)](https://resources.altium.com/p/dfa-guidelines-efficient-pcb-design), [Features of IPC-7351 standards (Sierra Circuits)](https://www.protoexpress.com/blog/features-of-ipc-7351-standards-to-design-pcb-component-footprint/)

### [DFA-003] Inconsistent orientation of similar parts

- **Severity:** Low
- **Detectable from image:** Yes
- **How it looks in the image:** Parts of the same type (decoupling capacitors, an LED row, identical ICs) randomly rotated by 0°/90°/180°/270°; the plus/cathode terminals of polarized parts face different directions; placement at non-orthogonal angles such as 45°.
- **Why it matters:** Consistent orientation makes visual inspection and AOI programming easier and reduces reverse-fitting errors; in wave soldering, the position of the part axis relative to the flow direction affects solder quality.
- **Recommended fix:** Group similar parts and rotate them to the same orientation; e.g. line up QFPs so that pin 1 is in the same corner (Sierra/Altium). On polarized parts, have all "+" or cathodes face the same direction.
- **Exceptions:** Electrical requirements (loop area, shortest path from a decoupling capacitor to the pin) take precedence over orientation consistency (see PLC/PWR).
- **Example:** —
- **Source:** [DFA Guidelines for an Efficient PCB Design (Altium/Sierra)](https://resources.altium.com/p/dfa-guidelines-efficient-pcb-design), [DFA rules (Sierra Circuits)](https://www.protoexpress.com/kb/dfa-rules/)

### [DFA-004] Insufficient part-to-part spacing for pick-and-place/reflow/rework

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** Much less gap between the pads of two adjacent passives than one 0402 body width (0.5 mm); part bodies/silkscreen outlines touch or overlap each other; a row of passives right at the foot of a large IC. Scale: 10 mil = 0.25 mm ≈ half of a 0402 body width.
- **Why it matters:** Narrow spacing increases the risk of solder bridges, causes the placement nozzle to hit the neighbouring part, and blocks soldering-iron/hot-air access during rework.
- **Recommended fix:** Sierra Circuits DFA table (2026-10): chip–chip 10–20 mil (min 10 mil, optimum 30 mil), SOT–SOT 15–25 mil, SOIC–SOIC 30–50 mil, between QFP/PLCC/BGA 100–120 mil, THT–THT 100–150 mil. Courtyard clearance: default 0.25 mm, below 0603 0.15 mm, BGA 1.0 mm, connector/crystal/can capacitor 0.5 mm. PowerLab: no overlap; for library parts without a courtyard, check with silkscreen and 3D.
- **Exceptions:** Very high-density designs (IPC-7351 level C) can be done with smaller spacing, but the assembler's approval is needed.
- **Example:** —
- **Source:** [DFA rules (Sierra Circuits)](https://www.protoexpress.com/kb/dfa-rules/), [PCB design for assembly checklist (Sierra Circuits)](https://www.protoexpress.com/blog/pcb-design-for-assembly-checklist-important-checks-for-layout-engineers/), [PowerLab PCB_DESIGN_RULES](https://github.com/odtu/Powerlab/blob/master/KiCAD/PCB_DESIGN_RULES.md)

### [DFA-005] No rework clearance around a BGA/QFN/large IC

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** Other parts within 1–2 mm on all four sides of a BGA or large QFN; parts at the same location on the back side of the board too (passives under the BGA projection in the bottom-side render). Scale: 2 mm ≈ slightly more than one 0603 body length (1.6 mm).
- **Why it matters:** The hot-air rework nozzle needs free space around the BGA; neighbouring parts have to be removed first, or they heat up, shift or get damaged. Parts on the back side reflow again during rework.
- **Recommended fix:** Sierra Connect: ≥20 mil courtyard clearance around a BGA and 2–4 mm to other parts; avoid placing parts on the opposite side of the BGA. Sierra courtyard: BGA 1.0 mm.
- **Exceptions:** Placing decoupling capacitors under the BGA (on the back side) may be electrically necessary — it should be noted as an intentional decision (see PWR/HS).
- **Example:** —
- **Source:** [DFA rules (Sierra Circuits)](https://www.protoexpress.com/kb/dfa-rules/), [Ask Me Anything about PCB Design for Assembly (Sierra Connect)](https://sierraconnect.protoexpress.com/t/ask-me-anything-about-pcb-design-for-assembly/2626), [Printed circuit board design for assembly (Cadence)](https://resources.pcb.cadence.com/blog/jbj-printed-circuit-board-design-for-assembly-how-to-dfa)

### [DFA-006] Asymmetric thermal connection on small passives (tombstoning risk)

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** One pad of a 0402/0603 (or 0201) part is embedded directly in a large pour without thermal spokes; the other pad is connected to a thin trace. Or a wide power trace enters one pad and a thin signal trace the other; there is a via just inside one pad and not in the other. Mark it if the "copper surroundings" of the two pads are not visually symmetric.
- **Why it matters:** During reflow the pad connected to the pour melts later; surface tension on the pad that melts first lifts the part upright (tombstone). Pronounced at 0402 and below, can start at 0603.
- **Recommended fix:** Equalize the heat path of both pads: use thermal spokes on the pad connected to the pour, use a trace of the same width as on the other side; if needed, add equivalent copper to the isolated pad as well (Suntron/Reno recommendation: the copper density of each pad should be equal). Check small passives before enabling "solid" connection globally on pours.
- **Exceptions:** Symmetric parts with both pads connected to the same large pour; on 0805 and larger bodies the risk is low. The preference for solid connections on power parts is in PWR/THM.
- **Example:** Link: https://forum.kicad.info/t/questions-about-assembly-and-tombstoning/27659 — Visible error: heavy tombstoning on 0201 resistors with one pad connected to a pour without thermal spokes and the other to a trace. Link: https://forum.allaboutcircuits.com/threads/thermal-relief-yes-or-no.205214/ — discussion of thermal spokes for asymmetric heat paths on 0402s.
- **Source:** [Suntron recommends solutions to 0402 tombstoning (Circuits Assembly)](https://circuitsassembly.com/ca/editorial/menu-news/20006-suntron-recommends-solutions-to-0402-tombstoning.html), [Questions about assembly and tombstoning — KiCad forum](https://forum.kicad.info/t/questions-about-assembly-and-tombstoning/27659), [Avoid PCB Tombstoning in Assembly (LCSC)](https://www.lcsc.com/blog/avoid-tombstoning-in-pcb-assembly-causes-and-analysis/)

### [DFA-007] Global fiducials missing, wrongly sized or symmetric

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** Fiducial: a round copper dot without a hole, ≈1 mm in diameter, with a ≈2 mm mask-free ring around it. Check: at least 3 on each side with SMD parts; near the corners, in an L shape, not on a single straight line and not symmetric (the board must not look the same when rotated by 180°); no trace/silkscreen/via around it; not too close to the board edge.
- **Why it matters:** The pick-and-place machine calculates the board's position and rotation from the fiducials; missing/symmetric fiducials lead to offset or 180°-reversed placement.
- **Recommended fix:** PCBWay (2026-10): diameter 1.0–3.0 mm (standard 1.0), clear area radius ≥2R (3R is better), no copper/silkscreen, ≥5 mm to the board edge, 3 in an L shape, diagonal and asymmetric; on each side for double-sided assembly. JLCPCB (2026-10): ≈1 mm copper, mask opening ≥2× diameter, ≥3.35 mm to the edge including the clear area, min 2 (3 recommended). PowerLab: 3 on each SMD side, 1 mm copper, 2 mm mask opening, 3 mm keepout.
- **Exceptions:** On boards to be assembled only by hand, severity drops to Low (ask the user about the assembly method). If the fiducials are placed on the panel edge rails, they may not be on the single board — ask for a panel image. Panelization falls under MEC.
- **Example:** —
- **Source:** [PCBWay Design Instruction: Panelization, Breakaway Rails, Fiducial Marks, Tooling Holes](https://www.pcbway.com/helpcenter/design_instruction/PCB_Panelization__Breakaway_Rails__Fiducial_Marks__Tooling_Holes.html), [Fiducial Marks (JLCPCB)](https://jlcpcb.com/blog/fiducial-marks), [PowerLab PCB_DESIGN_RULES](https://github.com/odtu/Powerlab/blob/master/KiCAD/PCB_DESIGN_RULES.md)

### [DFA-008] Local fiducials missing for a fine-pitch part

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** No small fiducial dots at two diagonal corners of the footprint around a BGA, QFP or QFN with a pitch of ≤0.5 mm. Estimate the pitch: 0.5 mm pitch ≈ ~40% of the SOIC pitch (1.27 mm); if 3 pins fit within one 0603 body length (1.6 mm) along a QFN side, the pitch is ≈0.5 mm.
- **Why it matters:** Because of board flex and the distance to the global fiducials, the position error on a fine-pitch part can exceed the pad width; local fiducials let the machine re-align in the part's area.
- **Recommended fix:** JLCPCB (2026-10): for BGA/QFP/QFN with ≤0.5 mm pitch, typically 2 local fiducials at diagonal corners of the footprint. Sierra: 2 diagonal ones outside the part. PowerLab: a diagonal local pair for every part with ≤0.5 mm pitch. Size and clear area the same as for global fiducials.
- **Exceptions:** If the assembler has stated that it does not want local fiducials or there is no room; on small boards, if the global fiducials are very close to the part.
- **Example:** —
- **Source:** [Fiducial Marks (JLCPCB)](https://jlcpcb.com/blog/fiducial-marks), [PCB design for assembly checklist (Sierra Circuits)](https://www.protoexpress.com/blog/pcb-design-for-assembly-checklist-important-checks-for-layout-engineers/), [PowerLab PCB_DESIGN_RULES](https://github.com/odtu/Powerlab/blob/master/KiCAD/PCB_DESIGN_RULES.md)

### [DFA-009] Parts in the conveyor/edge rail zone (too close to the board edge)

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** SMD parts or pads closer than a few mm to the long edges of the board; no edge rail (breakaway rail) added. Scale: 3.5 mm ≈ two 0603 body lengths (2×1.6 mm) + a little; 5 mm ≈ two pin header pitches (2×2.54 mm).
- **Why it matters:** The pick-and-place and reflow conveyor holds the board by its long edges; parts in this zone end up under the clamp, get crushed, or clash with the stencil/clamp during paste printing. The manufacturer either adds rails (extra cost) or puts the order on hold.
- **Recommended fix:** PCBWay assembly FAQ (2026-10): if the edge–copper distance is less than 3.5 mm (or a panel is needed), breakaway rails on the two long edges are mandatory; rail ≥3 mm (5/6/7/8/10 mm options). JLCPCB assembly terms (2026-10, via a secondary source): part body–edge ≥2.5 mm; edge rail ≥5 mm. PowerLab: part–edge ≥3.5 mm, otherwise a rail. Sierra: BGA 125 mil, small parts 25 mil (varies by assembler).
- **Exceptions:** Edge-facing connectors (hand/selective soldering, solved with a rail); boards to be assembled only by hand.
- **Example:** —
- **Source:** [PCBWay PCB Assembly FAQ](https://www.pcbway.com/assembly-faq.html), [PCBWay Design Instruction: Panelization, Breakaway Rails, Fiducial Marks, Tooling Holes](https://www.pcbway.com/helpcenter/design_instruction/PCB_Panelization__Breakaway_Rails__Fiducial_Marks__Tooling_Holes.html), [Terms and Conditions of JLCPCB Assembly Service](https://jlcpcb.com/help/article/61-Terms-and-Conditions-of-JLCPCB-Assembly-Service), [PowerLab PCB_DESIGN_RULES](https://github.com/odtu/Powerlab/blob/master/KiCAD/PCB_DESIGN_RULES.md)

### [DFA-010] Tall parts shadow small parts (AOI/nozzle/reflow)

- **Severity:** Medium
- **Detectable from image:** Partly (3D render or height information needed)
- **How it looks in the image:** In the 3D render, 0402/0603 passives or fine-pitch IC leads right at the foot of a tall electrolytic capacitor, inductor, connector or transformer body (at a distance shorter than the body height); tall parts lined up at close spacing with small parts between them. In a 2D image it can only be estimated from the body size; ask for the height from the datasheet.
- **Why it matters:** A tall body prevents the AOI camera from seeing the solder joint of the small part and restricts placement-nozzle access; closely spaced tall parts can create dead zones in a convection oven (this last effect is less well documented).
- **Recommended fix:** Group tall parts with parts of similar height and keep them away from the line of sight of small parts (Cadence). Sierra's test-probe formula gives a height-dependent scale: L = 0.29×H + 0.7 mm (e.g. 4 mm part → ≈1.9 mm); using this distance as a lower bound for small parts too is a reasonable starting point (our own interpretation, see DECISIONS.md).
- **Exceptions:** Electrically mandatory proximity (e.g. power inductor and output capacitor) — in that case add a note for manual inspection instead of AOI.
- **Example:** —
- **Source:** [Cadence DFA guidance (PCB design guide)](https://resources.pcb.cadence.com/i/1541046/25), [PCB design for assembly checklist (Sierra Circuits)](https://www.protoexpress.com/blog/pcb-design-for-assembly-checklist-important-checks-for-layout-engineers/), [PCB design tips for assembly (Elecrow)](https://www.elecrow.com/blog/pcb-design-tips-for-assembly.html)

### [DFA-011] THT parts on both sides / heavy parts on the bottom side

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** THT bodies (connector, electrolytic, relay) in both the top and bottom side renders; large/heavy SMD parts on the bottom side (large inductor, BGA, heavy connector); SMD parts close to THT pins on the solder side (an obstacle for the wave/selective soldering nozzle).
- **Why it matters:** THT on both sides prevents wave soldering; it requires selective soldering (programming cost) or hand soldering (inconsistent quality, high cost). In the second reflow, heavy parts on the bottom side can reflow upside down and fall off.
- **Recommended fix:** Gather THT parts on one side and choose the SMD equivalent if possible; put heavy parts on the top side and leave only small passives/ICs on the bottom side. If a heavy part on the bottom side is unavoidable, ask the assembler about the need for glue. Leave clearance from SMDs around THT pins on the solder side.
- **Exceptions:** Low-volume boards built with an assembler that has selective soldering capability; prototypes assembled only by hand.
- **Example:** —
- **Source:** [Selective or wave soldering (Escatec)](https://www.escatec.com/blog/electronic-pcb-assembly-soldering-selective-or-wave-soldering), [Wave soldering vs reflow for double-sided boards (ALLPCB)](https://www.allpcb.com/es-ES/blog/pcb-knowledge/wave-soldering-vs-reflow-for-double-sided-boards-choosing-the-right-process.html)

### [DFA-012] QFN/BGA pad and stencil design not suitable for assembly

- **Severity:** High
- **Detectable from image:** Partly (paste layer image needed)
- **How it looks in the image:** On the paste (F.Paste) layer, the large centre pad of a QFN has a single opening the same size as the pad (1:1), whereas it should be divided into several small windows. The gap between the centre pad and the perimeter pads is very narrow (0.2 mm ≈ below half of a 0402 body width). A via or trace in the exposed-metal area under the package at the QFN pin-1 corner.
- **Why it matters:** 1:1 centre paste makes the part float on the solder (open leads), and produces bridges and voids; the exposed metal under pin 1 can short to a nearby via.
- **Recommended fix:** TI SLUA271 (2026-10): centre pad paste coverage 50–70% of the pad area (windowed), centre pad–perimeter pad gap ≥0.2 mm, stencil 0.125 mm, at 0.5 mm pitch and below the perimeter apertures can be reduced by up to 20%; NSMD pads are recommended; leave a trace/via keepout next to pin 1. Thermal via placement and count fall under THM.
- **Exceptions:** Cases where the assembler applies its own stencil rules and regenerates the paste layer — ask the assembler.
- **Example:** —
- **Source:** [TI SLUA271 QFN/SON PCB Attachment](https://edgeworker.ti.com/lit/pdf/slua271), [TI SLUA271C — Solder Stencils](https://www.ti.com/document-viewer/lit/html/SLUA271C/GUID-97E90003-17DF-4B4B-9F07-32B6C507B069)

### [DFA-013] Unfilled via inside an SMD pad (solder wicking)

- **Severity:** High
- **Detectable from image:** Partly (the fill/cap order option is not visible in the image)
- **How it looks in the image:** A via with an open hole inside small SMD pads (passive, IC lead, BGA ball); the hole appears as a dark dot in the middle of the pad. If the order notes do not contain "via-in-pad / POFV / filled & capped", assume it is unfilled and ask the user. The design decision to put a via in a pad is in the VIA section; here only the assembly consequence is evaluated.
- **Why it matters:** An open via draws molten solder into the hole during reflow; insufficient solder remains on the pad, and voids and open joints form. This cannot be fixed by process tuning; a design/order fix is required.
- **Recommended fix:** Either move the via out of the pad (leave a mask bridge between pad and via; PowerLab rule), or order filled and copper-capped vias (POFV). JLCPCB (2026-10): POFV free on 6+ layers, paid on 4 layers; epoxy/copper paste fill, min hole 0.15 mm, pad ≥0.35 mm. The PCBWay standard price class includes tented vias; plugged/filled vias carry a surcharge (PowerLab specification). TI SLUA271: on thermal pad vias, a small hole or plugging/tenting reduces solder loss (see VIA, THM).
- **Exceptions:** Thermal vias inside exposed/thermal pads (THM scope; accepted with small holes and windowed paste). Primary rule for this finding: VIA-001; report it as VIA-001.
- **Example:** —
- **Source:** [Free Via in Pad on 6–20 Layer PCBs with POFV (JLCPCB)](https://jlcpcb.com/blog/Free-Via-in-Pad-on-6-20-Layer-PCBs-with-POFV), [BGA Design Guidelines (JLCPCB)](https://jlcpcb.com/help/article/bga-design-guidelines---pcb-layout-recommendations-for-bga-packages), [TI SLUA271 QFN/SON PCB Attachment](https://edgeworker.ti.com/lit/pdf/slua271), [PowerLab PCB_DESIGN_RULES](https://github.com/odtu/Powerlab/blob/master/KiCAD/PCB_DESIGN_RULES.md)
