# 08 — Switching Power Supplies (SMPS)

This section covers the layout of buck/boost converters and discrete MOSFET half bridges: hot loop, input capacitor, switch node area, inductor placement and orientation, feedback and current-sense traces, snubber and gate driver loops. In switching stages the layout is part of the circuit: even a few nH of extra inductance turns into volt-level spikes during ns-scale transitions. For general trace width and decoupling see PWR, for thermal topics see THM, for ground plane integrity see GND.

---

### [SMPS-001] Buck input ceramic capacitor far from the VIN–PGND pins

- **Severity:** Critical
- **Detectable from image:** Yes
- **How it looks in the image:** There is no small ceramic capacitor (0402–1206) right next to the regulator IC's VIN and PGND pins; the nearest input capacitor is several mm away, or there is only a distant electrolytic; the VIN or PGND connection is a thin trace. In a package with more than one VIN/PGND pin pair, one of the pairs has no capacitor.
- **Why it matters:** In a buck, the input capacitor–high-side switch–low-side switch loop carries purely switched current; the loop inductance produces a V = L·di/dt spike. ADI/Würth example: ~2.5 cm of trace ≈ 20 nH; with a 5 A, 5 ns transition ≈ 20 V. According to TI, this spike can go as far as IC failure.
- **Recommended fix:** Make the input capacitor the first part placed and the first connected after the IC; as close as the manufacturing rules allow, with short and wide copper. ROHM: 0.1–0.47 µF X5R/X7R bypass at the IC terminal on the top layer; even shortening the connection by 1 mm is recommended. With multiple VIN/PGND pairs, one capacitor per pair, placed symmetrically.
- **Exceptions:** In controller designs (external FETs) the critical point is the MOSFETs, not the IC pin (see SMPS-003).
- **Example:** Link: https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf — Visible: Figure 3-a good (CBYPASS right at the foot of the IC, on the same side). Link: https://edgeworker.ti.com/lit/pdf/slyt614 — Visible: Figure 2, correct placement of the input capacitor relative to the IC.
- **Source:** [TI SLYT614 — Five steps to a great PCB layout for a step-down converter](https://edgeworker.ti.com/lit/pdf/slyt614), [ROHM — PCB Layout Techniques of Buck Converter](https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf), [TI LM61440 — Layout Guidelines](https://ti.com/document-viewer/LM61440/datasheet/GUID-B3BC1FF3-222C-4456-916C-6A98740CD6F4), [ADI/Würth — PCB Board Layout Optimization](https://www.we-online.com/files/pdf1/pcb-board-layout-optimization-v2.pdf)

### [SMPS-002] Hot loop elements on the opposite side / via in the loop

- **Severity:** Critical
- **Detectable from image:** Yes (both sides needed)
- **How it looks in the image:** The regulator or MOSFETs are on the top side, the input bypass capacitor (or freewheeling diode) on the bottom side; the connection between them goes through vias. A via in the power trace between the parts forming the hot loop.
- **Why it matters:** Via inductance is added directly to the hot loop; according to ROHM a bypass capacitor on the opposite side increases noise and has the reverse effect, and noise gets worse if the diode is placed on the bottom side. TI requires that no vias be used in connecting the power components.
- **Recommended fix:** Connect the input bypass capacitor, the switch(es) and the diode on the same side, with copper on the same layer. Place the transition vias to the system VIN/GND outside the circuit, where they do not interrupt critical connections.
- **Exceptions:** ROHM Figure 3-c: acceptable only if the large CIN is on the bottom side and the small CBYPASS is on top; ripple may increase at high current. In packages such as WCSP, taking SW to the inductor through a via is better than displacing the input capacitor (TI).
- **Example:** Link: https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf — Visible: Figure 3-d (bad: CBYPASS and CIN on the bottom side). Link: https://courses.fedevel.com/forum/schematic-design-pcb-layout/16381-buck-converter-layout-review — Visible error: passives in the power loop are on the opposite side; the reviewer recommends moving them to the same side (community).
- **Source:** [ROHM — PCB Layout Techniques of Buck Converter](https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf), [TI SLYT614](https://edgeworker.ti.com/lit/pdf/slyt614)

### [SMPS-003] Large hot loop in a discrete-MOSFET synchronous buck / half bridge

- **Severity:** Critical
- **Detectable from image:** Partly (the schematic may be needed to tell which MOSFET is high-side/low-side)
- **How it looks in the image:** The high-side and low-side MOSFETs are far from each other; the input ceramics are not between the high-side FET drain and the low-side FET source (PGND) but somewhere else; the high-side FET source–low-side FET drain connection is long; the area enclosed by the loop is large and there is no continuous GND layer underneath.
- **Why it matters:** The parasitic inductance between the high-side source and the low-side drain produces large negative spikes at the switch node; the loop area determines radiation and overshoot voltage.
- **Recommended fix:** Put the two MOSFETs side by side and place the input ceramics as a bridge between the high-side drain and low-side source pads; according to TI LM2104 there should be a low-ESR electrolytic + good-quality ceramic between the high-side drain and GND. Make the layer directly below the top layer continuous GND (lowers loop inductance).
- **Exceptions:** —
- **Example:** Link: https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf — Visible: Figure 1-c, showing the paths where current changes abruptly (the ones needing attention).
- **Source:** [TI LM2104 — Layout Guidelines](https://ti.com/document-viewer/LM2104/datasheet/GUID-279F829C-5876-42DE-8AC0-6603E6D505E9), [TI LM61440 — Layout Guidelines](https://ti.com/document-viewer/LM61440/datasheet/GUID-B3BC1FF3-222C-4456-916C-6A98740CD6F4), [ROHM — PCB Layout Techniques of Buck Converter](https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf)

### [SMPS-004] Large critical loop (switch–diode–output capacitor) in a boost

- **Severity:** Critical
- **Detectable from image:** Partly (the topology must be confirmed from the schematic)
- **How it looks in the image:** The boost converter is laid out with buck logic: the input capacitor is close to the IC but the output capacitor is far from the diode/high-side switch; the distance between the low-side switch (or IC SW pin) and the diode is long; the switch's source/PGND connection is thin and long; there is no small high-frequency bypass capacitor at the output.
- **Why it matters:** In a boost, the switched current is in the switch–diode–output capacitor loop on the output side; parasitic L and C here cause ringing above 200 MHz at the switch node. In the TI example, the peak at a 5 V output rose to 9.8 V and threatened the low-side switch.
- **Recommended fix:** Minimise the distance between the switch and the diode; connect the FET source to PGND with a short path; place the bulk output capacitor as close as possible to the diode cathode and PGND; add a 0.01–2.2 µF high-frequency bypass between the output and PGND.
- **Exceptions:** —
- **Example:** Link: https://www.thierry-lequeu.fr/data/AN-1149.pdf — Visible: Figure 2 bad boost layout (scattered parts, long power traces), Figures 3–4 good layout.
- **Source:** [TI SLVA255 — Minimizing Ringing at the Switch Node of a Boost Converter](https://www.ti.com/lit/pdf/slva255), [TI/National AN-1149 (SNVA021)](https://www.thierry-lequeu.fr/data/AN-1149.pdf)

### [SMPS-005] Switch node copper area larger than necessary

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** An unnecessarily wide polygon between the SW pin/MOSFET midpoint and the inductor; SW copper fills the area under or around the inductor; SW copper is duplicated onto other layers; the SW trace is long.
- **Why it matters:** The SW node swings very fast from input to GND; all copper connected to it forms one plate of a parasitic capacitor with the other nodes in the circuit, and is the main source of capacitive noise coupling/radiation. Unnecessarily wide copper acts like an antenna.
- **Recommended fix:** Make the SW copper wide enough to carry the current (see PWR-001) but as short as possible; place the inductor close to the IC and rotate it so that the SW area is minimised.
- **Exceptions:** For some regulators with integrated FETs the datasheet may recommend copper on the SW pins for heat; the datasheet's example layout takes priority. According to ROHM, thermal pad copper at GND potential does not increase EMI (the problem is the SW copper).
- **Example:** Link: https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf — Visible: Figure 6-a good, Figure 6-b bad (unnecessarily wide copper going to the inductor).
- **Source:** [TI SLYT614](https://edgeworker.ti.com/lit/pdf/slyt614), [ROHM — PCB Layout Techniques of Buck Converter](https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf), [TI LM61440 — Layout Guidelines](https://ti.com/document-viewer/LM61440/datasheet/GUID-B3BC1FF3-222C-4456-916C-6A98740CD6F4)

### [SMPS-006] Sensitive trace runs next to/under the switch node or inductor

- **Severity:** High
- **Detectable from image:** Yes (all layers must be visible)
- **How it looks in the image:** An FB, COMP, SS, current-sense or ADC trace runs parallel and close to the SW copper; on any layer it passes under the inductor body or the diode; it runs parallel to a power line over a long distance.
- **Why it matters:** The inductor's magnetic field and the SW node's electric field couple noise into high-impedance traces; noise on the feedback trace causes output voltage error and instability.
- **Recommended fix:** Route sensitive traces away from the SW node, inductor and diode, if necessary on the opposite side with a GND plane in between; they should not run parallel to a power line.
- **Exceptions:** —
- **Example:** Link: https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf — Visible: Figure 7-c good (FB trace on the bottom layer, away from SW), Figure 7-d bad (FB trace next to the inductor).
- **Source:** [ROHM — PCB Layout Techniques of Buck Converter, Section 7](https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf), [TI/National AN-1149 (SNVA021)](https://www.thierry-lequeu.fr/data/AN-1149.pdf)

### [SMPS-007] Feedback divider far from the IC, large FB node

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** The FB divider resistors (and the feedforward capacitor, if any) are next to the output capacitor, far from the IC; the trace to the FB pin is long and thin (the high-impedance node is long).
- **Why it matters:** The FB pin is high-impedance; the larger the copper of this node, the more noise it picks up, degrading regulation and causing switching jitter.
- **Recommended fix:** Place the divider and CFF right at the foot of the FB pin; keep the FB–divider–AGND connection short. The connection that has to be long is the VOUT sense trace; route it away from noise sources as well.
- **Exceptions:** In fixed-output versions the FB pin goes directly to the output; it should still be routed away from noise.
- **Example:** Link: https://edgeworker.ti.com/lit/pdf/slyt614 — Visible: Figure 5, FB resistors placed adjacent to the IC.
- **Source:** [TI SLYT614](https://edgeworker.ti.com/lit/pdf/slyt614), [TI LM61440 — Layout Guidelines](https://ti.com/document-viewer/LM61440/datasheet/GUID-B3BC1FF3-222C-4456-916C-6A98740CD6F4), [ROHM — PCB Layout Techniques of Buck Converter](https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf)

### [SMPS-008] Output voltage sensed at the wrong point

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** The VOUT sense trace (top end of the divider or the VOS pin) is taken from the inductor pad, near SW, or from a point before the output capacitor; the bottom end of the divider connects to the noisy PGND area (input capacitor/diode GND).
- **Why it matters:** The trace resistance and ripple between the sense point and the output capacitor enter the regulation as error; load regulation and stability degrade.
- **Recommended fix:** Take the sense point after the output capacitor (or at the load, if remote sensing is needed); route the VOS/FB trace short, direct and isolated from other connections; connect the divider's GND to AGND.
- **Exceptions:** If the load is far away and remote sensing is wanted, the sense point may be the load (see PWR-015).
- **Example:** Link: https://edgeworker.ti.com/lit/pdf/slyt614 — Visible: Figure 4, the VOS trace taken to the output capacitor with two vias and a separate trace.
- **Source:** [ROHM — PCB Layout Techniques of Buck Converter, Section 7](https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf), [TI SLYT614](https://edgeworker.ti.com/lit/pdf/slyt614)

### [SMPS-009] Wrong placement/orientation of the inductor and output capacitor

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** The inductor is far from the IC (long SW trace); the output capacitor is far from the inductor; there is a copper area between the inductor pads (under the body); the GND ends of the input and output capacitors are side by side, at the same point.
- **Why it matters:** A long SW trace increases radiation; copper between the inductor terminals carries the high frequency at SW to the output through stray capacitance; noise of hundreds of MHz on the input GND can pass to a nearby output capacitor.
- **Recommended fix:** Place the inductor close to the IC (not as critical as the input capacitor) and rotate it so that SW is short and the connection to the output is easy; place the output capacitor close to the inductor. ROHM: 1–2 cm distance between the CIN and CO GNDs. Do not leave copper between the inductor pads.
- **Exceptions:** If the datasheet/EVM example layout differs, it takes priority.
- **Example:** Link: https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf — Visible: Figure 6-d bad (copper between the inductor terminals).
- **Source:** [ROHM — PCB Layout Techniques of Buck Converter, Sections 5–6](https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf), [TI SLYT614](https://edgeworker.ti.com/lit/pdf/slyt614)

### [SMPS-010] GND plane under the inductor: cut out or continuous? (conflicting)

- **Severity:** Medium
- **Detectable from image:** Yes (inner/bottom layer image needed)
- **How it looks in the image:** There is or is not a rectangular gap (keepout) in the GND plane under the inductor body; whether there is a signal/power trace underneath.
- **Why it matters:** ROHM: eddy currents form in the GND layer directly under the inductor, inductance drops and losses increase; therefore do not place GND directly underneath. Signal Integrity Journal (Practical EMC) measurement: on a single buck board, the continuous plane gave lower emissions than the cut-out plane in most measurements (~20 dB at 100–300 MHz in the field scan).
- **Recommended fix:** Report both views. Accept a continuous GND plane with a shielded inductor on a multilayer board; accept the gap with an open-core inductor or if the datasheet asks for a keepout. In both cases no signal/power trace should pass under the inductor (on any layer) (see SMPS-006).
- **Exceptions:** The land pattern/keepout recommended by the inductor manufacturer always takes priority.
- **Example:** Link: https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf — Visible: Figure 6-c (bad according to ROHM: GND copper directly under the inductor).
- **Source:** [ROHM — PCB Layout Techniques of Buck Converter, Section 5](https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf), [Signal Integrity Journal — DC-DC Converters: Solid Return Plane or Cutouts](https://www.signalintegrityjournal.com/blogs/17-practical-emc/post/2694-dc-dc-converters-solid-return-plane-or-cutouts-under-switch-node-and-inductor?v=preview)

### [SMPS-011] Open-core inductor close to a sensitive circuit

- **Severity:** Medium
- **Detectable from image:** Partly (the winding may be visible in the 3D view; the part number is needed for the exact type)
- **How it looks in the image:** In the 3D image, a drum/rod-core inductor with an exposed winding; analog front end, crystal, sensor or feedback components nearby.
- **Why it matters:** The stray magnetic field of an open-core inductor couples noise into the surrounding traces and components; rod cores emit the most unwanted noise.
- **Recommended fix:** Prefer a closed-core inductor (toroid, encapsulated E-core, shielded SMD). If an open core is unavoidable, choose a low-EMI type, place it further from low-power traces and components, and orient its poles perpendicular to the PCB.
- **Exceptions:** Low severity if there is no sensitive circuit around and no EMI test is required.
- **Example:** —
- **Source:** [TI/National AN-1149 (SNVA021)](https://www.thierry-lequeu.fr/data/AN-1149.pdf)

### [SMPS-012] Snubber far from the switch/IC

- **Severity:** High
- **Detectable from image:** Partly (the schematic must confirm that the RC pair is a snubber)
- **How it looks in the image:** A small resistor + small ceramic capacitor (RC snubber) connected at a point far from the SW node (e.g. on the inductor side of the diode); the snubber's GND end runs to PGND through a long trace.
- **Why it matters:** The snubber must be in parallel with the parasitic inductance that causes the ringing; if it is placed far away, it cannot damp the spike because of the trace inductance in between.
- **Recommended fix:** Connect the RC snubber between the SW and PGND pins (in a discrete design, the switch's drain–source) by the shortest path. Choose the resistor's package by its loss: P ≈ ½·C·V²·f (TI SLVA255).
- **Exceptions:** Most modern regulators do not need a snubber; if there is no snubber, this rule does not apply.
- **Example:** Link: https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf — Visible: Figure 3-g good (close to the IC SW and GND terminals), Figure 3-h bad (across the diode terminals).
- **Source:** [TI SLYT614](https://edgeworker.ti.com/lit/pdf/slyt614), [ROHM — PCB Layout Techniques of Buck Converter](https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf), [TI SLVA255](https://www.ti.com/lit/pdf/slva255)

### [SMPS-013] Current-sense traces run next to the SW node or share a common path

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** The controller's CS/ISENSE traces are taken from the outer ends of the shunt or from the power pour; the two traces take separate paths, passing by SW copper or the inductor; in low-side shunt measurement the controller GND is connected at a point far from the shunt's GND end.
- **Why it matters:** In current-mode control the sensed signal is small and fast; coupled noise triggers early switching/a false current limit, and common-path resistance causes gain error.
- **Recommended fix:** Use a Kelvin connection and matched-pair routing (see PWR-014, PWR-015); route the traces away from the SW node and the inductor, close to each other; give the shunt as much copper as possible (reduces thermal drift).
- **Exceptions:** If sensing is done inside the IC (via RDS(on)), there are no external traces.
- **Example:** —
- **Source:** [TI LMP8640 — Layout Guidelines](https://www.ti.com/document-viewer/LMP8640/datasheet/layout), [ROHM — PCB Layout Techniques of Buck Converter](https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf)

### [SMPS-014] Gate driver far from the MOSFET, large gate loop

- **Severity:** Critical
- **Detectable from image:** Yes
- **How it looks in the image:** The gate driver IC is centimetres away from the MOSFETs; the GATE trace is thin and long, the return (source/GND) trace comes along a different path and leaves a large area between the two; the gate resistor sits at a random point between the driver and the gate.
- **Why it matters:** During FET turn-on/turn-off, gate current pulses of several amperes lasting ~10 ns occur; the loop inductance leads to L·di/dt drop, gate ringing and false turn-on.
- **Recommended fix:** Place the driver as close to the MOSFETs as possible; route the gate and return traces side by side (or stacked on an adjacent layer) to minimise the loop area; size the gate resistors for the pulse current. Gate traces should not run on the same layer as, and parallel to, high-current copper.
- **Exceptions:** —
- **Example:** Link: https://www.allegromicro.com/-/media/files/guide/ahv85311nk-pcb-layout-guide.pdf?sc_lang=en — Visible: pp. 8–10, a good example where the turn-on and turn-off current paths are kept short.
- **Source:** [TI LM2104 — Layout Guidelines](https://ti.com/document-viewer/LM2104/datasheet/GUID-279F829C-5876-42DE-8AC0-6603E6D505E9), [Allegro — AHV85311NK PCB Layout Guide](https://www.allegromicro.com/-/media/files/guide/ahv85311nk-pcb-layout-guide.pdf?sc_lang=en)

### [SMPS-015] Gate return not Kelvin: source path shared with the power current

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** The high-side driver's SOURCE/SH reference trace is taken from a distant point of the phase (switch node) pour (e.g. the inductor side); the low-side driver's GND is connected to a distant point of the power GND pour; on a FET whose package has a separate Kelvin source (KS) pin, KS is not used.
- **Why it matters:** If the gate–source current shares copper with the drain–source power current, the di/dt of the power current produces a voltage across that shared inductance and corrupts the effective gate voltage.
- **Recommended fix:** If there is a KS pin, use it; otherwise connect the source return to the FET's source pin as a Kelvin connection (directly from the foot of the pin, with a separate trace). Allegro: running the source return as a plane on the inner layer under the driver and connecting it to the decoupling capacitors with many vias is often best.
- **Exceptions:** —
- **Example:** —
- **Source:** [Allegro — AHV85311NK PCB Layout Guide](https://www.allegromicro.com/-/media/files/guide/ahv85311nk-pcb-layout-guide.pdf?sc_lang=en), [TI LM2104 — Layout Guidelines](https://ti.com/document-viewer/LM2104/datasheet/GUID-279F829C-5876-42DE-8AC0-6603E6D505E9)

### [SMPS-016] Bootstrap and driver supply capacitors far from the driver

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** The BST–SH (HB–HS) capacitor and the VDD/GVDD bypass capacitor are far from the driver IC or connected through vias; the bootstrap diode, bootstrap capacitor and VDD capacitor are scattered.
- **Why it matters:** These capacitors supply the peak current that turns the gate on; the bootstrap capacitor recharges every period in a short time with a high peak current, and the inductance of this loop corrupts the charging and the gate voltage.
- **Recommended fix:** Connect low-ESR/ESL ceramics directly to the GVDD–GND and BST–SH pins, close to the IC; keep the loop formed by the bootstrap capacitor, bootstrap diode, local bypass capacitor and low-side FET short; do not put a via between the capacitor and the pin.
- **Exceptions:** —
- **Example:** Link: https://www.allegromicro.com/-/media/files/guide/ahv85311nk-pcb-layout-guide.pdf?sc_lang=en — Visible: p. 3, bootstrap capacitors placed adjacent to their pin pairs.
- **Source:** [TI LM2104 — Layout Guidelines](https://ti.com/document-viewer/LM2104/datasheet/GUID-279F829C-5876-42DE-8AC0-6603E6D505E9), [Allegro — AHV85311NK PCB Layout Guide](https://www.allegromicro.com/-/media/files/guide/ahv85311nk-pcb-layout-guide.pdf?sc_lang=en)

### [SMPS-017] GND of small-signal components connected at random to the noisy power ground

- **Severity:** Medium
- **Detectable from image:** Partly (AGND/PGND net names and the datasheet recommendation are needed)
- **How it looks in the image:** The GND ends of the FB divider, soft-start and compensation components are connected with separate vias to the noisy area right next to the input capacitor/diode GND; there is no connection between the AGND pin and the exposed pad/PGND, or there are connections at several points.
- **Why it matters:** If the switching voltage differences in the power grounds ride on the reference of the quiet components, regulation degrades and digital input levels may shift.
- **Recommended fix:** Follow the datasheet's grounding recommendation; usually the quiet components return to the AGND pin and AGND and PGND join at a single point (mostly at the exposed pad). Transition vias to the system plane go at the GND ends of the input/output capacitors. For general plane rules see GND.
- **Exceptions:** Datasheets that recommend a single continuous GND plane do not need a separate AGND island.
- **Example:** Link: https://edgeworker.ti.com/lit/pdf/slyt614 — Visible: Figures 6–7, finished layout with single-point grounding.
- **Source:** [TI SLYT614](https://edgeworker.ti.com/lit/pdf/slyt614), [ROHM — PCB Layout Techniques of Buck Converter, Section 8](https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf)
