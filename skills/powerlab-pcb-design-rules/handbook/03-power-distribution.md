# 03 — Power Distribution (PWR)

This section covers carrying the supply voltages from the input to the load: trace width and copper thickness, layer transitions, decoupling and bulk capacitors, LDO placement, star distribution, Kelvin sense connections and input protection (fuse, reverse polarity). Because the auditor only sees a screenshot, current, copper thickness and part values are often not in the image; in that case the rule says which information to ask the user for. For loops specific to switching regulators see `08-switching-power.md` (SMPS), for thermal topics see `10-thermal.md` (THM), for general ground plane rules see GND, for via drill/annular ring limits see VIA/DFM.

---

### [PWR-001] Power trace too thin for the current (outer layer)

- **Severity:** Critical
- **Detectable from image:** Partly (the width can be measured; current and copper thickness must be requested from the user)
- **How it looks in the image:** Between the pads of a connector, fuse, MOSFET, inductor, shunt or regulator, traces almost as thin as the signal traces; a wide power pad entered with a trace much narrower than the pad width. Compare against a reference of known width (e.g. SOIC pin pitch 1.27 mm). If one part of the same net is wide and another part thin, the thin part is decisive.
- **Why it matters:** The I²R loss in the trace resistance heats the trace and creates a voltage drop; overheating stresses the laminate and solder joints. The IPC-2221 curves give the required cross-sectional area for the allowed temperature rise.
- **Recommended fix:** Size with IPC-2221 (I = 0.048·ΔT^0.44·A^0.725, A in mil², outer layer). 1 oz, ΔT = 10 °C: 1 A ≈ 0.30 mm, 2 A ≈ 0.78 mm, 3 A ≈ 1.37 mm, 5 A ≈ 2.8 mm. 1 oz, ΔT = 20 °C: 1 A ≈ 0.20 mm, 3 A ≈ 0.90 mm, 5 A ≈ 1.8 mm. Above ~3 A use a pour/polygon instead of a trace. Ask the user for the continuous current, the allowed ΔT and the copper thickness.
- **Exceptions:** The formula is for long traces; it does not apply to very short connections such as a pin exit neck of a few mm or a thermal relief (see PWR-004). A narrower trace can be justified with IPC-2152 taking a nearby plane into account (see PWR-002). For pulse currents the RMS value is used.
- **Example:** —
- **Source:** [How To Calculate Maximum Track Current (mbedded.ninja)](https://blog.mbedded.ninja/pcb-design/how-to-calculate-maximum-track-current/), [ROHM — PCB Layout Techniques of Buck Converter, Figure 5](https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf), [Cadence — IPC-2152 vs. IPC-2221](https://resources.system-analysis.cadence.com/blog/ipc-2152-vs-ipc-2221-which-to-use-for-pcb-thermal-analysis)

### [PWR-002] Inner layer power trace sized with the outer layer table

- **Severity:** High
- **Detectable from image:** Partly (the layer name must be visible in the screenshot; the current must be asked for)
- **How it looks in the image:** In the inner layer (In1.Cu/In2.Cu) image a power trace has the same width as an outer layer trace carrying the same current; or all power traces have the width of a single net class regardless of layer.
- **Why it matters:** An inner layer trace cannot give its heat to the air; in IPC-2221 the inner layer constant is half that of the outer layer (k = 0.024), which means a trace about 2.6 times wider for the same current.
- **Recommended fix:** IPC-2221 inner layer, 1 oz, ΔT = 10 °C: 1 A ≈ 0.78 mm, 2 A ≈ 2.0 mm, 3 A ≈ 3.6 mm. If the designer used an IPC-2152-based calculator (with board thickness and nearby plane distance entered), a narrower value can be accepted; ask which standard was used.
- **Exceptions:** If the trace is adjacent to a full plane through a thin dielectric, IPC-2152 gives inner traces a current capacity close to that of outer traces; in that case the IPC-2221 value is more conservative than necessary.
- **Example:** —
- **Source:** [Cadence — IPC-2152 vs. IPC-2221](https://resources.system-analysis.cadence.com/blog/ipc-2152-vs-ipc-2221-which-to-use-for-pcb-thermal-analysis), [Sierra Circuits — Trace Width Calculator (IPC-2152)](https://www.protoexpress.com/pcb/trace-width-calculator/), [mbedded.ninja — Maximum Track Current](https://blog.mbedded.ninja/pcb-design/how-to-calculate-maximum-track-current/)

### [PWR-003] Copper thickness assumption unclear (especially 0.5 oz inner layer)

- **Severity:** High
- **Detectable from image:** No (stackup/order information needed)
- **How it looks in the image:** Not visible. Before assessing trace widths, the auditor must ask the user for the manufacturer name and the finished copper thickness of the outer and inner layers. If a stackup table or fabrication note is on screen, read it from there.
- **Why it matters:** Current capacity depends on cross-sectional area; for the same current 0.5 oz copper needs about twice the width of 1 oz. At some manufacturers the inner layers of multilayer boards are 0.5 oz by default.
- **Recommended fix:** JLCPCB (accessed 2026-10): multilayer outer 1/2 oz, inner 0.5/1/2 oz, inner default 0.5 oz. PCBWay (accessed 2026-10): outer 1–8 oz, inner 1/1.5/2/3/4 oz (4–10 layers). Recalculate the width with the actual finished thickness (width ≈ inversely proportional to thickness) or order the inner layer as 1 oz.
- **Exceptions:** If the inner layer has only low-current signals or full planes, the effect is small.
- **Example:** —
- **Source:** [JLCPCB — PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [PCBWay — PCB Capabilities](https://www.pcbway.com/capabilities.html)

### [PWR-004] Neck-down in the power path or perforated plane

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** A wide power pour narrows into a thin bridge at a pad, connector pin or via group; the pour passes between pads of other nets with a single thin strip; the antipads of a dense via array merge and form a slot in the inner plane; a power pad connected with four thin spokes (thermal relief).
- **Why it matters:** The current has to pass through the narrowest cross-section; in the neck the current density and local heating increase and the IR drop rises. Because copper conductivity changes by ~4%/10 °C with temperature, a heating neck feeds itself.
- **Recommended fix:** The width at the narrowest point must meet the PWR-001/002 value. Remove the neck, or draw parallel copper on the other layer and stitch it with vias. In via arrays leave spacing so that a copper web remains between vias. Connect high-current SMD pads to the pour without spokes (see THM-009).
- **Exceptions:** A short (a few mm) narrowing at the entry to a fine-pitch IC pin is unavoidable; it should widen again right after the pin.
- **Example:** —
- **Source:** [PCD&F — Current Control](https://pcdandf.com/pcdesign/index.php/2012-archive-articles/7789-current-control), [JLCPCB — Thermal Relief Pad Design](https://jlcpcb.com/blog/thermal-relief-pad-design)

### [PWR-005] One or too few vias where the power path changes layer

- **Severity:** High
- **Detectable from image:** Partly (the via count is visible; the current must be asked for)
- **How it looks in the image:** A wide power pour or thick trace passes to another layer through a single signal-size via; the vias are lined up in a single row in the current direction (the first via carries most of the current).
- **Why it matters:** The via barrel plating is thin (about half the surface copper); a single via is a bottleneck both as resistance and as inductance, and it heats up.
- **Recommended fix:** Sources give different numbers: AN-1149 ~200 mA per standard via, ROHM ~0.4 A for a 0.3 mm via (2 mm/A rule for the barrel), TI SLYT614 one via per ampere as a rough rule ("more is better if there is room"). This handbook's planning value is ≈0.5 A/via for a 0.3 mm drill (see VIA-006); in a hot/critical design use 0.2 A, put at least 2 vias at every power transition and line up the vias perpendicular to the current direction. For drill/annular ring limits see VIA/DFM.
- **Exceptions:** Low-current (<~100 mA) supply branches may pass through a single via.
- **Example:** —
- **Source:** [TI/National AN-1149 (SNVA021)](https://www.thierry-lequeu.fr/data/AN-1149.pdf), [ROHM — PCB Layout Techniques of Buck Converter, Section 10](https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf), [TI SLYT614 — Five steps to a great PCB layout](https://edgeworker.ti.com/lit/pdf/slyt614)

### [PWR-006] Decoupling capacitor far from the IC supply pin

- **Severity:** Critical
- **Detectable from image:** Yes
- **How it looks in the image:** A 0402/0603 capacitor a few mm away from the IC body and connected to the pin with a thin long trace; the IC's capacitors gathered together in another corner of the board; some of an IC's supply pins have no capacitor next to them at all.
- **Why it matters:** The inductance of the decoupling path = the capacitor's ESL + mounting inductance (~3–3.5 nH) + trace inductance (~5–7 nH/inch). A long trace easily doubles or triples the total inductance, and the capacitor becomes useless at high frequency.
- **Recommended fix:** TI THS4281 example: 0.1 µF ceramic within 0.1 inch (2.54 mm) of the supply pin, 6.8–22 µF bulk within 1 inch (25.4 mm). One capacitor per supply pin; place the capacitor before the IC's other passives. If the IC datasheet has a layout recommendation, it takes priority.
- **Exceptions:** With tight power/ground plane pairs separated by <10 mil of dielectric, the position is less critical (e.g. BGA inner pins); it should still not be excessively far.
- **Example:** Link: https://www.allegromicro.com/-/media/files/guide/ahv85311nk-pcb-layout-guide.pdf?sc_lang=en — Visible: on p. 2, a good placement with each VDRV pin having its own capacitor next to it.
- **Source:** [Altium — When Does Decoupling Capacitor Location Matter](https://resources.altium.com/p/when-does-decoupling-capacitor-location-matter-pcb), [TI THS4281 — Power-Supply Decoupling](https://ti.com/document-viewer/THS4281/datasheet/power_supply_recommendations)

### [PWR-007] Via between the decoupling capacitor and the IC pin (capacitor on the opposite side)

- **Severity:** High
- **Detectable from image:** Yes (images of both sides needed)
- **How it looks in the image:** The IC on the top side, the decoupling capacitor on the bottom side, connected through vias; or, even with the capacitor on top, there is a via on the path from the capacitor pad to the IC pin (current: plane → capacitor → via → pin).
- **Why it matters:** The via inductance sits between the capacitor and the load; the high-frequency effectiveness of the capacitor drops, and according to ROHM's measurement a bypass capacitor on the opposite side can even have a negative effect.
- **Recommended fix:** Put the capacitor on the same side as the IC, directly next to the pin. If a via is needed, place it between the supply source and the capacitor (plane → via → capacitor pad → pin), not between the capacitor and the pin.
- **Exceptions:** For BGAs, placing capacitors on the bottom side with via-in-pad is a common and accepted solution.
- **Example:** Link: https://www.allegromicro.com/-/media/files/guide/ahv85311nk-pcb-layout-guide.pdf?sc_lang=en — Visible: in the diagram on p. 2, "Preferred if vias are required" (via on the supply side) and "Avoid" (via between the capacitor and the pin). ROHM note Figure 3-d: bypass capacitor on the bottom side (bad).
- **Source:** [Allegro — AHV85311NK PCB Layout Guide](https://www.allegromicro.com/-/media/files/guide/ahv85311nk-pcb-layout-guide.pdf?sc_lang=en), [ROHM — PCB Layout Techniques of Buck Converter](https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf)

### [PWR-008] Decoupling capacitor order reversed

- **Severity:** Medium
- **Detectable from image:** Partly (if the value is not written in the image it is estimated from the package size; the exact value needs the BOM)
- **How it looks in the image:** There are two or three capacitors for the same supply pin; the one with the large package (e.g. 0805/1206, usually in the µF range) is closest to the pin, and the small-package 100 nF is behind it.
- **Why it matters:** The small-value/small-package capacitor has the lowest ESL and supplies the high-frequency current; the place where loop inductance matters most is right at the pin.
- **Recommended fix:** Order the smallest-value capacitor closest to the pin and the larger ones behind it; keep the bulk capacitor close to the supply input/regulator output.
- **Exceptions:** If they are all parallel capacitors of the same value, the order does not matter. If the IC datasheet shows a different arrangement, follow it.
- **Example:** —
- **Source:** [TI THS4281 — Power-Supply Decoupling](https://ti.com/document-viewer/THS4281/datasheet/power_supply_recommendations)

### [PWR-009] Large decoupling loop: long GND return of the capacitor

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** The supply end of the capacitor is close to the pin, but the GND end goes not to the IC's GND pin but to a distant via or pour through a long thin trace; the capacitor–VDD pin–GND pin–capacitor loop encloses a large area; many capacitors are connected to a single distant GND via.
- **Why it matters:** What matters is the capacitor's proximity not only to the supply pin but to the whole current loop; a long path on the GND side adds the same mounting/trace inductance.
- **Recommended fix:** Connect the GND pad to the IC's GND pin/exposed pad short and wide, or put the GND via directly at the capacitor's GND pad; give each capacitor its own short GND connection.
- **Exceptions:** If the IC's GND is only the exposed pad, the loop is assessed as capacitor → pin → exposed pad.
- **Example:** —
- **Source:** [Altium — When Does Decoupling Capacitor Location Matter](https://resources.altium.com/p/when-does-decoupling-capacitor-location-matter-pcb), [TI TPS7A85A — Layout](https://www.ti.com/document-viewer/TPS7A85A/datasheet/layout)

### [PWR-010] Bulk capacitor missing or far from the power input

- **Severity:** Medium
- **Detectable from image:** Partly (a large capacitor body is visible; the value needs the BOM)
- **How it looks in the image:** At the power input connector or at the start of a board supply branch there is no electrolytic/polymer or large-body ceramic (1206/1210); or the bulk capacitor is at the far end of a long line from the connector, far from both the load and the input.
- **Why it matters:** The bulk capacitor supplies the low-frequency load current changes limited by the cable/line inductance; if it is placed far away, the line inductance sits in between.
- **Recommended fix:** Have a bulk capacitor at the input and at every local load group; the TI THS4281 example recommends 6.8–22 µF within 1 inch of the pins. According to ROHM, the large input capacitor may be ~2 cm away as long as the small bypass capacitor is close to the IC.
- **Exceptions:** If the board is fed by a very close, well-decoupled source with only a short cable, the need is smaller; for switching regulator inputs see SMPS-001.
- **Example:** Link: https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf — Visible: Figure 3-b, large CIN ~2 cm away, CBYPASS right at the IC (acceptable).
- **Source:** [TI THS4281 — Power-Supply Decoupling](https://ti.com/document-viewer/THS4281/datasheet/power_supply_recommendations), [ROHM — PCB Layout Techniques of Buck Converter](https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf)

### [PWR-011] LDO input/output capacitors far from the pins or connected through vias

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** There is no capacitor next to the IN and OUT pins of the LDO (SOT-23-5, SOT-223, DFN); the capacitors are on the opposite side or at the end of a long trace; the GND ends of the capacitors are connected to separate, distant points rather than the LDO's GND pin.
- **Why it matters:** LDO stability depends on the value and ESR of the output capacitor; trace/via inductance in between degrades the transient response, increases noise and can lead to instability.
- **Recommended fix:** TI recommendation: all parts on the same side as the LDO and as close as possible to the pins; vias and long traces to the input/output capacitors are "strongly discouraged"; the GND returns of the capacitors and the LDO GND pin close to each other and connected by wide component-side copper; a GND reference plane underneath (inner or bottom layer).
- **Exceptions:** For very low-current (<~10 mA) reference LDOs the effect is smaller, but the datasheet still specifies the capacitor position.
- **Example:** —
- **Source:** [TI TPS7A85A — Layout Guidelines](https://www.ti.com/document-viewer/TPS7A85A/datasheet/layout)

### [PWR-012] No copper for the LDO's thermal load

- **Severity:** High
- **Detectable from image:** Partly (the copper area is visible; Vin, Vout and load current must be asked for)
- **How it looks in the image:** The tab or thermal pad of a SOT-223/D-PAK/DFN LDO has only as much copper as the footprint pad, with no vias underneath; the LDO sits in a small, crowded area.
- **Why it matters:** In an LDO the loss is P = (Vin − Vout) × Iload and all of it turns into heat; according to TI, in most applications a GND plane connected to the thermal pad is necessary to meet the thermal requirement.
- **Recommended fix:** Ask the user for Vin, Vout and load current; calculate the loss. Connect the tab/thermal pad to wide copper and with vias to the inner/bottom GND plane (see THM-001, THM-007, THM-008).
- **Exceptions:** If the loss is in the range of a few tens of mW (e.g. 5 V → 3.3 V, 10 mA), no special copper is needed.
- **Example:** —
- **Source:** [TI TPS7A85A — Layout Guidelines](https://www.ti.com/document-viewer/TPS7A85A/datasheet/layout), [Diodes AN1157 — Understanding Thermal Resistance in the Real World](https://www.diodes.com/assets/Uploads/Understanding-Thermal-Resistance-in-the-Real-World-Application-Note.pdf)

### [PWR-013] Daisy-chain supply: sensitive load behind a high-current load

- **Severity:** High
- **Detectable from image:** Partly (the trace topology is visible; the schematic/user is needed to know which load is sensitive)
- **How it looks in the image:** A single supply trace first passes a high-current load such as a motor driver, relay or LED string and continues from there to the input of an ADC/reference/sensor/LDO; the return of the sensitive circuit shares the same thin trace as the power return.
- **Why it matters:** The voltage created by the high current across the shared trace resistance is added to the supply/reference of the sensitive load. Example (ROHM): 1 oz, 3 mm × 50 mm trace ≈ 8.2 mΩ; ≈ 24.5 mV drop at 3 A.
- **Recommended fix:** Use star distribution: let the branches split off from a common node at the bulk capacitor/regulator output, and feed the sensitive load with its own trace. No part of the sense/measurement path should carry load current. For the ground side see GND.
- **Exceptions:** If all loads are low-current, or power is distributed through a full plane (very low plane resistance), the effect is negligible.
- **Example:** Link: https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf — Visible: Figure 7-b, ΔV = Io × r across the GND trace resistance is added to the feedback reference.
- **Source:** [ROHM — PCB Layout Techniques of Buck Converter, Sections 7 and 9](https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf), [TI LMP8640 — Layout](https://www.ti.com/document-viewer/LMP8640/datasheet/layout)

### [PWR-014] No Kelvin connection on the shunt resistor

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** Wide power copper enters the pads of the shunt resistor (usually 2512/2010/1206 body, low value) and the sense traces are taken from an arbitrary point of this copper or from the outer end of the pad; the input of the sense amplifier is connected directly to the power pour; there are no two separate thin sense traces.
- **Why it matters:** If the sense path shares the copper through which the load current flows, that copper's resistance is added in series with the shunt and a gain error results; for shunts in the mΩ range this error is large.
- **Recommended fix:** 4-wire (Kelvin) connection: take the sense traces from the shunt pads at a point outside the direct path of the load current (in practice the inner edge of the pad), and make sure no part of them carries load current.
- **Exceptions:** If the error budget is wide (e.g. overcurrent protection only) and the shunt value is relatively large, a simple connection may be accepted; ask the user for the accuracy target.
- **Example:** —
- **Source:** [TI LMP8640 — Layout Guidelines](https://www.ti.com/document-viewer/LMP8640/datasheet/layout)

### [PWR-015] Kelvin/remote sense traces not matched or passing through a noisy area

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** One of the ISENSE+/− or SENSE+/− traces is on the top layer and the other on the bottom; their lengths and via counts differ; there is a wide gap between them (large loop); the traces pass next to the switch node, inductor or gate traces; there is a jumper/connector in between.
- **Why it matters:** If the two inputs see different noise, different thermal EMF (thermocouple effect) and different resistance, the error cannot be rejected as common mode and turns into a differential error.
- **Recommended fix:** Run the two traces along the same path, close to each other and ideally on the same layer; if vias are used, have an equal number on both traces with continuous plating; avoid jumpers/connectors, and if unavoidable, have an equal number on both traces. With a high-voltage shunt, keep the required clearance around the traces.
- **Exceptions:** Very short (a few mm) sense traces that stay on the same layer cause no problems in practice.
- **Example:** —
- **Source:** [TI LMP8640 — Layout Guidelines](https://www.ti.com/document-viewer/LMP8640/datasheet/layout)

### [PWR-016] Fuse/protection elements not at the power input or in the wrong order

- **Severity:** High
- **Detectable from image:** Partly (the order can be seen by following the traces; the part type needs the BOM/schematic)
- **How it looks in the image:** The fuse (F*, PTC/polyfuse 1206/1812, fuse holder) is far from the connector or in only one of the branches splitting off from the input; branches to other loads split off between the connector and the fuse; a unidirectional TVS is placed before the reverse polarity element.
- **Why it matters:** Branches that split off before the fuse are unprotected. A unidirectional TVS conducts like a forward-biased diode under reverse connection, and if it is before the reverse polarity element it blows the fuse or stresses the TVS.
- **Recommended fix:** Build the protection chain close to the connector and before any branching. The order recommended by the community: connector → reverse polarity element → fuse → TVS → bulk capacitor/load; if a bidirectional TVS is used, a different order is possible. For a short and wide GND connection of the TVS see ESD.
- **Exceptions:** On a board fed from a current-limited source the fuse may be ineffective; ask the user for the source's short-circuit current.
- **Example:** —
- **Source:** [EEVblog Forum — Optimum arrangement for circuit protection components](https://eevblog.com/forum/beginners/optimum-arrangement-for-circuit-protection-components), [TI SLVA139 — Reverse Current/Battery Protection Circuits](https://ti.com/lit/pdf/SLVA139)

### [PWR-017] Reverse polarity protection bypassed or in the wrong direction

- **Severity:** High
- **Detectable from image:** Partly (pin assignment/schematic needed; the direction can be checked from the silkscreen)
- **How it looks in the image:** The cathode band (silkscreen line) of a series diode is on the connector side; a P-MOSFET is at the input but some loads (fan, LED, second connector) branch off before the protection; on a board protected by an N-MOSFET in the GND return, the GND pin of the connector is also connected directly to the main GND pour (FET bypass).
- **Why it matters:** If the protection element does not interrupt the whole current path, under reverse connection the current flows through the bypass path. In MOSFET protection the body diode must be in the normal current direction; otherwise the circuit does not work or does not protect.
- **Recommended fix:** Put the protection element (series diode, P-MOSFET in the power path or N-MOSFET in the return path) at the point closest to the connector, before all loads. If the diode drop is unacceptable, use a MOSFET with low rDS(on) (drop ≈ rDS(on) × Iload). Ask the user for the schematic sheet.
- **Exceptions:** For connectors that mechanically cannot be inserted reversed (polarised), electronic protection is optional.
- **Example:** —
- **Source:** [TI SLVA139 — Reverse Current/Battery Protection Circuits](https://ti.com/lit/pdf/SLVA139)

### [PWR-018] Connector current rating below the expected current

- **Severity:** High
- **Detectable from image:** Partly (the part number and expected current must be obtained from the user)
- **How it looks in the image:** A path carrying high current (motor phase, power input, LED strip output) ends at a small connector: a 2.54 mm pin header (square + round small pads), a small JST-type header or a 2.1 mm DC barrel jack (three large oval/slot pads). The traces/pours to the connector are wide while the connector pads are small.
- **Why it matters:** Connector contact resistance heats up with current; if the rated current is exceeded, the contact and plastic housing degrade and the voltage drops. Example: the common PJ-002A barrel jack is rated for 2.5 A / 24 Vdc (Same Sky datasheet, 2025-03 rev.).
- **Recommended fix:** Ask the user for the expected continuous current and compare it with the rated current in the connector datasheet; leave a 20–30% margin below the rated current (this handbook's recommendation, not from a source). If insufficient, use a screw terminal, a larger-pitch power connector or parallel contacts; for trace width see PWR-001.
- **Exceptions:** For short pulse currents the datasheet's pulse rating applies. Signal/low-current connectors are outside this rule.
- **Example:** Link: https://eevblog.com/forum/projects/seeking-feedback-on-my-novice-bldc-driver-pcb-design — Visible error: >2 A motor current is carried through a barrel jack and a 2.54 mm header; experts point out that the connectors may not be able to handle the current.
- **Source:** [Same Sky (CUI) PJ-002A datasheet](https://www.sameskydevices.com/product/resource/pj-002a.pdf)
