# 07 — Crystal and Oscillator (XTL)

Pierce-type crystal oscillators (the MCU's OSC_IN/OSC_OUT pins + crystal + two load capacitors) run at very small current and amplitude; this makes them among the circuits most sensitive to parasitic capacitance and noise coupling — especially 32.768 kHz LSE crystals. Most rules in this section can be audited from a screenshot: the crystal's distance to the MCU, the position of the load capacitors, traces passing under the crystal, vias and the surrounding GND copper are all visible. For general GND plane rules see GND; for keeping high-speed lines away from the crystal see HS-012.

### [XTL-001] Crystal far from the MCU oscillator pins, long traces

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** The crystal (a rectangular SMD with 2 or 4 pads, e.g. 3225/2016, or an HC-49 metal can) sits centimetres away from the MCU's OSC/XTAL pins; the XIN/XOUT traces wind around the MCU or pass between other components. In the correct case the crystal sits directly opposite the relevant pins, within a few mm, and the traces are straight and short.
- **Why it matters:** A long trace adds parasitic inductance/capacitance, shifts the frequency and acts like an antenna, both picking up noise and causing problems in EMI tests (ST AN2867).
- **Recommended fix:** Place the crystal as close to the MCU as possible (ST AN2867). Microchip: the oscillator circuit should be on the same side as the device and within 0.5 in (≈12 mm) of the oscillator pins.
- **Exceptions:** Espressif RF SoCs require the crystal to sit at a **minimum** distance from the clock pin (e.g. ESP32-S3 ≥2.0 mm, ESP32-H2 ≥1.8 mm, ESP32-C6 ≥2.4 mm, ESP32-P4 ≥4.5 mm); this means placement directly adjacent to the chip must not be flagged as an error — the value in the chip's own guide applies.
- **Example:** Link: https://www.raltron.com/webproducts/technical/technical_notes/Oscillator-design-guide-for-STM8S-STM8A-and-STM32-microcontrollers-ST-MICRO-1.pdf — Visible error: AN2867 Figures 14 and 18 show bad examples with long paths and no guard ring; Figure 15 shows the corrected design.
- **Source:** [ST AN2867 Oscillator design guide](https://www.st.com/resource/en/application_note/an2867-oscillator-design-guide-for-stm32-microcontrollers-stmicroelectronics.pdf), [Microchip – External Oscillator Layout Guidance](https://onlinedocs.microchip.com/oxy/GUID-E48B4A26-F201-4F0A-BCBA-16461582816A-en-US-3/GUID-AA04B64F-3C38-4E1C-8B51-49DE3CFE2419.html), [Espressif ESP32-S3 PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html)

### [XTL-002] Load capacitors far from the crystal, asymmetric, or with a long GND return

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** The two small capacitors (usually 0402/0603, pF range) are far from the crystal, in different orientations, or one is next to the crystal and the other on the far side of the MCU; the capacitors' GND pads run through long thin traces to a distant GND point. In the correct case the two capacitors sit at the two ends of the crystal in mirror symmetry, and their GND pads connect by a short path to the crystal's GND / the same GND copper.
- **Why it matters:** Load capacitance = C1·C2/(C1+C2) + parasitic capacitance (Cs); asymmetry and long connections make Cs uncertain and the frequency drifts; the capacitor GND loop picks up noise.
- **Recommended fix:** Place the load capacitors on both sides of the crystal, at the end of the clock trace; do not connect them directly to series components, so that the capacitor's GND pad is close to the crystal's (Espressif). Keep the two capacitors symmetric (ST AN2867 Example 2). Calculate the capacitor value including PCB parasitics (AN2867 example: CL=15 pF, Cs=5 pF → C1=C2=20 pF).
- **Exceptions:** MCUs with internal load capacitors (most 32 kHz LSE options) or ready-made oscillator modules do not need external capacitors — needs verification from the schematic.
- **Example:** —
- **Source:** [ST AN2867](https://www.st.com/resource/en/application_note/an2867-oscillator-design-guide-for-stm32-microcontrollers-stmicroelectronics.pdf), [Espressif ESP32-S3 PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html)

### [XTL-003] Signal/power trace runs under or right next to the crystal

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** A trace passes under the crystal body or the load capacitors (between the pads on the same layer, or on the bottom layer); power trace vias, a clock/data bus, PWM or USB line are present in the crystal area. If no bottom-layer view is available, ask the user for one.
- **Why it matters:** A fast signal running underneath injects noise into the low-amplitude oscillator nodes through capacitive coupling; this causes unstable oscillation and jitter.
- **Recommended fix:** Do not route high-frequency digital traces under the crystal, ideally no signal traces at all; keep power vias on both sides of the clock trace as far away as possible (Espressif). On a two-layer board there should be no trace on the opposite side of the crystal (Microchip). Route high-frequency paths away from the oscillator (ST AN2867).
- **Exceptions:** On a 4+ layer board with a continuous GND layer in between, slow signals on inner/bottom layers are less risky; they can still be noted as a "Low" finding.
- **Example:** —
- **Source:** [Espressif ESP32-S3 PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html), [Microchip – External Oscillator Layout Guidance](https://onlinedocs.microchip.com/oxy/GUID-E48B4A26-F201-4F0A-BCBA-16461582816A-en-US-3/GUID-AA04B64F-3C38-4E1C-8B51-49DE3CFE2419.html), [ST AN2867](https://www.st.com/resource/en/application_note/an2867-oscillator-design-guide-for-stm32-microcontrollers-stmicroelectronics.pdf)

### [XTL-004] No GND reference / guard copper in the crystal area

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** The crystal and load capacitors sit in a bare area; there is no GND pour or guard ring around them; the layer underneath has a split/empty area instead of GND. In the correct case the oscillator group is surrounded by GND copper, has continuous GND underneath, and this copper connects by a short path to the MCU's GND pin.
- **Why it matters:** Surrounding with GND and GND underneath isolate the oscillator nodes from neighbouring signals; without them the low-amplitude oscillator is exposed to noise (ST AN2867).
- **Recommended fix:** Surround the oscillator circuit with GND copper connected directly to the MCU GND, and do not route signal/power traces through this copper (Microchip); use a guard ring connected to GND (ST AN2867); provide a full GND plane under the crystal and the chip, and surround both sides of the clock trace with GND copper and dense GND vias (Espressif).
- **Exceptions:** Sources conflict: ST AN2867 recommends a dedicated oscillator GND area, separate from the application GND and connected to the nearest MCU GND; Espressif instead requires a continuous GND plane and, if there is enough GND on the top layer, recommends a copper-free gap (keep-out) around the crystal (to reduce parasitic capacitance and heat conduction). Both approaches are acceptable; the error is having no reference at all, or a plane that is slotted under the crystal. For the AN2867 note saying the can of a metal-can crystal should not be connected to the oscillator GND, follow the crystal datasheet.
- **Example:** Link: https://eevblog.com/forum/projects/atmega328pb-unstable-outputting-amplified-audio-over-pwm-into-a-speaker/msg5573087 — Visible situation: disagreement about vias in the crystal line and about a GND plane under the crystal.
- **Source:** [ST AN2867](https://www.st.com/resource/en/application_note/an2867-oscillator-design-guide-for-stm32-microcontrollers-stmicroelectronics.pdf), [Microchip – External Oscillator Layout Guidance](https://onlinedocs.microchip.com/oxy/GUID-E48B4A26-F201-4F0A-BCBA-16461582816A-en-US-3/GUID-AA04B64F-3C38-4E1C-8B51-49DE3CFE2419.html), [Espressif ESP32-S3 PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html) — for general GND see GND

### [XTL-005] Via in the XIN/XOUT traces, or crystal on the opposite side from the MCU

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** The crystal is on the bottom side, the MCU on the top side, and the OSC traces change layer through vias; or, although they are on the same side, there is a via in the XIN/XOUT trace.
- **Why it matters:** Every via adds parasitic inductance/capacitance and a noise coupling point; the oscillator node is sensitive because it is high-impedance.
- **Recommended fix:** No vias in the clock input/output traces (Espressif); the oscillator circuit should be on the same side as the device (Microchip); TI USB hub guides also recommend placing the crystal close to the chip and on the top layer for a short, via-free path.
- **Exceptions:** In very dense BGA breakouts a single via may be unavoidable; in that case place a GND via next to it and keep the trace as short as possible.
- **Example:** —
- **Source:** [Espressif ESP32-S3 PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html), [Microchip – External Oscillator Layout Guidance](https://onlinedocs.microchip.com/oxy/GUID-E48B4A26-F201-4F0A-BCBA-16461582816A-en-US-3/GUID-AA04B64F-3C38-4E1C-8B51-49DE3CFE2419.html), [TI SLLA329 USB hub design guide](https://ti.com/lit/pdf/slla329)

### [XTL-006] Oscillator traces asymmetric, with test points or branches

- **Severity:** Low
- **Detectable from image:** Yes
- **How it looks in the image:** The XIN and XOUT trace lengths differ noticeably (one straight, the other meandering); test pads, header pins or probe points are added to the oscillator nodes; the series resistor (Rext) is not on the crystal side but far from the MCU.
- **Why it matters:** Asymmetry makes the parasitic capacitance of the two nodes differ; test points add capacitance and pick up noise (ST AN2867 Example 2 lists "too many test points" as an error).
- **Recommended fix:** Keep the two oscillator traces symmetric and equally short; do not use test points on the oscillator nodes (ST AN2867). Place series components in the clock trace close to the chip side (Espressif). In humid environments a conformal coating over the LSE area is recommended (ST AN2867).
- **Exceptions:** A small (≈1 mm) length difference caused by the package pinout is insignificant.
- **Example:** Link: https://www.raltron.com/webproducts/technical/technical_notes/Oscillator-design-guide-for-STM8S-STM8A-and-STM32-microcontrollers-ST-MICRO-1.pdf — Visible error: AN2867 Figure 14 (asymmetry, many test points) and the corrected Figure 15.
- **Source:** [ST AN2867](https://www.st.com/resource/en/application_note/an2867-oscillator-design-guide-for-stm32-microcontrollers-stmicroelectronics.pdf), [Espressif ESP32-S3 PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html)

### [XTL-007] Crystal next to switching power, an inductor or a heat source

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** The crystal is within a few mm of a buck/boost inductor, a switching IC, a motor driver/power MOSFET or a large regulator; the crystal sits at the board edge or right at the foot of a connector.
- **Why it matters:** Magnetic fields and switching noise couple into the oscillator; heat shifts the crystal frequency.
- **Recommended fix:** Keep magnetic components such as large inductors away from the crystal (Espressif); keep high-current, modulated circuits such as a DC-DC output away from the oscillator, and keep noise-emitting or sensitive lines away from the board edge (SiTime AN10006). For placement rules see PLC.
- **Exceptions:** Shielded inductors and low-current LDOs are less risky; distance is still preferred.
- **Example:** —
- **Source:** [Espressif ESP32-S3 PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html), [SiTime AN10006 Best Design and Layout Practices](https://www.sitime.com/support/resource-library/application-notes/an10006-best-design-and-layout-practices)

### [XTL-008] Wrong decoupling or output arrangement on an active oscillator module

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** There is no 100 nF capacitor close to the VDD pin of the 4-pad active oscillator (VDD, GND, OUT, OE/NC), or the capacitor is centimetres away; the series resistor in the clock trace leaving the OUT pin is far from the oscillator (next to the receiver); a high-speed trace runs under the oscillator. To avoid confusing it with a passive crystal (2 pads, with load capacitors), ask for the schematic/part number.
- **Why it matters:** Supply noise turns directly into phase noise/jitter; decoupling is effective only while the inductance is small.
- **Recommended fix:** Place a 100 nF ceramic capacitor between VDD and GND as close to the VDD pin as possible; for large packages, 0.1 µF close by + 10 µF within 2 in (≈5 cm). With a single-ended output the series termination resistor should be adjacent to the oscillator output; no high-speed trace should run under the oscillator (SiTime AN10006). The MCU's own supply must also be well decoupled (ST AN2867; for details see PWR).
- **Exceptions:** For oscillators with differential outputs the termination should be close to the receiver (SiTime AN10006).
- **Example:** —
- **Source:** [SiTime AN10006 Best Design and Layout Practices](https://www.sitime.com/support/resource-library/application-notes/an10006-best-design-and-layout-practices), [ST AN2867](https://www.st.com/resource/en/application_note/an2867-oscillator-design-guide-for-stm32-microcontrollers-stmicroelectronics.pdf)
