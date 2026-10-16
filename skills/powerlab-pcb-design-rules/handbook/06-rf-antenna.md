# 06 — RF and Antenna (RF)

This section contains the rules for auditing, from a screenshot, boards with a wireless module (ESP32-WROOM/S3, nRF52 modules, u-blox NINA) or a chip/PCB antenna. RF errors pass DRC but halve the range or break certification; this is why the auditor should always look at the antenna area first. The rules are based on manufacturers' application notes; if the module manufacturer's own drawing contradicts this handbook, **the module manufacturer's document always prevails** (see the RF-003 exceptions).

### [RF-001] Copper beneath the module antenna or in the antenna keepout area

- **Severity:** Critical
- **Detectable from image:** Yes
- **How it looks in the image:** ESP32-WROOM/S3-WROOM module: at one end of the silver metal shield rectangle, a meandering gold/copper-coloured antenna trace in the ~18 × 6 mm area outside the shield. If beneath this area the board shows light green (solder mask over copper) fill, in KiCad an F.Cu red / B.Cu blue zone fill, a trace, via or part, it is an error. In the correct case the area beneath the antenna is the dark/semi-transparent bare FR-4 colour, or there is no board there at all (cutout/overhang). If there is no back-side image, ask the user for B.Cu and inner layer images.
- **Why it matters:** Copper beneath the antenna detunes it and shields the radiation; the ESP32-S3 HDG recommends clearing even the board material beneath and on both sides of the antenna area. Nordic requires the keepout to be repeated on inner layers on multilayer boards.
- **Recommended fix:** Draw a keepout (rule area: no copper/tracks/vias/pads) over the antenna area **on all copper layers** and refill the zones; if possible, move the antenna so it overhangs the board (see RF-002).
- **Exceptions:** u-blox NINA-B3x2 (metal PIFA antenna) requires solid GND beneath the entire module, including the antenna section; modules with a u.FL output (ESP32-S3-WROOM-1U etc.) do not need an antenna keepout (Espressif datasheet).
- **Example:** Link: https://forum.kicad.info/t/pcb-review-request/40027 — Visible error: on an LED board with an ESP32 module the placement and ground plane are criticised; the user later realises that the antenna area must be kept free of copper and parts.
- **Source:** [ESP32-S3 HDG — PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html), [ESP32-S3-WROOM-1/1U Datasheet v1.8](https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf), [Nordic DevZone — nRF52832 PCB Layout Review](https://devzone.nordicsemi.com/f/nordic-q-a/83955/nrf52832-pcb-layout-review/349182), [u-blox NINA-B3 SIM](https://content.u-blox.com/sites/default/files/NINA-B3_SIM_UBX-17056748.pdf)

### [RF-002] Module antenna not at the board edge (buried inside the board)

- **Severity:** Critical
- **Detectable from image:** Yes
- **How it looks in the image:** The module's meander antenna end is far from the board edge line (Edge.Cuts, yellow), in the interior of the board; the antenna is surrounded on all sides by board material and copper. In the 3D view the antenna end does not overhang the board and is not flush with the edge either.
- **Why it matters:** Espressif recommends that the PCB antenna overhang the board and that the feed point be close to the board edge; it explicitly does not recommend exposing the module by cutting out the board on all four sides. An antenna inside the board is loaded by the surrounding ground and parts, and the radiation pattern is distorted.
- **Recommended fix:** Move the module to the edge so that the antenna end overhangs the board (the "✓" positions in Espressif Fig. 24/25). If an overhang is not possible, make the antenna flush with the edge and cut out the board on both sides of and beneath the antenna (see RF-004).
- **Exceptions:** Module variants using an external antenna (u.FL/SMA); flush-with-edge placement is acceptable if the antenna cutout carries a mechanical breakage risk.
- **Example:** Link: https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/esp-hardware-design-guidelines-en-master-esp32s3.pdf — Good/bad: in Fig. 24–25, positions 1 and 5, at the corner and overhanging, are marked as recommended; positions at the middle of an edge and inside the board are marked as not recommended.
- **Source:** [ESP32-S3 HDG (PDF, master)](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/esp-hardware-design-guidelines-en-master-esp32s3.pdf), [ESP32 HDG — PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32/pcb-layout-design.html)

### [RF-003] Antenna feed point not at the corner/edge position recommended by the module manufacturer

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** The module is at the edge but the antenna tip side faces the middle of the board instead of the corner, or the feed point (the end where the meander connects to the module body) is far from the board corner. The module pin-1/antenna orientation is read by comparing with the datasheet; if the feed side is not clear from the image, ask the user for the module part number.
- **Why it matters:** In Espressif's placement drawings only positions where the feed point comes to the board corner are recommended; for u-blox NINA-B3x2 corner placement gives the best performance, while other edge positions give "moderately" lower performance.
- **Recommended fix:** On ESP32 modules bring the feed point to the board corner (Espressif Fig. 24/25). u-blox NINA-B3x2: feed (pins 15–16) at the corner; NINA-B3x6 (PCB trace antenna): at the **middle** of an edge, with ≥ 10 mm of ground on both sides of the module (u-blox SIM R15).
- **Exceptions:** Manufacturers require different positions (ESP32 corner vs. NINA-B3x6 middle of edge); the integration manual of that specific module always prevails.
- **Example:** —
- **Source:** [ESP32-S3 HDG (PDF, master)](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/esp-hardware-design-guidelines-en-master-esp32s3.pdf), [u-blox NINA-B3 SIM](https://content.u-blox.com/sites/default/files/NINA-B3_SIM_UBX-17056748.pdf)

### [RF-004] Antenna clear area (clearance/keepout) too small

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** There is an antenna keepout but it is narrow: copper pour or parts end a few mm from the non-feed end of the antenna. The module width can be used for scale (ESP32-S3-WROOM-1 body 18 mm, antenna area ~6 mm). If an exact measurement cannot be made from the image, ask the user for dimensions/a dimensioned image.
- **Why it matters:** The clear area determines the antenna's resonance and efficiency; as the area shrinks the antenna detunes.
- **Recommended fix:** According to the Espressif ESP32-S3 keepout drawing (feed on the right): **at least 15 mm** of clear (board cut away) area on the non-feed side of the antenna, antenna end at most ~1–2 mm inside the board edge. Inside the product enclosure, **at least 15 mm** of clearance in every direction around the antenna (Espressif, ESP32/S3 HDG, accessed 2026-10).
- **Exceptions:** If the module's own datasheet gives a different dimension, that one prevails; for non-ESP32 modules see their own manual.
- **Example:** —
- **Source:** [ESP32-S3 HDG (PDF, master) — Fig. 26 Keepout Zone](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/esp-hardware-design-guidelines-en-master-esp32s3.pdf), [ESP32-S3 HDG — PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html)

### [RF-005] Insufficient ground plane/vias around the antenna and beneath the module

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** There is no continuous GND pour beneath the module body and along the edge of the antenna keepout; the pour is broken into islands or there are no vias at the keepout boundary. The module sits at the end of a very small board and the board has almost no GND pour.
- **Why it matters:** Monopole-type module antennas use the main board ground as the counterpoise; Espressif requires enough GND copper and dense GND vias near the antenna, and u-blox considers a large ground plane a prerequisite.
- **Recommended fix:** Solid GND beneath the module (except the antenna); dense GND vias along the keepout boundary. For NINA-B3x6 the ground should extend ≥ 10 mm on both sides of the module; the minimum ground size should be about ~λ/4 of the lowest frequency (u-blox). Johanson: stitch the antenna-side edge of the ground plane to the bottom layer with many vias.
- **Exceptions:** The only area where ground is unwanted is the antenna keepout; this rule applies outside the keepout (see RF-001).
- **Example:** —
- **Source:** [ESP32-S3 HDG — PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html), [u-blox NINA-B3 SIM](https://content.u-blox.com/sites/default/files/NINA-B3_SIM_UBX-17056748.pdf), [Johanson — Chip Antenna Layout Considerations](https://johansontechnology.com/docs/2/jti-antenna-mounting.pdf)

### [RF-006] Metal part, battery, screw, tall connector or cable close to the antenna

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** Near the antenna end there is a mounting hole/screw, battery holder or battery clip, a metal-bodied connector such as USB/RJ45, a large electrolytic capacitor, a heatsink, a display (LCD) connection or a cable exit. In the 3D view tall metal parts are level with the antenna. The enclosure material and distance cannot be determined from the image: ask the user whether the enclosure is metal and how far it is from the antenna.
- **Why it matters:** Metal and RF-absorbing materials absorb radiated power, shift the resonant frequency and distort the radiation pattern (u-blox); even a plastic enclosure and a hand pull the resonance down (TI AN058).
- **Recommended fix:** Keep tall/large and metal parts **≥ 10 mm** from the module antenna (u-blox NINA-B3); antenna to enclosure ≥ 5 mm (NINA-B3x2) / ≥ 10 mm (NINA-B3x6); for ESP32 ≥ 15 mm in every direction inside the enclosure (Espressif). Do not use an internal antenna in a metal enclosure; switch to an external antenna. Test the final product inside its enclosure.
- **Exceptions:** Designs where the antenna itself requires a metal ground plane (some external antennas) follow their manufacturer's instructions.
- **Example:** —
- **Source:** [u-blox NINA-B3 SIM](https://content.u-blox.com/sites/default/files/NINA-B3_SIM_UBX-17056748.pdf), [ESP32-S3 HDG — PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html), [TI AN058 Antenna Selection Guide (SWRA161B)](https://www.ti.com/lit/an/swra161b/swra161b.pdf)

### [RF-007] Chip antenna ground clearance (no-ground area) and placement do not match the datasheet

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** A small white/black ceramic rectangle (e.g. a 1206-size 2.4 GHz chip antenna) is not at the board edge, or there is GND pour beneath/beside it; there is no copper-free rectangular area around the antenna, or it is very narrow. The feed line reaches the antenna via a long path parallel to the board edge.
- **Why it matters:** Chip antennas are not designed to operate near a ground plane; when the ground distance falls below the recommended value, performance degrades severely (Johanson). The feed microstrip is also part of the resonant system.
- **Recommended fix:** Place the antenna at the board corner/edge as an exact copy of the evaluation board in the datasheet. Johanson 2.4 GHz example: > 2 mm from the antenna's short sides to ground (> 1 mm for the other mounting style), > 4 mm from its long side; the feed line should connect to the antenna perpendicular to the microstrip.
- **Exceptions:** Every chip antenna model has its own dimensions; if the part number is not known, ask the user for it.
- **Example:** —
- **Source:** [Johanson — Chip Antenna Layout Considerations for 802.11](https://johansontechnology.com/docs/2/jti-antenna-mounting.pdf), [Nordic — General PCB design guidelines for nRF52 series](https://devzone.nordicsemi.com/guides/hardware-design-test-and-measuring/b/nrf5x/posts/general-pcb-design-guidelines-for-nrf52-series)

### [RF-008] PCB trace antenna (IFA/meander/monopole) not copied exactly from the reference design

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** The board has an F-shaped (IFA) or meander antenna drawn in copper; its dimensions do not resemble a known reference (TI CC2511 IFA, Nordic DK antenna), its corners are 90°, it is very close to the ground edge (less than a few mm) or there is copper beneath it. Board thickness and material are not visible in the image: ask the user which reference was copied and what the stackup is.
- **Why it matters:** Small changes in antenna dimensions change performance considerably; TI recommends importing the reference design's Gerber/DXF and using the same board thickness/material. The size and shape of the ground plane also affect the result.
- **Recommended fix:** Import the antenna from the reference Gerber/DXF and use the same thickness/material; do not put ground or traces beneath the antenna (TI AN058). Also copy the distance to the ground plane and add a matching network; Nordic gives ≥ 5 mm clearance to ground for a quarter-wave monopole.
- **Exceptions:** Original designs verified by electromagnetic simulation and VNA measurement.
- **Example:** Link: https://devzone.nordicsemi.com/f/nordic-q-a/16740/nrf52-antenna-design-review/64003 — Visible: Nordic recommends ~5 mm ground clearance and two 45° bends instead of 90° corners; for a meander antenna it advises copying the dongle design.
- **Source:** [TI AN043 Small Size 2.4 GHz PCB Antenna (SWRA117D)](https://www.ti.com/lit/an/swra117d/swra117d.pdf), [TI AN058 (SWRA161B)](https://www.ti.com/lit/an/swra161b/swra161b.pdf), [Nordic — General PCB design guidelines for nRF52 series](https://devzone.nordicsemi.com/guides/hardware-design-test-and-measuring/b/nrf5x/posts/general-pcb-design-guidelines-for-nrf52-series)

### [RF-009] RF feed line width/spacing is not 50 Ω for the stackup

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** The trace from the RF pin to the antenna/connector is as thin as the board's ordinary signal traces; the gap between it and the GND pour on both sides is irregular or changes along the line. Impedance cannot be calculated without knowing the stackup: ask the user for layer count, dielectric thickness, trace width and GND gap.
- **Why it matters:** RF pins are designed for 50 Ω; impedance mismatch means reflection and power loss. Silicon Labs makes it mandatory that every RF trace longer than λ/16 at the fundamental frequency be a 50 Ω transmission line.
- **Recommended fix:** Calculate the line as CPWG for the manufacturer's stackup (JLCPCB/Saturn calculator). Example: JLCPCB JLC04161H-7628 4 layers, L1→L2 reference: ~0.30–0.34 mm trace, ~0.18–0.20 mm gap (LibreCAL discussion, accessed 2026-10). Espressif typically gives the RF trace on 2 layers as > 20 mil (0.5 mm). Guard the line with GND on both sides, trace–GND gap ≥ 2 × trace width (u-blox, for microstrip design).
- **Exceptions:** For lines shorter than λ/16 (a few mm in FR-4 at 2.4 GHz) impedance is not critical. At PCBWay standard price, impedance control costs extra (PowerLab rule); uncontrolled fabrication with the calculated geometry is acceptable.
- **Example:** —
- **Source:** [JLCPCB — User Guide to the Impedance Calculator](https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator), [LibreCAL PR #8 (JLC04161H-7628 CPWG)](https://github.com/jankae/LibreCAL/pull/8), [Silicon Labs — Z-Wave 800 PCB Implementation](https://docs.silabs.com/z-wave/8.0.1/z-wave-800-series-integration-guide/08-pcb-implementation), [ESP32 HDG — PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32/pcb-layout-design.html), [u-blox NINA-B3 SIM](https://content.u-blox.com/sites/default/files/NINA-B3_SIM_UBX-17056748.pdf)

### [RF-010] Via, branch, 90° corner or unnecessary length on the RF line

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** The RF trace changes layers (a via on the trace), has a T-shaped side branch (test pad or a second part), makes sharp 90° turns or wanders unnecessarily long between the module/chip and the antenna; the trace width changes along the route.
- **Why it matters:** Vias, branches and sharp corners create impedance discontinuities; a long FR-4 line increases dielectric loss.
- **Recommended fix:** Keep the RF trace on an outer layer, without vias, at constant width, without branches and as short as possible; make turns with 135° (two 45°) or an arc (Espressif). If an RF path longer than a few centimetres is needed, use a coaxial connector and cable (u-blox).
- **Exceptions:** The pads of matching network parts are part of the line; they are not counted as "branches".
- **Example:** —
- **Source:** [ESP32-S3 HDG — PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html), [u-blox NINA-B3 SIM](https://content.u-blox.com/sites/default/files/NINA-B3_SIM_UBX-17056748.pdf)

### [RF-011] Another trace beneath the RF line, or the reference ground plane is interrupted

- **Severity:** Critical
- **Detectable from image:** Partly
- **How it looks in the image:** Directly beneath the RF trace on the top layer (in the B.Cu or inner layer image) there is a crossing trace, a power line, or a slot/gap in the pour. Not detectable if only the top layer image is available: ask for bottom and inner layer images.
- **Why it matters:** The RF line's return current flows in the reference plane directly beneath it; an interruption disturbs the impedance and creates coupling. Nordic requires that no trace be placed directly beneath the RF path and that continuous ground run from the chip's centre pad to the antenna feed.
- **Recommended fix:** Continuous GND beneath the RF line, chip and crystal (on 4 layers L2 entirely GND, no signals on L2 — Espressif). On a 2-layer board the bottom layer must be continuous GND in this area.
- **Exceptions:** Nordic reference designs on multilayer boards specify a keepout on the **inner** layers beneath the RF path (the reference is moved to a lower plane and the trace widens). This differs from Espressif's "adjacent layer reference" approach: follow whatever the reference design of the chip in use does.
- **Example:** —
- **Source:** [Nordic — General PCB design guidelines for nRF52 series](https://devzone.nordicsemi.com/guides/hardware-design-test-and-measuring/b/nrf5x/posts/general-pcb-design-guidelines-for-nrf52-series), [ESP32-S3 HDG — PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html)

### [RF-012] Ground via fence along the RF line missing or sparse

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** There is no regular via row on the GND pour on both sides of the RF trace, only a few scattered vias, or the vias are on one side of the line only. Correct appearance: a row of small, evenly spaced vias on both sides of the trace, close to the edge.
- **Why it matters:** Densely stitching the top and bottom grounds confines the fields at the line edge and suppresses parallel-plate resonances and coupling; Espressif and u-blox require dense GND vias around the RF line.
- **Recommended fix:** Via spacing ≤ λ/20 at the highest relevant frequency (general via fence rule). At 2.4 GHz the free-space λ/20 ≈ 6 mm; since the wavelength is shorter inside FR-4, in practice aim for ≤ ~3 mm spacing (this handbook's calculation, see DECISIONS.md). In other ground areas at least one via every 5 mm (Nordic).
- **Exceptions:** Very short (below λ/16) lines; if the line is on an inner layer between two planes (stripline), edge vias are still recommended.
- **Example:** —
- **Source:** [Wikipedia — Via fence](https://en.wikipedia.org/wiki/Via_fence), [RF Essentials — Shielded compartment design](https://rfessentials.com/rf-knowledge-base/how-do-i-design-a-shielded-compartment-on-a-pcb-to-isolate-sensitive-rf-stages/), [Nordic — General PCB design guidelines for nRF52 series](https://devzone.nordicsemi.com/guides/hardware-design-test-and-measuring/b/nrf5x/posts/general-pcb-design-guidelines-for-nrf52-series), [ESP32-S3 HDG — PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html)

### [RF-013] Matching network (pi/CLC) missing, far from the RF pin or far from the antenna

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** In a chip-down RF design there is no group of 2–3 small passives (series L/C + two shunt C, "π" arrangement) between the RF pin and the antenna; or this group is far from the chip, in the middle of the line. Two separate matching groups are expected for the chip and the antenna: one adjacent to the pin, the other adjacent to the antenna.
- **Why it matters:** The chip-side network is for harmonic filtering and output power adjustment, the antenna-side network is for matching the antenna to 50 Ω; trace length in between changes the network's effect. The ESP32 HDG considers the π network "required" for matching the antenna.
- **Recommended fix:** Chip CLC network closest to the pin, on the same layer (Espressif: 0201, zigzag arrangement so the two capacitors do not face the same direction). Antenna CLC network as close to the antenna as possible. Nordic QFN: the GND of the shunt capacitor closest to the pin connects to the VSS pin closest to ANT. Values are tuned on the board with a VNA.
- **Exceptions:** In certified modules (antenna included) the network is inside the module; only the external antenna side is needed on the main board.
- **Example:** Link: https://devzone.nordicsemi.com/f/nordic-q-a/83955/nrf52832-pcb-layout-review/349182 — Visible: the user placed only the radio matching network and did not add an antenna; Nordic also recommended removing the top-layer GND connection of the first capacitor.
- **Source:** [ESP32-S3 HDG — PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html), [Nordic — General PCB design guidelines for nRF52 series](https://devzone.nordicsemi.com/guides/hardware-design-test-and-measuring/b/nrf5x/posts/general-pcb-design-guidelines-for-nrf52-series), [Silicon Labs — Z-Wave 800 PCB Implementation](https://docs.silabs.com/z-wave/8.0.1/z-wave-800-series-integration-guide/08-pcb-implementation)

### [RF-014] U.FL/IPEX or SMA connector placed incorrectly, trace/copper beneath it

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** The small square U.FL connector is far from the RF pin, in the middle of the board or connected by a long RF trace; a trace passes through the area between the two GND pads. On an SMA, the GND pour around the centre pin is not cleared back to the four GND legs. The inner layer clearance is not visible in the image: ask for an inner layer image.
- **Why it matters:** Ground beneath the connector's wide active pad adds parasitic capacitance and spoils the 50 Ω; a conductive trace between the U.FL GND pads carries a short-circuit/coupling risk.
- **Recommended fix:** Place the connector close to the RF pin and close to the board edge. U.FL: no traces between the GND pads; a GND void beneath the active pad on at least the first inner layer. SMA (THT): GND void around the centre pin on all layers (u-blox). Espressif: all layers clear beneath the IPEX connector.
- **Exceptions:** If the connector manufacturer has its own recommended land pattern, that one prevails.
- **Example:** —
- **Source:** [u-blox NINA-B3 SIM](https://content.u-blox.com/sites/default/files/NINA-B3_SIM_UBX-17056748.pdf), [ESP32 HDG — PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32/pcb-layout-design.html)

### [RF-015] Noise sources (SMPS, inductor, crystal, USB/UART, DDR, clock) close to the antenna or RF line

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** Right next to the antenna keepout there is a switching regulator (small SOT/QFN + large square power inductor), a crystal (metal-can part with 2 or 4 pads), a USB connector/USB-serial chip, a UART header, test points or fast digital bus traces; UART TX/RX traces cross the RF trace.
- **Why it matters:** Harmonics from these sources couple into the antenna and reduce receiver sensitivity (Espressif: UART TX/RX crossing the RF trace can degrade RX performance). Silicon Labs recommends locating the RF chip in a board corner, away from switching DC supplies, main processors and motor drivers.
- **Recommended fix:** Place SMPSs and inductors, the crystal, USB/UART and fast clock/DDR lines as far as possible from the antenna and RF line; surround UART traces with GND pour and vias; they must not cross the RF trace. Manufacturers give no numeric distance; report it if a noise source in the image is adjacent to the antenna keepout. For the SMPS hot loop see SMPS; for crystal placement see XTL.
- **Exceptions:** The module's own internal crystal/regulator is under the shield; the rule is for parts on the main board.
- **Example:** —
- **Source:** [ESP32 HDG — PCB Layout Design](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32/pcb-layout-design.html), [Silicon Labs — Z-Wave 800 PCB Implementation](https://docs.silabs.com/z-wave/8.0.1/z-wave-800-series-integration-guide/08-pcb-implementation), [u-blox NINA-B3 SIM](https://content.u-blox.com/sites/default/files/NINA-B3_SIM_UBX-17056748.pdf)

### [RF-016] GND ring of the RF shield can footprint interrupted or with sparse vias

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** Around the RF section there is an exposed copper (no mask) ring drawn for the shield frame, but the ring is cut in places for trace crossings; there are no or few GND vias along the ring; signal traces run from inside the shield to outside on the top layer. Parts very close to the shield wall may also be visible.
- **Why it matters:** The shield's effectiveness is limited by the continuity of contact between the lid and the PCB GND ring; openings in the ring and sparse vias let fields leak.
- **Recommended fix:** A continuous copper ring on the top layer, connected to the inner GND plane with a dense via row; via spacing < λ/20 at the relevant frequency (< 6 mm for 2.4 GHz, RF Essentials). Route DC/control lines leaving the shield on an inner layer or through filters. Use the shield manufacturer's land pattern for pad size and part-to-wall distance.
- **Exceptions:** Certified modules have their own shield; no additional shield is needed on the main board.
- **Example:** —
- **Source:** [RF Essentials — Shielded compartment design](https://rfessentials.com/rf-knowledge-base/how-do-i-design-a-shielded-compartment-on-a-pcb-to-isolate-sensitive-rf-stages/), [Wikipedia — Via fence](https://en.wikipedia.org/wiki/Via_fence)
