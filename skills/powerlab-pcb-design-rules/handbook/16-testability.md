# 16 — Testability (TST)

Testability means the board can be measured, programmed and split into sections during first power-up (bring-up), in production test and when troubleshooting in the field. A screenshot shows whether test points exist, their size, their solder mask and their access; but which net they connect to is often not certain without the netlist — in that case the auditor should infer it from nearby parts (regulator output capacitor, MCU pin) and have the user confirm. For silkscreen rules on test point labels see SLK-010.

### [TST-001] No test points on the power rails

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** Around the output capacitor of each regulator (SOT-23-5, SOIC-8, buck/boost block with inductor, LDO) there is no round pad with open solder mask, no test loop and no "TP" label; there is no measurement point for the input voltage (VIN/VBAT) either. Estimate the number of rails from the number of regulators; without the netlist, have the user confirm which pad belongs to which rail.
- **Why it matters:** The first thing measured in bring-up is the rail voltage; without a test point the probe is pressed onto a small capacitor pad, slips and can short to a neighbouring pin.
- **Recommended fix:** Place at least one (≥2 for production test) test point for each power rail and each isolated GND; 2–10 probe points for the main power (Altium). Power/GND pads 1.5–2.0 mm (JLCPCB recommendation); for bring-up a 2–3 mm tall wire loop may be preferred.
- **Exceptions:** If the output connector or a large THT pad is already accessible and labelled, a separate TP may not be needed.
- **Example:** —
- **Source:** [Circuit Board Design for In-Circuit Testers (Altium)](https://resources.altium.com/p/circuit-board-design-circuit-testability), [Maximizing Circuit Reliability with PCB Test Points and Smart DFT (JLCPCB)](https://jlcpcb.com/blog/pcb-test-points-and-smart-dft), [DFT guidelines – test escape (PCBCart)](https://www.pcbcart.com/article/content/dft-guidelines-test-escape)

### [TST-002] No access to critical signals (reset, clock, enable, PGOOD, communication)

- **Severity:** Medium
- **Detectable from image:** No (netlist needed)
- **How it looks in the image:** The image can only show that there are no TPs or accessible vias/pads at all around the MCU/driver; you may notice that signals routed out from pins under a QFN/BGA do not reach any pad or header outside. Ask the user which signals are critical (reset, crystal/clock, UART/I²C/SPI, PWM/gate drive, PGOOD, feedback).
- **Why it matters:** If these signals cannot be measured, a "board does not start" fault cannot be diagnosed; pressing a probe on a fine-pitch package pin cracks the solder (100–200 g probe force).
- **Recommended fix:** Place a separate test pad for reset, clock, communication lines and any signal that can be a single point of failure for a block; for ICT, 100% coverage means "one pad per net". On high-speed lines keep the pad stub short (< ~2 mm for a 100 ps edge, JLCPCB) or use boundary-scan.
- **Exceptions:** Test points are not placed on very high-speed differential lines (see HS).
- **Example:** —
- **Source:** [DFT guidelines – test escape (PCBCart)](https://www.pcbcart.com/article/content/dft-guidelines-test-escape), [Maximizing Circuit Reliability with PCB Test Points and Smart DFT (JLCPCB)](https://jlcpcb.com/blog/pcb-test-points-and-smart-dft), [Circuit Board Design for In-Circuit Testers (Altium)](https://resources.altium.com/p/circuit-board-design-circuit-testability)

### [TST-003] Test pad too small, too dense or too close to parts/the edge

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** The TP pad is smaller than a neighbouring 0402 pad (≈ < 0.8 mm); TPs are clearly denser than the 2.54 mm header pitch; a TP is at the foot of a tall part (electrolytic, connector) or very close to the board edge. Compare the size with a known dimension.
- **Why it matters:** The probe slips on a small pad; dense pads require expensive fine probes and a guided fixture; a tall part hits the probe body.
- **Recommended fix:** Pad diameter 1.0 mm preferred, 0.9 mm acceptable, 0.8 mm only with tooling holes (Altium, PCBCart); JLCPCB nominal 0.89 mm. Centre-to-centre 2.54 mm preferred, 1.27 mm min. ≥ 1.0 mm to a component body; ≥ 5.0 mm to parts taller than 6.4 mm; ≥ 3.2 mm to the board edge (preferably 3.8 mm). If a fixture will be used, ≥ 2 tooling holes of 3.2 mm NPTH.
- **Exceptions:** On prototypes probed only by hand or by flying probe, the spacing and edge requirements can be relaxed; the pad size must still stay ≥ 0.8 mm.
- **Example:** —
- **Source:** [Circuit Board Design for In-Circuit Testers (Altium)](https://resources.altium.com/p/circuit-board-design-circuit-testability), [Test point design for ICT and FP (PCBCart)](https://www.pcbcart.com/article/content/test-point-design-ict-fp.html), [The Benefits of Bed of Nails Testing (JLCPCB)](https://jlcpcb.com/blog/bed-of-nails-pcb-testing)

### [TST-004] Test point covered by solder mask, a tented via, or spread over both sides

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** A point labelled "TP" looks green (solder mask colour) with no copper/tin shine; a via shown as a test point is covered by solder mask (tented); there is silkscreen on the TP pad; some TPs are on the top side and some on the bottom.
- **Why it matters:** A masked pad reads as electrically open; a probe cannot touch a tented via; a double-sided fixture is more expensive than a single-sided one.
- **Recommended fix:** Leave the TP pad without solder mask, with no silkscreen or conformal coating on it. If a via is to be a test point, make the hole ≤ 0.36 mm, the annular ring the size of a TP and the mask open. Gather all TPs on one side (usually the bottom).
- **Exceptions:** If testing happens before coating, temporary masking is acceptable.
- **Example:** —
- **Source:** [Test point design for ICT and FP (PCBCart)](https://www.pcbcart.com/article/content/test-point-design-ict-fp.html), [Circuit Board Design for In-Circuit Testers (Altium)](https://resources.altium.com/p/circuit-board-design-circuit-testability), [Assigning Testpoints on the Board (Altium Docs)](https://www.altium.com/documentation/altium-designer/adding-testpoints-pcb)

### [TST-005] Programming/debug connector missing, non-standard or inaccessible

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** On a board with an MCU there is no 2×5 1.27 mm (Cortex Debug), 2×10 2.54 mm (ARM 20-pin), Tag-Connect, or at least labelled SWDIO/SWCLK/GND/VCC/RESET pads; or the connector is behind a tall part, a heatsink or the enclosure wall; there is no pin-1 mark/key.
- **Why it matters:** The board cannot be programmed or the debug cable cannot be plugged in; a debug cable plugged in reversed can damage the target or the programmer.
- **Recommended fix:** In new designs use the 10-pin 0.05 in Cortex Debug connector recommended by Arm (Samtec FTSH-105, pin 7 key; 6.35 × 4.78 mm body) or Tag-Connect; mark pin 1 in silkscreen, leave free space around it for the cable direction, place it near the board edge. VTref (pin 1) must be connected to the target supply voltage.
- **Exceptions:** On boards programmed over USB/UART through a bootloader a UART header may be enough; SWD pads are still recommended for recovery.
- **Example:** —
- **Source:** [Cortex-M Debug Connectors (Arm)](https://documentation-service.arm.com/static/5fce6c49e167456a35b36af1), [Debug Connectors (SEGGER KB)](https://kb.segger.com/Connectors), [19-pin JTAG/SWD and Trace Connector – VTref (SEGGER KB)](https://kb.segger.com/19-pin_JTAG/SWD_and_Trace_Connector), [J-Link connectors (Keil)](https://keil.com/support/man/docs/jlink/jlink_connectors.asp)

### [TST-006] Tag-Connect footprint keepout and hole rules violated

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** TC2030 footprint: 2×3 pads of 0.787 mm (1.27 mm pitch), 3 NPTH alignment holes of 0.991 mm, and in the legged version 4 NPTH locking holes of 2.375 mm. It is an error if there are vias/traces in the hatched area between the pads, another trace passes within 0.02 in (0.5 mm) of the pads, or there are tall parts on either side of the locking holes (the finger-squeeze side). The pads must have no paste (stencil) opening.
- **Why it matters:** A via in the keepout catches a spring pin; paste forms a solder bump and spoils the contact; without finger access the legged cable cannot be attached.
- **Recommended fix:** Use the current revision of the manufacturer's drawing; leave the keepout empty and the pads without paste; with a prototype fabricator that plates all holes, define the holes as "plated" in the footprint; write "DNL" in the BOM.
- **Exceptions:** The no-legs (NL) version has no locking holes; only the alignment holes and the keepout apply.
- **Example:** Link: https://www.tag-connect.com/wp-content/uploads/bsk-pdf-manager/2026/07/TC2030-Footprint.pdf — Visible: correct footprint, keepout and finger access directions (good example).
- **Source:** [Footprint for TC2030 Plug-of-Nails, Legged (Tag-Connect)](https://www.tag-connect.com/wp-content/uploads/bsk-pdf-manager/2026/07/TC2030-Footprint.pdf), [J-Link 6-Pin Needle Adapter Datasheet (SEGGER)](https://www.SEGGER.com/downloads/jlink/J-Link_6-Pin_Needle_Adapter_Datasheet.pdf)

### [TST-007] No GND point next to the measurement point for an oscilloscope probe

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** There is no GND test point or GND copper with open solder mask within a few mm of the rail/switch-node test point; the board has a single GND loop and it is far from the measurement points (e.g. in the opposite corner).
- **Why it matters:** A long probe ground lead forms a large loop; in switching power supplies the measured ripple and spikes become measurement artefacts rather than real values.
- **Recommended fix:** For ripple measurement place the rail TP and the GND TP right next to the output capacitor, at a spacing suited to probe tip + ground spring or tip-and-barrel measurement; use an adjacent TP pair or a probe socket as on TI EVMs.
- **Exceptions:** On rails where only the DC level is measured (e.g. a reference voltage) a distant GND is acceptable.
- **Example:** Link: https://ti.com/document-viewer/lit/html/SLUU420A/GUID-D997C164-6B9E-4599-815E-FAFD360244F5 — Visible: adjacent TP7 (probe tip) / TP8 (GND barrel) pair on the TPS51217 EVM (good example).
- **Source:** [TPS40400 EVM User's Guide – ripple measurement (TI)](https://www.ti.com/document-viewer/lit/html/SLUU535A/GUID-5EF28725-519D-4789-B6CF-66152BCBDACB), [TPS51217 EVM User's Guide (TI)](https://ti.com/document-viewer/lit/html/SLUU420A/GUID-D997C164-6B9E-4599-815E-FAFD360244F5), [Measuring Methods – ABC of Power Modules (Würth Elektronik)](https://www.we-online.com/catalog/media/o198246v446%20Measuring%20Methods%20ABC%20of%20Power%20Modules%20EN%20(rev1).pdf)

### [TST-008] No 0 Ω / solder jumper / jumper to separate rails

- **Severity:** Low
- **Detectable from image:** Partly
- **How it looks in the image:** On the path from the regulator output to the load there is no series 0 Ω resistor, solder jumper (two half pads) or 2-pin jumper; or there is one but it is unlabelled and not large enough to carry the current (0402/0603 0 Ω on a high-current rail).
- **Why it matters:** Not being able to separate the source from the load in bring-up and test it unloaded first makes it harder to find the faulty part on a shorted rail; in ICT, joined rails prevent localizing the fault.
- **Recommended fix:** Add a series 0 Ω or solder jumper at each regulator output (and critical sub-blocks); choose the part's current rating for the rail current, use two in parallel if needed; label it in silkscreen, e.g. "JPx 3V3".
- **Exceptions:** On very high-current/low-impedance rails, a current-sense shunt or a removable copper bridge can be considered instead of a series element.
- **Example:** Link: https://community.sparkfun.com/t/what-do-you-call-this-jumper-connection-on-a-pcb/15824 — Visible: suggestion of a 0 Ω jumper to test two supplies first and then connect the rest of the board.
- **Source:** [DFT guidelines – test escape (PCBCart)](https://www.pcbcart.com/article/content/dft-guidelines-test-escape), [SparkFun Forum – jumper/0 Ω connection](https://community.sparkfun.com/t/what-do-you-call-this-jumper-connection-on-a-pcb/15824)

### [TST-009] No LED showing that power is present

- **Severity:** Low
- **Detectable from image:** Partly
- **How it looks in the image:** The board has no LED at all (0603/0805 LED footprint, "PWR", "3V3" label); or a multi-rail board has an LED only for the input, not on the regulator outputs.
- **Why it matters:** An LED shows instantly, without a meter, which rail is missing; in the field it also answers the question "is the board powered" for safety.
- **Recommended fix:** Put an LED at least on the input and the main regulator output; on multi-rail boards use an LED on each rail or driven by the PGOOD signal (a separate LED per rail is common on TI EVMs). Label the LED (as in SLK-010).
- **Exceptions:** On battery-powered low-power boards an always-on LED ruins the current budget; prefer one that can be disconnected by a jumper or an MCU-controlled LED.
- **Example:** —
- **Source:** [LIGO PCB design checklist E060231 (Caltech/LIGO)](https://dcc-lho.ligo.org/LIGO-E060231/public), [MCT8315Z EVM User's Guide – status LEDs (TI)](https://ti.com/document-viewer/lit/html/SNLU342/GUID-B85CF074-3940-428B-9B28-30CBD2D062BD)
