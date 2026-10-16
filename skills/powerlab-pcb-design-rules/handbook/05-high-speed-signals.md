# 05 — High-Speed Signals (HS)

This section covers differential pairs such as USB 2.0 / USB-C, Ethernet MDI, HDMI/MIPI and fast-edged single-ended lines (SPI, clock). From a screenshot the pair's symmetry, via count, bend angles, stubs, meander (serpentine) structures and plane gaps beneath it can be seen; **impedance, edge rate and stackup cannot be read from the image** — for these, ask the user for the stackup, target impedance and interface speed (e.g. USB FS 12 Mbit/s or HS 480 Mbit/s). For general GND plane/stitching rules see GND, for layer order and dielectric choice see STK, for antenna/RF lines see RF.

> Unit note: 1 mil = 0.0254 mm. Values given in mil in the sources are written together with their mm equivalent.

### [HS-001] Differential pair does not run together, symmetric and parallel

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** After leaving the connector, the D+/D- (or TX±/RX±) traces separate and take different paths (e.g. one to the left of a component, the other to its right); the gap between the two traces visibly changes along the route; another trace or via passes between the pair. In the correct case two traces of equal width run side by side at constant spacing like "railway tracks"; separation is only a few mm at the pin/pad entry.
- **Why it matters:** Differential impedance is set by trace width and intra-pair spacing; as the spacing changes the impedance deviates, and reflection and common-mode conversion (EMI) increase.
- **Recommended fix:** Run the pair together with constant width and spacing along the whole route; keep the separation at the package breakout short — TI requires the package escape to end within 0.25 in (≈6.4 mm) of the package. The USB 2.0 target is 90 Ω ±15% differential (Renesas, based on the USB specification).
- **Exceptions:** USB Full-Speed (12 Mbit/s) links tolerate poor geometry over short distances (KiCad forum, community opinion); still, routing them as a pair is a free improvement. Unavoidable short separation at the pad/pin entry is not a violation.
- **Example:** Link: https://forum.kicad.info/t/differential-pair-routing-in-kicad-6-0/36935 — Visible error: the pair is broken because of the ESD diodes and the D+/D- pin order, requiring a crossover with vias.
- **Source:** [TI SPRAAR7 High-Speed Interface Layout Guidelines](https://www.ti.com/lit/an/spraar7j/spraar7j.pdf), [Renesas RX71M Guidelines for High-Speed USB2.0 Board Design](https://www.renesas.com/en/document/oth/rx71m-high-speed-usb-guidelines-high-speed-usb20-board-design)

### [HS-002] Controlled impedance target not verified against the stackup

- **Severity:** High
- **Detectable from image:** No (stackup needed)
- **How it looks in the image:** Impedance cannot be calculated from the image. Warning signs: on a 2-layer board the USB/Ethernet pair is drawn with the same thin width as other traces (e.g. 0.2 mm); the width of the pair traces changes along the route; the layer directly below the pair is not GND. The auditor agent should ask the user for: layer count, board thickness, dielectric thickness and εr, trace width/spacing, target impedance and which calculator was used.
- **Why it matters:** A trace width and spacing give the correct impedance only for a specific stackup; the same geometry produces a very different impedance on a board of different thickness.
- **Recommended fix:** Calculate the geometry for the stackup with the manufacturer's calculator. The JLCPCB calculator supports 20–90 Ω single-ended and 50–150 Ω differential, assumes NP-155F material for 4–8 layers and presents results as "reference only" (accessed 2026-10). Targets: USB 2.0 90 Ω ±15% (Renesas), Ethernet MDI 100 Ω ±10% (TI SNLA387). The correct material/stackup must be selected when ordering.
- **Exceptions:** On short and slow lines (e.g. USB FS, a few cm) impedance control is not mandatory; the decision depends on bandwidth and the accepted impedance deviation (Altium, critical length discussion).
- **Example:** —
- **Source:** [User Guide to the JLCPCB Impedance Calculator](https://jlcpcb.com/help/article/User-Guide-to-the-JLCPCB-Impedance-Calculator), [Renesas RX71M USB2.0 Board Design](https://www.renesas.com/en/document/oth/rx71m-high-speed-usb-guidelines-high-speed-usb20-board-design), [TI SNLA387 Ethernet PHY PCB Design Layout Checklist](https://ti.com/lit/pdf/snla387) — for stackup choice see STK

### [HS-003] Pair crosses a slot/gap in the reference plane or a plane edge

- **Severity:** Critical
- **Detectable from image:** Partly
- **How it looks in the image:** With the bottom layer (or inner GND) visible, a gap line, split plane boundary (e.g. GND/AGND or 3V3/5V split), a long trace slot or a via-row "fence" crosses beneath the pair; the pair runs very close to the board edge or pour edge. In a single-layer image what lies beneath is not visible → ask the user for a bottom/inner layer image.
- **Why it matters:** The return current is forced to detour around the slot; loop area and impedance discontinuity increase, and radiation and reflection occur.
- **Recommended fix:** Run the pair over continuous GND along its whole route. TI: the pair should be ≥90 mil (≈2.3 mm) from the plane edge and ≥1.5× trace width from voids in the plane; Renesas: the GND plane beneath should be at least 2 mm wider than the USB lines. If crossing a slot is unavoidable, place a ≤1 µF stitching capacitor at the crossing point (TI).
- **Exceptions:** Intentional voids beneath SMD pads on the pair (AC coupling capacitor, ESD) are outside this rule (see HS-017).
- **Example:** —
- **Source:** [TI SPRAAR7](https://www.ti.com/lit/an/spraar7j/spraar7j.pdf), [Renesas RX71M USB2.0 Board Design](https://www.renesas.com/en/document/oth/rx71m-high-speed-usb-guidelines-high-speed-usb20-board-design), [TI TS3USB221A-Q1 Layout Guidelines](https://www.ti.com/document-viewer/TS3USB221A-Q1/datasheet/layout-guidelines-scds300728) — for the general return path see GND

### [HS-004] Unequal via count at a layer change, or no GND return via next to it

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** 2 vias on one leg of the pair, 1 via on the other; vias far apart from each other or in a diagonal position; no GND via near the pair where it changes layers. In the correct case the two signal vias sit side by side symmetrically, with one GND via right next to them (on each side).
- **Why it matters:** A via is an impedance discontinuity; an unequal via count creates intra-pair delay difference and common-mode conversion. When the reference plane changes, a nearby GND via is needed so the return current can change layers too.
- **Recommended fix:** Use an equal number of vias on both legs, placed as symmetrically as possible; place the vias close to the SoC/chip (TI). If the reference GND changes, place symmetric GND stitching vias within ≤200 mil (≈5.1 mm, closer is better) of the signal vias (TI); Espressif recommends a pair of GND return vias at every transition. The TI AM335x table allows at most 4 vias per USB 2.0 trace.
- **Exceptions:** If both reference layers are GND and many stitching vias already exist between them, the need for extra vias decreases. For via geometry (stub, anti-pad) see VIA.
- **Example:** Link: https://forum.kicad.info/t/differential-pair-routing-in-kicad-6-0/36935 — Visible recommendation: place a GND via next to each USB via at a via crossover.
- **Source:** [TI SPRAAR7](https://www.ti.com/lit/an/spraar7j/spraar7j.pdf), [Espressif ESP32-S3 PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html)

### [HS-005] Intra-pair length difference (skew) not matched, or matched in the wrong place

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** When the pair turns a corner the inner leg ends up noticeably shorter and this is not compensated anywhere; or the compensation meander sits in the middle of the pair, far from the end where the mismatch arises. For the exact difference, ask the user for the EDA's length report (e.g. the KiCad "Length tuning" value).
- **Why it matters:** Delay difference between the legs converts part of the differential signal to common mode; jitter and radiation increase.
- **Recommended fix:** For USB 2.0 the D+/D- difference ≤2.5 mm (Renesas RX71M) or ≤50 mil ≈1.27 mm (TI AM335x table); for Ethernet MDI 100M ≤50 mil, for 1G ≤20 mil ≈0.51 mm (TI SNLA387). Place the compensation as close as possible to the end where the mismatch arises (TI SPRAAR7); keep the structures short (Altium).
- **Exceptions:** Length matching between pairs (TX pair vs. RX pair) is not required (TI SPRAAR7). Parallel clocked buses (MIPI, parallel LVDS) excepted.
- **Example:** —
- **Source:** [TI SPRAAR7](https://www.ti.com/lit/an/spraar7j/spraar7j.pdf), [Renesas RX71M USB2.0 Board Design](https://www.renesas.com/en/document/oth/rx71m-high-speed-usb-guidelines-high-speed-usb20-board-design), [Altium – Differential Pair Length Matching Best Practices](https://resources.altium.com/p/differential-pair-length-matching-best-practices-signal-integrity)

### [HS-006] Unnecessary or excessive meander (serpentine) length tuning

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** Long, dense, high-amplitude "accordion" waves on one leg of the pair; the meander structure covers most of the pair's length; millimetre-level tuning done even where the tolerance is very wide (e.g. USB FS); the two legs move far apart from each other inside the meander.
- **Why it matters:** Every length tuning structure produces some mode conversion and reflection; the larger the tuning structure, the greater the degradation. Reducing the length difference to zero does not eliminate the sources of jitter.
- **Recommended fix:** First reduce the difference by fixing the routing; remove the remaining difference with a single short, low-amplitude structure close to the source of the mismatch (Altium). Take the tolerance from the interface specification (HS-005); do not set an unnecessarily tight target.
- **Exceptions:** On tightly timed buses such as DDR/MIPI heavy meandering may be unavoidable; simulation is recommended in that case.
- **Example:** —
- **Source:** [Altium – Differential Pair Length Matching Best Practices](https://resources.altium.com/p/differential-pair-length-matching-best-practices-signal-integrity), [Altium – Trombone, Accordion and Sawtooth Tuning](https://resources.altium.com/p/length-matching-for-high-speed-signals-trombone-accordion-and-sawtooth-tuning)

### [HS-007] 90° or sharp corner on a high-speed pair

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** The pair traces turn with a single right angle (L shape) or an even sharper (acute) angle. In the correct case turns are made of two 45° bends or an arc; the inner angle is greater than 135°.
- **Why it matters:** At a sharp corner the trace width increases locally (impedance drops) and an inner/outer leg length difference arises.
- **Recommended fix:** Keep the angle at turns >135° (TI SPRAAR7); use two 45° bends or an arc instead of 90° (TI TS3USB221A); Renesas recommends a smooth arc or at most a 135° bend.
- **Exceptions:** On slow lines such as USB FS the effect is negligible; it may still be noted in the report as "Low".
- **Example:** —
- **Source:** [TI SPRAAR7](https://www.ti.com/lit/an/spraar7j/spraar7j.pdf), [TI TS3USB221A-Q1 Layout Guidelines](https://www.ti.com/document-viewer/TS3USB221A-Q1/datasheet/layout-guidelines-scds300728), [Renesas RX71M USB2.0 Board Design](https://www.renesas.com/en/document/oth/rx71m-high-speed-usb-guidelines-high-speed-usb20-board-design)

### [HS-008] Stub, branch or test point on a differential pair

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** A short branch (T-junction) leaving the D+/D- trace sideways goes to a test pad, a header pin, a pull-up resistor or a second connector; there are round test point pads on the pair; on a through-hole (THT) USB connector the trace connects to the pin from the top layer (the pin remains as a stub below).
- **Why it matters:** Stubs and test pads are capacitive discontinuities; the wave reflected from the stub end is superimposed back onto the signal.
- **Recommended fix:** TI AM335x table: 0 stubs and 0 test points on the USB pair. Renesas: no branching on USB lines. On through-hole connectors (USB-A) make the high-speed connection from the bottom layer; on SMD connectors (Micro-B) from the top layer (TI SPRAAR7 3.5). If testing is needed, place the pad directly on the trace (no branch) or measure at the connector.
- **Exceptions:** The reversible D+/D- connection of USB-C produces an unavoidable stub (see HS-009). An ESD diode pad sitting on the trace is not counted as a stub (see ESD-002).
- **Example:** —
- **Source:** [TI SPRAAR7](https://www.ti.com/lit/an/spraar7j/spraar7j.pdf), [Renesas RX71M USB2.0 Board Design](https://www.renesas.com/en/document/oth/rx71m-high-speed-usb-guidelines-high-speed-usb20-board-design)

### [HS-009] A6/B6 and A7/B7 bridge on USB-C creates a long stub

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** The D+ (A6, B6) and D- (A7, B7) pads in the two pin rows of the USB-C connector are joined by a long ring/loop; the bridge point is far from the connector and the pair runs from there to the MCU; vias far from the connector are used for the crossover; or only one row is connected and the other is left open (USB does not work when the cable is plugged in reversed).
- **Why it matters:** While one row connects to the main path, the arm going to the other row becomes an open-ended stub; if long, it causes reflection at 480 Mbit/s.
- **Recommended fix:** Join the two rows right next to the connector; keep the stub formed by the bridge ≤3.5 mm (TI TUSB320). If needed, make the crossover with vias adjacent to the connector, or choose a connector with a suitable pin layout.
- **Exceptions:** Both rows must be connected except in special cases with only one plug orientation (fixed USB-C cable). For USB FS the 3.5 mm limit is loose.
- **Example:** Link: https://forum.kicad.info/t/routing-differential-pairs-on-usb-c-connector/47672 — Visible situation: difficulty connecting the outer-row pins and D+/D- mix-up (A7–B6 short). Link: https://forum.kicad.info/t/usb-c-routing-dealing-with-the-reversible-d-d-crossover-on-a-4-layer-board/66679 — Visible situation: discussion of a via crossover on a 4-layer board.
- **Source:** [TI TUSB320 Layout Guidelines](https://ti.com/document-viewer/TUSB320/datasheet/GUID-E36D6653-F4F2-4CAB-A505-E16E4AA2D6C7)

### [HS-010] USB-C CC1/CC2 tied to a single resistor, or Rd missing

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** The two traces leaving the CC1 (A5) and CC2 (B5) pins of the USB-C connector merge and go to a single resistor; or only one of the CC pins is connected and the other is floating. In the correct case two separate resistors for CC1 and CC2 (5.1 kΩ to GND in a sink device) are visible near the connector. Ask for the schematic/BOM to verify the value.
- **Why it matters:** Each CC pin must see its own Rd; a shared resistor causes the source not to supply 5 V with e-marked cables (the Raspberry Pi 4 bug).
- **Recommended fix:** In a sink device put a separate 5.1 kΩ pulldown on each of CC1 and CC2 (kernel.org article citing USB Type-C Spec 1.4 §4.5.1.3.2). CC lines are low-speed; they are not matched like a differential pair, but TI recommends keeping them short and of similar length.
- **Exceptions:** If a CC controller IC (e.g. TUSB320, PD controller) is used, Rd is inside the chip; the absence of a separate resistor is not an error.
- **Example:** Link: https://people.kernel.org/bleung/how-to-design-a-proper-usb-c-power-sink-hint-not-the-way-raspberry-pi-4 — Visible error: both CC pins tied to a single 5.1 kΩ resistor.
- **Source:** [How to design a proper USB-C power sink (kernel.org)](https://people.kernel.org/bleung/how-to-design-a-proper-usb-c-power-sink-hint-not-the-way-raspberry-pi-4), [TI TPS25821 Layout Guidelines](https://www.ti.com/document-viewer/TPS25821/datasheet/layout-guidelines-slvscr16354)

### [HS-011] Insufficient spacing between pairs and between a pair and other signals (3W/5W)

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** Two differential pairs, or a pair and another trace, run in parallel over a long distance with a gap less than 2–3 times the trace width; a clock (CLK, SCK) trace runs parallel right next to a USB pair. Use the trace width as a ruler for scale.
- **Why it matters:** Capacitive/inductive coupling (crosstalk) between parallel neighbouring traces increases rapidly as the distance decreases; periodic signals such as clocks superimpose noise onto the pair.
- **Recommended fix:** For single-ended traces centre-to-centre ≥3W (edge gap ≥2W) (TI, 3W rule). Between pairs ≥5W; for a 6 mil trace ≥30 mil ≈0.76 mm; pair–other signal ≥30 mil, pair–clock/periodic signal ≥50 mil ≈1.27 mm (TI SPRAAR7). Renesas: GND guard copper on the same layer ≥1 mm from the USB line.
- **Exceptions:** The rule can be relaxed over short distances at the package escape and connector entry. If a coplanar structure is designed intentionally (GND pour included in the impedance calculation), a closer pour is acceptable; otherwise GND on the same layer should be at least 3w, preferably 5w away (TI SNLA387, Ethernet). 3W is a valid approximation in structures where the trace width is close to the height (h) above the reference plane (thin dielectric, controlled impedance); the real criterion is h (LearnEMC: crosstalk is determined by s/h). On a 1.6 mm 2-layer board, since W ≪ h, 3W may be insufficient; use a spacing of 2–3 times h.
- **Example:** —
- **Source:** [TI SPRAAR7](https://www.ti.com/lit/an/spraar7j/spraar7j.pdf), [TI DSLVDS1001 – Separation Between Traces](https://www.ti.com/document-viewer/lit/html/SNLS622A/separation-between-traces-slls3739388), [Renesas RX71M USB2.0 Board Design](https://www.renesas.com/en/document/oth/rx71m-high-speed-usb-guidelines-high-speed-usb20-board-design)

### [HS-012] Pair runs beneath or near a crystal/SMPS/magnetic/mounting hole

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** A USB/Ethernet pair passes beneath, or within a few mm of, a crystal, oscillator, buck/boost inductor or switching IC; the pair skims the edge of a mounting hole; the pair runs along the board edge.
- **Why it matters:** These sources emit strong electric/magnetic fields and couple noise into the pair; a mounting hole and the board edge are where the reference plane ends.
- **Recommended fix:** Do not route the pair beneath/near crystals, oscillators, clock generators, switching regulators, mounting holes, magnetic components or ICs that use clocks (TI SPRAAR7, TI TS3USB221A). Renesas: keep it away from oscillators, power circuits and other I/O connectors. Do not place bypass capacitors next to the D+/D- traces (TI TS3USB221A).
- **Exceptions:** Crossings on a different layer with a continuous GND layer in between are less risky; still, for directly beneath the crystal see XTL-003.
- **Example:** —
- **Source:** [TI SPRAAR7](https://www.ti.com/lit/an/spraar7j/spraar7j.pdf), [TI TS3USB221A-Q1 Layout Guidelines](https://www.ti.com/document-viewer/TS3USB221A-Q1/datasheet/layout-guidelines-scds300728), [Renesas RX71M USB2.0 Board Design](https://www.renesas.com/en/document/oth/rx71m-high-speed-usb-guidelines-high-speed-usb20-board-design)

### [HS-013] Series termination resistor far from the driver

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** The series resistor on a clock/SPI/RGMII/USB line (usually 22–33 Ω, 0402/0603) sits in the middle of the line or at the receiver side; there is a long trace from the driver pin to the resistor pad. Which end is the driver must be known from the schematic/net direction → ask the user.
- **Why it matters:** Series termination makes the sum of the driver's output impedance and the resistor equal to the trace impedance; if the trace between them gets long, the two no longer act as a single resistor and reflection remains.
- **Recommended fix:** On unidirectional lines place the resistor adjacent to the driver pin. The delay of the trace between driver and resistor should be less than 1/3 of the edge time (±25% accuracy); less than 1/6 for ≥20 dB reflection suppression (Sigcon/Johnson). Value: Zout+Rs ≤ 90% of Z0 (≤45 Ω for 50 Ω) (Altium/Ritchey). Espressif places the series components on USB close to the chip side.
- **Exceptions:** On bidirectional lines the position should be determined by simulation (TI E2E, AM335x DDR2). On differential clock outputs the termination should be close to the receiver (SiTime AN10006).
- **Example:** —
- **Source:** [How Close is Close Enough? (Sigcon)](https://sigcon.com/Pubs/edn/close.htm), [Altium – The Right Termination at the Right Place](https://resources.altium.com/p/the-right-termination-of-the-right-size-at-the-right-place), [SiTime AN10006](https://www.sitime.com/support/resource-library/application-notes/an10006-best-design-and-layout-practices)

### [HS-014] Fast-edged SPI/clock line not treated as a transmission line

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** The SCK/CLK trace runs long (e.g. >10 cm) from one end of the board to the other, changes layers several times, branches to multiple devices (star/T), has no continuous GND beneath it and no series resistor. The auditor agent should ask the user for the edge time (tr) or the driver IC; the clock frequency alone is not enough.
- **Why it matters:** Reflection and ringing depend on edge rate; even a 1 MHz SPI driven with ns edges can cause double clocking on a long trace.
- **Recommended fix:** Run the clock point-to-point, over continuous GND, and short; on a long line add a series resistor at the driver (HS-013). The "critical length = x of the edge length" rule is inconsistent (values from 1/2 to 1/20 circulate); on impedance-controlled lines do a direct impedance calculation, and on uncontrolled fast lines use the rule only to decide whether a series resistor is needed (Altium).
- **Exceptions:** Short (a few cm) and slow-edged lines need no extra measures.
- **Example:** —
- **Source:** [Altium – Can We All Stop Quoting the Critical Length Rule?](https://resources.altium.com/p/can-we-all-stop-quoting-critical-length-rule), [How Close is Close Enough? (Sigcon)](https://sigcon.com/Pubs/edn/close.htm)

### [HS-015] Ethernet MDI pairs and magnetics (transformer) area laid out incorrectly

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** There is copper/trace/pour on any layer beneath a discrete Ethernet transformer (or common-mode choke); the MDI pairs between PHY and transformer are long (>5 cm) with many vias; GND pour on the same layer is poured very close to the pairs; there is no clear gap between the chassis (earth) copper on the RJ45 side and the circuit GND, or they are merged with copper.
- **Why it matters:** Metal beneath the transformer degrades isolation and common-mode rejection; impedance mismatch reduces performance and in severe cases breaks communication.
- **Recommended fix:** TI SNLA387: MDI 100 Ω ±10% differential, each trace <2 in (≈50.8 mm), length matching ≤20 mil at 1G, ≤50 mil at 100M/10M; vias/stubs minimum; same-layer GND ≥3w (preferably 5w); no metal on any layer beneath the transformer; earth ground separated from the circuit by a ≥20 mil (≈0.51 mm) gap, connected only through a capacitor + ≥1 MΩ resistor.
- **Exceptions:** Metal beneath an RJ45 with integrated magnetics (MagJack) is acceptable (TI SNLA387). Bob Smith termination and chassis layout are debated; the PHY manufacturer's reference design takes priority (Altium).
- **Example:** —
- **Source:** [TI SNLA387 Ethernet PHY PCB Design Layout Checklist](https://ti.com/lit/pdf/snla387), [Altium – Bob Smith Termination: Is it Correct?](https://resources.altium.com/p/bob-smith-termination-it-correct-ethernet)

### [HS-016] HDMI/MIPI pairs change layers or spacing between pairs is narrow

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** The 4–5 pairs (3 data + 1 clock TMDS; in MIPI clock + 1–4 lanes) leaving an HDMI connector or camera/display FPC connector spread to different layers through vias; the spacing between pairs is not much different from the intra-pair spacing; there is no meander between the legs of the pairs but there is a clear length difference.
- **Why it matters:** At the Gbit/s scale of these interfaces, via discontinuities and intra-pair skew turn directly into jitter; crosstalk between neighbouring lanes closes the eye diagram.
- **Recommended fix:** Route TMDS lines preferably on a single layer (top layer) without vias and match the intra-pair electrical length (TI TDP158, SLLA324). MIPI D-PHY (AMD Versal example): 100 Ω ±10%, intra-pair spacing 2.5×W, 5×W to other MIPI pairs, 6×W to non-MIPI pairs, intra-pair skew ±2 ps. The guide of the SoC in use takes priority over these values.
- **Exceptions:** Some SoC/board manufacturers specify 90 Ω for MIPI (Toradex/NVIDIA, community-sourced); ask the user for the target value.
- **Example:** —
- **Source:** [TI TDP158 Layout](https://ti.com/document-viewer/TDP158/datasheet/GUID-91754872-9E39-438E-8109-F03769DBD27A), [TI SLLA324 (TPD12S016 HDMI)](https://ti.com/lit/pdf/slla324), [AMD UG863 – MIPI D-PHY](https://docs.amd.com/r/en-US/ug863-versal-pcb-design/MIPI-D-PHY)

### [HS-017] Components on the pair (AC capacitor, ESD, CMC) asymmetric or in large packages

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** The two AC coupling capacitors or series resistors on the pair are offset relative to each other (one ahead, one behind) or oriented differently; pads much larger than the trace width, such as 0805; long trace between the common-mode choke (CMC) and ESD; no void in the reference plane beneath the pads.
- **Why it matters:** A large SMD pad is a capacitive discontinuity; asymmetric placement produces intra-pair skew and mode conversion.
- **Recommended fix:** SMDs on the pair should be at most 0603, preferably 0402 or smaller, and placed symmetrically on both legs; void the reference plane beneath the pad 100%, with the void at least two layers deep; 60% void beneath ESD/EMI component signal pads; AC capacitor on the protected side of the CMC and close to the CMC; AC capacitor + CMC + ESD chain short and close to the connector (TI SPRAAR7 3.10, 3.14).
- **Exceptions:** USB 2.0 HS has no AC coupling; on low-speed interfaces pad voiding is not needed. The decision to void beneath pads depends on the stackup → ask the user (see STK).
- **Example:** —
- **Source:** [TI SPRAAR7](https://www.ti.com/lit/an/spraar7j/spraar7j.pdf)
