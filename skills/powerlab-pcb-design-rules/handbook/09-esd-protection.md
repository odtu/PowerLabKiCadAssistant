# 09 — ESD Protection (ESD)

An ESD pulse (IEC 61000-4-2, ≈30 A peak at 8 kV contact discharge, ≈0.8 ns rise — TI SLVA680 Figure 1-1, ROHM Figure 4) almost always enters the board through a connector, a button or exposed metal. A TVS diode only works if it can divert the pulse to GND before the protected IC and through a low-inductance path; even with a correct schematic, a bad layout makes the protection ineffective (ROHM's field failure example). Most rules in this section can be audited from the image: the TVS distance to the connector, whether the trace passes through the TVS pad, vias and the TVS GND connection are visible. TVS selection (Vbr, capacitance) cannot be verified from the image → ask the user for the part number. For the general GND/chassis plane see GND; for connector position see PLC/MEC.

### [ESD-001] TVS placed far from the connector, close to the protected IC

- **Severity:** Critical
- **Detectable from image:** Yes
- **How it looks in the image:** The TVS/ESD array (a small 2–6 pin package such as SOT-23, SOD-323, SOT-563, DFN, with a D/U prefix in the schematic) sits centimetres away from the connector, next to the protected MCU/PHY or in an empty corner of the board; there is a long trace from the connector to the TVS. In the correct case the TVS is the first component, right behind the connector pins (a few mm).
- **Why it matters:** The trace inductance between connector and TVS (L·di/dt) raises the clamping voltage excessively; in ROHM's simulation, with a ≈52 nH connection the first peak rises to 3.4 kV and is not clamped, while with ≈1 nH it stays at 107 V. In addition, the field radiated from the long trace couples into neighbouring traces.
- **Recommended fix:** Place the TVS as close to the connector as the design rules allow; the protected IC should be much farther from the TVS than the connector is from the TVS (TI SLVA680). Place ESD/EMI components closest to the connector (TI SPRAAR7).
- **Exceptions:** For Ethernet, TI recommends placing the protection element on the PHY side of the transformer because of high common-mode voltage (see ESD-009). A KiCad forum answer says "being close to the connector is not required, as long as the path follows the connector→TVS→circuit order"; this community view conflicts with the manufacturer notes, and the manufacturer note should be followed.
- **Example:** Link: https://fscdn.rohm.com/en/products/databook/applinote/discrete/diodes/pcb_layout_for_tvs_diodes_an-e.pdf — Visible error: the TVSs were placed in an empty corner after the circuit was laid out, and the IC was damaged by ESD in the field (Figure 2); corrected layout in Figure 8.
- **Source:** [ROHM – PCB Layout for TVS Diodes](https://fscdn.rohm.com/en/products/databook/applinote/discrete/diodes/pcb_layout_for_tvs_diodes_an-e.pdf), [TI SLVA680 ESD Protection Layout Guide](https://ti.com/lit/pdf/slva680), [TI SPRAAR7](https://www.ti.com/lit/an/spraar7j/spraar7j.pdf)

### [ESD-002] Signal connected to the TVS through a branch (stub), not passing through the TVS pad

- **Severity:** Critical
- **Detectable from image:** Yes
- **How it looks in the image:** The main trace from the connector to the IC passes beside the TVS and connects to it through a separate short side branch (T-junction); or the trace first goes to the IC and then comes back to reach the TVS. In the correct case the trace comes from the connector, **passes directly over the TVS signal pad** ("flow-through") and continues from there to the IC.
- **Why it matters:** The branch inductance (L2 in SLVA680) steers the pulse current away from the TVS; the current seeks the lowest-impedance path and the protected IC may take most of the pulse.
- **Recommended fix:** No stub between the TVS and the protected line; the trace should go directly from the ESD source to the TVS (TI SLVA680). For high-speed pairs, choose packages that allow flow-through routing (TI SPRAAR7 3.13).
- **Exceptions:** In a trace passing through the pad, the unavoidable separation of a few hundred µm at the pad entry does not count as a stub.
- **Example:** Link: https://forum.kicad.info/t/differential-pair-routing-in-kicad-6-0/36935 — Visible situation: discussion of routing a USB pair over its ESD diodes and how to route the pair in the diode area.
- **Source:** [TI SLVA680 ESD Protection Layout Guide](https://ti.com/lit/pdf/slva680), [TI SPRAAR7](https://www.ti.com/lit/an/spraar7j/spraar7j.pdf)

### [ESD-003] Via or layer change between the connector and the TVS

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** The trace leaving the connector pin moves to another layer through a via before reaching the TVS; the TVS is on the opposite side of the board and connected through a via; or the via is positioned so that it forms a branch off the main line between the connector and the TVS.
- **Why it matters:** The via inductance enters the TVS path in series; if it forms a branch, the pulse current is shared between the IC and the via, and the voltage at the IC rises by L_via·di/dt.
- **Recommended fix:** Do not use a via between the ESD source and the TVS; if a via is needed between the ESD source and the protected IC, the trace should go to the TVS first and the via should come after the TVS (SLVA680 Case 1). If having the TVS on the opposite layer is unavoidable, the "Case 3" arrangement, which forces the current into the TVS pin before it finds a path to the IC, is an acceptable compromise.
- **Exceptions:** Through-hole (THT) connector pins already extend through all layers; connecting the TVS directly to the pin's annular ring does not count as a via.
- **Example:** —
- **Source:** [TI SLVA680 ESD Protection Layout Guide](https://ti.com/lit/pdf/slva680)

### [ESD-004] TVS GND connection long, thin or with a single via

- **Severity:** Critical
- **Detectable from image:** Yes
- **How it looks in the image:** The TVS GND pad runs through a thin, long trace to a distant GND via or GND pour; there is no via next to the GND pad at all; there is no GND plane under the TVS (gap/other signal on the bottom layer). In the correct case the GND pad pours directly into the GND copper on the same layer, and one or more vias right next to it drop to the inner/bottom GND plane.
- **Why it matters:** The TVS–GND inductance (L3 in SLVA680) adds directly to the clamping voltage; with di/dt ≈4·10^10 A/s in an 8 kV pulse, even a few nH means hundreds of volts.
- **Recommended fix:** Connect the TVS GND pin to the GND plane on the same layer, stitch this plane to the GND on the adjacent layer with vias, and place one via directly adjacent to the GND pin (TI SLVA680; 4 vias in the example). Large-diameter vias and multiple parallel vias lower the inductance; place the GND plane directly under the diode (ROHM). If a trace is needed, keep it short and wide.
- **Exceptions:** For BGA/WLCSP TVS packages, the manufacturer's recommended arrangement for the separate GND ball applies (SLVA680).
- **Example:** Link: https://fscdn.rohm.com/en/products/databook/applinote/discrete/diodes/pcb_layout_for_tvs_diodes_an-e.pdf — Visible error: in Figures 11/14 the anode side is connected to GND with a long trace.
- **Source:** [TI SLVA680 ESD Protection Layout Guide](https://ti.com/lit/pdf/slva680), [ROHM – PCB Layout for TVS Diodes](https://fscdn.rohm.com/en/products/databook/applinote/discrete/diodes/pcb_layout_for_tvs_diodes_an-e.pdf)

### [ESD-005] Unprotected traces run parallel to the protected section between connector and TVS

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** Another signal trace runs parallel beside (on the same layer or directly below) the short trace section between the connector and the TVS; there are 90° corners in the protected section; unprotected traces pass next to the via in this section.
- **Why it matters:** During an ESD event the trace hit by the pulse radiates a strong field and couples into nearby unprotected traces, causing early system failure; the field concentrates at a 90° corner (in TI's 8 kV simulation ≥7 kV at the corner, with risk of arcing through air at a radius below ≈2.6 mm).
- **Recommended fix:** Keep unprotected traces away from protected traces (TI SLVA680, SPRAAR7); route the connector–TVS path as straight and short as possible; if a corner is needed, use a large-radius arc, at most 45° (TI SLVA680).
- **Exceptions:** Other protected lines of the same connector (going to the same TVS array) may run side by side.
- **Example:** —
- **Source:** [TI SLVA680 ESD Protection Layout Guide](https://ti.com/lit/pdf/slva680), [TI SPRAAR7](https://www.ti.com/lit/an/spraar7j/spraar7j.pdf)

### [ESD-006] Series protection resistor in the wrong place (between TVS and connector)

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** The series resistor in the line (usually 22 Ω–1 kΩ) is between the connector and the TVS; or the TVS is next to the IC and the resistor on the connector side. Correct arrangement: connector → TVS (adjacent to the connector) → trace → series resistor (close to the IC pin) → IC. The resistor's function (termination or protection) needs verification from the schematic.
- **Why it matters:** A series resistor next to the IC slows the voltage rise at the IC pin and gives the TVS time to turn on; it also creates a voltage drop between the two so that the IC's internal ESD structure does not conduct before the TVS and take the energy. If the resistor is on the connector side rather than between the TVS and the IC, the IC sees the same waveform as the TVS.
- **Recommended fix:** Place the TVS close to the connector and the series resistor close to the IC (LearnEMC, Hubing). TI SLVA680 also supports increasing the impedance between the TVS and the protected IC.
- **Exceptions:** On high-speed differential lines a series resistor can degrade signal integrity; low-inductance protection components containing diode + series impedance in a single package are preferred (LearnEMC). The series resistor on USB D+/D- is a PHY requirement (see HS-013).
- **Example:** —
- **Source:** [LearnEMC – EMC Question of the Week, 24 July 2023](https://learnemc.com/qotw-230724), [TI SLVA680 ESD Protection Layout Guide](https://ti.com/lit/pdf/slva680)

### [ESD-007] Connector shell/chassis connection undefined or far from the TVS GND

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** The shell (shield) tab pads of a USB/RJ45/D-sub connector are not connected to any copper (floating); or the shell is connected to a separate chassis copper but there is neither a gap nor a bridging component (R‖C, ferrite) between this copper and the circuit GND; the chassis screw hole is far from the TVS GND. Ask the user whether the chassis/GND separation is intentional.
- **Why it matters:** The shell is the first metal the user touches; a floating shell lets ESD jump into the board along a random path. The distance between the TVS GND and the chassis connection causes a shift in circuit GND during the pulse.
- **Recommended fix:** Make the grounded chassis connection (e.g. chassis screw) directly adjacent to the TVS GND and to the GND of the ESD source (connector shell); if there is no chassis ground, use tightly coupled multilayer GND planes (TI SLVA680). If a separate chassis copper is used, separate it from the circuit with a gap of ≥20 mil (≈0.51 mm) and bridge it only with a capacitor + ≥1 MΩ resistor (TI SNLA387, Ethernet); the chassis plane should be only near the connector (TI TUSB2077A).
- **Exceptions:** The shell–GND connection method is debated: 1 MΩ‖4.7 nF is a common empirical value (TI E2E, EEVblog), some designers prefer a direct connection with USB-C; the product enclosure and EMC testing decide. A direct connection does not count as an error; a floating shell does.
- **Example:** Link: https://www.eevblog.com/forum/projects/usb-shield-ground-connection/msg597292/ — Visible situation: discussion of whether the USB shell should be connected to GND directly or through RC.
- **Source:** [TI SLVA680 ESD Protection Layout Guide](https://ti.com/lit/pdf/slva680), [TI SNLA387 Ethernet PHY PCB Design Layout Checklist](https://ti.com/lit/pdf/snla387), [TI TUSB2077A Layout](https://www.ti.com/document-viewer/ja-jp/TUSB2077A/datasheet/layout) — for chassis/GND plane separation see GND

### [ESD-008] ESD component breaks impedance and symmetry on a high-speed pair

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** On a USB/HDMI pair, separate single-channel TVSs at different positions for each leg; the pair splits apart and detours to reach the TVSs; the TVS is in the middle of the pair's route, far from the connector; there is no reference plane cutout under the TVS pads. In the correct case a single multi-channel package with flow-through pins sits directly on the pair, close to the connector.
- **Why it matters:** The TVS pad and its internal capacitance add a capacitive load to the pair; different loads and positions on the two legs create skew and mode conversion.
- **Recommended fix:** Choose flow-through packages that the pair can pass through without bending (TI SPRAAR7 3.13); apply a 60% reference plane cutout under the ESD signal pads; keep the AC capacitor + CMC + ESD chain short and close to the connector (TI SPRAAR7 3.14). Integrated clamp arrays provide intra-pair matching (TI SLLA324, TPD12S016). Keep components close to the USB lines and the connection short; choose a USB 2.0 compatible (low-capacitance) part (Renesas).
- **Exceptions:** On USB FS and low-speed lines, single-channel TVSs are acceptable. TVS capacitance cannot be read from the image → ask for the part number.
- **Example:** Link: https://forum.kicad.info/t/differential-pair-routing-in-kicad-6-0/36935 — Visible situation: single-channel ESD diodes breaking up the USB pair.
- **Source:** [TI SPRAAR7](https://www.ti.com/lit/an/spraar7j/spraar7j.pdf), [Renesas RX71M USB2.0 Board Design](https://www.renesas.com/en/document/oth/rx71m-high-speed-usb-guidelines-high-speed-usb20-board-design), [TI SLLA324 (TPD12S016 HDMI)](https://ti.com/lit/pdf/slla324) — for pair geometry see HS-017

### [ESD-009] In Ethernet, the ESD element is on the wrong side of the transformer or bridges the transformer isolation

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** A TVS array on the RJ45 (cable) side of a discrete Ethernet transformer, connected to circuit GND in a way that crosses the transformer isolation gap; or the TVS GND is connected by extending copper into the gap under the transformer. If there is a TVS on the PHY side, on the MDI lines between the PHY and the transformer, this is the arrangement TI recommends.
- **Why it matters:** There can be high common-mode voltage swings (other than ESD) on the cable side; a protection element on this side can be damaged by these voltages, and connecting it to circuit GND weakens the isolation.
- **Recommended fix:** Following TI's Ethernet-specific recommendation, place the protection element on the PHY side of the transformer; this recommendation conflicts with the general ESD note's "closest to the connector" rule, and TI explains the difference by the common-mode voltage risk (TI SNLA387). Do not leave metal under the transformer on any layer (see HS-015).
- **Exceptions:** On the line side, chassis-connected protection rated for the isolation withstand (e.g. a GDT or high-voltage component) may be used depending on product requirements; follow the PHY manufacturer's reference design.
- **Example:** —
- **Source:** [TI SNLA387 Ethernet PHY PCB Design Layout Checklist](https://ti.com/lit/pdf/snla387)
