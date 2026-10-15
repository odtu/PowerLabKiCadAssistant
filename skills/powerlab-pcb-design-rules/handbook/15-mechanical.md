# 15 — Mechanical (MEC)

Mechanical rules decide whether the board "fits" the enclosure, the screws, the cables and the panel; an electrically flawless board can become unusable because a screw head crushes a trace or a connector does not reach its panel cut-out. Some of these rules cannot be confirmed from the image alone: the auditor should ask the user for the screw size, the enclosure (box) drawing and the mounting method. Fabricator clearances from copper to the board edge and to the V-cut line belong to DFM; connector placement strategy belongs to PLC.

### [MEC-001] Mounting hole diameter does not match the screw size

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** Compare the diameter of the round hole(s) in the corners with a known dimension (2.54 mm header pitch, 1.6 mm 0603 pad length): for M3 the hole should be ~1.3 times the 2.54 mm pitch. Flag it if the hole looks smaller than the screw (e.g. ~2.5 mm for M3) or if "mounting" holes of different diameters are mixed on the board. Ask the user for the screw size.
- **Why it matters:** In a hole that is too tight the screw does not go in or strips the plating; in a hole that is too wide the board shifts and the connector loses alignment with the panel cut-out.
- **Recommended fix:** ASME B18.2.8 / ISO 273 clearance hole (close / normal / loose, mm): M2 2.2/2.4/2.6; M2.5 2.7/2.9/3.1; M3 3.2/3.4/3.6; M4 4.3/4.5/4.8. Default to the "normal" series; use "close" if position tolerance is critical.
- **Exceptions:** If a press-fit/self-clinching fastener or a plastic clip is used, the hole diameter in the manufacturer's datasheet applies.
- **Example:** —
- **Source:** [Metric Clearance Hole Chart (AMES, ASME B18.2.8)](https://amesweb.info/Screws/Metric-Clearance-Hole-Chart.aspx), [ISO 273:1979 Fasteners — Clearance holes](https://www.iso.org/standard/4183.html)

### [MEC-002] No keepout ring around the screw head / washer / standoff

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** There are traces, vias, pads or component bodies around the mounting hole (on the top AND bottom side); copper is visible within the washer radius from the hole centre. For M3, mentally draw a circle of ~3.5 mm radius from the hole centre (washer outer diameter 7 mm); any copper/component inside this circle is suspect. A tall part next to the hole that blocks screwdriver/wrench access (electrolytic, heatsink, TO-220) is also an error.
- **Why it matters:** A metal screw head/washer/standoff crushes the solder mask over traces and causes a short (especially to the chassis); the tightening force cracks nearby parts; the tool cannot reach the hole.
- **Recommended fix:** Size the keepout diameter for the largest element that will be used: ISO 7089 washer outer diameter M2.5 6.0 / M3 7.0 / M4 9.0 mm; ISO 7045 M3 pan head at most 5.6 mm; ISO 4762 M3 socket head 5.5 mm. Add margin on every side for position tolerance and apply the keepout on both sides (do not route signal traces through it on inner layers either).
- **Exceptions:** An exposed GND copper ring left on purpose for chassis grounding (see MEC-003) does not count as a keepout violation; signals outside the ring must still be kept away.
- **Example:** Link: https://www.protocasedesigner.com/pdf/Protocase_Designer_Mounting_pcb.pdf — Visible error: mounting holes too close to the edge in Figure 1; correct placement in Figure 1-B.
- **Source:** [DIN EN ISO 7089 washer dimensions (fasten.it)](https://fasten.it/Norms/Norm/DIN_EN_ISO_7089), [ISO 7045 pan head dimensions (CDE Fasteners)](https://cdefasteners.com/sites/default/files/product-specs/meti7045pozi.pdf), [ISO 4762 M3 socket head (Accu)](https://accu-components.com/us/metric-cap-head-screws/3818-SSCF-M3-8-A2), [PCB Mounting Holes and What to Watch Out For (MacroFab)](https://nws.macrofab.com/blog/attaching-your-project-to-things-mounting-holes-and-what-to-watch-out-for)

### [MEC-003] Plating and grounding decision for the mounting hole is unclear

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** A plated (PTH) hole shows a copper annular ring and a solder mask opening; if the ring is connected to the GND pour, thermal spokes or a ring of vias around it are visible. An NPTH hole has no copper ring. The auditor should ask: is the enclosure metal, is the chassis grounded, does the board carry high voltage?
- **Why it matters:** In a grounded metal enclosure the GND–chassis connection determines EMC shielding; a wrong connection creates a ground loop or, at high voltage, a safety/isolation problem.
- **Recommended fix:** Make the decision explicit: (a) direct GND (plated, ring with mask opening, vias in the ring); (b) to chassis through a capacitor and/or a ~1 MΩ resistor (RF connection, DC isolation); (c) isolated NPTH. Draw NPTH on the mechanical layer; JLCPCB NPTH diameter ≥ 0.50 mm (accessed 2026-10).
- **Exceptions:** With a plastic enclosure and nylon screws the choice does not matter for EMC; on high-voltage boards an isolated hole needs clearance/creepage distance (see PWR/DFM).
- **Example:** —
- **Source:** [Everything you need to know about drilling PCB mounting holes (Cadence)](https://resources.pcb.cadence.com/blog/everything-you-need-to-know-about-drilling-pcb-mounting-holes-2), [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [EEVblog Forum – Plated mounting holes: grounded or not?](https://eevblog.com/forum/projects/plated-mounting-holes-grounded-or-not/msg488137)

### [MEC-004] Mounting holes too close to the enclosure wall/edge or poorly distributed support

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** The hole centre is a few mm from the board edge and there is a panel connector on the same edge; a large board has only two holes, or all holes are on one side; the middle of the board is left as a long unsupported span.
- **Why it matters:** The bend radius of the enclosure wall and the fastener cannot reach a hole too close to the edge; unbalanced support lets the board flex under vibration and when a connector is plugged in.
- **Recommended fix:** If the board sits against an enclosure wall, keep the hole centre ≥ 0.375 in (≈ 9.5 mm) in from the edge (Protocase rule of thumb). Place holes symmetrically at the corners; add a middle support on large boards. Ask for the enclosure drawing for the exact value.
- **Exceptions:** If the board is held by a card guide, the card guide keepout applies instead of holes; take the guide width from the enclosure drawing.
- **Example:** Link: https://www.protocasedesigner.com/pdf/Protocase_Designer_Mounting_pcb.pdf — Visible error: in Figure 1-A the holes are on the same edge as the DB-9, 0.150 in from the edge; 1-B is the good example.
- **Source:** [Protocase Designer – Mounting Printed Circuit Boards](https://www.protocasedesigner.com/pdf/Protocase_Designer_Mounting_pcb.pdf)

### [MEC-005] Connector in the wrong position relative to the board edge (set back inside / overhanging without support)

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** The mating face of a connector that must be reached through the panel (USB, RJ45, DC jack, D-sub) is a few mm inside the board edge; or the connector body overhangs the edge by a long way with no support/pad under the overhanging part. In the 3D render, check how the mating face relates to the board edge line.
- **Why it matters:** A cable cannot reach a connector set back inside from the panel; a connector exactly flush with the edge jams the board in the enclosure because of tolerances; an unsupported overhanging part can break during depaneling.
- **Recommended fix:** Place the mating face of a panel connector according to the edge reference recommended in the datasheet, overhanging the edge by the panel thickness + tolerance (Protocase: a slight overhang instead of exactly flush with the edge). Do not put an overhanging part over a panel breakaway tab; the 2 mm breakaway gap in a Eurocircuits panel only accommodates an overhang the size of a micro-USB.
- **Exceptions:** Internal cable connectors (e.g. JST) do not have to be at the edge; for placement strategy see PLC.
- **Example:** Link: https://www.protocasedesigner.com/pdf/Protocase_Designer_Mounting_pcb.pdf — Visible error: connector flush with the edge in Figure 2-A; 2-B is correct.
- **Source:** [Overhanging components (Eurocircuits)](https://www.eurocircuits.com/technical-guidelines/pcb-assembly-guidelines/overhanging-components/), [Protocase Designer – Mounting Printed Circuit Boards](https://www.protocasedesigner.com/pdf/Protocase_Designer_Mounting_pcb.pdf)

### [MEC-006] No clearance for the overmold of a USB-C (or similar) plug

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** The mouth of the USB-C receptacle is inside the board edge; right in front of/next to the receptacle there are tall parts reaching to the edge, a second connector or a mounting hole (the plug's plastic overmold hits them). If a mid-mount receptacle is used, the notch from the datasheet should be visible in the board edge.
- **Why it matters:** The metal part of the plug is only a few mm long; the overmold is wider/thicker and if it catches on the panel cut-out or a neighbouring part, the plug does not seat fully and contact is intermittent.
- **Recommended fix:** Bring the receptacle mouth to the board edge (or to the datasheet reference); leave lateral clearance for overmolds between neighbouring connectors; if the panel is recessed, get the cable overmold length from the cable manufacturer. No generally applicable overmold dimension standard could be verified — ask the user for the cable and enclosure drawing.
- **Exceptions:** If the board will be used without an enclosure (development board), only check for collisions with neighbouring parts.
- **Example:** Link: https://forum.digikey.com/t/overmold-size-of-the-usb-c-male-end/70874 — Visible error: cable selection problem on a recessed USB-C port because of the overmold length (~12.5 mm limit).
- **Source:** [Overhanging components (Eurocircuits)](https://www.eurocircuits.com/technical-guidelines/pcb-assembly-guidelines/overhanging-components/), [DigiKey Forum – Overmold size of the USB-C male end](https://forum.digikey.com/t/overmold-size-of-the-usb-c-male-end/70874)

### [MEC-007] Sharp board corners / inner corner radius not defined

- **Severity:** Low
- **Detectable from image:** Yes
- **How it looks in the image:** The board outline (Edge.Cuts) has exact 90° sharp corners; the inner corners of notches/cut-outs are drawn sharp.
- **Why it matters:** A sharp outer corner chips during depaneling and handling, scratches cables/hands and does not fit the enclosure's inner radius; an inner corner comes out rounded anyway because of the router bit, and if it is left undefined an enclosure part may collide with it.
- **Recommended fix:** JLCPCB recommendation (accessed 2026-10): board < 30 mm R0.5–1.0 mm; 30–100 mm R1.0–2.0 mm; > 100 mm R3.0–5.0 mm. Draw inner corners at least R0.5 mm (≈1.0 mm router bit); if the board fits into an enclosure, match the enclosure's inner radius.
- **Exceptions:** On card-edge connector boards the corner on the connector side follows the card standard; on edges separated by V-cut, corner rounding can only be done by routing.
- **Example:** —
- **Source:** [The Smart Advantages of Rounded Corners in Modern PCB Design (JLCPCB)](https://jlcpcb.com/blog/rounded-corners-pcb-design), [How to ensure the Board Outline is correct (MacroFab)](https://help.macrofab.com/knowledge/how-to-ensure-the-board-outline-is-correct)

### [MEC-008] Panelization method does not suit the board geometry and edge parts

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** In the panel view: the V-cut line passes along a curved/irregular edge; there are parts (especially MLCCs, connectors) closer than 3 mm to the V-cut line; mouse bite holes are on an arc/curved edge or under an overhanging connector; there are no rails on the panel edge. If a single-board image has no panel information, ask the user about the assembly method.
- **Why it matters:** V-cut is only possible on a straight line, and breaking cracks the solder joints/bodies of parts at the edge; a tab in the wrong place prevents the board from separating.
- **Recommended fix:** JLCPCB (accessed 2026-10): V-cut 25°, straight horizontal/vertical only, panel ≥ 70 × 70 mm, parts 3–4 mm away from the V-cut centre. Mouse bites: 5–8 holes of 0.60 mm per set, 0.35–0.4 mm spacing, 1.6–2 mm between boards (min 1.2 mm), on straight edge segments, one set every 50–60 mm. Rail width 5–10 mm. PCBWay: ≥ 1.6 mm between boards for tab-routing, 0 mm for V-score. For copper clearance to the V-cut see DFM.
- **Exceptions:** The rule does not apply if the board is produced singly (without a panel) and assembled by hand.
- **Example:** —
- **Source:** [The Ultimate Guide to PCB Panelization (JLCPCB)](https://jlcpcb.com/blog/184-the-ultimate-guide-to-pcb-panelization:-tools-and-techniques), [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [PCBWay PCB Capabilities](https://www.pcbway.com/capabilities.html)

### [MEC-009] Component height not checked against the enclosure limit

- **Severity:** High
- **Detectable from image:** No (enclosure drawing needed)
- **How it looks in the image:** Height is not visible in a 2D image. If a 3D render is available, identify the tallest parts (electrolytic, inductor, transformer, heatsink, vertical connector) and ask the user for the enclosure's inner height, standoff height and bottom-side clearance. On the bottom side, THT lead ends also count toward height.
- **Why it matters:** The lid does not close, a part presses against the lid, or it touches a metal enclosure and causes a short/arc.
- **Recommended fix:** For each part take body + solder/lead height, subtract standoff and board thickness from the enclosure's inner height, and leave margin at the top (in the Protocase example 0.15 in ≈ 3.8 mm margin was added to the tallest part). Verify that the KiCad 3D models match the real parts.
- **Exceptions:** Development boards without an enclosure.
- **Example:** —
- **Source:** [Protocase Designer – Mounting Printed Circuit Boards](https://www.protocasedesigner.com/pdf/Protocase_Designer_Mounting_pcb.pdf)

### [MEC-010] Heavy and fragile parts not protected against board flex

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** Heavy parts such as transformers, large electrolytics and heatsinks sit in the middle of a wide unsupported span; there is no mounting hole near a frequently mated connector; MLCCs and ferrite beads are right next to a mounting hole or a V-cut/breakaway line with their long axis perpendicular to the breakaway line.
- **Why it matters:** Board flex (screw tightening, depaneling, vibration, connector insertion force) causes cracks in ceramic capacitors and fatigue cracks in solder joints; a cracked MLCC can become a short.
- **Recommended fix:** Place heavy parts and connectors that take force near mounting holes, or use extra support/stiffening; keep MLCCs away from mounting holes and breakaway lines and turn their long axis parallel to the breakaway line; if unavoidable, use soft-termination MLCCs or a board slot.
- **Exceptions:** Numeric values for breakaway lines and mounting holes are in PLC-013 (AVX: ≥5 mm to the breakaway edge; PowerLab: Ø6–7 mm keepout around M3); no numeric source was found for heavy-part support, so ask the assembly house for its DFM rule.
- **Example:** Link: https://article.murata.com/en-eu/article/layout-helps-prevent-chip-mlcc-from-cracking — Visible error: in the article's figure, of the MLCC positions near the breakaway line A gets the most stress and B and D the least; orienting parallel to the breakaway line is the most effective measure.
- **Source:** [Layout helps prevent chip MLCC from cracking (Murata)](https://article.murata.com/en-eu/article/layout-helps-prevent-chip-mlcc-from-cracking), [TDK FAQ – flex crack countermeasures](https://product.tdk.com/en/contact/faq/capacitors-0089.html), [PCB Mounting Holes and What to Watch Out For (MacroFab)](https://nws.macrofab.com/blog/attaching-your-project-to-things-mounting-holes-and-what-to-watch-out-for)

### [MEC-011] The board has no mounting holes at all

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** Inside the board outline (Edge.Cuts), at the corners or edges, there is no large unplated/plated hole (~3.2 mm for M3); the board is filled only with connectors and parts.
- **Why it matters:** The board cannot be fixed to an enclosure or standoffs; connector mating force and vibration load the solder joints and connector pads (see MEC-010). Protocase describes fixing the board to the enclosure with standoffs and screws through holes as the basic method.
- **Recommended fix:** Ask the user how the board will be fixed. If it will be mounted in an enclosure or on standoffs, add holes at least at the corners (typically 4 on a rectangular board); put extra holes next to heavy parts and frequently mated connectors. For hole–edge distance and keepout see MEC-002, MEC-004.
- **Exceptions:** Modules/daughter boards carried by board-to-board connectors, boards that slide into a card guide, castellated modules and shields that plug onto a development kit.
- **Example:** Link: https://eevblog.com/forum/projects/seeking-feedback-on-my-novice-bldc-driver-pcb-design — Visible error: the power board has no mounting holes; the experts recommend adding them.
- **Source:** [Protocase Designer — Mounting Printed Circuit Boards](https://www.protocasedesigner.com/pdf/Protocase_Designer_Mounting_pcb.pdf), [MacroFab — PCB Mounting Holes and What to Watch Out For](https://nws.macrofab.com/blog/attaching-your-project-to-things-mounting-holes-and-what-to-watch-out-for)
