# Sources

All sources cited in the handbook, grouped by topic. In the notes, "(opened)" means the page was read; "(search result only)" means only the search summary was seen. Access date: 2026-10 (unless stated otherwise). If the same URL appears in more than one group, it is listed only where it first appears.
Total 281 unique sources.


## STK, GND, VIA

Access date: 2026-10-13. "(opened)" = page/PDF content was read; "(search result only)" = the URL came back in a search result, but the content could not be read directly because of a timeout/404.
- [TI SLYT512 — Grounding in mixed-signal systems demystified, Part 2](https://www.ti.com/lit/pdf/SLYT512) — Pithadia & More, TI Analog Applications Journal 2Q 2013; split plane, bridge, partitioning, connector 30–40% GND (opened, application note)
- [TI SNLA426 — High-Speed PCB Layout for PCIe Gen 5](https://www.ti.com/lit/an/snla426/snla426.pdf) — TI, 2023; via staggering, stub, back-drill, symmetry of via count (opened, application note)
- [TI SNLA426 Section 19 (HTML)](https://www.ti.com/document-viewer/lit/html/SNLA426/GUID-1AE18886-EA7A-45F0-9BA7-15EAE462B587) — ≤50 mil stitching via at a reference plane change (opened)
- [TI SPRAAR7J — reference plane section](https://www.ti.com/document-viewer/lit/html/SPRAAR7J/GUID-AD6D2D54-84AC-47F5-A2ED-87883A148A25) — TI application note; crossing a split, ≤1 µF stitching capacitor, ≤200 mil stitching via (opened)
- [Barry Olney — Split Planes in Multilayer PCBs](https://www.icd.com.au/articles/Split_Planes_PCBD-Mar2015.pdf) — PCB Design Magazine, March 2015; partitioning instead of splitting, route fence, 10 mm rule (opened, expert article)
- [ADI Analog Dialogue RAQ 63](https://www.analog.com/en/resources/analog-dialogue/raqs/raq-issue-63.html) — split AGND/DGND "usually no" (search result only; page timed out)
- [ADI Analog Dialogue RAQ 9 — Grounding Converters](https://www.analog.com/en/analog-dialogue/raqs/raq-issue-9.html) — AGND/DGND pins are joined next to the package, no ferrite/resistor (search result only)
- [ADI MT-031 — Grounding Data Converters and Solving the Mystery of AGND and DGND](https://wcm-cce.cldnet.analog.com/media/en/training-seminars/tutorials/mt-031.pdf) — Kester/Bryant/Byrne tutorial (search result only; connection refused)
- [Autodesk — Everyday App Note: Mixed-Signal PCB With Partitioning](https://www.autodesk.com/products/fusion-360/blog/everyday-app-note-successfully-design-mixed-signal-pcb-partitioning/) — summary of Henry Ott's partitioning method (search result only, secondary source)
- [Altium — PCB Stackup Basics](https://resources.altium.com/p/pcb-stackup-basics) — GND next to every signal layer; 4/6/8-layer arrangements (opened, expert blog)
- [Altium — SIG/GND/SIG + PWR/GND Stackups](https://resources.altium.com/p/siggndsig-pwrgnd-stackups-will-work-4-layer-pcbs) — Z. Peterson; 4-layer options and choosing by current/number of rails (opened)
- [Altium — Understanding Ground Planes in Your Two-Layer PCB](https://resources.altium.com/pcb-design-blog/understanding-ground-planes-in-your-two-layer-pcb) — bottom GND on 2 layers, coplanar GND, via from the GND pin (opened)
- [Altium — Copper Pour and Stitching: Do You Need Them?](https://resources.altium.com/p/copper-pour-and-stitching-do-you-need-them-pcb-layout) — Z. Peterson; floating copper, via spacing and resonance, thin pour (opened)
- [Altium — When to Use Tented vs. Untented Vias](https://resources.altium.com/p/when-use-tented-vias-your-pcb-layout) — tenting ≤~12 mil, view on leaving vias open under BGA (opened)
- [Altium — Aspect Ratios and Their Importance in Multilayer PCBs](https://resources.altium.com/p/aspect-ratios-and-their-importance-multi-layered-pcbs) — 10:1 rule, 6:1 in practice, microvia 1:1 (opened)
- [Altium — The PCB Layout Rules of Thumb Debate Rages On](https://resources.altium.com/p/great-pcb-layout-rules-thumb-debate-rages) — limited benefit of the 20H rule (search result only)
- [LearnEMC — EMC Design Myths](https://learnemc.com/emc-design-myths) — Hubing; the 20H rule myth (opened, academic/expert)
- [Missouri S&T — 20-H Rule Modeling and Measurements](https://scholarsmine.mst.edu/ele_comeng_facwork/5806) — Shim & Hubing measurements (search result only, academic)
- [In Compliance Magazine — PCB Layer Stack-Up Considerations for EMC](https://incompliancemag.com/most-important-pcb-layer-stack-up-considerations-that-achieve-optimal-emc-performance/) — PWR–GND 2–3 mil recommendation attributed to Ott (search result only; page content came back empty)
- [JLCPCB — Circuit Board Ground Plane and Power Plane Guide](https://jlcpcb.com/blog/circuit-board-ground-plane-and-power-plane-guide-2026) — solid plane, not crossing slots, stitching locations, 2/4/6 layers (opened, manufacturer)
- [JLCPCB — Five Via Finishes](https://jlcpcb.com/blog/five-via-finishes) — open/tented/plugged/epoxy-filled/copper-filled via (opened, manufacturer)
- [JLCPCB — PCB Via Covering](https://jlcpcb.com/help/article/pcb-via-covering) — covering ≤0.4/0.5 mm, 0.2 mm HASL clearance, 0.35 mm rule (opened, manufacturer)
- [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities) — min via 0.15/0.25 mm, preferred 0.2 mm, barrel copper avg. 18 µm, POFV 0.15–0.55 mm, 7628 Dk 4.4 (opened, manufacturer)
- [JLCPCB — BGA Design Guidelines](https://jlcpcb.com/help/article/bga-design-guidelines---pcb-layout-recommendations-for-bga-packages) — via-in-pad at 0.5 mm pitch, BGA clearances (opened, manufacturer)
- [JLCPCB — Free Via in Pad on 6-20 Layer PCBs with POFV](https://jlcpcb.com/blog/Free-Via-in-Pad-on-6-20-Layer-PCBs-with-POFV) — 2022 announcement, extra charge on 4 layers (search result only)
- [JLCPCB Help Center — PCB Stackup](https://jlcpcb.com/quote/pcbOrderFaq/PCB%20Stackup) — 4-layer 7628: 0.2 mm prepreg, 1.065 mm core (search result only; 404 when opened directly)
- [PCBWay PCB Capabilities](https://www.pcbway.com/capabilities.html) — min hole 0.15 mm (<0.2 mm extra charge), aspect ratio ≤8 normal, barrel copper 18–25 µm (opened, manufacturer)
- [Sierra Circuits — Via Tenting Design Rules and Fabrication Notes](https://www.protoexpress.com/kb/pcb-via-tenting-design-rules-and-fabrication-notes) — ≤12 mil two-sided tenting, IPC-4761 types (opened, manufacturer)
- [Sierra Circuits — How to Design a Via with Current Carrying Capacity](https://www.protoexpress.com/blog/how-to-design-via-with-current-carrying-capacity/) — IPC-2152/2221 formula, K=0.048/0.024 (opened, manufacturer)
- [Sierra Circuits forum — Ground Plane Strategy for a 2-Layer PCB](https://sierraconnect.protoexpress.com/t/ground-plane-strategy-for-a-2-layer-pcb-from-an-emi-emc-perspective/3630) — bottom GND on 2 layers (search result only, community)
- [Signal Integrity Journal — Vias Are Cooler Than We Think](https://signalintegrityjournal.com/articles/1459-vias-are-cooler-than-we-think) — vias run cooler than the connected trace (search result only; data quoted in the Sierra article)
- [Eurocircuits — Solder Escape/Wick](https://www.eurocircuits.com/pcb-assembly-guidelines-solder-escape-wick/) — pad–via ≥0.25 mm, resin fill (opened, manufacturer)
- [Electronic Design — Via-In-Pad Guidelines for PCBs](https://www.electronicdesign.com/analog/pad-guidelines-pcbs) — D. Benson (Screaming Circuits); wicking, voids, recommendations (opened, assembly expert)
- [Atlas PCB — Ground Plane Stitching Via](https://atlaspcb.com/blog/pcb-ground-plane-stitching-via) — λ/20 calculation in the dielectric (search result only, manufacturer blog)
- [RF Essentials — Via stitching and shielding effectiveness](https://rfessentials.com/rf-knowledge-base/what-is-the-effect-of-via-stitching-on-the-shielding-effectiveness-of-a-ground-p/) — λ/20 free-space calculation (search result only)
- [KiCad 8 PCB Editor documentation](https://docs.kicad.org/8.0/en/pcbnew/pcbnew.html) — layer names, zone fill (B / Ctrl+B), Remove islands, "Isolated copper fill" DRC, via types (opened, official documentation)
- [KiCad Forum — Design PCB with USB port](https://forum.kicad.info/t/design-pcb-with-usb-port/20754) — open via under a metal housing (search result only, community)

## PWR, SMPS, THM

All links were opened and read on 2026-10-13 (PDFs were downloaded and examined page by page).
### Standard / formula / manufacturer DFM
- [How To Calculate Maximum Track Current (mbedded.ninja)](https://blog.mbedded.ninja/pcb-design/how-to-calculate-maximum-track-current/) — IPC-2221A formula (k = 0.048/0.024, b = 0.44, c = 0.725), validity ranges, note that IPC-2152 is more accurate.
- [Cadence — IPC-2152 vs. IPC-2221](https://resources.system-analysis.cadence.com/blog/ipc-2152-vs-ipc-2221-which-to-use-for-pcb-thermal-analysis) — scope of the two standards, conservatism of IPC-2221.
- [Sierra Circuits — Trace Width, Current Capacity and Temperature Rise Calculator](https://www.protoexpress.com/pcb/trace-width-calculator/) — IPC-2152-based calculator; plane proximity inputs.
- [JLCPCB — Thermal Relief Pad Design](https://jlcpcb.com/blog/thermal-relief-pad-design) — relief/solid choice, solid for >3 A, spoke dimensions, thermal via 0.25–0.33 mm / 1.0–1.2 mm.
- [PCD&F — Current Control](https://pcdandf.com/pcdesign/index.php/2012-archive-articles/7789-current-control) — neck-downs, via bottleneck, change of conductivity with temperature.
### Semiconductor application notes / datasheets
- [TI/National AN-1149 (SNVA021) — Layout Guidelines for Switching Power Supplies (mirror)](https://www.thierry-lequeu.fr/data/AN-1149.pdf) — 15 mil/A, 200 mA/via, FB trace, closed-core inductor, bad/good boost placement figures.
- [TI SLYT614 — Five steps to a great PCB layout for a step-down converter](https://edgeworker.ti.com/lit/pdf/slyt614) — input capacitor priority, SW area, snubber, VOS/FB, single-point ground, 1 via/A.
- [ROHM 60AN066E — PCB Layout Techniques of Buck Converter](https://fscdn.rohm.com/en/products/databook/applinote/ic/power/switching_regulator/converter_pcb_layout_appli-e.pdf) — good/bad placement figures, thermal via 0.3 mm/1.2 mm, GND under the inductor, trace/via resistance and inductance.
- [TI LM61440 — Layout Guidelines](https://ti.com/document-viewer/LM61440/datasheet/GUID-B3BC1FF3-222C-4456-916C-6A98740CD6F4) — symmetric input capacitors, SW area, FB, 2 oz recommendation, inner-layer GND.
- [TI SLVA255 — Minimizing Ringing at the Switch Node of a Boost Converter](https://www.ti.com/lit/pdf/slva255) — boost critical loop, 0.01–2.2 µF output bypass, snubber sizing.
- [TI LM2104 — Layout Guidelines (half-bridge gate driver)](https://ti.com/document-viewer/LM2104/datasheet/GUID-279F829C-5876-42DE-8AC0-6603E6D505E9) — gate loop, bootstrap loop, HS source–LS drain inductance.
- [Allegro — AHV85311NK PCB Layout Guide](https://www.allegromicro.com/-/media/files/guide/ahv85311nk-pcb-layout-guide.pdf?sc_lang=en) — gate-drive loop (~10 ns pulses), Kelvin source, decoupling via location (prefer/avoid diagram), bootstrap placement.
- [ADI/Würth — PCB Board Layout Optimization (seminar)](https://www.we-online.com/files/pdf1/pcb-board-layout-optimization-v2.pdf) — 2.5 cm trace ≈ 20 nH, 5 A/5 ns example.
- [TI TPS7A85A — Layout Guidelines](https://www.ti.com/document-viewer/TPS7A85A/datasheet/layout) — LDO capacitors, warning about vias/long traces, GND plane as a thermal requirement.
- [TI THS4281 — Power-Supply Decoupling](https://ti.com/document-viewer/THS4281/datasheet/power_supply_recommendations) — smallest capacitor closest; 0.1 µF ≤0.1 inch, bulk ≤1 inch.
- [Altium — When Does Decoupling Capacitor Location Matter](https://resources.altium.com/p/when-does-decoupling-capacitor-location-matter-pcb) — components of path inductance, 5–7 nH/inch, effect of location with tightly coupled plane pairs.
- [TI LMP8640 — Layout Guidelines](https://www.ti.com/document-viewer/LMP8640/datasheet/layout) — Kelvin, matched sense traces, thermocouple, thermal symmetry.
- [TI SLVA139 — Reverse Current/Battery Protection Circuits](https://ti.com/lit/pdf/SLVA139) — series diode, PMOS in the power path, NMOS in the return path, body diode direction.
- [TI SLMA002H — PowerPAD Thermally Enhanced Package](https://ti.com/cn/lit/slma002) — thermal land, via ≤0.33 mm, 5–9 vias, solid connection, tenting side, ≥50% solder area.
- [TI SLUA271C — QFN and SON PCB Attachment](https://www.ti.com/lit/pdf/slua271) — 0.3 mm/1.0 mm via, plugging/tenting, 50–70% paste coverage, ≤50% voiding.
- [Diodes AN1157 — Understanding Thermal Resistance in the Real World](https://www.diodes.com/assets/Uploads/Understanding-Thermal-Resistance-in-the-Real-World-Application-Note.pdf) — variation of θJA with pad area (1 oz, single layer).
- [Würth Elektronik SN008 — Expected Lifetime of Aluminum Electrolytic and Polymer Capacitors](https://www.we-online.com/components/media/o173043v410%20SN008a%20EN.pdf) — 10 °C rule and lifetime table.
### Expert / community
- [Signal Integrity Journal — DC-DC Converters: Solid Return Plane or Cutouts Under Switch Node and Inductor](https://www.signalintegrityjournal.com/blogs/17-practical-emc/post/2694-dc-dc-converters-solid-return-plane-or-cutouts-under-switch-node-and-inductor?v=preview) — single-board measurement: the continuous plane is better in most measurements.
- [EEVblog Forum — Optimum arrangement for circuit protection components](https://eevblog.com/forum/beginners/optimum-arrangement-for-circuit-protection-components) — discussion of the diode → fuse → TVS order (community).
- [FEDEVEL Forum — Buck converter layout review](https://courses.fedevel.com/forum/schematic-design-pcb-layout/16381-buck-converter-layout-review) — criticism of power-loop passives on the opposite side (bad example, community).

## HS, XTL, ESD

Access date: 2026-10. "(opened)" = document text was read; "(search result only)" = only the search result/summary was used.
### High-speed signals (HS)
- [TI SPRAAR7J High-Speed Interface Layout Guidelines](https://www.ti.com/lit/an/spraar7j/spraar7j.pdf) — (opened, PDF text) 5W, 30/50 mil keep-out, 90 mil plane edge, 1.5W void, ≤200 mil stitching via, ≤1 µF stitching capacitor, >135° bend, ≤15 mil via stub, 0402/0603, ESD/EMI rules, AM335x USB table.
- [Renesas RX71M Guidelines for High-Speed USB2.0 Board Design (R01AN4851)](https://www.renesas.com/en/document/oth/rx71m-high-speed-usb-guidelines-high-speed-usb20-board-design) — (opened, PDF text) 90 Ω ±15%, 300/100 mm, D+/D- difference ≤2.5 mm, GND ≥2 mm wide, 1 mm guard copper, no vias/branches.
- [TI TS3USB221A-Q1 Layout Guidelines](https://www.ti.com/document-viewer/TS3USB221A-Q1/datasheet/layout-guidelines-scds300728) — (opened) ≤4 in, 45° bends, not passing under crystals/SMPS, keeping bypass capacitors away from D+/D-.
- [TI TUSB320 Layout Guidelines](https://ti.com/document-viewer/TUSB320/datasheet/GUID-E36D6653-F4F2-4CAB-A505-E16E4AA2D6C7) — (opened) USB-C A6/B6, A7/B7 bridge stub ≤3.5 mm.
- [TI TPS25821 Layout Guidelines](https://www.ti.com/document-viewer/TPS25821/datasheet/layout-guidelines-slvscr16354) — (search result only) keep CC lines at similar lengths.
- [How to design a proper USB-C power sink (kernel.org, B. Leung)](https://people.kernel.org/bleung/how-to-design-a-proper-usb-c-power-sink-hint-not-the-way-raspberry-pi-4) — (opened) Separate 5.1 kΩ Rd for each CC; the Raspberry Pi 4 mistake.
- [TI DSLVDS1001 – Separation Between Traces](https://www.ti.com/document-viewer/lit/html/SNLS622A/separation-between-traces-slls3739388) — (opened) definition of the 3W rule.
- [TI SNLA387 Ethernet PHY PCB Design Layout Checklist](https://ti.com/lit/pdf/snla387) — (opened, PDF text) MDI 100 Ω ±10%, <2 in, 20/50 mil matching, 3w/5w GND, no metal under the transformer, 20 mil earth clearance, 1 MΩ+C, do not put ESD on the PHY side.
- [Altium – Bob Smith Termination: Is it Correct?](https://resources.altium.com/p/bob-smith-termination-it-correct-ethernet) — (search result only) Bob Smith termination is controversial.
- [User Guide to the JLCPCB Impedance Calculator](https://jlcpcb.com/help/article/User-Guide-to-the-JLCPCB-Impedance-Calculator) — (opened) 20–90 Ω SE, 50–150 Ω diff, NP-155F, "for reference only".
- [Altium – Differential Pair Length Matching Best Practices](https://resources.altium.com/p/differential-pair-length-matching-best-practices-signal-integrity) — (opened) Make the tuning short and close to the skew source, mode conversion.
- [Altium – Trombone, Accordion and Sawtooth Tuning](https://resources.altium.com/p/length-matching-for-high-speed-signals-trombone-accordion-and-sawtooth-tuning) — (search result only) Types of length-tuning structures.
- [Altium – Can We All Stop Quoting the Critical Length Rule?](https://resources.altium.com/p/can-we-all-stop-quoting-critical-length-rule) — (opened) Inconsistency of the critical length rule; use on uncontrolled lines such as SPI.
- [Altium – The Right Termination, Of The Right Size, At The Right Place](https://resources.altium.com/p/the-right-termination-of-the-right-size-at-the-right-place) — (opened) Series resistor at the driver; Zout+Rs ≤ 0.9·Z0.
- [How Close is Close Enough? (Sigcon / H. Johnson, EDN)](https://sigcon.com/Pubs/edn/close.htm) — (opened) Stub delay < tr/3 (±25%), < tr/6 (≥20 dB).
- [TI TDP158 Layout](https://ti.com/document-viewer/TDP158/datasheet/GUID-91754872-9E39-438E-8109-F03769DBD27A) — (search result only) TMDS on a single layer, without vias, electrical length matching.
- [TI SLLA324 (TPD12S016 HDMI)](https://ti.com/lit/pdf/slla324) — (search result only) Matching of the HDMI ESD array, 45° routing.
- [AMD UG863 – MIPI D-PHY](https://docs.amd.com/r/en-US/ug863-versal-pcb-design/MIPI-D-PHY) — (opened) 100 Ω ±10%, 2.5W/5W/6W spacing, ±2 ps intra-pair skew.
- [Espressif ESP32-S3 PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html) — (opened) USB 90 Ω ±10%, pair of GND return vias at transitions, series components close to the chip; crystal rules.
- [KiCad forum – Differential pair routing in KiCad 6.0](https://forum.kicad.info/t/differential-pair-routing-in-kicad-6-0/36935) — (opened) Example: ESD diodes and D+/D- crossover.
- [KiCad forum – Routing differential pairs on USB-C connector](https://forum.kicad.info/t/routing-differential-pairs-on-usb-c-connector/47672) — (opened) Example: USB-C outer-row connection, A7–B6 short.
- [KiCad forum – USB-C Routing: reversible D+/D- crossover on a 4-layer board](https://forum.kicad.info/t/usb-c-routing-dealing-with-the-reversible-d-d-crossover-on-a-4-layer-board/66679) — (opened) Example: crossover with vias; community views on TVS location.
### Crystal / oscillator (XTL)
- [ST AN2867 Oscillator design guide for STM32](https://www.st.com/resource/en/application_note/an2867-oscillator-design-guide-for-stm32-microcontrollers-stmicroelectronics.pdf) — (official URL from search result only; ST server timed out) Official source; content was read from the Rev 10 copy below.
- [AN2867 Rev 10 copy (Raltron)](https://www.raltron.com/webproducts/technical/technical_notes/Oscillator-design-guide-for-STM8S-STM8A-and-STM32-microcontrollers-ST-MICRO-1.pdf) — (opened, PDF text) §5.1 PCB rules, guard ring, separate oscillator GND, symmetry, test point, conformal coating; CL calculation example.
- [Microchip – External Oscillator Layout Guidance](https://onlinedocs.microchip.com/oxy/GUID-E48B4A26-F201-4F0A-BCBA-16461582816A-en-US-3/GUID-AA04B64F-3C38-4E1C-8B51-49DE3CFE2419.html) — (search result only; page returned 503) Same side, within 0.5 in, GND pour, no trace on the opposite side.
- [SiTime AN10006 Best Design and Layout Practices](https://www.sitime.com/support/resource-library/application-notes/an10006-best-design-and-layout-practices) — (opened) 100 nF close to VDD, 0.1 µF+10 µF (2 in), series resistor close to the output, no high-speed trace passing underneath.
- [TI SLLA329 USB hub design guide](https://ti.com/lit/pdf/slla329) — (search result only) Crystal close to the chip and on the top layer (without vias).
- [EEVblog – ATmega328PB unstable… (crystal discussion)](https://eevblog.com/forum/projects/atmega328pb-unstable-outputting-amplified-audio-over-pwm-into-a-speaker/msg5573087) — (search result only) Example: via in the crystal line, disagreement about GND under the crystal.
### ESD protection (ESD)
- [TI SLVA680A ESD Protection Layout Guide](https://ti.com/lit/pdf/slva680) — (opened, PDF text) Proximity to the connector, no stub, via order (Case 1/2/3), 45°/arc corners, via adjacent to the GND pin, chassis screw.
- [ROHM – PCB Layout for TVS Diodes (66AN067E)](https://fscdn.rohm.com/en/products/databook/applinote/discrete/diodes/pcb_layout_for_tvs_diodes_an-e.pdf) — (opened, PDF text) Field failure example, 52 nH → 3.4 kV / 1 nH → 107 V, anode GND connection, via inductance.
- [LearnEMC – EMC Question of the Week, 24 July 2023](https://learnemc.com/qotw-230724) — (opened) TVS at the connector, series resistor at the IC.
- [TI TUSB2077A Layout](https://www.ti.com/document-viewer/ja-jp/TUSB2077A/datasheet/layout) — (search result only) Single GND plane; chassis ground only near the USB connectors.
- [EEVblog – USB Shield Ground Connection](https://www.eevblog.com/forum/projects/usb-shield-ground-connection/msg597292/) — (search result only) Discussion of the shell–GND connection (1 MΩ‖4.7 nF vs direct).

## PLC, RF

Access date: 2026-10-13 (all).
### RF (06-rf-antenna.md)
- [ESP32-S3 Hardware Design Guidelines (PDF, master)](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/esp-hardware-design-guidelines-en-master-esp32s3.pdf) — Fig. 24–26: module positions (✓ 1 and 5) and keepout dimensions (Min 15 / 6 / Max 2 / Max 1 mm).
- [ESP32 Hardware Design Guidelines — PCB Layout Design (HTML)](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32/pcb-layout-design.html) — RF trace > 20 mil on 2 layers, clear under the IPEX, π network, crystal–clock pin ≥ 2.7 mm.
- [ESP32-S3-WROOM-1/1U Datasheet v1.8](https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf) — module 18 × 25.5 mm, antenna area ~6 mm; no keepout on the 1U variant.
- [u-blox NINA-B3 System Integration Manual (UBX-17056748 R15)](https://content.u-blox.com/sites/default/files/NINA-B3_SIM_UBX-17056748.pdf) — corner/mid-edge placement, metal ≥ 10 mm, enclosure 5/10 mm, ground ≥ 10 mm on both sides, under the U.FL/SMA, trace–GND ≥ 2W, ≥ 200 µm trace.
- [Nordic — General PCB design guidelines for nRF52 series](https://devzone.nordicsemi.com/guides/hardware-design-test-and-measuring/b/nrf5x/posts/general-pcb-design-guidelines-for-nrf52-series) — no trace under the RF path, inner-layer keepout, via at least every 5 mm, monopole ≥ 5 mm clearance, copying the reference. (Page carries a "no longer maintained" warning.)
- [Nordic DevZone — nRF52832 PCB Layout Review](https://devzone.nordicsemi.com/f/nordic-q-a/83955/nrf52832-pcb-layout-review/349182) — example: missing antenna, inner-layer keepout, GND connection of the first capacitor.
- [Nordic DevZone — nRF52 antenna design review](https://devzone.nordicsemi.com/f/nordic-q-a/16740/nrf52-antenna-design-review/64003) — example: ~5 mm ground clearance, 2 × 45° instead of 90°.
- [Johanson — Chip Antenna Layout Considerations for 802.11 Applications](https://johansontechnology.com/docs/2/jti-antenna-mounting.pdf) — chip antenna ground distances (> 2 / > 1 / > 4 mm), edge vias, perpendicular feed.
- [TI AN058 Antenna Selection Guide (SWRA161B)](https://www.ti.com/lit/an/swra161b/swra161b.pdf) — no ground/trace under the antenna; a plastic enclosure and a hand lower the resonance.
- [TI AN043 Small Size 2.4 GHz PCB Antenna (SWRA117D)](https://www.ti.com/lit/an/swra117d/swra117d.pdf) — copying the reference antenna exactly from Gerber/DXF, same board thickness.
- [Silicon Labs — Z-Wave 800 Integration Guide, PCB Implementation](https://docs.silabs.com/z-wave/8.0.1/z-wave-800-series-integration-guide/08-pcb-implementation) — traces longer than λ/16 must be 50 Ω, matching close by on the same layer, corner placement and distance from the SMPS.
- [LibreCAL PR #8 (GitHub)](https://github.com/jankae/LibreCAL/pull/8) — CPWG 50 Ω ≈ 0.34/0.20 mm and 0.30/0.18 mm examples for JLC04161H-7628.
- [Wikipedia — Via fence](https://en.wikipedia.org/wiki/Via_fence) — via fence spacing < λ/20 rule (sourced from Archambeault, Harper et al.).
- [RF Essentials — Shielded compartment design](https://rfessentials.com/rf-knowledge-base/how-do-i-design-a-shielded-compartment-on-a-pcb-to-isolate-sensitive-rf-stages/) — shield GND ring, via < λ/20 (< 6 mm at 2.4 GHz), feedthrough.
- [KiCad Forum — PCB Review Request (ESP32 LED sign)](https://forum.kicad.info/t/pcb-review-request/40027) — example: criticism of ESP32 placement/ground; warning about a ceramic part next to a mounting hole (also in PLC-013).
### PLC (02-placement.md)
- [Sierra Circuits — Component Placement Guidelines for PCB Design and Assembly](https://www.protoexpress.com/blog/component-placement-guidelines-pcb-design-assembly/) — placement order, grouping, orientation consistency, single-side SMD, hot parts and airflow, surge suppressor next to the connector.
- [LearnEMC — Good EMC Design Guidelines](https://learnemc.com/other-good-emc-design-guidelines) — connectors on one edge/corner, I/O devices within ~2 cm, non-I/O parts ≥ ~2 cm away.
- [TI SZZA009 — PCB Design Guidelines for Reduced EMI](https://www.ti.com/lit/an/szza009/szza009.pdf) — board zoning, regulator next to the power input, oscillator away from analog/connectors, cable should not fold over the MCU.
- [TI SLVA959B — Best Practices for Board Layout of Motor Drivers](https://www.ti.com/lit/an/slva959b/slva959b.pdf) — digital/analog/high-power partitioning, shrinking the high-current loop through placement.
- [TI SLYT512 — Grounding in mixed-signal systems demystified, Part 2](https://www.ti.com/lit/an/slyt512/slyt512.pdf) — partitioned plane, power enters from the digital section, analog is fed through filtering.
- [TI SLYT682 — Reduce buck-converter EMI and voltage stress by minimizing inductive parasitics](https://www.ti.com/lit/an/slyt682/slyt682.pdf) — hot loop concept (details in the SMPS section).
- [TI SNVA419C — AN-2020 Thermal Design by Insight, Not Hindsight](https://www.ti.com/lit/an/snva419c/snva419c.pdf) — ~15.3 cm² two-sided copper for 1 W / 40 °C, copper extending to the board edge.
- [TI ADS1299 Datasheet — Layout Guidelines](https://ti.com/document-viewer/ADS1299/datasheet/layout) — analog/digital separation, analog inputs on one side, digital on the opposite side.
- [KYOCERA AVX — Cracks: The Hidden Defect](https://www.kyocera-avx.com/docs/techinfo/CeramicCapacitors/cracks.pdf) — 200 mil edge margin passes / 20 mil fails, corners are the riskiest, flexing from screwing, orientation parallel to the stress.
- [JLCPCB — PCB Assembly Capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities) — Economic PCBA single-sided only, Standard double-sided.
- PowerLab `PCB_DESIGN_RULES.md` (local: `D:/Belgeler/METUPowerLab/Powerlab-rules/KiCAD/PCB_DESIGN_RULES.md`) — §3.1 M3 keepout Ø 6–7 mm, §3.2 zone separation/decoupling priority/polarity orientation/single side, §3.3 IPC-2221B clearance table. (Not a URL; used as an additional source.)

## DFM, DFA

Access date: 2026-10-13 (all).
### Manufacturer capability and DFM pages
- [PCBWay PCB Manufacturing Tolerances](https://www.pcbway.com/pcb_prototype/PCB_Manufacturing_tolerances.html) — extra charge for holes below 0.3 mm, 6/6 mil recommendation, outline–copper 0.3/0.25 mm, V-cut–copper 0.35 mm, NPTH–copper (opened).
- [PowerLab PCB_DESIGN_RULES](https://github.com/odtu/Powerlab/blob/master/KiCAD/PCB_DESIGN_RULES.md) — the lab's PCBWay standard-price specification and default DRC values (opened + local skill copy read).
- [Eurocircuits PCB Classification](https://www.eurocircuits.com/pcb-design-guidelines/classification/) — pattern/drill class logic, NPTH ring 0.30 mm (class table is an image, could not be read) (opened).
- [Castellated PCBs: Introduction and Design Requirements (JLCPCB)](https://jlcpcb.com/blog/142-castellated-pcbs-introduction-and-design-requirements) — half-hole 0.6 mm diameter/spacing, 1 mm corner (search result only).
- [Copper Balancing in PCBs (JLCPCB)](https://jlcpcb.com/blog/pcb-copper-balancing) — density targets, thieving pattern (opened).
- [Understanding the Importance of Annular Rings in PCB Design (JLCPCB)](https://jlcpcb.com/blog/annular-rings) — breakout acceptance by IPC class (search result only).
- [Fiducial Marks (JLCPCB)](https://jlcpcb.com/blog/fiducial-marks) — fiducial size, clearance, edge 3.35 mm, local fiducial at ≤0.5 mm pitch (opened).
- [Terms and Conditions of JLCPCB Assembly Service](https://jlcpcb.com/help/article/61-Terms-and-Conditions-of-JLCPCB-Assembly-Service) — part–edge ≥2.5 mm (from the search result summary; page was not opened).
- [PCBWay Design Instruction: Panelization, Breakaway Rails, Fiducial Marks, Tooling Holes](https://www.pcbway.com/helpcenter/design_instruction/PCB_Panelization__Breakaway_Rails__Fiducial_Marks__Tooling_Holes.html) — fiducial ≥5 mm from edge, 2R/3R clear area, rail ≥3 mm (opened).
- [PCBWay PCB Assembly FAQ](https://www.pcbway.com/assembly-faq.html) — rails required if edge–copper <3.5 mm, IPC-A-610 Class 2 (opened).
### Standard/application notes
- [TI SLUA271 QFN/SON PCB Attachment (PDF)](https://edgeworker.ti.com/lit/pdf/slua271) — land pattern, NSMD, mask, 50–70% paste, stencil, via plugging (opened, PDF text extracted).
- [TI SLUA271C — Solder Stencils (HTML)](https://www.ti.com/document-viewer/lit/html/SLUA271C/GUID-97E90003-17DF-4B4B-9F07-32B6C507B069) — stencil 0.125 mm (opened).
- [TI LMG3622 datasheet — Solder-Joint Stress Relief](https://www.ti.com/document-viewer/LMG3622/datasheet/GUID-F43232EE-8176-4A62-AFFA-1DE030FFB851) — trace into an NSMD pad ≤2/3 of pad width (opened).
- [IPC-7351B Compliance (Altium)](https://techdocs.altium.com/display/ADOH1/IPC-7351B+Compliance) — IPC-7351 density levels (search result only).
- [Features of IPC-7351 standards (Sierra Circuits)](https://www.protoexpress.com/blog/features-of-ipc-7351-standards-to-design-pcb-component-footprint/) — A/B/C levels, zero orientation, polarity marking (opened).
### Expert / tool content
- [Preventing Top DFM Errors in Your PCB Design (Altium/Sierra)](https://resources.altium.com/p/preventing-top-dfm-errors-your-pcb-design) — sliver, acid trap, annular ring 4 mil, drill-to-copper 8 mil, edge 10/15 mil (opened).
- [DFA Guidelines for an Efficient PCB Design (Altium/Sierra)](https://resources.altium.com/p/dfa-guidelines-efficient-pcb-design) — edge 125 mil, orientation consistency, location of polarity marking (opened).
- [4 less obvious PCB DFM violations (Siemens)](https://blogs.sw.siemens.com/electronic-systems-design/2020/03/16/4-less-obvious-pcb-dfm-violations/) — acid trap = closed pocket, plane bottleneck in a row of holes (opened).
- [DFA rules (Sierra Circuits)](https://www.protoexpress.com/kb/dfa-rules/) — part-to-part spacing table, courtyard values (opened).
- [PCB design for assembly checklist (Sierra Circuits)](https://www.protoexpress.com/blog/pcb-design-for-assembly-checklist-important-checks-for-layout-engineers/) — edge distances, fiducial, height formula (opened).
- [Balanced copper distribution and copper weight in PCBs (Sierra)](https://www.protoexpress.com/blog/balanced-copper-distribution-and-copper-weight-in-pcbs/) — copper balance and warping (search result only).
- [What is copper thieving in PCBs (Sierra)](https://www.protoexpress.com/kb/what-is-copper-thieving-in-pcbs/) — definition of thieving (search result only).
- [Use of Teardrops in PCB Design (Sierra Connect)](https://sierraconnect.protoexpress.com/t/use-of-teardrops-in-pcb-design/2781) — need for teardrops depending on trace width (search result only).
- [Ask Me Anything about PCB Design for Assembly (Sierra Connect)](https://sierraconnect.protoexpress.com/t/ask-me-anything-about-pcb-design-for-assembly/2626) — 2–4 mm around BGA (search result only).
- [PCB Teardrops (Labcenter)](https://www.labcenter.com/blog/pcb-teardrops/) — teardrop against breakout (search result only).
- [SMT - SMD Neck-Down (Altium)](https://www.altium.com/documentation/altium-designer/pcb-smt-rule-smd-neck-down) — trace/pad width ratio rule (search result only).
- [Pulsonix copper check rules](https://pulsonix.com/docs/technology/idh_technology_copper_check_rules) — definition of sliver (search result only).
- [Cadence DFA guidance](https://resources.pcb.cadence.com/i/1541046/25) — shadowing by tall parts (search result only).
- [Printed circuit board design for assembly (Cadence)](https://resources.pcb.cadence.com/blog/jbj-printed-circuit-board-design-for-assembly-how-to-dfa) — BGA rework nozzle area (search result only).
- [Suntron recommends solutions to 0402 tombstoning (Circuits Assembly)](https://circuitsassembly.com/ca/editorial/menu-news/20006-suntron-recommends-solutions-to-0402-tombstoning.html) — equal copper density at the pads (search result only).
- [Avoid PCB Tombstoning in Assembly (LCSC)](https://www.lcsc.com/blog/avoid-tombstoning-in-pcb-assembly-causes-and-analysis/) — unequal trace widths (search result only).
- [Component Orientation and Polarity Rules for Assembly (Aisler)](https://community.aisler.net/t/component-orientation-and-polarity-rules-for-assembly/45) — polarity marking rules (opened).
- [Selective or wave soldering (Escatec)](https://www.escatec.com/blog/electronic-pcb-assembly-soldering-selective-or-wave-soldering) — double-sided THT and selective soldering (opened).
- [Wave soldering vs reflow for double-sided boards (ALLPCB)](https://www.allpcb.com/es-ES/blog/pcb-knowledge/wave-soldering-vs-reflow-for-double-sided-boards-choosing-the-right-process.html) — wave soldering problem on double-sided boards (search result only).
- [PCB design tips for assembly (Elecrow)](https://www.elecrow.com/blog/pcb-design-tips-for-assembly.html) — AOI shadowing, Z axis (search result only).
### Community (example links)
- [Questions about assembly and tombstoning — KiCad forum](https://forum.kicad.info/t/questions-about-assembly-and-tombstoning/27659) — 0201 tombstoning case (opened).
- [Thermal Relief – Yes or No? (AllAboutCircuits)](https://forum.allaboutcircuits.com/threads/thermal-relief-yes-or-no.205214/) — discussion of 0402 thermal spokes (search result only).
- [Thermal relief connection to zone incomplete — KiCad forum](https://forum.kicad.info/t/thermal-relief-connection-to-zone-incomplete/62623) — spoke count DRC, island removal (search result only).
- [Thermal relief ... connected to isolated island — KiCad forum](https://forum.kicad.info/t/thermal-relief-connection-to-zone-incomplete-layer-in1-cu-5-spokes-connected-to-isolated-island/66037) — spokes connecting to an island on an inner layer (search result only).
- [KiCad issue 15568](https://gitlab.com/kicad/code/kicad/-/issues/15568) — false positive on adjacent spokes (search result only).
- [JLCPCB "Silkscreen overlap" — KiCad forum](https://forum.kicad.info/t/jlcpcb-silkscreen-overlap/58557) — warning about silkscreen close to pads (search result only).
- [Dealing with silkscreen over solder mask — KiCad forum](https://forum.kicad.info/t/dealing-with-silkscreen-over-solder-mask/46011) — differing behaviour of manufacturers (search result only).
- [How bad is having no mask between SMD pads? — KiCad forum](https://forum.kicad.info/t/how-bad-is-having-no-mask-between-smd-pads/43923) — mask slivers (search result only).
- [Solder mask bridge between QFN pads — EEVblog](https://eevblog.com/forum/eda/solder-mask-bridge-between-qfn-pads-how-important/msg2403045) — discussion of mask without bridges on QFN (search result only).
- [Another PCB Design Noob — SparkFun forum](https://community.sparkfun.com/t/another-pcb-design-noob-new-thread-for-new-board/16280) — comment on acute-angle trace/acid trap (search result only).
- [PCB Libraries forum: neck-down discussion](https://www.pcblibraries.com/forum/printer_friendly_posts.asp?TID=2025) — opposing view on the need for neck-down (search result only).

## SLK, MEC, TST, EST

Access date: 2026-10-13. "(opened)" = page was read with WebFetch; "(search result only)" = only came back in a search result, content was taken from the search summary.
### Manufacturer / standard
- [The Ultimate Guide to PCB Panelization (JLCPCB)](https://jlcpcb.com/blog/184-the-ultimate-guide-to-pcb-panelization:-tools-and-techniques) — (opened) V-cut 25°, parts 3–4 mm from V-cut, mouse-bite 5–8 × 0.60 mm, rail 5–10 mm.
- [The Smart Advantages of Rounded Corners (JLCPCB)](https://jlcpcb.com/blog/rounded-corners-pcb-design) — (opened) corner radii by board size, inner corner ≥ R0.5.
- [The Benefits of Bed of Nails Testing (JLCPCB)](https://jlcpcb.com/blog/bed-of-nails-pcb-testing) — (opened) test pad 0.89 mm nominal, spacing 1.27/2.54 mm, part 1.02 mm.
- [Maximizing Circuit Reliability with PCB Test Points and Smart DFT (JLCPCB)](https://jlcpcb.com/blog/pcb-test-points-and-smart-dft) — (opened) TP types, power pad 1.5–2.0 mm, edge 3.2 mm, TP label, stub length.
- [Overhanging components (Eurocircuits)](https://www.eurocircuits.com/technical-guidelines/pcb-assembly-guidelines/overhanging-components/) — (opened) 2 mm break-off clearance, overhanging parts are not placed over tabs.
- [How to ensure the Board Outline is correct (MacroFab)](https://help.macrofab.com/knowledge/how-to-ensure-the-board-outline-is-correct) — (search result only) inner corner min. 0.5 mm (1.0 mm router bit).
- [Test point design for ICT and FP (PCBCart)](https://www.pcbcart.com/article/content/test-point-design-ict-fp.html) — (opened) pad 1.0/0.9/0.8 mm, spacing, mask, via ≤ 0.36 mm.
- [DFT guidelines – test escape (PCBCart)](https://www.pcbcart.com/article/content/dft-guidelines-test-escape) — (search result only) separate TP for power/reset/clock, 0 Ω link between rails.
- [Metric Clearance Hole Chart (AMES, ASME B18.2.8)](https://amesweb.info/Screws/Metric-Clearance-Hole-Chart.aspx) — (opened) M2–M6 close/normal/loose hole diameters.
- [ISO 273:1979 (ISO)](https://www.iso.org/standard/4183.html) — (search result only) clearance hole standard, confirmed in 2024.
- [DIN EN ISO 7089 (fasten.it)](https://fasten.it/Norms/Norm/DIN_EN_ISO_7089) — (search result only) washer outer diameters M2.5 6 / M3 7 / M4 9 mm.
- [ISO 7045 pan head (CDE Fasteners)](https://cdefasteners.com/sites/default/files/product-specs/meti7045pozi.pdf) — (search result only) M3 head diameter max. 5.6 mm.
- [ISO 4762 M3 socket head (Accu)](https://accu-components.com/us/metric-cap-head-screws/3818-SSCF-M3-8-A2) — (search result only) M3 socket head 5.5 mm.
- [Footprint for TC2030, Legged (Tag-Connect)](https://www.tag-connect.com/wp-content/uploads/bsk-pdf-manager/2026/07/TC2030-Footprint.pdf) — (opened, PDF read) pad/hole dimensions, keepout, pads without paste, DNL.
- [J-Link 6-Pin Needle Adapter Datasheet (SEGGER)](https://www.SEGGER.com/downloads/jlink/J-Link_6-Pin_Needle_Adapter_Datasheet.pdf) — (search result only) tall parts blocking finger access.
- [Debug Connectors (SEGGER KB)](https://kb.segger.com/Connectors) — (opened) 20-pin 0.1 in, 19-pin and 9-pin 0.05 in; pin 7 key.
- [19-pin JTAG/SWD and Trace Connector (SEGGER KB)](https://kb.segger.com/19-pin_JTAG/SWD_and_Trace_Connector) — (search result only) function of pin 1 VTref.
- [Cortex-M Debug Connectors (Arm)](https://documentation-service.arm.com/static/5fce6c49e167456a35b36af1) — (search result only) 10-pin 0.05 in Cortex Debug pinout; recommended for new designs.
- [J-Link connectors (Keil)](https://keil.com/support/man/docs/jlink/jlink_connectors.asp) — (search result only) Samtec FTSH-105, pin 7 key.
### Semiconductor / component manufacturer
- [Layout helps prevent chip MLCC from cracking (Murata)](https://article.murata.com/en-eu/article/layout-helps-prevent-chip-mlcc-from-cracking) — (opened) orientation parallel to the break line, slot.
- [TDK FAQ – flex crack countermeasures](https://product.tdk.com/en/contact/faq/capacitors-0089.html) — (search result only) keep MLCCs away from break lines and screw locations.
- [TPS40400 EVM User's Guide (TI)](https://www.ti.com/document-viewer/lit/html/SLUU535A/GUID-5EF28725-519D-4789-B6CF-66152BCBDACB) — (search result only) ripple measurement, short probe loop.
- [TPS51217 EVM User's Guide (TI)](https://ti.com/document-viewer/lit/html/SLUU420A/GUID-D997C164-6B9E-4599-815E-FAFD360244F5) — (search result only) adjacent TP7/TP8 probe/GND pair.
- [Measuring Methods – ABC of Power Modules (Würth Elektronik)](https://www.we-online.com/catalog/media/o198246v446%20Measuring%20Methods%20ABC%20of%20Power%20Modules%20EN%20(rev1).pdf) — (search result only) measuring at the output capacitor with a spring-ground probe.
- [MCT8315Z EVM User's Guide (TI)](https://ti.com/document-viewer/lit/html/SNLU342/GUID-B85CF074-3940-428B-9B28-30CBD2D062BD) — (search result only) per-rail status LEDs.
- [High-speed layout guidelines (TI SLLA284)](https://ti.com/document-viewer/lit/html/SLLA284G/GUID-B9B310F5-9021-45EE-8935-8E219F9D693D) — (search result only) no layer changes on high-speed traces, return via.
### Expert content
- [EMC Design Myths (LearnEMC)](https://www.learnemc.com/emc-design-myths) — (opened) 90° corner radiation myth, > 50 Gbps, 3W rule myth.
- [Slaying the PCB 90° Right-Angle Bend Dragon (Altium)](https://resources.altium.com/p/slaying-900-right-angle-bend-dragon) — (opened) 125 ps TDR, ~70 GHz, acid trap myth, corona.
- [PCB Routing Angle Myths: 45° vs 90° (Altium)](https://resources.altium.com/pcb-design-blog/pcb-routing-angle-myths-45-degree-angle-versus-90-degree-angle) — (opened, partly) no notable difference in simulation up to 120 GHz.
- [Should you worry about 90° bends (Signal Integrity Journal, Bogatin)](https://www.signalintegrityjournal.com/articles/2104-should-you-worry-about-90-degree-bends-in-circuit-board-traces?v=preview) — (search result only) "there is a reflection; whether it is a problem depends on the case". Not cited directly in the rules.
- [8 Common DFM Problems (Altium)](https://resources.altium.com/p/common-dfm-problems) — (opened) sliver, acid trap, acute angle rule.
- [How to Make Your PCB Layout AOI and X-Ray Friendly (Altium)](https://resources.altium.com/p/optimize-pcb-layout-for-aoi-x-ray) — (opened) polarized parts in the same orientation, tall-short shadowing, not hiding labels.
- [PCB Component Orientation Considerations (Cadence)](https://resources.pcb.cadence.com/blog/2021-pcb-component-orientation-considerations-for-optimum-part-placement) — (search result only) electrical requirements may determine orientation.
- [Multi-Channel Design with a Flat Project (Altium)](https://resources.altium.com/p/multi-channel-design-with-a-flat-project) — (search result only) channel replication.
- [PCB Layout Replication (Altium Docs)](https://www.altium.com/documentation/altium-designer/pcb-layout-replication) — (search result only) copying placement/routing.
- [Customizing Performance-Based Electrical Design Rules (Altium)](https://resources.altium.com/p/customizing-electrical-performance-based-design-rules-altium-designer) — (search result only) width rule by net class.
- [Routing Rule Types (Altium Docs)](https://www.altium.com/documentation/altium-designer/pcb/design-rule-types/routing?version=24) — (search result only) width rule priorities.
- [Circuit Board Design for In-Circuit Testers (Altium)](https://resources.altium.com/p/circuit-board-design-circuit-testability) — (opened) TP size/spacing/edge/part distances, 2–10 points for power.
- [Assigning Testpoints on the Board (Altium Docs)](https://www.altium.com/documentation/altium-designer/adding-testpoints-pcb) — (search result only) TP assignment, tented via problem.
- [PCB Silkscreen Guidelines (Altium)](https://resources.altium.com/p/your-guide-pcb-silkscreen) — (opened) labels, pin-1, connector pinout, logo, DNP marking.
- [Via Inductance (SigCon, Howard Johnson)](https://www.sigcon.com/Pubs/news/6_04.htm) — (search result only) ~1.2 nH via example for a 63 mil board.
- [Aesthetic PCB Design Tips For Improved Functionality (Hackaday / Phil's Lab)](https://hackaday.com/2022/11/29/aesthetic-pcb-design-tips-for-improved-functionality/) — (permalink from a fetch result) readable placement, grid, partitioning.
- [The myth of the pretty design (Siemens)](https://blogs.sw.siemens.com/electronic-systems-design/2014/08/13/the-myth-of-the-pretty-design/) — (opened) if the rules are met, pretty ≠ works better.
- [Everything you need to know about drilling PCB mounting holes (Cadence)](https://resources.pcb.cadence.com/blog/everything-you-need-to-know-about-drilling-pcb-mounting-holes-2) — (search result only) plated holes and chassis grounding.
- [PCB Mounting Holes and What to Watch Out For (MacroFab)](https://nws.macrofab.com/blog/attaching-your-project-to-things-mounting-holes-and-what-to-watch-out-for) — (opened) tool access, exposed copper ring, keeping MLCCs away from holes.
- [Protocase Designer – Mounting Printed Circuit Boards](https://www.protocasedesigner.com/pdf/Protocase_Designer_Mounting_pcb.pdf) — (opened, PDF read) hole–edge ≥ 0.375 in, connectors should not be flush with the edge, height allowance.
- [Top ten tips for nailing your PCB silkscreen design (EE World)](https://www.eeworldonline.com/top-ten-tips-for-nailing-your-pcb-silkscreen-design/) — (opened) 2 reading directions, ≥ 6 mil line, ≥ 5 mil from pads, no text under the body, no line between two pads.
- [PCB Silkscreen: Consider your Stakeholders (Boulder Engineering)](https://www.boulderes.com/resource-library/pcb-silkscreen-know-your-audience-0) — (opened) silkscreen under the body lifts small parts, TP/connector labels.
- [Atlas PCB – Silkscreen legend design](https://atlaspcb.com/blog/pcb-silkscreen-legend-design) — (opened) clearance table, pin-1 dot diameter, revision/date code area, TP label.
- [What Is Silkscreen on PCB? (Best Technology)](https://www.bestpcbs.com/blog/2026/05/what-is-silkscreen-on-pcb-clear-marking-for-better-assembly/) — (search result only) board name/revision/date code and traceability.
- [LIGO PCB design checklist E060231](https://dcc-lho.ligo.org/LIGO-E060231/public) — (search result only; PDF could not be opened because of a certificate error) power LED, TP, label items.
### Community
- [PCB Libraries Forum – IPC-7351 pin 1 / polarity](https://www.pcblibraries.com/forum/topic1530.html) — (opened) types of polarity marking, gap in the outline on QFN/BGA.
- [KiCad Forum – Silkscreen clipped by solder mask](https://forum.kicad.info/t/warning-silkscreen-clipped-by-solder-mask/46445) — (search result only) SLK-001 example.
- [KiCad Forum – Silkscreen/fab layer confusion](https://forum.kicad.info/t/silkscreen-fab-layer-confusion/52521) — (search result only) bottom silkscreen should look mirrored from the top.
- [KiCad Forum – Back Layer Silkscreen Reference Designators Reversed](https://forum.kicad.info/t/back-layer-silkscreen-reference-designators-reversed/53339) — (search result only) SLK-012 example.
- [KiCad GitLab issue #18235](https://gitlab.com/kicad/code/kicad/-/issues/18235) — (search result only) text mirroring behaviour.
- [KiCad Forum – Track has unconnected end](https://forum.kicad.info/t/6-0-rc1-track-has-unconnected-end/32080) — (search result only) dangling trace warning.
- [KiCad GitLab issue #10539](https://gitlab.com/kicad/code/kicad/-/issues/10539) — (search result only) request to clean up unconnected trace ends.
- [KiCad Forum – Easy way to find unrouted traces?](https://forum.kicad.info/t/easy-way-to-find-unrouted-traces/5061/) — (search result only) finding unconnected ratsnest.
- [EEVblog Forum – Plated mounting holes: grounded or not?](https://eevblog.com/forum/projects/plated-mounting-holes-grounded-or-not/msg488137) — (search result only) direct / C / RC / isolated options.
- [EEVblog Forum – EEVblog 1334 teardown thread](https://eevblog.com/forum/blog/eevblog-1334-mystery-dumpster-teardown) — (search result only) criticism of sloppy labelling (SLK-004 example).
- [DigiKey Forum – Overmold size of the USB-C male end](https://forum.digikey.com/t/overmold-size-of-the-usb-c-male-end/70874) — (search result only) overmold length for a recessed port.
- [SparkFun Forum – jumper/0 Ω connection](https://community.sparkfun.com/t/what-do-you-call-this-jumper-connection-on-a-pcb/15824) — (search result only) testing supplies separately with a 0 Ω.

## Visual audit guide (GOR)

Access date: 2026-10-13. "(search result only)" = taken only from a search result, page was not opened.
### KiCad
- [KiCad builtin_color_themes.h — master](https://gitlab.com/kicad/code/kicad/-/raw/master/common/settings/builtin_color_themes.h) — Default/Classic theme PCB and 3D colours (downloaded with curl and grepped)
- [KiCad builtin_color_themes.h — 8.0](https://gitlab.com/kicad/code/kicad/-/raw/8.0/common/settings/builtin_color_themes.h) — via/pad/THT colours, 3D colours
- [KiCad builtin_color_themes.h — 7.0](https://gitlab.com/kicad/code/kicad/-/raw/7.0/common/settings/builtin_color_themes.h) — LAYER_VIA_THROUGH etc. present in 7.0
- [KiCad builtin_color_themes.h — 9.0](https://gitlab.com/kicad/code/kicad/-/raw/9.0/common/settings/builtin_color_themes.h) — no via/pad keys in 9.0
- [KiCad Forum — How to control NET NAMES on traces](https://forum.kicad.info/t/how-to-control-net-names-on-traces-spacing-display-threshold/47608) (search result only) — location of the net name display setting
- [KiCad footprint R_0402_1005Metric](https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/master/Resistor_SMD.pretty/R_0402_1005Metric.kicad_mod) — pad 0.54×0.64, centre ±0.51
- [KiCad footprint R_0603_1608Metric](https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/master/Resistor_SMD.pretty/R_0603_1608Metric.kicad_mod) — pad 0.8×0.95, centre ±0.825
- [KiCad footprint R_0805_2012Metric](https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/master/Resistor_SMD.pretty/R_0805_2012Metric.kicad_mod) — pad 1.025×1.4, centre ±0.9125
- [KiCad footprint SOT-23](https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/master/Package_TO_SOT_SMD.pretty/SOT-23.kicad_mod) — body 1.3×2.9, pitch 1.9, outside-to-outside 3.35
- [KiCad footprint SOT-223-3_TabPin2](https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/master/Package_TO_SOT_SMD.pretty/SOT-223-3_TabPin2.kicad_mod) — pitch 2.3
- [KiCad footprint TO-252-2](https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/master/Package_TO_SOT_SMD.pretty/TO-252-2.kicad_mod) — body ~6.22×6.5, lead centres ±2.28
- [KiCad footprint TO-220-3_Vertical](https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/master/Package_TO_SOT_THT.pretty/TO-220-3_Vertical.kicad_mod) — RM 2.54, Fab body 10.0 mm
- [KiCad footprint MountingHole_3.2mm_M3_Pad](https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/master/MountingHole.pretty/MountingHole_3.2mm_M3_Pad.kicad_mod) — hole 3.2, pad 6.4, courtyard r=3.45
### Altium
- [Altium — PCB Editor Layer Colors Preferences](https://www.altium.com/documentation/altium-designer/pcb-editor-layer-colors-preferences) — system profiles cannot be deleted, 2D colour is system-wide, DRC Error Markers is a system colour; no default values
- [Altium — Board Layers and Colors](https://www.altium.com/documentation/cstu/board-layers-and-colors) — Default.PCBSysColors / Classic.PCBSysColors; no values
- [Altium — Your View of the PCB](https://www.altium.com/documentation/altium-designer/pcb/your-view-of-the-board) — single layer mode (hide / grayscale / monochrome), dimming, highlighting, net color override
- [Altium — Polygon Pour](https://www.altium.com/documentation/cstu/polygon-pour-0) (search result only) — Solid / Hatched / None (Outlines Only)
- [Altium — Shelve Polygons](https://altium.com/documentation/altium-designer/pcb-cmd-shelvepolygonsshelvepolygons-ad) (search result only) — shelve = temporary hiding
- [Altium — Modified Polygon rule](https://altium.com/jp/documentation/altium-designer/pcb-electrical-rule-modified-polygon) (search result only) — Allow shelved option
- [Fedevel forum — Learn Altium Essentials](https://fedevel.com/forum/your-projects/17183-course-learn-altium-essentials-second-edition) — user: Top red, Bottom blue; green = DRC violation
### EasyEDA
- [EasyEDA PCB File Format](https://docs.easyeda.com/en/DocumentFormat/3-EasyEDA-PCB-File-Format/) — layer ID/name/hex colour table, canvas #000000
- [EasyEDA Layer Manager](https://docs.easyeda.com/en/PCB/Layer-Manager/index.html) — layer list, no colour values
- [EasyEDA Pro Layer Manager](https://prodocs.easyeda.com/en/pcb/tools-layer-manager/) (search result only) — colour/transparency setting; Top/Bottom cannot be disabled
### Package and connector dimensions
- [Wikipedia — List of integrated circuit packaging types](https://en.wikipedia.org/wiki/List_of_integrated_circuit_packaging_types) — chip sizes, SOIC/TSSOP/LQFP/BGA pitch, SOT-23/223, tantalum and aluminium cases
- [Wikipedia — Surface-mount technology](https://en.wikipedia.org/wiki/Surface-mount_technology) — opened; no size table (not used)
- [Wikipedia — USB-C](https://en.wikipedia.org/wiki/USB-C) — receptacle opening 8.34 × 2.56 mm, 6.20 mm deep
- [Wikipedia — USB hardware](https://en.wikipedia.org/wiki/USB_hardware) — Micro-B, Mini-B, Standard-A opening dimensions
- [Wikipedia — TO-220](https://en.wikipedia.org/wiki/TO-220) — 2.54 mm pitch
- [Wikipedia — TO-252](https://en.wikipedia.org/wiki/TO-252) — 3 pins, 2.3 mm (90 mil) pitch
- [Wikipedia — JST connector](https://wikipedia.com/wiki/JST_connector) (search result only) — PH 2.0, XH 2.5, SH 1.0, GH 1.25, ZH 1.5, VH 3.96 mm
- [Matt Millman — Common JST connector types](https://www.mattmillman.com/info/crimpconnectors/common-jst-connector-types/) (search result only) — JST pitches (secondary)
- [HQ Online — GCT USB4105-GF-A](https://hqonline.com/product-detail/usb-connectors-gct-usb4105-gf-a-2500389379) (search result only) — package 8.94 × 7.35 mm (secondary)
- [Arrow — GCT USB4105 drawing (PDF)](https://static6.arrow.com/aropdfconversion/5da1d78683a8f83396815f68bf69e3b83c010277/usb4105.pdf) (search result only; attempt to open timed out) — the 8.94 value is in the land pattern section
- [RS Components — QANTEK HC-49/U-S](https://uk.rs-online.com/web/p/crystal-units/1734305) (search result only) — 11.05 × 4.65 mm
- [DigiKey — Epson TSX-3225](https://azcus.digikey.com/en/products/detail/epson/TSX-3225-25-0000MF10P-C0/7430946) (search result only) — 3.2 × 2.5 mm
- [Espressif — ESP32-WROOM-32E/32UE Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.pdf) (search result only) — 18.0 × 25.5 × 3.1 mm
### Surface finish
- [MCL — PCB Surface Finishes: HASL, OSP and ENIG](https://www.mclpcb.com/blog/pcb-surface-finishes-hasl-osp-enig) — HASL has poor planarity, OSP/ENIG are flat; no colour description (colours are general knowledge)
### ESP32 antenna (background)
- [EEVblog — ESP32 copper keep-out with elevated module](https://www.eevblog.com/forum/microcontrollers/esp32-do-i-follow-copper-keep-out-rule-even-with-elevated-module/msg6359902/) (search result only) — no metal around the antenna
### Review examples
- [EEVblog — ESP32 PCB & Schematic Review](https://www.eevblog.com/forum/beginners/esp32-pcb-schematic-review-is-there-anything-wrong/)
- [EEVblog — First custom ESP32 PCB LED matrix](https://www.eevblog.com/forum/projects/designed-my-first-custom-esp32-pcb-to-drive-a-led-matrix-over-wifi/)
- [EEVblog — Buck converter Design](https://www.eevblog.com/forum/altium/buck-converter-design/)
- [Fedevel — Buck converter Layout Review](https://fedevel.com/forum/schematic-design-pcb-layout/16381-buck-converter-layout-review)
- [EEVblog — Novice BLDC driver](https://eevblog.com/forum/projects/seeking-feedback-on-my-novice-bldc-driver-pcb-design)
- [Fedevel — USB Controlled Impedance on 4-Layer PCB](https://fedevel.com/forum/schematic-design-pcb-layout/11347-usb-controlled-impedance-on-4-layer-pcb-routing-on-l3)
- [KiCad Forum — PDB for micro drone](https://forum.kicad.info/t/pcb-review-request-pdb-for-a-micro-drone/48178) — eliminated
- [KiCad Forum — Smart doorbell ESP32-CAM](https://forum.kicad.info/t/review-request-2-layer-smart-doorbell-layout-esp32-cam-solid-front-gnd/71350) — eliminated

## Added during validation testing (main agent)

- [JLCPCB Help — How to mark on PCB?](https://jlcpcb.com/help/article/how-to-mark-on-pcb) — (opened, browser) 2026-05-22 update: no default marking; barcode/serial number location with a filled silkscreen square (SLK-013)
- [Same Sky (CUI) PJ-002A datasheet](https://www.sameskydevices.com/product/resource/pj-002a.pdf) — (opened, pdftotext) 2.5 A / 24 Vdc (PWR-018)
- [onsemi AN1040/D — Mounting Considerations for Power Semiconductors](https://www.onsemi.com/pub/Collateral/AN1040-D.PDF) — (opened, pdftotext) lead bending, heatsink flatness, mounting order (THM-012)
- [KiCad forum — PCB Review Request (ESP32 LED)](https://forum.kicad.info/t/pcb-review-request/40027) — (opened) validation test 1
- [EEVblog — Seeking Feedback on My Novice BLDC Driver PCB Design](https://eevblog.com/forum/projects/seeking-feedback-on-my-novice-bldc-driver-pcb-design) — (opened) validation test 2
- [Fedevel — Buck converter Layout Review](https://fedevel.com/forum/schematic-design-pcb-layout/16381-buck-converter-layout-review) — (opened) validation test 3
