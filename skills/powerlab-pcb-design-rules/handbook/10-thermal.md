# 10 — Thermal Design (THM)

This section covers using the PCB as a heatsink: thermal vias under an exposed pad (QFN/DFN/PowerPAD), heat-spreading copper, the solder paste aperture of the exposed pad, the choice between thermal relief and a full connection, and keeping temperature-sensitive parts away from heat sources. In surface-mount power packages most of the heat passes through the solder joint into the PCB copper; therefore the real θJA depends much more on the board's copper than on the datasheet value. In most cases the auditor does not know the power dissipation; this information should be requested from the user. For via hole/annular ring manufacturing limits see VIA/DFM, for power trace width see PWR.

---

### [THM-001] No thermal vias under the exposed pad

- **Severity:** High
- **Detectable from image:** Yes (the absence of vias is visible; ask for the power dissipation to judge whether they are needed)
- **How it looks in the image:** The large central pad of a QFN/DFN/PowerPAD/SO-8-EP package has no holes at all; the pad is connected only on the top layer, to copper no larger than the footprint; the layers below have no copper corresponding to this area.
- **Why it matters:** On a multilayer board the main heat path is from the exposed pad down through thermal vias to the inner/bottom copper planes. The θJA values published by TI are measured on a 4-layer JEDEC High-K board with vias; on a board without vias the real temperature is higher.
- **Recommended fix:** Ask the user for the part's power dissipation. In a thermally demanding application, place a thermal via array inside the exposed pad and connect it to the inner/bottom GND plane (for size/pitch see THM-002). The exposed pad must be soldered to the board in every case.
- **Exceptions:** According to TI not every application needs vias; for a low-loss part (e.g. a few tens of mW) a via-less design is acceptable. On a single/double-layer board heat is spread by the surface copper (THM-007).
- **Example:** Link: https://edgeworker.ti.com/lit/pdf/slyt614 — Visible: Figure 6, finished buck layout with vias under the exposed pad.
- **Source:** [TI SLUA271C — QFN and SON PCB Attachment](https://www.ti.com/lit/pdf/slua271), [TI SLMA002H — PowerPAD Thermally Enhanced Package](https://ti.com/cn/lit/slma002), [TI LM61440 — Layout Guidelines](https://ti.com/document-viewer/LM61440/datasheet/GUID-B3BC1FF3-222C-4456-916C-6A98740CD6F4)

### [THM-002] Thermal via diameter or pitch not suitable

- **Severity:** Medium
- **Detectable from image:** Yes (scale needed; the pad size can be used as reference)
- **How it looks in the image:** There are vias with large holes (e.g. ≥0.5 mm hole) inside the exposed pad; or the vias are sparsely arranged at 2–3 mm pitch in only one corner of the pad.
- **Why it matters:** A large hole wicks solder away from the pad during reflow, causing voids and insufficient fill in the solder joint. Sparse vias do not lower the thermal resistance.
- **Recommended fix:** The range common to the sources: hole ~0.3–0.33 mm, pitch ~1.0–1.5 mm. TI SLUA271: start with a 0.3 mm hole, ~1.0 mm pitch. TI SLMA002: ≤0.33 mm hole (1 oz plating), 1.3–1.5 mm pitch in the examples. ROHM HTSOP-J8 example: 0.30 mm hole, 1.20 mm pitch. Check the manufacturer's minimum hole diameter (see DFM; e.g. 0.3 mm at PCBWay standard price, accessed 2026-10).
- **Exceptions:** Vias outside the pad (in copper that is not soldered) have no solder-wicking problem and may be larger.
- **Example:** Link: https://ti.com/cn/lit/slma002 — Visible: Figure 10, example thermal via patterns by package size (good).
- **Source:** [TI SLUA271C](https://www.ti.com/lit/pdf/slua271), [TI SLMA002H](https://ti.com/cn/lit/slma002), [ROHM — PCB Layout Techniques of Buck Converter, Section 4](https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf), [JLCPCB — Thermal Relief Pad Design](https://jlcpcb.com/blog/thermal-relief-pad-design)

### [THM-003] Insufficient number of thermal vias

- **Severity:** Medium
- **Detectable from image:** Partly (the count is visible; the power dissipation is needed to judge sufficiency)
- **How it looks in the image:** An exposed pad several mm on a side has only 1–2 vias; on a large power package the via array covers only a small part of the pad area.
- **Why it matters:** According to the TI SLMA002 graphs, as the via count increases the board thermal resistance first drops quickly and then reaches a point of diminishing returns; the difference between a single via and a few vias is large.
- **Recommended fix:** TI SLMA002: for a small die, 5–9 vias are enough in most applications; on a large package, more as space allows. The JLCPCB blog gives a typical array as 9–25 vias. Take the via count of the datasheet's example land pattern as the starting point.
- **Exceptions:** For low-loss parts a small number of vias is enough; ask the user for the power dissipation.
- **Example:** —
- **Source:** [TI SLMA002H — Figures 8–9](https://ti.com/cn/lit/slma002), [JLCPCB — Thermal Relief Pad Design](https://jlcpcb.com/blog/thermal-relief-pad-design)

### [THM-004] Thermal vias connected to the plane with thermal relief (spokes)

- **Severity:** High
- **Detectable from image:** Yes (inner/bottom layer image needed)
- **How it looks in the image:** In the inner or bottom layer image, a clearance ring with four thin bridges ("wagon wheel") around the exposed pad vias; the vias are connected to the plane with spokes rather than around their full circumference.
- **Why it matters:** Thermal relief means adding thermal resistance to make soldering easier; this is the exact opposite of a thermal via's purpose.
- **Recommended fix:** Connect all thermal vias under the package to the inner planes continuously (solid) around the hole circumference; in CAD, set the zone connection type for these vias or this area to "solid".
- **Exceptions:** —
- **Example:** —
- **Source:** [TI SLMA002H — Section 2.4](https://ti.com/cn/lit/slma002), [JLCPCB — Thermal Relief Pad Design](https://jlcpcb.com/blog/thermal-relief-pad-design)

### [THM-005] Tenting/plugging of exposed pad vias on the wrong side or missing

- **Severity:** Medium
- **Detectable from image:** Partly (solder mask layers and the fabrication note are needed)
- **How it looks in the image:** In the mask layer image, the vias inside the exposed pad are open on the component side, have large holes and there is no plugging note; or the vias are covered with mask only from the opposite (bottom) side (this second case is a common, low-cost choice; see Exceptions below, do not count it as an error on its own).
- **Why it matters:** Open vias can wick solder. Covering from the opposite side traps air inside the via and increases the voids (voiding) seen in X-ray; covering from the component side blocks solder flow.
- **Recommended fix:** Order of preference (TI): plugged via (no risk of solder loss) > mask cap on the component side (cap diameter = hole + at least 0.1 mm). Write the chosen method in the fabrication note and consult the manufacturer. Ask what the manufacturer's standard process does (e.g. at PCBWay standard price "tented via", plugging at extra cost; accessed 2026-10).
- **Exceptions:** According to TI, with an OSP surface finish leaving the vias completely uncovered can give repeatable results; a small hole (≤0.3 mm) reduces the risk. Tenting from the opposite side is the low-cost option accepted in the PCBWay standard-price process and in the METU PowerLab rule (pad side open, opposite side covered); according to TI it increases voiding. If the hole is ≤0.3 mm, note this choice with "Low" severity; do not report it as an error.
- **Example:** Link: https://www.ti.com/lit/pdf/slua271 — Visible: Figure 3-4, X-ray images of different tenting methods.
- **Source:** [TI SLMA002H](https://ti.com/cn/lit/slma002), [TI SLUA271C — Section 3.4.1](https://www.ti.com/lit/pdf/slua271), [PCBWay — PCB Capabilities](https://www.pcbway.com/capabilities.html)

### [THM-006] Exposed pad paste aperture is a single piece at 100%

- **Severity:** Medium
- **Detectable from image:** Partly (F.Paste layer image needed)
- **How it looks in the image:** On the paste layer, a single large rectangular opening over the exposed pad covering the whole pad; the vias fall inside the paste opening.
- **Why it matters:** Printing 1:1 paste on a large pad gives too much solder volume, the part "floats", and opens and bridges can form on the perimeter pins; outgassing is blocked and voids increase.
- **Recommended fix:** TI SLUA271: exposed pad paste coverage is typically ~50–70% of the pad area, split into several small windows (windowpane) (in the example 4 windows, 66%, 0.125 mm stencil). Leave the vias between the windows. At high power the void ratio should be ≤50% by X-ray (TI preference).
- **Exceptions:** For very small exposed pads a single window with a reduced opening may be enough; consult the stencil manufacturer.
- **Example:** Link: https://www.ti.com/lit/pdf/slua271 — Visible: Figure 4-3, example stencil with 4 windows and 66% coverage (good).
- **Source:** [TI SLUA271C — Section 4.4](https://www.ti.com/lit/pdf/slua271), [TI SLMA002H — Section 2.5](https://ti.com/cn/lit/slma002)

### [THM-007] Insufficient tab/drain copper on a power package

- **Severity:** High
- **Detectable from image:** Partly (the copper area can be measured; ask for the power dissipation and ambient temperature)
- **How it looks in the image:** The tab/drain pad of a D-PAK, SOT-223, PowerPAK/SO-8 type MOSFET, diode or regulator has copper only as large as the footprint; traces of other nets crowd around the pad; there is no free copper to spread heat.
- **Why it matters:** Most of θJA depends on the PCB. Diodes AN1157 (1 oz, single-layer FR-4): the θJA of a 5×6 mm package is ~120 °C/W on the minimum pad and drops to ~50 °C/W with ~645 mm² (1 in²) of copper; the curve is logarithmic, the gain decreases as the area grows.
- **Recommended fix:** Ask the user for the power dissipation and maximum ambient temperature; compute Tj = Tambient + P·θJA using a θJA appropriate to the board's copper area (not with RθJC). Connect the tab to the widest copper possible, and if needed duplicate it on the opposite side through vias (THM-008). Some datasheets such as TI LM61440 recommend 2 oz on the top/bottom layers (at least 1 oz).
- **Exceptions:** If the tab is a high-dv/dt node (e.g. the switch node), wide copper increases EMI; balance heat against EMI (see SMPS-005).
- **Example:** —
- **Source:** [Diodes AN1157 — Understanding Thermal Resistance in the Real World](https://www.diodes.com/assets/Uploads/Understanding-Thermal-Resistance-in-the-Real-World-Application-Note.pdf), [TI LM61440 — Layout Guidelines](https://ti.com/document-viewer/LM61440/datasheet/GUID-B3BC1FF3-222C-4456-916C-6A98740CD6F4)

### [THM-008] Heat-spreading copper on one side only, not connected to other layers

- **Severity:** Medium
- **Detectable from image:** Yes (all layers must be visible)
- **How it looks in the image:** There is wide copper around the power part on the top side but no counterpart on the bottom side; or there is wide copper on the bottom side but no vias connecting the two; the vias are only inside the pad, none in the surrounding copper.
- **Why it matters:** The board material has low thermal conductivity; heat passes to copper on the other side/inner layer through vias. Thin copper on the top side alone spreads heat over a limited area.
- **Recommended fix:** Connect the heat-spreading copper to the opposite side and, if present, to the inner GND planes with via arrays. ROHM: if the vias under the pad are insufficient, place additional thermal vias around the IC. Keep the copper area on the opposite side as continuous as possible.
- **Exceptions:** Not applicable on a single-layer board; heat is removed by surface copper and an external heatsink.
- **Example:** Link: https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf — Visible: Figure 3-a, additional thermal vias around the IC.
- **Source:** [TI SLMA002H — Figure 1](https://ti.com/cn/lit/slma002), [ROHM — PCB Layout Techniques of Buck Converter, Section 4](https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf), [Diodes AN1157](https://www.diodes.com/assets/Uploads/Understanding-Thermal-Resistance-in-the-Real-World-Application-Note.pdf)

### [THM-009] Thermal relief in the wrong place: spokes on a power pad, full connection on a THT pin

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** (a) A high-current SMD power pad (MOSFET source/drain, shunt, inductor pad) or exposed pad connected to the pour with 4 thin spokes. (b) A THT connector/pin pad inside a wide GND/power plane, fully embedded in the plane with no clearance ring around it.
- **Why it matters:** (a) Spokes narrow the cross-section: by JLCPCB's estimate a 4-spoke relief with 0.25 mm arms adds ~1–3 mΩ; at 5 A that is ~5–15 mV drop and 25–75 mW of heat. (b) The plane acts like a heatsink and leaves the THT solder joint cold.
- **Recommended fix:** JLCPCB: thermal pads and >3 A pads solid; THT pins in a plane with 0.3–0.5 mm spokes, 0.4–0.6 mm clearance; spoke width at least 0.2 mm (citing IPC-2221B). On a current-carrying THT pin the total spoke cross-section must meet the trace requirement (PWR-001). The assembly problem with a solid pad is solved by preheating. For the assembly side see DFA.
- **Exceptions:** On a very high-current THT pin a solid connection may be a deliberate choice; in this case JLCPCB recommends solving soldering with preheating. Ask the user about the assembly method.
- **Example:** —
- **Source:** [JLCPCB — Thermal Relief Pad Design](https://jlcpcb.com/blog/thermal-relief-pad-design), [TI SLMA002H](https://ti.com/cn/lit/slma002)

### [THM-010] Electrolytic capacitor or temperature-sensitive part adjacent to a heat source

- **Severity:** Medium
- **Detectable from image:** Partly (proximity is visible; measurement/simulation is needed for the real temperature)
- **How it looks in the image:** An aluminium electrolytic (a cylinder in 3D, a circle with a minus sign on the silkscreen) right next to a power MOSFET, shunt, LDO, power resistor or heatsink, on the same heat-spreading copper; a temperature sensor or crystal next to the power stage.
- **Why it matters:** Würth SN008: the expected lifetime of a liquid electrolytic capacitor doubles for every 10 °C drop in component temperature (2 000 h at 105 °C → 8 000 h at 85 °C → 32 000 h at 65 °C); for polymer types a 20 °C drop increases the lifetime tenfold. A capacitor adjacent to a heat source falls far short of its rated lifetime.
- **Recommended fix:** Separate electrolytics and temperature-sensitive parts from heat sources and their heat-spreading copper. No universal mm distance value was found; ask the user for a thermal camera measurement or simulation, and calculate the capacitor lifetime with the real component temperature.
- **Exceptions:** If proximity of the input/output capacitor to the power part is electrically required (SMPS-001), the proximity is kept; in that case a ceramic or high-temperature-class (125 °C) capacitor is chosen.
- **Example:** —
- **Source:** [Würth Elektronik SN008 — Expected Lifetime of Aluminum Electrolytic and Polymer Capacitors](https://www.we-online.com/components/media/o173043v410%20SN008a%20EN.pdf)

### [THM-011] Thermal gradient in a precision measurement circuit (asymmetric copper, proximity to a heat source)

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** A current-sense amplifier, voltage reference or precision op-amp right next to the power switches/shunt; one differential input pin is connected to wide copper and the other to a thin trace; the two inputs are at different distances from the heat source.
- **Why it matters:** A temperature difference between the input pins produces thermal EMF and offset/drift errors; the shunt itself changes resistance as it heats up.
- **Recommended fix:** Place the amplifier in the board's most temperature-stable region, away from heat sources and fast airflow; give both input pins equal copper mass and keep them at equal distance from the heat source. TI: lengthening the input traces is preferred over placing the amplifier in a bad environment (provided the traces stay matched, see PWR-015). Give the shunt as much copper area as possible.
- **Exceptions:** If the accuracy target is loose (e.g. overcurrent detection only), the importance is lower.
- **Example:** —
- **Source:** [TI LMP8640 — Layout Guidelines](https://www.ti.com/document-viewer/LMP8640/datasheet/layout)

### [THM-012] Heatsink mounting not planned for TO-220/TO-247 power packages

- **Severity:** Medium
- **Detectable from image:** Partly (power dissipation and heatsink plan must come from the user)
- **How it looks in the image:** Three-pin in-line THT footprints (TO-220: 2.54 mm pitch, a thick line on the body outline showing the tab side) face different directions on the board and are scattered; the tab sides face other parts and are not lined up on a common line/board edge; there is no footprint, mounting hole or free space for a heatsink.
- **Why it matters:** A common heatsink cannot be fitted to scattered, differently oriented packages; the leads have to be bent afterwards. According to onsemi AN1040, bending leads is not recommended; if necessary, the bend radius on a TO-220 must be >1/32 in and there must be no twisting at the base of the body; the part should first be fixed to the heatsink and then soldered.
- **Recommended fix:** Arrange packages that need a heatsink in a single row with their tab sides facing the same direction, preferably parallel to the board edge. Add to the footprint the height at which the leads seat on the heatsink without bending, and the heatsink mounting holes. Use an insulating pad if needed; according to AN1040 the heatsink surface flatness should be ≤4 mil/in.
- **Exceptions:** Low-loss parts (able to run without a heatsink); in surface-mount packages (D-PAK etc.) heat goes into the board copper (see THM-007).
- **Example:** Link: https://eevblog.com/forum/projects/seeking-feedback-on-my-novice-bldc-driver-pcb-design — Visible error: TO-220 MOSFETs face different directions; experts point out that a heatsink cannot be fitted.
- **Source:** [onsemi AN1040/D — Mounting Considerations for Power Semiconductors](https://www.onsemi.com/pub/Collateral/AN1040-D.PDF)
