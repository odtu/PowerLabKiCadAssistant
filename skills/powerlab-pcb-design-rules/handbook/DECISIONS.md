# Decisions

The task was run unattended; the interpretations chosen at ambiguous points are recorded here.

## General

- **K-001 Location:** The handbook was written to the `pcb-el-kitabi/` folder at the root of the `PCBDesignWClaude` repository (the English edition is in `pcb-handbook/`). No commit/push was made; the user will decide.
- **K-002 File names:** The 17 topics in the task were mapped one-to-one, in order, to the files `01-…` – `17-…`; the prefixes are the same as in the task list (STK, PLC, PWR, GND, HS, RF, XTL, SMPS, ESD, THM, VIA, DFM, DFA, SLK, MEC, TST, EST).
- **K-003 ID format:** `[PREFIX-NNN]`, three digits, starting at 001 in each file.
- **K-004 Rule target:** To leave a safe margin over the total target of ≥150, ~190 rules were planned; GND, PWR, HS, RF, DFM and SMPS are denser.
- **K-005 Parallel work:** The topics were split across 7 research agents (A: STK/GND/VIA, B: PWR/SMPS/THM, C: HS/XTL/ESD, D: RF/PLC, E: DFM/DFA, F: SLK/MEC/TST/EST, G: visual audit guide). Merging, the checklist, the glossary, the sources and the validation were done by the main agent.
- **K-006 Manufacturer values:** Because the user's lab (METU PowerLab) uses the PCBWay standard-price class, the DFM numeric values are given at least for JLCPCB **and** PCBWay, with access dates.
- **K-008 No Reddit access:** reddit.com (including old.reddit) is closed in this environment by a security restriction, both to the web tools and to the browser. Therefore Reddit example links could not be verified and were not written. The examples and validation step 6 were moved to "layout review" threads of the same kind (KiCad forum, EEVblog forum, All About Circuits, etc.). The spirit of the task (comparison with a real layout + expert criticism) is kept; only the source type changes.
- **K-007 Visual examples:** No images were copied; only link + description. No link that could not be verified was written; in rules where no example was found the "Example" field was left as "—" (the template treats this field as optional).

## Agent decisions

Each research agent's own interpretation decisions and the source conflicts it found (original notes, `../pcb-el-kitabi/_calisma/kararlar-*.md` (Turkish working notes; they exist only in the Turkish edition)):

### Agent A — STK, GND, VIA

#### Scope and boundaries
- The return via (GND via at a layer change) was written into GND-009, and "via count/symmetry at a layer transition" into VIA-007; the two rules reference each other.
- Thermal vias were left to THM, minimum hole/annular ring/edge distance to DFM. VIA-008 (aspect ratio) and VIA-009 (via size selection) were kept as design choices, with "see DFM" added for limit values; there may be partial overlap with DFM.
- Decoupling capacitor via placement was left to PWR (GND-015 covers only the GND pin connection).
- The edge via fence (GND-011) and stitching spacing (GND-010) may overlap with the "via fence" in the RF section; the RF details were left to RF.
- The mandatory plane gap under an isolation barrier (the GND-005 exception) was left to the ESD/isolation topic.
- STK-009 in the first draft (analog/digital partitioning discipline) was removed because it clashed with GND-008; a "reference plane not filled / partial zone" rule was written in its place.

#### Interpretation decisions
- STK-001: Because KiCad layer colours change with theme/version (forum sources contradict each other), guessing the layer from colour was forbidden; the auditor asking for the layer information was made a rule.
- STK-007 microstrip widths (≈2.76 mm @1.5 mm, ≈0.33 mm @0.2 mm, εr 4.4, 50 Ω) were calculated by the agent with the IPC-2141 approximate microstrip formula; there is no opened source URL for this formula. The exact value should be verified with the manufacturer's calculator.
- VIA-006 via current: with the IPC formula given by Sierra Circuits (I = K·ΔT^0.44·A^0.725, K=0.048 outer / 0.024 inner), the agent's own calculation for a 0.3 mm hole + 18 µm wall (JLCPCB average) is ≈1.4 A / ≈0.7 A (10 °C). As the design value, the conservative ≈0.5 A/via found in content linked from the JLCPCB guide was chosen. On the Sierra page the exponent 0.725 appears misprinted as "0.7,5"; 0.725, consistent with IPC tradition, was used.
- GND-010 λ/20: the wavelength was calculated inside the dielectric (Dk 4.4) (1 GHz → ≈7.2 mm). For the knee frequency the 0.35/t_r relation from TI SNLA426 was used (Atlas PCB gives 0.5/t_r — conflict; the lower frequency gives looser spacing, the TI value was chosen).
- In GND-015 no numeric standard was found for the pad–via distance; the wording "shortest" and an inductance value of ≈1 nH/mm (from content linked from the JLCPCB guide) were used.
- The VIA-005 dog-bone/via-in-pad threshold was defined not by BGA pitch but by JLCPCB's BGA clearance rules (no verified source for a pitch threshold).
- The claim in VIA-002 that "0805 and larger are less sensitive" comes only from forums; the rule states that it is not verified.

#### Source conflicts
- **Stitching via – signal via distance:** TI SNLA426 (PCIe Gen5) ≤50 mil; TI SPRAAR7J ≤200 mil. Condition: data rate. Both were written into GND-009 with their condition.
- **4-layer stack-up:** the Bogatin/Hartley line (SIG–GND–GND–SIG, no power plane) ↔ Altium/Peterson (power layer for high current/many rails). In STK-004 it was made conditional on current and number of rails. Hartley's primary source could not be opened; the view was taken via the Altium article.
- **AGND/DGND split:** TI/ADI/Olney prefer a single plane; many ADC datasheets recommend a split. Written in GND-005 together with the exceptions (form factor, ≥20 bit, datasheet).
- **Via tenting under BGA:** Altium recommends leaving them open for flux evacuation, Sierra Circuits recommends tenting dog-bone vias. Left in VIA-003 as "ask the assembler".
- **Via-in-pad:** Assembly sources (Eurocircuits, Benson, JLCPCB) recommend avoiding it or fill+cap; TI SNLA426 recommends via-in-pad at very high speed. Written into the VIA-001 exception (fill+cap in every case).
- **20H rule:** Traditional EMC guides ↔ LearnEMC/Shim-Hubing measurements (no benefit or increased radiation) ↔ Altium summary (limited benefit below ≈300 MHz). STK-008 was written so that the auditor does not demand 20H.
- **λ/20 calculation basis:** Atlas PCB uses the in-dielectric wavelength, RF Essentials the free-space wavelength (≈2× difference); the conservative in-dielectric value was chosen.
- **JLCPCB 4-layer stack-up:** 0.2 mm prepreg / 0.0175 mm inner copper (help-centre search summary) ↔ 0.2104 mm / 0.0152 mm (forum and GitHub). Given with "≈" in STK-006; must be verified at order time.

#### Could not be verified
- The ADI RAQ 9, RAQ 63 and MT-031 pages could not be opened because of timeouts/connection refusal; the content was taken from search results and from TI SLYT512's statements pointing the same way.
- The JLCPCB stack-up help page returned 404 when opened directly; the In Compliance Magazine page returned empty content.
- No Reddit review examples were found (search budget exhausted); in the "Example" fields only verified TI/Olney application-note figures were used, the others are "—".

### Agent B — PWR, SMPS, THM

#### Interpretation decisions
- **B-01 IPC-2221 numbers:** The widths in the tables were calculated and rounded by us with the IPC-2221A formula verified on mbedded.ninja (k = 0.048 outer / 0.024 inner, b = 0.44, c = 0.725, width = A / (1.378·oz)). Cross-checked against the ROHM Figure 5 curve (35 µm, 2 A, 20 °C → 0.53 mm; formula 0.51 mm). The default condition is 1 oz, ΔT = 10 °C (same as the METU PowerLab default); 20 °C values are also given.
- **B-02 IPC-2221 vs. IPC-2152 conflict:** IPC-2221 uses half the outer-layer constant for inner layers; IPC-2152 gives inner traces a capacity close to outer traces and takes plane proximity into account. In the rule text the conservative IPC-2221 value is given as the default; it is stated that a narrower trace may be accepted if the designer presents an IPC-2152 calculation (PWR-001/002).
- **B-03 Current-per-via conflict (PWR-005):** AN-1149: ~200 mA per standard via; ROHM: 0.3 mm via ~0.4 A (2 mm/A barrel rule); TI SLYT614: 1 via per amp (rule of thumb). All three were written; the auditor is given the conservative value and the "at least 2 vias" recommendation. Via geometry/limits were left to the VIA/DFM agent.
- **B-04 GND plane under the inductor (SMPS-010):** ROHM recommends not putting the plane directly under the inductor (eddy currents, L drop). A Signal Integrity Journal measurement shows that an unbroken plane is better for EMI (single board, buck). Decision: both views were written; with a shielded inductor + multilayer board an unbroken plane is accepted, with an open core or a datasheet keepout a gap is accepted; in both cases traces under the inductor are forbidden.
- **B-05 Thermal via tenting (THM-005):** TI SLMA002/SLUA271 say that tenting from the opposite side increases voids, and that a cap from the component side or plugging is preferred. PCBWay's standard process is "tented via", plugging costs extra (METU PowerLab rule: exposed-pad vias open on the pad side, tented on the other side). Decision: the TI order of preference was written, confirmation with the manufacturer and a fabrication note were requested; the conflict with the lab rule is reported to the main agent.
- **B-06 Thermal via spacing:** TI SLUA271 ~1.0 mm, ROHM 1.2 mm, TI SLMA002 examples 1.3–1.5 mm, JLCPCB 1.0–1.2 mm. Instead of a single number, a "~1.0–1.5 mm" range and per-source values were given.
- **B-07 Paste coverage:** TI SLUA271 gives 50–70%; the ADI/Maxim QFN note was seen as 50–80% in a search result but the page could not be opened (analog.com connection error), so only the TI value was used in the handbook.
- **B-08 Fuse/protection order (PWR-016):** The order "connector → reverse polarity → fuse → TVS" comes only from an EEVblog community discussion. A higher-tier source (TI SLVA139) supports only the series/before-load position of the reverse-polarity element; no manufacturer source was found for the fuse order. In the rule text it was marked as a "community recommendation" and the TVS detail was redirected to ESD.
- **B-09 Decoupling "shared via" (PWR-009):** No source stating directly that a shared GND via is bad could be opened (the Microchip note appeared only in a search summary). In the rule we wrote it not as independent evidence but as a consequence of Altium's mounting/path inductance explanation.
- **B-10 Heat-source distance (THM-010):** No source giving a universal mm value between an electrolytic or sensitive part and a heat source was found. No number was written into the rule; the Würth 10 °C rule was given and the auditor was told to ask for a measurement/simulation.
- **B-11 Diodes AN1157 numbers (THM-007):** The θJA values (≈120 → ≈50 °C/W) were read from the PowerDI5060 curve in AN1157 Figure 2; they are approximate and the condition (1 oz, single-layer FR-4, no heatsink) is stated in the text.
- **B-12 Kelvin split:** In the task Kelvin appears in both PWR and SMPS. PWR-014/015 cover the general shunt/remote-sense Kelvin rules; SMPS-013 covers the noise/common-path problem of the CS traces of a current-mode controller and references PWR.
- **B-13 Gate return and SMPS ground:** SMPS-017 (AGND/PGND single point) overlaps with the GND topic; its SMPS-specific aspect (datasheet recommendation, quiet component GND) was written, and "see GND" was left for the general plane rules.

#### Research constraints
- **B-14 Reddit not reachable:** `old.reddit.com` and `www.reddit.com` (and `.json`) were blocked by WebFetch; the search engine did not return any r/PrintedCircuitBoard posts either. As bad/good examples, the "suitable/unsuitable" figures in manufacturer application notes (ROHM, AN-1149, Allegro, TI) and a FEDEVEL forum review were used. In rules where no example was found the field is "—".
- **B-15 analog.com not reachable:** ADI AN-136, AN-139, "Layout for Power Designs #1: Hot Loops", "Staying Well Grounded" and the Maxim QFN note gave timeouts/connection refusals; these sources were not put in the handbook. The ADI/Würth seminar presentation could be read via we-online.com.
- **B-16 Search quota:** The session's shared WebSearch quota (200) ran out during the work. Later verifications were done only by opening previously found URLs with WebFetch (e.g. TI SLVA255, from the reference in SLYT614).
- **B-17 Mirror URL:** AN-1149 was read from a mirror that could be opened (thierry-lequeu.fr) instead of the TI site; the content is identical to the TI/National original (AN101247, 2002).

### Agent C — HS, XTL, ESD

#### Interpretation decisions
- Reddit (reddit.com, old.reddit.com, .json) could not be reached from this environment (WebFetch and WebSearch refused the reddit domain). Example links were taken from the KiCad forum, EEVblog and the "bad/good" figures in manufacturer notes. Community claims were backed by at least one manufacturer note.
- TI, ST, ROHM and Renesas PDFs were downloaded as binary with WebFetch, converted to text with local `pdftotext` and read; because ST's official AN2867 address timed out, the content was read from the Rev 10 copy at Raltron (the official address is also given as the source). Rev 10 (2015) is an old revision; the current revision (2026 Rev 24 according to a search result) may contain different wording.
- The Microchip online docs page returned 503; the information "0.5 in (12 mm)", "no trace on the opposite side" and "GND pour to the MCU GND" was taken from a search-result summary — it could not be verified directly.
- The USB 2.0 90 Ω ±15% value could not be read directly from the USB-IF specification; it is consistent with the Renesas RX71M note (which states it is based on the specification) and TI/Qualcomm/Cadence secondary sources. Espressif and TI TUSB4041I give a tighter ±10% → in the rule ±15% is presented as the specification and ±10% as some manufacturers' target.
- There are two values for the USB 2.0 intra-pair length mismatch: Renesas ≤2.5 mm, TI AM335x table ≤50 mil (≈1.27 mm). Both were given; the auditor should use the tighter one as "good" and 2.5 mm as the upper limit. The guide for the PHY/MCU in use takes precedence.
- The ">1.5×trace width" and ">5×trace width" dimensions in TI SPRAAR7 Figure 3-10 were not included in the rule because they are not explained in the text (it is unclear which dimension they refer to); only ">135° bend" was used.
- The statement "below 200 mm if the stub is unavoidable" on the TI TS3USB221A-Q1 page is most likely a unit error (200 mil may be meant); it was not used because it was judged unreliable.
- HS-014 (SPI/clock): No fixed "critical length" number was given; Altium's analysis that this rule is inconsistent was taken as the basis, and only Sigcon's driver–series-resistor stub criterion (< tr/3, < tr/6) was used as a numeric criterion.
- HS-010 (USB-C CC Rd) is partly a schematic topic; but it was taken into HS because whether two separate resistors are seen next to the connector can be checked from a screenshot.
- In HS-016 the MIPI numeric values were taken from the AMD Versal guide (FPGA-specific); it is stated that the SoC-specific guide takes precedence.
- In XTL-001 Espressif's "at least X mm from the clock pin" values are a lower limit (specific to RF SoCs) and do not contradict ST/Microchip's "as close as possible" recommendation; written as an exception.
- The 8 kV ≈30 A / ≈0.8 ns ESD input values were read from the graphs in TI SLVA680 Figure 1-1 and ROHM Figure 4 (graph reading, approximate).

#### Source conflicts
- **GND under the crystal:** ST AN2867 (Rev 10) recommends a dedicated oscillator GND area, separate from the application GND and connected to the nearest MCU GND. Espressif asks for an unbroken GND plane under the crystal and the chip, and recommends a copper-free keep-out around the crystal on the top layer. Microchip recommends surrounding it with a GND pour connected to the MCU GND. There is disagreement on EEVblog too. Decision: in XTL-004 both are acceptable; only the "no reference at all" or "slot underneath" case is an error.
- **Metal-can crystal:** AN2867 Rev 10 says the metal can should not be connected to the oscillator GND; many 4-pad SMD crystals have GND pads. Decision: the crystal datasheet governs, no finding is reported.
- **Proximity of the TVS to the connector:** TI SLVA680/SPRAAR7 and ROHM say "as close as possible to the connector". A KiCad forum reply says proximity is not required and that the order (connector→TVS→circuit) is enough. Decision: the manufacturer note applies; the forum view was noted in the exceptions field.
- **TVS position in Ethernet:** The general ESD note says close to the connector; TI SNLA387, specifically for Ethernet, recommends the PHY side of the transformer (common-mode voltage risk). Decision: in ESD-009 the PHY side applies for Ethernet, ESD-001 for the other interfaces.
- **Connector shell–GND connection:** There are options of 1 MΩ‖4.7 nF (TI E2E experience value, citing Microchip AN2587 — AN2587 could not be opened), 1 MΩ‖100 nF, ferrite or a direct connection; on EEVblog there is criticism of the ESD risk of the RC approach. Decision: in ESD-007 a floating shell is an error; the connection method depends on the product/EMC test.
- **Plane under the Ethernet transformer:** TI SNLA387 says "no metal on any layer under the transformer"; other sources have drawings that extend the chassis plane under the transformer (signalintegrityjournal, in a search summary). Decision: the TI checklist was taken as the basis; an integrated MagJack exception was added.
- **Bob Smith termination:** According to an Altium article its necessity is disputed. Decision: no rule was written; the HS-015 exception says "the PHY reference design takes precedence".
- **MIPI impedance:** AMD/Intel/Cadence 100 Ω; Toradex 90 Ω ±15%, NVIDIA 90 Ω (community). Decision: 100 Ω was given in HS-016, 90 Ω noted as an exception; the target should be asked of the user.
- **Same-layer GND pour distance:** Renesas ≥1 mm guard copper for USB; TI SNLA387 ≥3w (preferably 5w) for Ethernet MDI; Espressif recommends surrounding USB traces with GND copper (gives no distance). Decision: in HS-011, 3w–5w if no coplanar calculation was done, 1 mm for Renesas USB.

### Agent D — PLC, RF

#### Interpretation decisions

- **D-01 Espressif keepout shape (RF-004):** ESP32-S3 HDG Fig. 26 is a dimensioned drawing only (no text). I interpreted the "Min 15" dimension as the clean area, with the board cut away, on the non-feed side of the antenna being at least 15 mm; and the "Max 2" and "Max 1" dimensions as the largest allowed distances between the antenna edge and the board edge (the antenna may extend at most ~1–2 mm into the board). The "6" dimension is the depth of the antenna region. For exact dimensions, the module's current HDG figure should be checked.
- **D-02 "15 mm" in two different meanings:** Secondary sources (blog, Flux.ai) say "15 mm keepout around the antenna"; in the Espressif text 15 mm appears as clearance in every direction **inside the product enclosure**, while the 15 mm on the board is only the one-direction dimension in Fig. 26. I wrote the two separately in the handbook; I did not use the secondary sources as sources.
- **D-03 Via fence spacing (RF-012):** General rule ≤ λ/20 (Wikipedia/Archambeault etc., RF Essentials). 2.4 GHz free-space λ ≈ 125 mm → λ/20 ≈ 6 mm. Assuming εeff ≈ 3–3.5 for CPWG/microstrip on FR-4, λg ≈ 67–72 mm → λg/20 ≈ 3.4–3.6 mm. The practical target "≤ ~3 mm" is this handbook's own calculation; it does not appear directly in a source. For other ground areas Nordic's "at least every 5 mm" value was given.
- **D-04 CPWG width example (RF-009):** The official JLCPCB page gives no example width; the 0.30–0.34 mm / 0.18–0.20 mm values come from the LibreCAL project discussion (Saturn PCB Toolkit calculation + experimental result). They are presented only as a "starting value"; the designer must calculate with their own stack-up.
- **D-05 u-blox "trace–GND ≥ 2W" rule:** u-blox gives this as a general transmission-line recommendation. In CPWG the gap is already part of the impedance calculation; the rule was therefore given with the note "for microstrip design".
- **D-06 PCBWay and impedance control:** In the PowerLab standard-price specification impedance control costs extra (lab rules §2.0 "Extras"). An exception was added to RF-009 that uncontrolled fabrication with a calculated geometry can be accepted.
- **D-07 PLC-004 power-electronics exception:** LearnEMC says "all connectors on one edge"; in power converters it is common for the input and output power connectors to be on opposite edges (linear power flow, PLC-008). To reconcile the two, it was recommended to gather the control/communication connectors on one edge; this is the handbook's interpretation.
- **D-08 PLC-013 distance:** AVX's 200 mil (≈ 5 mm) value was measured under the condition of **depaneling by shearing/cutting**. For mounting holes, PowerLab's Ø 6–7 mm keepout value was used. No numeric value was found in a manufacturer source for screw holes.
- **D-09 PLC-015 IPC-2221B values:** The IPC-2221B table could not be verified online (the standard is paid). The values were cited only by reference to the PowerLab rules; no numeric value was written, and it was redirected to the DFM section.
- **D-10 Example links:** Reddit (including old.reddit.com) could not be reached with WebFetch; the JSON endpoint also returned HTML. The examples were taken from KiCad Forum and Nordic DevZone review threads. The Reddit post cited in the KiCad forum thread could not be opened, so it was not written as a source.
- **D-11 Search quota:** The shared WebSearch quota (200) in the session ran out in the middle of the work. After that, sources were added only by opening known official URLs directly (WebFetch/curl, with HTTP 200 verification); no URL that could not be opened was written. Silicon Labs AN928 (403), the ADI RF layout article (timeout) and the Murata/TDK MLCC pages (404/403) could therefore not be used.

#### Source conflicts

- **Ç-01 Ground under the antenna:** Espressif, TI, Johanson → no copper under the antenna. u-blox NINA-B3x2 (metal PIFA) → full GND under the whole module, including the antenna. Resolution: the RF-001 exception says "the module manufacturer's documentation applies".
- **Ç-02 Module position:** Espressif → feed point at the board corner (positions 1 and 5). u-blox NINA-B3x2 → corner; NINA-B3x6 (PCB trace antenna) → **middle** of an edge, with ≥ 10 mm of ground on both sides. Both were written in RF-003.
- **Ç-03 Reference layer of the RF line:** Espressif → adjacent layer (on 4 layers L2 is solid GND, no signals on L2). Nordic → on a multilayer board, keepout on the inner layers under the RF path (the reference is a plane further down). RF-011 says "follow the reference design of the chip used".
- **Ç-04 Enclosure clearance:** Espressif ≥ 15 mm in every direction; u-blox NINA-B3x2 ≥ 5 mm, NINA-B3x6 ≥ 10 mm. Differs by module; each was given with its source in RF-006.
- **Ç-05 Crystal–clock pin distance (information, belongs to XTL):** The Espressif ESP32 page says ≥ 2.7 mm, the ESP32-S3 page ≥ 2.0 mm. Not used in the handbook; for the XTL agent's information.

### Agent E — DFM, DFA

#### Interpretation decisions
- **E-01 Reddit access:** reddit.com is blocked for both WebFetch and WebSearch (including old.reddit). Example links were taken from the KiCad forum, EEVblog, AllAboutCircuits and SparkFun forums; "—" was written where none was found.
- **E-02 Scale reference:** For distance estimation in a screenshot, body dimensions derived from the package name (0603 = 1.6×0.8 mm, 0402 = 1.0×0.5 mm) and standard pitches (SOIC 1.27 mm, header 2.54 mm) were used instead of pad dimensions; since these are package definitions no separate source was cited. Pad dimensions were not used because they vary from library to library.
- **E-03 PCBWay "standard" definition:** PCBWay's capabilities page shows 4/4 mil and 0.15–0.2 mm holes as "possible", but the tolerances page counts holes below 0.3 mm as extra-cost and recommends 6/6 mil for cost. Because the user's lab uses the standard-price class, the rules are based on **PCBWay standard price = ≥0.15/0.15 mm trace/space, ≥0.3 mm hole** (consistent with PowerLab PCB_DESIGN_RULES).
- **E-04 JLCPCB values:** The 1–2 layer, 1 oz values on the JLCPCB capabilities page were taken as "standard"; multilayer values are stated separately.
- **E-05 Lab defaults:** In every rule the PowerLab default (more conservative) is given next to the manufacturer limit; it is recommended that the auditor agent classify the user's board as a "warning" against these values and as an "error" against the manufacturer limit.
- **E-06 Tombstoning / thermal relief:** Sources diverge on the fix (some thermal relief, Suntron/Reno equal copper/equal traces). The rule was written as "equalise the heat path of the two pads" and both methods were given.
- **E-07 Neck-down (DFM-020):** The only quantitative source is TI's 2/3 rule for an NSMD pad (a GaN power IC datasheet). The IPC text for general passives could not be verified; on the PCB Libraries forum an experienced designer states that he does not neck down. The rule was left at "Medium" severity and power pads were made an exception.
- **E-08 Tall-part shadowing (DFA-010):** No quantitative DFA distance was found. Sierra's test probe–part height formula (L = 0.29H + 0.7 mm) was proposed as a starting value for small parts; this is our interpretation, the source does not give it for this purpose.
- **E-09 Acid trap:** Siemens says "the real problem is the enclosed pocket, the angle is a proxy measure"; some manufacturer/forum views say the risk has shrunk in modern processes (the Cadence article could only be opened as a title, Sierra AMA search summary). Severity was kept at "Medium" because the fix costs nothing.
- **E-10 Boundary split:** The design choice of via-in-pad and tenting was left to VIA, thermal vias and exposed-pad thermal design to THM, silkscreen legibility to SLK, panel/rail/mounting hole to MEC; the DFM/DFA rules cover only the fabrication/assembly consequence and give cross-references.
- **E-11 Rule count:** DFM 20 rules (target ~19; the plane bottleneck from a row of holes was added to DFM-011 instead of a separate rule). DFA 13 rules.

#### Source conflicts
- **C-01 Copper–milled edge:** JLCPCB ≥0.2 mm; PCBWay normal 0.3 / min 0.25 mm; Sierra outer 0.25 mm, inner 0.38 mm; PowerLab 0.5 mm. → 0.3 mm applies for PCBWay, 0.5 mm for the lab.
- **C-02 Copper–V-cut:** JLCPCB ≥0.4 mm; PCBWay min 0.35 mm; PowerLab 1.0 mm. → Manufacturer limit and lab default were written separately.
- **C-03 Annular ring:** PCBWay via 0.15 mm (standard table) / 5 mil (normal process, 1 oz); JLCPCB 2-layer 0.18 mm min, 0.25 mm recommended; Sierra 4 mil. → JLCPCB's recommendation is larger; if ordering from JLCPCB, do not go below 0.18 mm.
- **C-04 Castellated hole:** PCBWay capabilities page 0.4 mm in the standard table, ≥0.5 mm (normal) in the advanced table, min 0.6 mm on the tolerances page; JLCPCB capabilities page ≥0.5 mm diameter / 0.5 mm spacing, JLCPCB blog 0.6 / 0.6 mm. → The most conservative value (0.6 mm diameter, 0.6 mm edge-to-edge) was recommended.
- **C-05 Mask bridge 2 oz:** JLCPCB 0.20 mm, PCBWay 5 mil (0.13 mm). → Must be applied separately per manufacturer.
- **C-06 Mask expansion:** JLCPCB 1:1 (the manufacturer does its own compensation), PCBWay ≥2 mil, Sierra (Altium article) 4 mil larger opening, TI NSMD total 0.1–0.14 mm. → The manufacturer's rule applies; CAD and the manufacturer must not both expand it.
- **C-07 Hole–hole:** JLCPCB via 0.2 mm / pad 0.45 mm; PCBWay via 0.28 mm / component 0.41 mm; PowerLab 0.4 / 0.5 mm.
- **C-08 Plated slot:** JLCPCB 2-layer 0.5 mm, multilayer 0.35 mm; PCBWay 0.5 mm. Non-plated: JLCPCB 1.0 mm, PCBWay 0.8 mm.
- **C-09 Fiducial edge distance:** PCBWay ≥5 mm; JLCPCB ≥3.35 mm including the clear zone (LCSC 3.85 mm from the centre); Sierra 118 mil (3 mm). → 5 mm for a PCBWay order.
- **C-10 Part–edge (assembly):** PCBWay: rail if edge–copper <3.5 mm; JLCPCB body–edge ≥2.5 mm (terms page, from a secondary summary); Sierra BGA 125 mil, small part 25 mil; the "5 mm" example in the task corresponds to the JLCPCB/PCBWay rail width (≥5 mm JLCPCB rail, 3–10 mm PCBWay rail). → The PowerLab 3.5 mm rule was taken as the basis.
- **C-11 Copper balance 15–20%:** JLCPCB bases this on IPC-6012; the IPC text could not be verified → given with a "not verified" note.
- **C-12 Pad–silkscreen:** JLCPCB 0.15 mm; PowerLab 0.1 mm; a KiCad forum user reproduced JLCPCB warnings with 0.18 mm; PCBWay gives no number.

### Agent F — SLK, MEC, TST, EST

#### Access and source constraints
- **F-01 Reddit not reachable:** reddit.com and old.reddit.com came back blocked for both WebFetch and WebSearch (domain filter). Therefore no Reddit review post was given as an example; the examples were chosen from the KiCad/EEVblog/DigiKey/SparkFun forums, Protocase PDF figures, a Murata article figure, a Tag-Connect drawing and TI EVM guides. "—" was left in rules where no example was found.
- **F-02 "(search result only)" sources:** Some URLs came back only as search results and their content was taken from the search summary (marked in `../pcb-el-kitabi/_calisma/kaynaklar-F.md`). All numeric values are backed by at least one opened (WebFetch) primary source; search-only sources were used as supporting sources.
- **F-03 LIGO checklist:** The PDF could not be opened because of a certificate error; for TST-009 the DCC page (search result) and a TI EVM guide were given together.
- **F-04 SLK-012 source:** Mirroring of bottom-side text was not found in the official KiCad manual; a KiCad GitLab issue + two KiCad forum threads were used. Since the rule is physically obvious (bottom-side print is read from below), it was allowed to rest on a community source.

#### Numeric value choices and conflicts
- **F-05 Silk min. height conflict:** JLCPCB 1.0 mm / 0.15 mm (1:6), PCBWay 0.8 mm / 0.15 mm (1:5) (2026-10). The safe value that satisfies both manufacturers was recommended as 1.0 mm / 0.15 mm. Atlas PCB's 0.8 mm for TP labels falls below JLCPCB, so it is noted explicitly in SLK-010. The 0.6 mm "minimum" claim on the EEVblog forum was not used because it is below both manufacturers' limits.
- **F-06 Silk–pad clearance:** JLCPCB 0.15 mm; EE World ≥ 5 mil (0.127 mm) general, ≥ 6 mil for BGA; Atlas min 0.15 / recommended 0.20 mm. The rule is based on the manufacturer value (0.15 mm). No pad–silk clearance was found on the PCBWay capabilities page.
- **F-07 Reading direction:** EE World "left to right + bottom to top", Atlas "read from the bottom or from the right (citing IPC-7351)", AllPCB "all horizontal". All were considered consistent with "at most two directions"; the IPC-7351 text could not be verified directly.
- **F-08 Mounting hole diameter:** The ASME B18.2.8 (AMES table) values were taken to be the same as ISO 273 (M3 3.2/3.4/3.6 mm); the full ISO 273 text is paid, so it was not read directly.
- **F-09 Keepout diameter:** No source gave "X mm keepout for M3" directly. The method of deriving the keepout from the largest diameter of the fastener (ISO 7089 washer, ISO 7045/4762 head) was chosen; no numeric tolerance margin was given (no source).
- **F-10 Hole–edge distance:** Protocase's 0.375 in (≈ 9.5 mm) value was given only as a practical rule valid "if the board is mounted close to an enclosure wall"; it is not a general rule.
- **F-11 Corner radius:** The JLCPCB blog values (R0.5–5 mm, depending on board size) as a recommendation; inner corner ≥ R0.5 mm was given as a physical limit because of the router bit (≈ 1.0 mm) (consistent with JLCPCB + MacroFab).
- **F-12 V-cut part distance:** The JLCPCB guide gives 0.4 mm for copper and 3–4 mm for parts; the copper value was left to DFM, and MEC-008 uses only the part distance. The "1.0 mm to the V-score" value in a third-party guide was not used because it contradicts JLCPCB.
- **F-13 Test pad size:** Altium/PCBCart 1.0 preferred / 0.9 acceptable / 0.8 with tooling holes; JLCPCB bed-of-nails 0.89 mm nominal (0.38–1.0 range); JLCPCB DFT blog signal 1.0–1.27, power 1.5–2.0 mm. All were given with their conditions in TST-001/003. There is no conflict between Altium's note "0.9 mm pad, 1.8 mm spacing is common" and the 2.54 mm preference; 2.54 was written as preferred, 1.27 as minimum.
- **F-14 Tall part–TP distance:** Altium: 2.0 mm to parts > 2.6 mm, 5.0 mm to parts > 6.4 mm; PCBCart: distance to parts > ~5 mm; JLCPCB DFT: min 2.0 / recommended 5.0 mm to parts > 6.4 mm. TST-003 uses the 6.4 mm / 5.0 mm value.
- **F-15 Debug connector name:** SEGGER calls the same 2×5 1.27 mm (0.05 in) connector "9-pin" in its pin-7-removed form, Arm calls it "10-pin Cortex Debug"; the rule uses "10-pin, pin 7 key".
- **F-16 USB-C overmould size:** The USB-IF specification could not be reached; a generally valid plug overmould size could not be verified. MEC-006 was left non-numeric (qualitative), and the auditor was told to ask for the cable/enclosure drawing. The ~12.5 mm value on the DigiKey forum was given only as an example.
- **F-17 MLCC–hole/break-line distance:** Murata/TDK/MacroFab give no numeric distance; no number was given in MEC-010.

#### Severity / scope interpretations
- **F-18 EST-001 (90° corner) "Cosmetic":** LearnEMC and Altium (Knack, Bogatin simulations) say the electrical effect is only significant at very high speeds (> 50 Gbps / ~70 GHz). The Altium "Slaying" article also counts the acid trap as a myth; Altium "Common DFM", on the other hand, recommends keeping the acute-angle rule. Resolution: 90° corner = Cosmetic (EST-001), < 90° acute angle = Low-severity DFM rule (EST-002).
- **F-19 EST-003 (parallel bundle) "Cosmetic":** On the grounds that crosstalk depends on height, not trace width (LearnEMC 3W myth), irregular spacing was counted as cosmetic; sensitive lines were redirected to HS.
- **F-20 EST-005 (symmetry) "Medium":** In repeated channels (e.g. the three phase legs of an ESC) symmetry was counted as a real requirement for matching; therefore it is not cosmetic.
- **F-21 EST-008 (ratsnest) "Critical":** Although it is in the aesthetics section, it was given Critical because it means an open circuit; it was kept here because the task assigned "ratsnest/unrouted remnants" to this section.
- **F-22 Asymmetric pad connection / tombstoning:** Although it seems to fit the aesthetics section, it was not written there because it is an assembly defect; it was left to DFA.
- **F-23 Board-edge copper distance, V-cut copper distance, fiducial:** Left to DFM/DFA because of the task boundaries; cross-references were given.
- **F-24 Polarity marking:** SLK-006 covers only silkscreen visibility; assembly orientation/AOI side was cross-referenced to DFA and EST-004.
- **F-25 Lab rule:** `hardware/ARCHITECTURE.md` in the repo shows that the lab uses 1.0 mm silkscreen and moves labels that have no room to F.Fab; the SLK-002 and SLK-004 exceptions were written to match this practice.

### Agent G — Visual audit guide (GOR)

- **G-001 KiCad colours from the source code:** Because the KiCad documentation does not list theme colours, the values were taken from the file `common/settings/builtin_color_themes.h` (7.0, 8.0, 9.0, master branches). The RGB values were written into the table, and a verbal description was added as well (the visual agent may not be able to measure RGB directly).
- **G-002 KiCad 9 via/pad colours:** 7.0/8.0 have `LAYER_VIA_THROUGH`, `LAYER_PADS_TH`, etc.; 9.0/master do not. From this, "in KiCad 9 vias/THT pads are drawn in the copper layer colour" was written as an **inference**; it was not verified with a KiCad 9 screenshot.
- **G-003 Rule area (keepout) colour:** The `LAYER_RULE_AREAS` (255,0,0) entry in master is in the schematic section of the file (schematic rule areas); no separate key was found for PCB keepouts. It was written as "in the colour of the layer it belongs to, hatched" (inference).
- **G-004 Altium default colours could not be verified:** The Altium documentation does not give the `Default.PCBSysColors` values. Top=red, Bottom=blue and DRC=green were verified only by forum (Fedevel) user reports; the others (Top Overlay yellow, Keep-Out magenta, Multi-Layer grey, etc.) were given as general knowledge with the label "Not verified".
- **G-005 Altium Internal Plane negative display:** No source was found (search budget exhausted, the guessed doc URL was 404). Written as general knowledge with the label "Needs verification".
- **G-006 EasyEDA Pro colours:** The official documentation has no values; that it is the same family as Standard was written as an observation/general knowledge with "Needs verification". The EasyEDA Standard values were taken from the file-format documentation (the documentation uses layer names of the form "TopPasterLayer/TopSolderLayer"; the table uses the user-interface names).
- **G-007 Footprint pads as a scale reference:** Because a 2D image shows pads, not bodies, both body (Wikipedia) and KiCad IPC-7351 nominal footprint pad values were given; preferring the pitch was recommended (pad size varies by library).
- **G-008 USB-C connector width:** The task asked for "~8.9 mm". The official GCT drawing could not be opened (timeout); 8.94 × 7.35 mm was given from a secondary distributor listing, and the 8.34 × 2.56 mm receptacle opening from Wikipedia. A search summary states that 8.94 appears in the land-pattern section of the drawing — so it was marked as "package ~8.94 × 7.35 (secondary)".
- **G-009 M3 hole 3.2 mm:** Verified from the KiCad `MountingHole_3.2mm_M3` footprint. The ISO 273 fine/medium/coarse (3.2/3.4/3.6) values could not be seen on the standard's page; they are cited only with a "general knowledge" note.
- **G-010 Surface finish colours:** The descriptions HASL silver/domed, ENIG gold/flat, OSP copper-coloured are general knowledge; the opened MCL source only confirms the flatness difference.
- **G-011 Resolution threshold "≥ 3–4 pixels":** Not a sourced standard; an engineering decision derived from antialiasing (±1 px/edge) and JPEG artefacts. The derivation is explained in the file.
- **G-012 Reddit not reachable:** reddit.com is blocked via WebFetch, WebSearch (`allowed_domains` 400 error: closed to the Anthropic user agent), the browser pane and curl (403). Redlib mirrors were caught by Anubis bot protection — not attempted, since bypassing bot protection is forbidden; archive/proxy services were not used either. On the main agent's instruction, keeping the Turkish file name `reddit-ornekleri.md` (in `../pcb-el-kitabi/_calisma/`) even though it holds no Reddit content, 7 real review threads were collected from EEVblog, the KiCad forum and Fedevel. electronics.stackexchange.com (blocked) and forum.allaboutcircuits.com (403) could not be reached.
- **G-013 Rule IDs in the example report:** Because the other agents' IDs were not final yet, placeholders such as `PWR-0xx`, `RF-0xx` were used in the example report; the main agent can replace them with the real IDs when merging.
- **G-014 GOR severity levels:** Because the GOR rules are method rules, severity was assigned by the criterion "how wrong the report will be if the rule is violated"; only GOR-005 (visible ratsnest) is a real board defect and is Critical.
- **G-015 Search budget:** The session-wide WebSearch limit (200, shared by all agents) ran out during the work; after that only known URLs were opened with WebFetch.

## Validation steps 1–5 — Results (2026-10-13)

The rule files were scanned with a script (field presence, severity/detectability values, URLs, ID uniqueness, line count, checklist coverage, cross-references).

| Step | Check | Result |
|---|---|---|
| 1 | Are all 8 template fields filled in every rule? | OK in 233/233 rules. The "Example" field is "—" in rules where no verified example was found. |
| 2 | Does every rule have at least one source link? | OK in 233/233 rules. |
| 3 | Are the rule IDs unique? | No repeated IDs, and no two rules with the same title. |
| 4 | Are there conflicting rules? | 8 cross-topic conflicts were found and resolved (table below). |
| 5 | Does the checklist contain all rules? | 233/233 rules are in the list. All "see XXX-nnn" references in the text point to existing rules. |
| 6 | Test with real review threads | 3 tests were done and 4 rules were added (below). |

Rule counts: STK 9, PLC 15, PWR 18, GND 16, HS 17, RF 16, XTL 8, SMPS 17, ESD 9, THM 12, VIA 10, DFM 20, DFA 13, SLK 13, MEC 11, TST 9, EST 10, GOR 10. **Total 233** (target ≥150).
Severity distribution: Critical 23, High 96, Medium 91, Low 21, Cosmetic 2.

## Cross-topic conflicts and their resolutions (validation step 4)

Rules written by different agents that touch the same subject were read side by side. Conflicts found:

| # | Rules | Conflict | Resolution |
|---|---|---|---|
| C-1 | VIA-006 ↔ PWR-005 | The current-per-via value (0.5 A ↔ 0.2–1 A) and the array direction ("along the flow" ↔ "perpendicular to the current") conflicted. | A common planning value was written into both rules: ≈0.5 A for a 0.3 mm hole, 0.2 A in a hot or critical design; the range given by the sources is also stated. The array was corrected to **perpendicular to the current (side by side across the trace width)**; the opposite wording in VIA-006 was an error. |
| C-2 | THM-005 ↔ VIA-003 ↔ PowerLab rule | THM-005 presented tenting thermal vias only from the bottom as if it were an error. But this is the PCBWay standard process and the PowerLab rule. | Made conditional: TI's preference (plug or cap from the component side) is kept; bottom-side tenting is not an error for holes ≤0.3 mm, only a "Low" note. |
| C-3 | EST-003 ↔ HS-011 | EST-003 says "the 3W rule is a myth", HS-011 recommended 3W based on TI. | Made conditional: 3W is a valid approximation in thin-dielectric structures where the trace width is close to the height above the plane (W≈h); the real criterion is the height above the plane h. On a 1.6 mm 2-layer board the spacing should be 2–3h. |
| C-4 | DFM-010 ↔ GND-012 ↔ EST-010 | The same finding (floating copper island) had different severities (Low/Medium/Low). | Primary rule GND-012 (Medium). DFM-010 was raised to Medium and points to GND-012; EST-010 is only for an irregular pour edge. |
| C-5 | DFM-008 ↔ EST-002 | Acid trap: Medium ↔ Low. | Primary rule DFM-008; EST-002 was raised to Medium and points to DFM-008. |
| C-6 | DFM-014 ↔ SLK-001 | Silkscreen on pads: Medium ↔ High. | Primary rule SLK-001, severity Medium (the manufacturer clips the silkscreen anyway; the risk is solderability and legibility). |
| C-7 | MEC-010 ↔ PLC-013 | MEC-010 said "no numeric distance" while PLC-013 gave ≥5 mm (AVX). | MEC-010 was redirected to the numbers in PLC-013. |
| C-8 | Example report (90) | The severities in the example report did not match those in the rules (RF-001 was under High although it is Critical) and there were `0xx` placeholders. | The real IDs were written. The principle "the severity in the report is the same as the severity in the rule; uncertainty goes in the confidence column" was added. |

For rule pairs that overlap but do not conflict, a "Primary rule for this finding: X" note was added to the secondary rule: DFA-013→VIA-001, SLK-006→DFA-002, PLC-012→DFA-003, DFM-014→SLK-001, DFM-010→GND-012, EST-002→DFM-008. Within-topic conflicts (e.g. ground under the crystal, ground under the antenna, plane under the inductor, Ethernet TVS position) were written two-sidedly in the Exceptions field of the rules concerned; details are in the agent decisions above.

## Validation step 6 — Test with real review threads

Because Reddit could not be reached (K-008), three forum threads of the same nature, with images and expert comments, were used. The method was: the images were downloaded from public forum addresses, an audit was done with the handbook (the analysis order in guide 90 and the checklist 91), and then the result was compared with a summary of the expert comments in the forum.

### Test 1 — KiCad forum, ESP32 RGB LED board (2 layers)
- **Link:** https://forum.kicad.info/t/pcb-review-request/40027 (3D render, front and back side)
- **Found with the handbook:**
  - RF-001 / RF-002 / RF-004: The module antenna stays inside the board and the 5 V pour on the front side extends under the antenna region. Confidence: Certain.
  - GND-001 / STK-003: The GND pour on the back side is split by long signal traces; the front side is a 5 V pour.
  - PLC-013 / MEC-002: There are MLCCs and LEDs right next to the corner mounting holes (C27, D30, C45).
  - ESD-001: No TVS is visible next to the USB-C. Confidence: Needs verification.
  - PWR-012: The tab copper of the SOT-223 LDO is small. Confidence: Needs verification.
  - Positive: Board name, revision and date are present (SLK-008); 3V3, VBUS and GND test points are present (TST-001/TST-007).
- **What the experts said:**
  - Antenna placement and clearance
  - Unbroken GND
  - Risk of cracking of the ceramic capacitor next to the mounting hole
  - Moving GND to the front side and routing signals on the back
  - Hiding the JLC order number
- **Comparison:** 4 of 5 expert findings were caught. The missed finding (order number placeholder) was added as **SLK-013**. The handbook also raised the ESD and LDO heat questions.

### Test 2 — EEVblog, novice BLDC driver (2 layers, TO-220)
- **Link:** https://eevblog.com/forum/projects/seeking-feedback-on-my-novice-bldc-driver-pcb-design (schematic and KiCad PCB image)
- **Found with the handbook:**
  - GND-001: The GND pour on B.Cu is split by the blue power traces.
  - PWR-001: The motor phase traces for more than 2 A are thin. Confidence: Needs verification.
  - PWR-005 / VIA-006: There are single small vias in the power path.
  - PWR-010: No bulk capacitor at the input (from the schematic).
  - SMPS-003: No local decoupling at the half-bridges, the hot loop is large.
  - SMPS-014: No gate driver, gate traces are long.
  - EST-005: The three phases are placed differently from each other.
  - PLC-001 / PLC-002: The placement is scattered.
  - SLK-001 / SLK-005 / SLK-008: Silkscreen on pads, labels on top of each other; no board name and revision.
- **What the experts said:**
  - No gate driver
  - The orientation of the TO-220s is not suitable for fitting a heatsink
  - No bulk capacitance
  - The barrel jack and header cannot carry this current
  - No GND plane, or it is split
  - Traces are thin and there are few vias
  - No mounting holes
  - Test points should be THT
  - No project name and date
  - The placement is scattered
- **Comparison:** 7 of 10 expert findings were caught. The missed findings were added:
  - **PWR-018:** The connector's current rating is insufficient.
  - **THM-012:** Heatsink mounting for the TO-220 is not planned.
  - **MEC-011:** The board has no mounting holes at all.
  
  Because the THT test point suggestion is a matter of preference, no separate rule was written; TST-003 covers it. The handbook also found the channel symmetry (EST-005).

### Test 3 — Fedevel, 2-phase buck (LTC3868, 4 layers)
- **Link:** https://fedevel.com/forum/schematic-design-pcb-layout/16381-buck-converter-layout-review (schematic and top-layer image)
- **Found with the handbook:**
  - SMPS-001 / SMPS-002: The input ceramics (C2–C5) are above the MOSFET row; the GND return may pass through a via and another layer. Confidence: Likely.
  - SMPS-009: The arrangement of the inductor and the output capacitors is problematic.
  - SMPS-017 / GND-005: The schematic has separate GND and GND1 symbols; the ground separation strategy is unclear. Confidence: Needs verification.
  - SMPS-005: Switch node (SN1/SN2) copper area.
  - GOR-002: Only the top layer is visible; images of the bottom and inner layers should be requested.
  - Positive: An "OBSERVE POLARITY" silkscreen warning (SLK) and corner mounting holes (MEC-001) are present.
- **What the experts said:**
  - The passives in the switching loop should be on the same side as the power parts (because of via inductance).
  - Rotate the inductor and bring Cout closer to the transistor GND.
  - A screenshot was requested for the review.
  - The AGND/PGND question was left unanswered.
- **Comparison:** All 3 of the 3 expert findings were caught (SMPS-002, SMPS-009, GOR-010). The handbook answers the AGND/PGND question left unanswered by the experts with SMPS-017 and GND-005. No missing rule was found.

### Test summary
| Test | Expert findings | Caught with the handbook | Rules added |
|---|---|---|---|
| 1 KiCad ESP32 LED | 5 | 4 | SLK-013 |
| 2 EEVblog BLDC | 10 | 7 | PWR-018, THM-012, MEC-011 |
| 3 Fedevel buck | 3 | 3 | — |
| **Total** | **18** | **14 (78%)** | **4** |

With the 4 added rules, all 18 expert findings now correspond to a rule in the handbook. The remaining four candidate threads (`../pcb-el-kitabi/_calisma/reddit-ornekleri.md` (Turkish working notes; they exist only in the Turkish edition)) can be used for further tests later.

**Limitation:** The main agent that did the audit had seen the summary of the expert comments before the audit. Therefore the catch rate is not the result of an independent, blind test; it should be read as an upper bound.

### Test-related source notes
- JLCPCB's "How to mark on PCB?" page (updated 22 May 2026, accessed 2026-10-13) now says that no marking is added to the board by default. SLK-013 was written accordingly.
- The ratings of the PJ-002A barrel jack (2.5 A / 24 Vdc) were taken from the Same Sky datasheet (2025-03 revision).
- The TO-220 mounting rules were taken from onsemi AN1040. These two PDFs were read after converting them to text locally with `pdftotext`.
- The JST XH datasheet could not be read because it is encoded; it was not used as a source.
