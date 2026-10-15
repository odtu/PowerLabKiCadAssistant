# 11 — Vias (VIA)

Vias provide connections between layers, but their proximity to pads, their tenting method, their count and their size directly affect assembly yield, current capacity and signal integrity. This section covers design choices about via usage. For manufacturer limits such as minimum hole/annular ring see DFM; for thermal vias see THM; for return/stitching vias see GND-009–GND-011.

### [VIA-001] Open (unfilled) via inside an SMD pad — solder wicking

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** A via hole inside the copper of an SMD pad (passive, IC lead, BGA ball) or cutting its edge: a dark/white circular hole within the pad-coloured area. Since the pad has no mask, the via has no mask either. If the fabrication note does not say "filled & capped / POFV", the via must be assumed open.
- **Why it matters:** An open via wicks solder away from the pad by capillary action; the joint may be left without solder, or a solder ball can form on the back of the board and cause a short circuit. Wicking varies from joint to joint, which makes it unreliable.
- **Recommended fix:** Move the via outside the pad and connect it with a short trace (see VIA-002). If it must stay in the pad, request "epoxy filled & capped" (POFV); at JLCPCB this process is defined for 0.15–0.55 mm holes and is the default at 6+ layers (accessed 2026-10). Plugging with ink cannot be applied to via-in-pad.
- **Exceptions:** Thermal pad vias of QFN/power packages (see THM). TI SNLA426 recommends via-in-pad on very high-speed (PCIe Gen5) lines to reduce inductance; filling+capping is also required in that case.
- **Example:** —
- **Source:** [JLCPCB — Five Via Finishes](https://jlcpcb.com/blog/five-via-finishes), [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [Electronic Design — Via-In-Pad Guidelines for PCBs](https://www.electronicdesign.com/analog/pad-guidelines-pcbs), [Eurocircuits — Solder Escape/Wick](https://www.eurocircuits.com/pcb-assembly-guidelines-solder-escape-wick/)

### [VIA-002] Via too close to an SMD pad, no solder mask dam in between

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** The via ring touches the pad edge or looks fused to the pad (no trace, the via is stuck directly to the pad); on the mask layer the pad and via openings form a single merged opening. Seen especially on one pad of 0402/0603 passives.
- **Why it matters:** Solder flows from the pad into the via (weak/dry joint); a via on one pad draws heat away, and when the two ends melt at different times this leads to tombstoning on small passives.
- **Recommended fix:** Leave at least 0.25 mm between the pad edge and the via ring edge (the general consensus reported by Eurocircuits), with a mask dam in the gap; connect the via with a short trace. If the distance cannot be achieved, fill the via with resin and cover it with mask.
- **Exceptions:** Filled and capped (POFV) vias; parts with large pads (according to forum opinion, 0805 and above are less sensitive — not verified with a high-level source).
- **Example:** —
- **Source:** [Eurocircuits — Solder Escape/Wick](https://www.eurocircuits.com/pcb-assembly-guidelines-solder-escape-wick/), [Altium — When to Use Tented vs. Untented Vias](https://resources.altium.com/p/when-use-tented-vias-your-pcb-layout)

### [VIA-003] Unsuitable via tenting choice, or via too large to be tented

- **Severity:** Medium
- **Detectable from image:** Partly (the mask layer must be visible or the fab note must be known)
- **How it looks in the image:** In the 3D/Gerber mask image, via rings are exposed in shiny tin/gold colour (not tented); or vias with holes larger than 0.5 mm are marked as tented. In KiCad, check the front/back "tent" setting in the via properties and the openings on the mask layer.
- **Why it matters:** With HASL, open vias can bridge to neighbouring exposed copper; on large vias the mask does not close completely, and contamination and corrosion form in the remaining gap. Tenting from one side leaves the hole wall on the other side unprotected.
- **Recommended fix:** By default, tent vias from both sides. The hole of a via to be tented is ideally ≤0.4 mm at JLCPCB, at most 0.5 mm (accessed 2026-10); Sierra Circuits recommends ≤12 mil (0.305 mm). The distance between an untented via and neighbouring exposed copper at JLCPCB is ≥0.2 mm (ENIG for less).
- **Exceptions:** Vias used as test points (see TST); Altium recommends leaving vias under a BGA open for flux escape, while Sierra recommends tenting BGA dog-bone vias — ask the assembler.
- **Example:** —
- **Source:** [JLCPCB — PCB Via Covering](https://jlcpcb.com/help/article/pcb-via-covering), [Sierra Circuits — Via Tenting Design Rules](https://www.protoexpress.com/kb/pcb-via-tenting-design-rules-and-fabrication-notes), [Altium — When to Use Tented vs. Untented Vias](https://resources.altium.com/p/when-use-tented-vias-your-pcb-layout)

### [VIA-004] Open via under a metal-bodied part

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** There is an untented via (shiny ring) or exposed copper inside the courtyard/silkscreen outline of a USB/RJ45 connector shell, crystal can, RF shield, heatsink or metal-bodied inductor. In the 3D view the via sits right under the metal body.
- **Why it matters:** The metal body can touch the open via and cause a short circuit; since the mask is thin at the via edge, mask alone does not always provide sufficient insulation (community opinion).
- **Recommended fix:** Do not place vias under a metal body; if unavoidable, tent them from both sides or apply fill+mask, and respect the keep-out area in the part's datasheet.
- **Exceptions:** If the body is connected to the same net (e.g. GND) and the via is also GND, there is no short-circuit risk (solder flow should still be checked).
- **Example:** —
- **Source:** [Sierra Circuits — Via Tenting Design Rules](https://www.protoexpress.com/kb/pcb-via-tenting-design-rules-and-fabrication-notes), [KiCad Forum — Design PCB with USB port (community)](https://forum.kicad.info/t/design-pcb-with-usb-port/20754)

### [VIA-005] Fanout method and via-in-pad choice on a fine-pitch BGA

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** The BGA pad array shows either the "dog-bone" pattern, where a short diagonal trace runs from each pad to a via, or a pattern with the vias directly in the pad centres. At 0.5 mm pitch, if there is no room for dog-bone vias between the pads, the vias appear to overlap/touch the pads.
- **Why it matters:** In the JLCPCB example, a dog-bone cannot be manufactured on a 0.5 mm pitch BGA with 0.09 mm trace/space; via-in-pad is required and this via must be filled+capped (VIA-001).
- **Recommended fix:** If the JLCPCB clearances between pads can be met, use dog-bone (via copper–BGA pad ≥0.10 mm; hole–BGA pad ≥0.35 mm on 2 layers; trace–pad ≥0.10 mm; accessed 2026-10). If not, e.g. at 0.5 mm pitch, a 0.25 mm pad + a 0.15/0.25 mm filled via-in-pad in the centre (JLCPCB example); write "epoxy filled & capped" in the fab note. At JLCPCB, POFV is free for 6–20 layers and charged for 4 layers (2022 announcement; should be verified on the order page in 2026-10).
- **Exceptions:** Structures using microvias (HDI) (see VIA-010).
- **Example:** —
- **Source:** [JLCPCB — BGA Design Guidelines](https://jlcpcb.com/help/article/bga-design-guidelines---pcb-layout-recommendations-for-bga-packages), [JLCPCB — Free Via in Pad on 6-20 Layer PCBs with POFV](https://jlcpcb.com/blog/Free-Via-in-Pad-on-6-20-Layer-PCBs-with-POFV)

### [VIA-006] Insufficient via count on a current-carrying path

- **Severity:** High
- **Detectable from image:** Partly (the current value must come from the user)
- **How it looks in the image:** A wide power trace or pour (e.g. 2–5 mm) drops to a single small via when changing layer; or there are only 1–2 vias at a power input/MOSFET/inductor connection. Visual cue: the wide copper forming a "bottleneck" at the via.
- **Why it matters:** Via current is limited by the copper cross-section of the hole wall (IPC-2152 approach: the via cross-section should equal that of the connected trace). A single via overheats, causing voltage drop and, in the long term, a risk of cracking.
- **Recommended fix:** For current per via, sources give values between 0.2 A (TI AN-1149) and ~1 A (TI SLYT614) (see PWR-005); this handbook's planning value is ≈0.5 A for a 0.3 mm hole (JLCPCB guide); in hot/critical designs use 0.2 A. Required count N ≥ I / I_via. Calculation example (agent's own calculation, IPC-2221 formula, 10 °C rise): 0.3 mm hole + 18 µm wall copper (JLCPCB average) ≈26 mil² → ≈1.4 A with the outer-layer coefficient, ≈0.7 A with the inner-layer coefficient. Arrange vias in a row perpendicular to the current direction (side by side across the trace width); with vias lined up one after another in the flow direction, the first via carries most of the current.
- **Exceptions:** For thermal via arrays see THM. Measurements show that vias run cooler than the connected trace; in critical designs use the Sierra Circuits via calculator and the plating thickness guaranteed by the manufacturer (PCBWay normal: 18–25 µm).
- **Example:** —
- **Source:** [Sierra Circuits — How to Design a Via with Current Carrying Capacity](https://www.protoexpress.com/blog/how-to-design-via-with-current-carrying-capacity/), [JLCPCB — Ground Plane and Power Plane Guide](https://jlcpcb.com/blog/circuit-board-ground-plane-and-power-plane-guide-2026), [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), [PCBWay PCB Capabilities](https://www.pcbway.com/capabilities.html), [Signal Integrity Journal — Vias Are Cooler Than We Think](https://signalintegrityjournal.com/articles/1459-vias-are-cooler-than-we-think)

### [VIA-007] Unnecessary layer transitions on a high-speed signal, or asymmetric vias on a differential pair

- **Severity:** Medium
- **Detectable from image:** Yes
- **How it looks in the image:** More than 2 vias along the route of a highlighted clock/USB/PCIe/HDMI net; one member of a differential pair has a via while the other does not, or the vias are at different points. The trace drops to the bottom layer and immediately comes back up to get past a short obstacle.
- **Why it matters:** Every via creates a capacitive/inductive discontinuity and (with the part extending to unused layers) a stub; asymmetry in a pair produces common-mode noise. Every transition also needs a return path (GND-009).
- **Recommended fix:** Keep high-speed traces on a single outer layer if possible; the two members of a differential pair should have an equal via count and symmetric via positions (TI SNLA426). At very high speed the stub should be shorter than ≈51 mil (FR-4, ~29 GHz band); back-drilling is recommended for stubs >15 mil (PCIe Gen5 context).
- **Exceptions:** For low-speed signals (I²C, UART, GPIO) the via count is usually insignificant. For details see HS.
- **Example:** —
- **Source:** [TI SNLA426 — High-Speed PCB Layout for PCIe Gen 5, Sections 21–24](https://www.ti.com/lit/an/snla426/snla426.pdf)

### [VIA-008] Via aspect ratio exceeds the manufacturer limit

- **Severity:** Medium
- **Detectable from image:** No (board thickness and hole diameter needed)
- **How it looks in the image:** The diameter cannot be measured from the image; the auditor should ask for the via properties window (hole/ring) and the board thickness. Indirect cue: vias that look very small compared with 0.5 mm pitch pads, used on a thick (≥2 mm) board.
- **Why it matters:** In high-ratio holes the plating solution has difficulty reaching the middle of the hole; the thin wall cracks under thermal cycling.
- **Recommended fix:** Ratio = board thickness / hole diameter. PCBWay normal process ≤8 (8–10 medium difficulty), Altium general rule ≤10:1 (accessed 2026-10). On a 1.6 mm board, a ≥0.2 mm hole meets ratio 8. For laser microvias ≤1:1. For minimum hole/ring values see DFM.
- **Exceptions:** Advanced processes specifically approved by the manufacturer.
- **Example:** —
- **Source:** [PCBWay PCB Capabilities](https://www.pcbway.com/capabilities.html), [Altium — Aspect Ratios and Their Importance in Multilayer PCBs](https://resources.altium.com/p/aspect-ratios-and-their-importance-multi-layered-pcbs)

### [VIA-009] Unjustified small or mixed via sizes (cost/yield)

- **Severity:** Low
- **Detectable from image:** Partly
- **How it looks in the image:** Very small vias (rings noticeably smaller than the passive pads) on a board with plenty of free space, or 4–5 different via sizes mixed on the board. For exact values, ask for the via properties/drill table (drill report).
- **Why it matters:** Holes below 0.2 mm cost extra in the PCBWay standard process; although JLCPCB accepts a minimum of 0.15 mm, the preferred minimum is 0.2 mm (accessed 2026-10). Unnecessarily small holes increase cost and aspect ratio, and every additional size means an additional drill tool.
- **Recommended fix:** If density does not require otherwise, use ≥0.3 mm holes for signal vias and limit the number of sizes to 1–2 (signal + power). At JLCPCB the via ring must be at least 0.1 mm (preferably 0.15 mm) larger than the hole; for details see DFM.
- **Exceptions:** BGA/fine-pitch fanout areas (VIA-005).
- **Example:** —
- **Source:** [PCBWay PCB Capabilities](https://www.pcbway.com/capabilities.html), [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities)

### [VIA-010] Unnecessary blind/buried/micro vias on a standard board

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** In KiCad, blind/buried vias (Alt+Shift+V) and microvias (Ctrl+V) are separate types; the type cannot always be distinguished in a screenshot, so ask for the via properties or the drill report. Indirect cue: drill files labelled "blind/buried" on a 2-layer board, or via rings visible only on some layers.
- **Why it matters:** Blind/buried and laser microvias are advanced processes requiring sequential lamination; they increase cost and lead time. A microvia connects only the outer layer to the adjacent layer, and its aspect ratio must be ≤1:1.
- **Recommended fix:** If fanout can be done with through vias + filled via-in-pad where needed (VIA-005), use only through vias on 2–4 layer boards. HDI should be chosen only if BGA density really requires it and the manufacturer's process has been approved.
- **Exceptions:** Boards with very fine-pitch BGA/WLCSP where a through via physically does not fit (decide together with the manufacturer).
- **Example:** —
- **Source:** [KiCad 8 PCB Editor — Via types](https://docs.kicad.org/8.0/en/pcbnew/pcbnew.html), [Altium — Aspect Ratios and Their Importance in Multilayer PCBs](https://resources.altium.com/p/aspect-ratios-and-their-importance-multi-layered-pcbs)
