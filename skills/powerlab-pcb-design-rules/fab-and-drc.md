## 2. Fab limits and DRC values (PCBWay)

### 2.0 Standard-price spec (default for every board)

These are the PCBWay quote-form defaults. Staying inside them avoids surcharges.

| Quote option | Standard (use this) | Costs extra — ask first |
|---|---|---|
| Layers | **2** | 4+ (use 4 only when routing, EMI or the power stage really needs it) |
| Material | FR-4, TG 150–160 | High-TG, Rogers, aluminium, HDI |
| Thickness | **1.6 mm** | Anything else |
| Min track/spacing | **6/6 mil (0.15 mm) or larger** | 5/5, 4/4, 3/3 mil |
| Min hole size | **0.3 mm or larger** | 0.25, 0.2, 0.15 mm |
| Solder mask | **Green** (red, yellow, blue are also free) | Other colours |
| Silkscreen | **White** (black also free) | — |
| Surface finish | **HASL lead-free** | ENIG, ENEPIG, hard gold, etc. |
| Via process | **Tented vias** | Plugged vias |
| Finished copper | **1 oz** outer, 1 oz inner | 2 oz and up |
| Extras | none | Castellated holes, edge plating, impedance control, blind/buried vias, gold fingers, removing the product number |

Cost-driven design habits:
- Keep boards compact. Price scales with area.
- Before asking for 2 oz copper, first try wider pours, parallel copper on both outer layers, and via arrays (§3.3, §3.5).
- Lead-free HASL handles 0.5 mm pitch QFNs and exposed pads fine for prototypes. Propose ENIG only for BGA, pitch below 0.5 mm, or very large exposed pads that must be flat, and ask first.

### 2.1 Board

| Item | PCBWay limit | Lab default |
|---|---|---|
| Layers | 1–14 | **2** (4 if justified and approved) |
| Thickness | 0.2–3.2 mm | **1.6 mm** |
| Thickness tolerance | ±10 % (t ≥ 1.0 mm), ±0.1 mm (t < 1.0 mm) | — |
| Outline tolerance | ±0.2 mm CNC routed, ±0.5 mm V-score | Keep mechanical fits ≥ 0.3 mm loose |
| Min board size | 3 × 3 mm (≥ 20 mm is "normal process") | ≥ 20 mm per side |
| Outer copper | 1–8 oz (surcharge above 1 oz) | **1 oz**; 2 oz only when the current requires it (§3.3) and the user approves |
| Inner copper | 1 / 1.5 / 2 / 3 / 4 oz | 1 oz |
| Surface finish | HASL, LF-HASL, ENIG, OSP, ENEPIG, … | **HASL lead-free** |

### 2.2 Tracks and spacing (per copper weight, "normal process")

| Copper | Width/space min (standard price) | **Lab default width/space** |
|---|---|---|
| 1 oz (35 µm) | 6 / 6 mil (0.15 / 0.15 mm) | **0.20 / 0.20 mm** |
| 2 oz (70 µm) | outer 7 / 8 mil (0.18 / 0.20 mm), inner 6 / 8 mil | **0.25 / 0.25 mm** |
| 3 oz (105 µm) | outer 10 / 12 mil (0.25 / 0.30 mm), inner 8 / 11 mil | **0.30 / 0.35 mm** |

**Hard floor: 0.15 mm / 0.15 mm (6/6 mil).** Anything finer puts the order into a surcharge tier. PCBWay can technically make 4/4 mil, but don't use it.
Hatched/grid copper needs larger values (1 oz: 9/11 mil). Prefer solid pours.

### 2.3 Drills, vias, annular ring

| Item | PCBWay limit | Lab default |
|---|---|---|
| Min drill | **0.3 mm** at standard price (0.15–0.25 mm costs extra) | 0.3 mm |
| Max drill | 6.0 mm (larger is milled) | — |
| Aspect ratio (thickness : drill) | ≤ 8 normal | ≤ 6 (1.6 mm board → drill ≥ 0.3 mm) |
| Annular ring, via (1 oz / 2 oz / 3 oz outer) | 5 / 7 / 8 mil (0.13 / 0.18 / 0.20 mm) | **0.15 mm** (1 oz), 0.2 mm (2–3 oz) |
| Annular ring, component hole (1 / 2 / 3 oz) | 10 / 12 / 14 mil (0.25 / 0.30 / 0.36 mm) | 0.3 mm (1 oz), 0.36 mm (2–3 oz) |
| Hole-to-hole, vias (≤ 0.45 mm) | 11 mil (0.28 mm) | 0.4 mm |
| Hole-to-hole, component holes | 16 mil (0.41 mm) | 0.5 mm |
| Inner-layer hole-to-copper (4 L / 6 L) | 7 / 8 mil (0.18 / 0.20 mm) | 0.25 mm |
| PTH finished-hole tolerance | ±0.08 mm | Size holes for lead + 0.2–0.3 mm |
| NPTH tolerance | ±0.05 mm | — |
| Plated slot width | ≥ 0.5 mm | ≥ 0.6 mm |
| Non-plated slot width | ≥ 0.8 mm | ≥ 1.0 mm |
| Castellated holes | Ø ≥ 0.5 mm, edge-to-edge ≥ 0.3 mm | Ø 0.6 mm |
| Via plugging (for via-in-pad) | Ø 0.2–0.4 mm, board 0.4–2.4 mm, **costs extra** | Don't use; tented vias are standard |

**Standard lab vias:**
- Signal: **0.3 mm drill / 0.6 mm pad**
- Power / thermal: **0.4 mm drill / 0.8 mm pad** (2 oz: 0.4 / 0.85 mm)

### 2.4 Solder mask and silkscreen

| Item | PCBWay limit | Lab default |
|---|---|---|
| Mask expansion (opening beyond pad) | ≥ 2 mil (0.05 mm) | 0.05 mm |
| Mask bridge (web), < 2 oz, green | 4 mil (0.10 mm) | 0.10 mm |
| Mask bridge, < 2 oz, black/other colours | 4.5 mil (0.115 mm) | 0.12 mm |
| Mask bridge, ≥ 2 oz | 5 mil (0.13 mm) | 0.13 mm |
| Silkscreen line width | 0.15 mm | 0.15 mm |
| Silkscreen text height | 0.8 mm | **1.0 mm** (1.2 mm for connector/polarity labels) |
| Width : height ratio | 1 : 5 recommended | 0.15–0.2 mm stroke for 1.0 mm text |
| Silk over pads / exposed copper | not allowed | keep ≥ 0.1 mm clear |

Green, red, yellow and blue mask, and white or black silk, cost nothing extra.

### 2.5 Board edge and panelization

| Item | PCBWay limit | Lab default |
|---|---|---|
| Copper to CNC-routed edge | 0.25 mm (0.20 mm "medium") | **0.5 mm** |
| Copper to V-score line | — | 1.0 mm |
| Board-to-board gap, tab routing | 1.6 mm | 2.0 mm |
| Board-to-board gap, V-score | 0 mm | 0 mm |
| V-score board thickness | 0.6–2.4 mm | — |

### 2.6 KiCad setup (Board Setup → Design Rules → Constraints)

Defaults for a **1 oz** board. For 2 oz or 3 oz, take the values from the tables above.

The board minimums are the **PCBWay standard-price floor** (§2.2), so DRC only rejects what can't be made without a surcharge. The **net classes** below carry the lab defaults, and that's what tracks are routed at. Signal tracks are 0.15 mm (the Default class) on 1 oz; on 2 oz they are 0.2 mm, with the 0.18 mm outer-layer floor kept for neck-downs at fine-pitch pins. Give a signal more only where it carries current or there's room and a reason. Power and GND tracks are sized for their current.

Put these values in **Board Setup** itself (Constraints and Net Classes), not only in a `.kicad_dru` rule: `set_design_rules` with `preset: "powerlab"` sets them, and `create_netclass` the Power and GND classes. Check them with `get_design_rules` before routing. A board whose Board Setup still shows KiCad's defaults (minimum clearance 0, track 0.2, annular ring 0.1, via 0.5 mm) isn't set up.

| KiCad constraint | Value |
|---|---|
| Minimum clearance | 0.15 mm |
| Minimum track width | 0.15 mm |
| Minimum connection width | 0.15 mm |
| Minimum annular width | 0.15 mm |
| Minimum via diameter | 0.6 mm |
| Copper to hole clearance | 0.25 mm |
| Copper to edge clearance | 0.5 mm |
| Minimum through hole | 0.3 mm |
| Hole to hole clearance | 0.4 mm |
| Minimum uvia / blind vias | not allowed |
| Solder mask expansion | 0.05 mm |
| Solder mask min web width | 0.1 mm |
| Minimum silk text height | 1.0 mm |
| Minimum silk thickness | 0.15 mm |

**Default net classes:**

| Net class | Track | Clearance | Via (drill/pad) | Use for |
|---|---|---|---|---|
| Default | 0.15 mm | 0.2 mm | 0.3 / 0.6 | Logic and low-current signals |
| Power | sized for current (≥ 0.5 mm) | 0.3 mm | 0.4 / 0.8 | Supply rails, DC bus, phase outputs (schematic: red, thick — §1.6) |
| GND | sized for current (≥ 0.5 mm) | 0.3 mm | 0.4 / 0.8 | All ground nets (schematic: blue, thick — §1.6) |
| HV | sized for current | per voltage (§3.3) | 0.4 / 0.8 | Any net > 50 V |

Run DRC with zones refilled before calling any layout done. Zero unexplained errors. Waivers are documented in the project.
