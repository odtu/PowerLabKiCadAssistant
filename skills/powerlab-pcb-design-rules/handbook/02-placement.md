# 02 — Placement Strategy (PLC)

This section audits the **strategic** position of parts on the board: functional blocks, signal and power flow, connector locations, separation of noisy and sensitive areas, heat and mechanical stress. In a screenshot these are usually visible at a glance and cannot be fixed later by routing; a wrong placement means redrawing the whole board. Detailed distance rules are in the relevant sections: decoupling distance → PWR, SMPS hot loop → SMPS, crystal → XTL, mounting hole and connector access → MEC, alignment → EST, assembly spacing → DFA, wireless module/antenna → RF.

### [PLC-001] Parts not grouped by functional block

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** Parts belonging to the same circuit (e.g. the input/output capacitors and inductor of a regulator, the resistor network of an op-amp) are scattered to different corners of the board; there are long ratsnest lines/traces between them. The reference designators (U3, C12, L2) are not next to each other; a part of another block has been placed in the middle of a block. Without the schematic, block membership is a guess: ask the user for the schematic or a block list.
- **Why it matters:** A scattered block means long connections, large current loops and coupling; placing one functional group inside another mixes the return currents.
- **Recommended fix:** Reserve an area on the board for each schematic sheet/block, keep the connections within a block short and leave space for routing channels; in KiCad all parts of a sheet can be selected and moved together.
- **Exceptions:** Protection/filter parts that must be placed next to the connector (see PLC-005) may appear outside the block.
- **Example:** —
- **Source:** [Sierra Circuits — Component Placement Guidelines for PCB Design and Assembly](https://www.protoexpress.com/blog/component-placement-guidelines-pcb-design-assembly/), [TI SZZA009 — PCB Design Guidelines for Reduced EMI](https://www.ti.com/lit/an/szza009/szza009.pdf)

### [PLC-002] Signal flow not one-directional (input → processing → output chain zigzags)

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** The input connector and the output connector are next to each other while the processing stages are at the other end of the board; traces run along the board and come back, with long crossing traces and many vias. In a good example analog inputs enter from one side, digital outputs leave from the opposite side, and power is fed from the top/bottom.
- **Why it matters:** A linear flow shortens traces and prevents coupling between input and output (or between sensitive and noisy); TI data converter layouts are partitioned so that the analog signal enters on one side and the digital leaves on the other.
- **Recommended fix:** Arrange the main ICs in an order in which the traces between them are short and the signal flow is one-directional; put the input and output connectors at the two ends of the chain.
- **Exceptions:** Boards on which, mechanically, all connectors must be on one edge (see PLC-004) — in that case the flow should be "U"-shaped but without crossings.
- **Example:** —
- **Source:** [Sierra Circuits — Component Placement Guidelines](https://www.protoexpress.com/blog/component-placement-guidelines-pcb-design-assembly/), [TI ADS1299 — Layout Guidelines](https://ti.com/document-viewer/ADS1299/datasheet/layout)

### [PLC-003] Connectors not at the board edge or not facing outward

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** A connector that takes a cable (terminal block, USB, pin header, JST) is in the middle of the board; the cable entry faces into the board or toward another part; in the 3D view, once the plug is inserted the cable will pass over other parts.
- **Why it matters:** Connectors are fixed reference points mechanically and for EMC; an I/O trace that enters the board carries noise to other circuits. A cable passing over the board couples noise into the board circuits (TI, warning about a cable folded over the oscillator/MCU).
- **Recommended fix:** Place connectors first, at the board edge with the opening facing outward, and lock them; place the other parts afterward. For mechanical access and edge distance see MEC.
- **Exceptions:** Board-to-board (mezzanine) connectors and programming headers may be inside the board.
- **Example:** —
- **Source:** [Sierra Circuits — Component Placement Guidelines](https://www.protoexpress.com/blog/component-placement-guidelines-pcb-design-assembly/), [TI SZZA009](https://www.ti.com/lit/an/szza009/szza009.pdf), [LearnEMC — Good EMC Design Guidelines](https://learnemc.com/other-good-emc-design-guidelines)

### [PLC-004] I/O connectors spread over different edges with high-frequency circuitry between them

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** Power input on one edge, communication connector on the opposite edge, and an MCU, clock source or switching regulator between the two. Cables leave from both ends of the board.
- **Why it matters:** On a board with cables leaving from both ends, the ground voltage difference created by the high-frequency circuit in between drives the cables like a dipole antenna (common-mode radiation). If all connectors are on one edge/corner, it is easier to keep them at the same reference potential.
- **Recommended fix:** Gather the I/O connectors on one edge or in one corner. If that is not possible, do not put high-frequency circuitry between two connectors; if that is not possible either, a metal enclosure and filtering to chassis ground are needed (LearnEMC).
- **Exceptions:** In power electronics, input and output power connectors on opposite edges (linear power flow, PLC-008) are accepted; in that case the control/communication connectors should be gathered on one edge.
- **Example:** —
- **Source:** [LearnEMC — Good EMC Design Guidelines](https://learnemc.com/other-good-emc-design-guidelines)

### [PLC-005] Interface circuit (transceiver, protection, filter) far from its connector

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** There is no protection diode (small SOT-23/SOD), common-mode choke or transceiver next to the USB/CAN/RS-485 connector; these are in the middle of the board, next to the MCU. The traces leaving the connector travel a long way and pass next to many parts.
- **Why it matters:** Noise/ESD arriving at the connector couples into the traces inside the board before it reaches the protection part; a long I/O trace also carries board noise onto the cable.
- **Recommended fix:** Place the device that communicates through the connector close to the connector (LearnEMC example: within ~2 cm); keep parts not connected to the I/O net ≥ ~2 cm away from I/O traces and connectors (LearnEMC, situational advice). Transient suppressors directly next to the connector, with no via in between (Sierra). For ESD details see ESD.
- **Exceptions:** On very small boards 2 cm cannot be achieved; the principle is that the "connector → protection → filter → IC" order is not broken.
- **Example:** —
- **Source:** [LearnEMC — Good EMC Design Guidelines](https://learnemc.com/other-good-emc-design-guidelines), [Sierra Circuits — Component Placement Guidelines](https://www.protoexpress.com/blog/component-placement-guidelines-pcb-design-assembly/)

### [PLC-006] Noisy and sensitive blocks intermixed (no zoning)

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** The inductor of a switching regulator, a MOSFET bridge, a motor driver or a clock oscillator is directly next to an ADC, voltage reference, op-amp front stage, current-sense amplifier or RF module. "Power / digital / analog" zones cannot be distinguished on the board.
- **Why it matters:** Coupling decreases with distance; TI recommends a zoning in which high-speed logic is close to the power supply, slower parts further away and analog parts furthest away. In motor drivers the power-stage FETs, bootstrap and charge pump are noisy and must be isolated from sensitive signals.
- **Recommended fix:** Divide the board into digital, analog and high-power zones ("partitioning" while keeping a single ground plane); keep oscillators away from analog circuitry, low-speed signals and connectors (TI SZZA009). Put sensitive analog furthest from switching parts and high-current paths (PowerLab rule §3.2). For ground splitting details see GND.
- **Exceptions:** A current-sense resistor is by nature in the power path; only its amplifier and Kelvin traces are pulled into the sensitive zone.
- **Example:** —
- **Source:** [TI SZZA009 — Board Zoning](https://www.ti.com/lit/an/szza009/szza009.pdf), [TI SLVA959B — Best Practices for Board Layout of Motor Drivers](https://www.ti.com/lit/an/slva959b/slva959b.pdf), [TI ADS1299 — Layout Guidelines](https://ti.com/document-viewer/ADS1299/datasheet/layout)

### [PLC-007] Power input in the wrong place or input chain order broken

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** The power connector is at one end of the board and the regulator at the opposite end; the raw input voltage is carried along the board on a long trace. Or the power enters through the analog zone. There are no fuse/reverse-polarity/TVS/filter parts next to the connector; they are after the regulator or scattered.
- **Why it matters:** An unfiltered input line carries noise across the board and the loop area grows. TI recommends placing the regulator where power enters the board and the MCU next to the regulator; on mixed-signal boards power should enter at the digital section and go to the analog section filtered/regulated.
- **Recommended fix:** Order: connector → protection (fuse/reverse polarity/TVS) → input filter/bulk capacitor → regulator → loads; all adjacent to the input connector. Let power enter from the digital/power zone, and branch the analog supply off from there through filtering.
- **Exceptions:** On boards with several independent supply inputs, each input should have its own chain.
- **Example:** —
- **Source:** [TI SZZA009](https://www.ti.com/lit/an/szza009/szza009.pdf), [TI SLYT512 — Grounding in mixed-signal systems demystified, Part 2](https://www.ti.com/lit/an/slyt512/slyt512.pdf)

### [PLC-008] High-current path long and winding (power parts scattered)

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** The power connector, DC-link/bulk capacitors, MOSFETs/bridge, shunt resistor and output connector are far from each other; wide copper pours wander around the board, a large area remains between the forward and return paths; the power path runs through the signal zone.
- **Why it matters:** The parasitic inductance of a high-current loop grows with trace length; this means voltage ripple, noise and the need for extra capacitors. TI asks for the loop to be minimised both with the correct trace width and with a placement that reduces the distance between parts.
- **Recommended fix:** Plan the power path at the placement stage: input → capacitors → switches → load/output connector on a straight line and adjacent to each other; forward and return paths stacked/side by side (small loop area). Trace width for current → PWR; SMPS hot loop → SMPS.
- **Exceptions:** —
- **Example:** —
- **Source:** [TI SLVA959B — High-Current Loop Paths](https://www.ti.com/lit/an/slva959b/slva959b.pdf), [TI SLYT682 — Reduce buck-converter EMI by minimizing inductive parasitics](https://www.ti.com/lit/an/slyt682/slyt682.pdf)

### [PLC-009] Heat sources clustered, airflow blocked, or close to heat-sensitive parts

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** Several power parts (MOSFET, regulator, power resistor, bridge diode) in the same small area; next to them an electrolytic capacitor, crystal, voltage reference or temperature sensor. Tall parts (large electrolytics, connectors) block the air path of the hot part. The thermal pad of the hot part is small and connected to an isolated copper island; there is no wide copper extending to the board edge.
- **Why it matters:** Concentrated heat creates hot spots; according to TI a typical board with copper pours on both sides needs ~15.3 cm² of area to dissipate 1 W with a 40 °C rise in natural convection, and copper extending to the board edge helps the heat spread.
- **Recommended fix:** Spread heat sources across the board, position them according to the airflow/heatsink direction, move tall parts out of the air path (Sierra). Keep heat-sensitive parts away from heat sources. For heatsink and thermal via details see THM.
- **Exceptions:** Lining up power parts that will be attached to a common heatsink is intentional; in that case sensitive parts should be kept away from the heatsink.
- **Example:** —
- **Source:** [TI SNVA419C — AN-2020 Thermal Design by Insight, Not Hindsight](https://www.ti.com/lit/an/snva419c/snva419c.pdf), [Sierra Circuits — Component Placement Guidelines](https://www.protoexpress.com/blog/component-placement-guidelines-pcb-design-assembly/)

### [PLC-010] Wrong placement order: no room left around the IC for decoupling and support parts

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** ICs are packed against each other or against connectors; there is no space for a capacitor next to the supply pins, the decoupling capacitors are lined up in a row away from the IC; pull-up/series resistors are adjacent to the IC but the supply capacitors are far away.
- **Why it matters:** Support parts such as decoupling capacitors and crystals only work if they can be placed directly next to the main IC; if the other passives are placed first, these spots get taken. The order recommended by Sierra Circuits: connectors → main ICs → support parts such as crystal and decoupling → other passives.
- **Recommended fix:** Place and lock the connectors and mechanically fixed parts, then place the main ICs; place each IC's decoupling capacitors **before** the other passives (PowerLab §3.2). For distance values see PWR; for the crystal see XTL.
- **Exceptions:** —
- **Example:** —
- **Source:** [Sierra Circuits — Component Placement Guidelines](https://www.protoexpress.com/blog/component-placement-guidelines-pcb-design-assembly/), [TI ADS1299 — Layout Guidelines](https://ti.com/document-viewer/ADS1299/datasheet/layout)

### [PLC-011] Analog front end (AFE) not isolated: digital/power circuitry between the sensor input and the ADC

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** Traces from the sensor/measurement connector pass next to the MCU, the SMPS or a digital bus on their way to a distant ADC/op-amp; the ADC sits in the middle of the digital parts. In a good example: sensor connector → input filter → op-amp → ADC as a short chain, the ADC on the boundary between the analog and digital zones; digital traces do not enter the analog zone.
- **Why it matters:** A low-level analog signal picks up coupling from digital edges and switching noise over a long path. TI recommends dividing the board into analog and digital sections and routing analog signals only in the analog section and digital ones only in the digital section; digital lines are kept away from analog lines.
- **Recommended fix:** Place the AFE adjacent to the sensor connector; put the ADC on the section boundary, oriented with its analog pins facing the analog side; position things so that traces of the digital section do not enter the analog zone. For ground plane details see GND.
- **Exceptions:** —
- **Example:** —
- **Source:** [TI SLYT512 — Grounding in mixed-signal systems, Part 2](https://www.ti.com/lit/an/slyt512/slyt512.pdf), [TI ADS1299 — Layout Guidelines](https://ti.com/document-viewer/ADS1299/datasheet/layout)

### [PLC-012] Inconsistent orientation of polarised and similar parts

- **Severity:** Low
- **Detectable from image:** Yes
- **How it looks in the image:** Diode bands, LED cathode marks, electrolytic/tantalum capacitor "+" marks and IC pin-1 dots point in random directions on the board (some left, some up, some right). A row of parts of the same type is rotated at different angles.
- **Why it matters:** A consistent orientation reduces reversed-insertion errors in assembly and visual inspection, and reduces the need for rotation on the pick-and-place machine and the assembly time.
- **Recommended fix:** Place polarised parts in the same direction as far as possible, with the pin 1 of ICs facing the same corner (PowerLab §3.2, Sierra). For alignment/aesthetics see EST; for assembly spacing see DFA.
- **Exceptions:** Where an electrically short path is required (e.g. the current direction of a power diode), orientation consistency is secondary. Primary rule for this finding: DFA-003; report it as DFA-003.
- **Example:** —
- **Source:** [Sierra Circuits — Component Placement Guidelines](https://www.protoexpress.com/blog/component-placement-guidelines-pcb-design-assembly/)

### [PLC-013] Stress-sensitive parts (MLCC, large ceramics, BGA) next to a mounting hole, corner or break line

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** A ceramic capacitor (especially 1206 and larger), ceramic resonator or BGA directly next to a screw hole, at a board corner, adjacent to a V-score/mouse-bite break line or next to a heavy connector; its long axis perpendicular to the break line.
- **Why it matters:** Board bending during screwing, depaneling and mounting of heavy parts crack ceramic parts; the crack often shows up later as a short circuit. KYOCERA AVX reports that leaving 200 mil (~5 mm) of margin from the cut edge prevents damage, while a 20 mil margin always failed; corners are the most stressed areas.
- **Recommended fix:** Keep ceramic parts away from corners, break lines and mounting holes (≥ 5 mm to the break edge, AVX; Ø 6–7 mm part keepout around an M3 hole, PowerLab §3.1); if unavoidable, orient the long axis parallel to the stress gradient. For hole mechanics see MEC.
- **Exceptions:** Soft-termination MLCCs are more tolerant, but the rule still applies.
- **Example:** Link: https://forum.kicad.info/t/pcb-review-request/40027 — Visible error: the reviewer warns that, for the capacitor, resistor and diode placed next to the mounting hole, the screw head may crush the board and crack the ceramic parts.
- **Source:** [KYOCERA AVX — Cracks: The Hidden Defect](https://www.kyocera-avx.com/docs/techinfo/CeramicCapacitors/cracks.pdf)

### [PLC-014] Unnecessary double-sided placement (higher cost)

- **Severity:** Low
- **Detectable from image:** Yes
- **How it looks in the image:** In the bottom side (B.Fab/B.Silkscreen, in KiCad usually purple/mirrored text) image there are a few SMD passives or a single IC, while the top side has free space to take them. THT parts are inserted from both sides.
- **Why it matters:** Each populated side means a separate placement/soldering pass and stencil. JLCPCB's cheap "Economic PCBA" option supports only single-sided placement; double-sided requires "Standard PCBA" (JLCPCB, accessed 2026-10).
- **Recommended fix:** Gather all SMDs on the top side; place THTs so that they are inserted from one direction (PowerLab §3.2, Sierra). Use the bottom side only if space has really run out, and tell the user.
- **Exceptions:** Space-constrained boards, sensors/LEDs that must be on the bottom side, decoupling capacitors placed directly behind the IC (see PWR).
- **Example:** —
- **Source:** [JLCPCB — PCB Assembly Capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities), [Sierra Circuits — Component Placement Guidelines](https://www.protoexpress.com/blog/component-placement-guidelines-pcb-design-assembly/)

### [PLC-015] High-voltage/high-power zone intermixed with low-voltage control circuitry

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** Wide copper carrying DC bus/mains voltage, bridge MOSFETs and DC-link capacitors are scattered among the MCU, sensor and communication parts; high-voltage traces run through the control zone; there is no clear boundary/gap between the two zones. Voltage values cannot be read from the image: ask the user for the net voltages.
- **Why it matters:** If the zones are not separated, clearance/creepage has to be maintained next to every high-voltage trace, noise couples into the control circuitry, and in a fault the low-voltage side is damaged. The TI motor driver note recommends separate zones for digital, analog and high-power signals.
- **Recommended fix:** Gather the high-voltage/power parts in one zone and put the low-voltage control in a separate zone; connect the two zones only through isolation elements (isolator, gate driver, optocoupler) or defined boundary crossings. For clearance values by voltage see DFM (IPC-2221B table in PowerLab §3.3); for mains-connected designs IEC 62368-1 / IEC 60664-1 apply.
- **Exceptions:** On boards where all voltages are ≤ 30 V, separation is needed only for noise reasons.
- **Example:** —
- **Source:** [TI SLVA959B — Partitioning](https://www.ti.com/lit/an/slva959b/slva959b.pdf), [TI SZZA009 — Board Zoning](https://www.ti.com/lit/an/szza009/szza009.pdf)
