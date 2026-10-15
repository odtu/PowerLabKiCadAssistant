# 90 — Visual Audit Guide: Analysing a PCB from a Screenshot

> **Reader:** An AI agent that uses this handbook to audit PCB layouts **from images only** (without a netlist, project file or Gerbers).
> **Goal:** Read the colours in the image correctly, recognise components and nets, estimate the scale, apply rule files 01–17 in the right order, separate what is certain from what is a guess, and present the findings in a standard report.
> **Rule prefix:** `GOR` (the "GOR rules" section at the end of this file).
> **Access date (all web sources):** 2026-10-13.

---

## Contents

1. [Colour codes](#1-colour-codes)
2. [Clues you can read from the image](#2-clues-you-can-read-from-the-image)
3. [Scale estimation](#3-scale-estimation)
4. [Analysis order](#4-analysis-order)
5. [Limits of the image](#5-limits-of-the-image)
6. [Suggested report format](#6-suggested-report-format)
7. [Which images to request](#7-which-images-to-request)
8. [GOR rules](#8-gor-rules)
9. [Sources](#9-sources)

---

## 1. Colour codes

**General warning:** The colours below are the programs' **default** themes. In all three tools the user can change the colours (KiCad: custom theme in Preferences → Colors; Altium: Preferences → PCB Editor → Layer Colors / View Configuration panel; EasyEDA: Layer Manager). The colour → layer mapping is therefore always at the **"Likely"** confidence level; if a layer list is visible in the image (KiCad *Appearance* panel, Altium bottom layer tabs, EasyEDA *Layers* panel), verify the mapping there (see [GOR-004]).

### 1.1 KiCad (7, 8, 9) — "KiCad Default" theme

Since KiCad 6 the default theme is "KiCad Default"; the old look can still be selected as "KiCad Classic". The values were read from the built-in theme file in the KiCad source code (`common/settings/builtin_color_themes.h`, branches: 7.0, 8.0, 9.0, master). The background is dark navy/black: RGB (0, 16, 35).

| Item (KiCad name) | Default colour (RGB, alpha) | Visual description | Notes |
|---|---|---|---|
| **F.Cu** (top copper) | (200, 52, 52) | Brick red | Traces, pads and pours share the same colour |
| **B.Cu** (bottom copper) | (77, 127, 196) | Medium blue | |
| **In1.Cu** | (127, 200, 127) | Light green | First clue that gives away a 4-layer board |
| **In2.Cu** | (206, 125, 44) | Orange/brown | |
| In3.Cu / In4.Cu | (79, 203, 203) / (219, 98, 139) | Cyan / pink | 6+ layers |
| In5.Cu / In6.Cu | (167, 165, 198) / (40, 204, 217) | Lilac-grey / turquoise | |
| **F.Silkscreen** (F.SilkS) | (242, 237, 161) | Pale yellow-cream | Reference labels (R1, U3…) |
| B.Silkscreen | (232, 178, 167) | Salmon/pinkish | |
| **F.Mask** | (216, 100, 255), alpha 0.4 | Semi-transparent purple | Shows the mask **openings** (negative layer) |
| B.Mask | (2, 255, 238), alpha 0.4 | Semi-transparent turquoise | |
| F.Paste / B.Paste | (180, 160, 154) α0.9 / (0, 194, 194) α0.9 | Grey-pink / cyan | |
| **Edge.Cuts** | (208, 210, 205) | Light grey-white line | Board outline |
| **F.Courtyard** (F.CrtYd) | (255, 38, 226) | Bright magenta | Thin rectangles, component boundary |
| B.Courtyard | (38, 233, 255) | Bright cyan | |
| **F.Fab** | (175, 175, 175) | Grey | Body outline + `${REFERENCE}` |
| B.Fab | (88, 93, 132) | Dark grey-blue | |
| Margin | (255, 38, 226) | Magenta | |
| Dwgs.User / Cmts.User | (194, 194, 194) / (89, 148, 220) | Grey / blue | Dimensions, notes |
| **Ratsnest (airwire)** | (0, 248, 255), alpha 0.35 | Thin, pale cyan straight line | If visible = unrouted connection ([GOR-005]) |
| **DRC error marker** | (215, 91, 107), alpha 0.8 | Red-pink arrow/marker | |
| DRC warning marker | (255, 208, 66), alpha 0.8 | Yellow arrow/marker | |
| DRC exclusion | (255, 255, 255), alpha 0.8 | White marker | The user chose "ignore" |
| Conflict shadow | (255, 0, 5), alpha 0.5 | Red halo | Drag/placement conflict |
| Plated hole (PTH pad hole) | (194, 194, 0) | Mustard yellow | |
| **Non-plated hole (NPTH)** | (26, 196, 210) | Cyan circle | Mounting holes |
| Via hole | (227, 183, 46) | Golden yellow | |
| Via (body, KiCad 7/8 only) | Through (236, 236, 236); Blind/Buried (187, 151, 38); Microvia (0, 132, 132) | Light grey-white ring / dark gold / dark cyan | These keys were removed in KiCad 9; vias and THT pads are drawn in the copper layer colours (inferred from comparing the source files) |
| THT pad (KiCad 7/8 only) | (227, 183, 46) | Golden yellow | In layer colour in KiCad 9 |
| Stitching via (KiCad 9+/master) | (77, 204, 178) | Green-turquoise | |
| Pad net names | (255, 255, 255), alpha 0.9 | White text (on the pad) | Preferences → Display → Net names |
| Trace net names | (255, 255, 255), alpha 0.7 | Pale white text along the trace | |
| Selection | (4, 255, 67) | Bright green | |
| Locked item shadow | (255, 38, 226), alpha 0.5 | Magenta halo | |

**Zones and rule areas (keepout):**

- A **filled zone** appears as a solid fill in the layer's own colour. In KiCad the left toolbar has "show filled areas" and "show outlines only" modes; in outline mode only the zone boundary is drawn — if there is no fill in the image, consider this first ([GOR-001]).
- A zone outline can be shown as **Line / Hatched / Fully Hatched** (line / hatched edge / fully hatched). A polygon with short diagonal lines on its edge but an empty interior is usually a zone that is **unfilled or shown in outline mode**.
- **Rule area (keepout)**: according to the KiCad 8 documentation it can be shown as "hatched outline, fully hatched area or outline only". There is no separate colour key in the PCB theme file; it is drawn in the colour of the layer it belongs to (inference). An area that is cross-hatched inside and that copper does not enter → most likely a keepout under an antenna or around a mounting hole.
- KiCad warns the user before DRC or output generation if zones are not up to date; filling is done with the `B` shortcut and zones can be unfilled with `Ctrl+B`. So **unfilled** zones in a screenshot are normal and must not be counted as an error.
- **High-contrast / dimming mode:** Inactive layers may appear dimmed. Pale, greyed-out traces are not "missing"; they are just on an inactive layer.

### 1.2 KiCad Classic theme (and KiCad 5 and earlier screenshots)

If you see a black background + **green bottom copper**, it is most likely the Classic theme or a KiCad 5 era image.

| Item | Classic colour |
|---|---|
| F.Cu | Red |
| B.Cu | **Green** |
| In1.Cu / In2.Cu | Yellow / light magenta |
| F.SilkS / B.SilkS | Cyan / magenta |
| F.Mask / B.Mask | Magenta / brown |
| Edge.Cuts | Yellow |
| F.CrtYd / F.Fab | Light grey / dark grey |
| Ratsnest | White |
| DRC error / warning | Pure red / pure green (α0.8) |
| NPTH | Yellow |
| Background | Black |

### 1.3 KiCad 3D viewer

| Item | Default (RGB 0–1) | Visual description |
|---|---|---|
| Solder mask (top/bottom) | (0.08, 0.20, 0.14), α0.83 | Dark green |
| Silkscreen | (0.9, 0.9, 0.9) | White |
| Exposed copper (pad) | (0.7, 0.61, 0.0) | Golden yellow (ENIG-like) |
| Board body (FR4) | (0.2, 0.17, 0.09), α0.9 | Dark brown (visible from the edge) |
| Solder paste | (0.5, 0.5, 0.5) | Grey |
| Background | Top (0.8, 0.8, 0.9) → bottom (0.4, 0.4, 0.5) | Light grey-blue gradient |

Note: If the "use colours from board layers/stackup" option is enabled in the KiCad 3D viewer, the mask and silkscreen colours come from the *Board Setup → Physical Stackup* definition (e.g. black mask). In 3D, traces under the mask appear only as a slight relief/tone difference — trace continuity cannot be read reliably from 3D ([GOR-007]).

### 1.4 Altium Designer

The Altium documentation does not list the default colour values; the defaults are stored in the `Default.PCBSysColors` (and `Classic.PCBSysColors`) system profiles, and these profiles cannot be deleted. 2D colour settings are system-wide (all PCB documents use the active profile). The table below lists commonly observed defaults; since no values were found in an official source, it is marked **Needs verification** (user forum reports confirm that the top layer is red and the bottom layer is blue).

| Altium layer | Typical default appearance | Verification level | KiCad equivalent |
|---|---|---|---|
| **Top Layer** | Red | Confirmed by forum report | F.Cu |
| **Bottom Layer** | Blue | Confirmed by forum report | B.Cu |
| Mid-Layer 1..n | Different shades (yellowish/greenish in most setups) | Not verified | In*.Cu (positive) |
| Internal Plane 1..n | Usually green/brown shades; **negative** display: the drawn shapes are where copper is *absent* (split lines, anti-pads) | Not verified (general knowledge) | In*.Cu plane zone |
| **Top Overlay** | Yellow | Not verified | F.Silkscreen |
| Bottom Overlay | Brown/mustard shade | Not verified | B.Silkscreen |
| Top/Bottom Paste | Grey / maroon | Not verified | F/B.Paste |
| Top/Bottom Solder | Purple / magenta shades | Not verified | F/B.Mask |
| Mechanical 1..n | Purple/pink/variable; the board outline is usually on a mechanical layer | Not verified | Edge.Cuts / User.* |
| **Keep-Out Layer** | Magenta/purple | Not verified | Rule area |
| **Multi-Layer** | Grey/silver (THT pads and vias) | Not verified | THT pad |
| **DRC violation** | **Green** highlight (DRC Error Markers system colour) | Confirmed by forum report | DRC marker |
| Connection lines (ratsnest) | Thin line; if "Use Layer Colors for Connection Drawing" is on, the ends take the layer colour | Documentation | Ratsnest |

**Altium-specific visual states:**

- **Single layer mode** (Shift+S): other layers are hidden, or shown in greyscale or as a single grey colour. Traces that appear grey are not "missing".
- **Masked/dimmed objects** are pale; **highlighted** objects appear whitened.
- **Polygon pour** has three modes: *Solid (Copper Regions)*, *Hatched* (grid/mesh; sometimes deliberately chosen for analog ground) and *None (Outlines Only)* — in the last one only the outline is visible. Polygons may also be **"shelved"** (temporarily hidden); in that case they look as if there is no pour, but they exist in the database. The "Modified Polygon" rule flags polygons that have not been repoured.
- If **Net Color Override** is on, traces appear in the **net colour** instead of the layer colour — in that case the colour → layer mapping breaks down ([GOR-004]).

### 1.5 EasyEDA (Standard) and EasyEDA Pro

Default layer colours from EasyEDA Standard's official file format documentation (black canvas, `#000000`):

| ID | EasyEDA layer | Default colour | KiCad equivalent |
|---|---|---|---|
| 1 | TopLayer | `#FF0000` (pure red) | F.Cu |
| 2 | BottomLayer | `#0000FF` (pure blue) | B.Cu |
| 3 | TopSilkLayer | `#FFFF00` (yellow) | F.Silkscreen |
| 4 | BottomSilkLayer | `#808000` (olive) | B.Silkscreen |
| 5 | TopPasteMaskLayer | `#808080` (grey) | F.Paste |
| 6 | BottomPasteMaskLayer | `#800000` (maroon) | B.Paste |
| 7 | TopSolderMaskLayer | `#800080` (purple) | F.Mask |
| 8 | BottomSolderMaskLayer | `#AA00FF` (violet) | B.Mask |
| 9 | Ratlines | `#6464FF` (lavender blue) | Ratsnest |
| 10 | BoardOutline | `#FF00FF` (magenta) | Edge.Cuts |
| 11 | Multi-Layer | `#C0C0C0` (silver) | THT pad / via |
| 12 | Document | `#FFFFFF` (white) | Dwgs.User |
| 21 | Inner1 | `#800000` (maroon) | In1.Cu |
| 22 | Inner2 | `#008000` (green) | In2.Cu |
| 23 | Inner3 | `#00FF00` (light green) | In3.Cu |
| 24 | Inner4 | `#000080` (navy) | In4.Cu |

- **Caution:** In EasyEDA **Inner1 (maroon) and BottomPaste (maroon) have the same colour**; also, Inner2 is green, and in KiCad Classic B.Cu is green. Do not decide by colour alone.
- EasyEDA also has DRCError, Hole, TopAssembly/BottomAssembly and Mechanical layers; their default colours are not listed in the official documentation.
- **EasyEDA Pro:** Colour, transparency and type can be set in the layer manager; TopLayer and BottomLayer cannot be disabled. Pro's default colour values were not found in the official documentation; visually the same family as Standard is observed (top red, bottom blue, silkscreen yellow) — **Needs verification**.

### 1.6 Other image types

| Image type | Typical appearance | What to watch for when reading |
|---|---|---|
| **KiCad/Altium/EasyEDA 3D render** | Green mask, white silkscreen, gold (ENIG-like) or silver pads, component 3D models | Traces are only a tone difference under the mask; inner layers are not visible at all; the perspective may be angled (ask for an orthographic view for scale) |
| **Manufacturer preview (JLCPCB/PCBWay Gerber viewer)** | Realistic look in the selected mask colour | Based on Gerbers, so pours are up to date; there is still no netlist |
| **Photo of a real board** | Mask green/black/blue/red/white; pad finish: **HASL** silver and domed/wavy, **ENIG** flat and golden yellow, **OSP** copper-coloured | HASL has poor flatness, ENIG and OSP are flat. Light, angle, reflection and lens distortion spoil measurement; traces under the mask are easier to see with backlighting |
| **Gerber viewer (KiCad GerbView, tracespace, etc.)** | Each Gerber file in a different colour; colours change with the program and the loading order | Read the layer name from the file name/legend, not from the colour |
| **PDF/SVG drawing output** | Mostly black/single colour on a white background | Layer name is in the title block; scale is often 1:1 and there may be dimension lines |

---

## 2. Clues you can read from the image

### 2.1 Package recognition table

In the 2D layout view you see the **pad pattern, not the body**. Recognition is done by pad count, pad arrangement, pitch and proportions. For dimensions see Section 3.

| Package / part | 2D pad pattern (layout view) | 3D/photo appearance | Typical use |
|---|---|---|---|
| **0402 / 0603 / 0805 / 1206 chip** | Two rectangular pads with a gap between them; pad outside-to-outside span ≈ 1.56 / 2.45 / 2.85 mm (KiCad IPC nominal) | Small brown/beige (capacitor) or black-topped printed (resistor) block | R, C, ferrite, LED |
| **SOD-123 / SOD-323 / SMA (DO-214AC)** | Two pads, one marked as cathode (line in the silkscreen) | Black body, cathode band | Diode, TVS |
| **SOT-23 (3 pin)** | 2 pads on one side, 1 on the opposite side; pins on the same side 1.90 mm apart | 2.9 × 1.3 mm black body | Transistor, MOSFET, LDO, ESD |
| **SOT-23-5/6** | 3+2 or 3+3 pads, 0.95 mm pitch | | LDO, small regulator, op-amp |
| **SOT-223** | 3 small pads on one side (2.3 mm pitch), 1 wide tab pad on the opposite side | 6.5 × 3.5 mm body | LDO (AMS1117, etc.) |
| **SOIC-8/14/16** | Two rows, 1.27 mm pitch, long pads | Body width 3.9 mm (narrow) / 7.5 mm (wide) | Op-amp, driver, flash |
| **TSSOP / SSOP** | Two rows, 0.65 mm pitch, thin long pads | | Logic, I/O expander |
| **QFN / DFN** | Short pads on four (QFN) or two (DFN) sides + **large square thermal pad in the middle**, often with a via grid inside | Leadless, silver contacts on the edge | Buck controller, MCU, driver |
| **QFP / LQFP / TQFP** | Rows of long thin pads on four sides, 0.5 / 0.65 / 0.8 mm pitch, empty centre (sometimes EP) | "Gull-wing" leads | MCU (STM32, etc.) |
| **BGA** | Regular grid of round pads, dog-bone vias between them | Balls underneath, not visible from the edge | FPGA, SoC, DDR |
| **USB-C receptacle (16-pin USB 2.0 type)** | ~12 thin pads in one row (around 0.5 mm grid) + 2–4 oval/square **plated slot** holes on both sides (shell retainers) | Oval opening, at the board edge | Power/USB input |
| **Micro-USB B** | 5 thin pads + two large shell pads + often 2 holes | Trapezoidal opening, ~6.9 mm wide | |
| **JST PH / XH / SH / GH, Molex PicoBlade** | Single row of pads/holes + a large mechanical retention pad on each side (SMD version) | White/beige plastic body, pin pitch 2.0 / 2.5 / 1.0 / 1.25 / 1.25 mm | Cable connections |
| **Pin header (2.54 mm)** | Row of round plated-through pads, pin 1 square pad | Black plastic + gold pins | Programming, I/O |
| **Crystal HC-49/S** | Two THT holes or two long SMD pads, body outline ~11 × 4.7 mm | Oval metal can | Old/cheap MCU clocks |
| **Crystal 3225 (3.2 × 2.5 mm), 2016, 2520** | 4 small square pads (2 of them NC or GND) or 2 pads | Ceramic package with a metal lid | MCU, USB, RF clocks; two small load capacitors next to it |
| **Electrolytic capacitor (SMD can)** | Two long pads, square silhouette with chamfered corners, polarity (+) or half-moon fill in the silkscreen | Silver cylinder, notch on top, black marking | Bulk input/output capacitance |
| **Electrolytic (THT)** | Two holes, circular silkscreen, (-) side hatched | | |
| **Shielded power inductor** | Two large pads, square/round body silhouette (4×4 – 12×12 mm) | Dark grey/black square block (e.g. printed "100") | Buck/boost inductor — centre of the switching power area |
| **ESP32-WROOM / nRF / similar module** | Row of castellated pads on the edges + GND pads underneath; a **pad-free antenna area** at one end | Metal shield + PCB antenna (meandering copper) | Wi-Fi/BLE; ESP32-WROOM-32E module 18.0 × 25.5 × 3.1 mm |
| **DPAK (TO-252)** | Two small pads (leads) + one large tab pad, leads at 2.28 mm pitch | | MOSFET, regulator |
| **D2PAK (TO-263)** | Larger version of DPAK | | High-current MOSFET/diode |
| **TO-220** | 3 holes in a single row, 2.54 mm pitch; body outline ~10 mm wide | Metal tab, heatsink hole | Linear regulator, MOSFET |
| **PowerPAK SO-8 / LFPAK / 5×6 DFN** | 4 separate pads on one side (S,S,S,G), merged wide drain pad on the opposite side | | Synchronous buck, motor driver MOSFETs |
| **Mounting hole M3** | Large circle, NPTH (cyan) or PTH with annular ring; hole Ø3.2 mm, pad Ø6.4 mm (KiCad) | | Mechanical |
| **Test point** | Single round pad, "TP1" | | Test |

### 2.2 Reading net names and designer markings

- **Reference designators:** The prefixes `R12`, `C3`, `U1`, `Q2`, `L1`, `D4`, `J1`, `Y1/X1`, `F1`, `SW1`, `TP1`, `FB1` in the silkscreen give the part type directly. In KiCad, `${REFERENCE}` is also present on F.Fab (grey text).
- **KiCad net names:** Can be shown "on pads / on tracks / both" via *Preferences → PCB Editor → Display Options → Annotations → Net names*. The white text on a pad is the net name (e.g. `GND`, `+3V3`, `/USB_D+`). In KiCad 8 long names with the hierarchical path added (`/Power/VBUS`) may appear — the sheet name is also informative. How often net names repeat along a trace cannot be configured.
- **Altium:** Net names are shown on traces in modes such as "Single and Centered" and are hidden below a minimum pixel height — if there is no net name in an image that is not zoomed in, this does not mean "no net".
- **Pad numbers:** Pin 1 is usually a square/rounded-rectangle pad, marked with a dot or chamfer in the silkscreen. If pad numbers are shown you can compare the IC pin assignment with the datasheet (only if the part number can be read in the silkscreen/3D).
- **Silkscreen text:** `VIN`, `5V`, `GND`, `SWDIO`, `TX/RX`, board name/revision are often found next to connectors; edge connector labels strengthen the net guess.

### 2.3 Guessing the net type (when there is no netlist)

| Visual clue | Likely net type | Confidence | Verification |
|---|---|---|---|
| Wide trace (≥ 0.5–1 mm) or pour running from a connector to a regulator/inductor | Power (VIN, VBUS, VOUT) | Likely | Ask for the net name, current information |
| Single wide pour across the board, stitched with many vias | GND | Likely → Certain (if the net name is visible) | |
| Two traces side by side, equally spaced, bending together (from a USB connector to the MCU) | Differential pair (USB D+/D−, CAN, Ethernet, LVDS) | Likely | Connector type + pin position |
| Meandering (serpentine) trace | Length-matched signal (DDR, high speed) | Likely | |
| Short trace from an IC pad to a small capacitor within 1–3 mm, the other end of the capacitor to a plane through a via | Decoupling | Likely | |
| Two small capacitors next to a crystal, two short symmetric traces to the MCU | Oscillator (XTAL_IN/OUT) | Likely | |
| Thin trace from an IC to a resistor away from it, and from there to the output capacitor/inductor | Feedback (FB) | Needs verification | Datasheet + schematic |
| Via grid in a QFN thermal pad | Heat path (GND or EP net) | Likely | |
| SW node: short, wide, small-area copper between the inductor pad and the MOSFET/IC SW pin | Switching node | Likely | |
| Small multi-pin SOT/DFN at the board edge, right behind the connector | ESD/TVS protection | Likely | Part number |
| Copper-free area in the antenna region, module edge at the board edge | RF keepout | Certain (visual) | Is there no copper on the other layers either? |

### 2.4 Determining the layer count (2 or 4+?)

1. **Is the layer list visible?** `In1.Cu`, `In2.Cu` rows in the KiCad *Appearance* panel; `Mid-Layer`/`Internal Plane` in the Altium bottom tabs; `Inner1..` in the EasyEDA *Layers* panel → multilayer.
2. **Colour:** In a KiCad image with all layers on, light green (In1) or orange (In2) traces/pours → 4+ layers. In EasyEDA, a maroon/green inner layer.
3. **Via behaviour:** On a two-layer board both ends of a via connect to visible traces. If vias connect to a trace on one side only and end "in empty space" → they connect to an inner layer (usually a GND/power plane) → 4+ layers (Likely).
4. **3D render edge:** Layer lines are not visible at the board edge; this method does not work.
5. **Blind/buried vias** (dark gold in KiCad 7/8, microvia dark cyan) → HDI, multilayer.
6. If you are not sure, ask the user for the **stackup** (Board Setup → Physical Stackup screen) ([GOR-009]).

---

## 3. Scale estimation

### 3.1 Known-dimension table (items to use as a "ruler")

**Rule:** For scale, use the **pad centre-to-centre spacing (pitch)** first; pitch is standard, whereas pad size varies with the footprint library. Body dimensions are only valid in 3D/photos.

| Item | Known dimension | What is measured | Source |
|---|---|---|---|
| 0402 (1005 metric) body | 1.0 × 0.5 mm | 3D/photo body | Wikipedia — List of IC packaging types |
| 0402 KiCad footprint | Pad 0.54 × 0.64 mm, centre-to-centre 1.02 mm, outside-to-outside 1.56 mm | 2D pad pattern | KiCad `R_0402_1005Metric` |
| 0603 (1608) body | 1.6 × 0.8 mm | | Wikipedia |
| 0603 KiCad footprint | Pad 0.8 × 0.95 mm, centre-to-centre 1.65 mm, outside-to-outside 2.45 mm | | KiCad `R_0603_1608Metric` |
| 0805 (2012) body | 2.0 × 1.25 mm | | Wikipedia |
| 0805 KiCad footprint | Pad 1.025 × 1.4 mm, centre-to-centre 1.825 mm, outside-to-outside 2.85 mm | | KiCad `R_0805_2012Metric` |
| 1206 (3216) | 3.2 × 1.6 mm | | Wikipedia |
| 1210 / 2512 | 3.2 × 2.5 / 6.3 × 3.2 mm | | Wikipedia |
| SOT-23 (3 pin) body | 2.92 × 1.3 mm | | Wikipedia |
| SOT-23 KiCad footprint | Same-side pin spacing 1.90 mm; outside-to-outside across rows 3.35 mm; pad 1.475 × 0.6 mm | | KiCad `SOT-23` |
| SOT-223 | Body 6.5 × 3.5 mm; pin pitch 2.3 mm | | Wikipedia; KiCad `SOT-223-3_TabPin2` |
| SOIC | Pitch **1.27 mm**; 8-SOIC body width 3.9 mm, tip to tip 5.8–6.2 mm | | Wikipedia |
| TSSOP / SSOP | Pitch **0.65 mm**; 8-TSSOP body width 4.3–4.5 mm | | Wikipedia |
| LQFP | Pitch 0.5 mm (TQFP-44: 0.8 mm) | | Wikipedia |
| QFN/MLF | Pitch typically 0.5 mm | | Wikipedia |
| BGA | Pitch 1.27 / ~0.8 (LFBGA) / ~0.5 mm (TFBGA) | | Wikipedia |
| DIP / pin header | Pitch **2.54 mm**; DIP row spacing 7.62 or 15.24 mm | | Wikipedia; KiCad `TO-220-3_Vertical` (RM 2.54) |
| DPAK (TO-252) | Lead pitch 2.3 mm (90 mil); KiCad body ~6.2 × 6.5 mm, lead pad centre-to-centre 4.56 mm | | Wikipedia TO-252; KiCad `TO-252-2` |
| TO-220 | Pitch 2.54 mm; KiCad Fab body width 10.0 mm | | Wikipedia TO-220; KiCad `TO-220-3_Vertical` |
| USB-C opening (receptacle) | 8.34 × 2.56 mm, 6.20 mm deep | Photo/3D front view | Wikipedia USB-C |
| USB-C receptacle connector (e.g. GCT USB4105) | Package ~8.94 × 7.35 mm | 2D silhouette/courtyard | Distributor listing (secondary) |
| Micro-USB B receptacle | 6.9 × 1.85 mm (opening) | | Wikipedia USB hardware |
| USB-A receptacle | 12.5 × 5.12 mm | | Wikipedia USB hardware |
| JST PH / XH / SH / GH | Pitch 2.0 / 2.5 / 1.0 / 1.25 mm | | Wikipedia JST connector (secondary) |
| HC-49 crystal | 11.05 × 4.65 mm body | | RS Components product listing |
| 3225 crystal | 3.2 × 2.5 mm | | Epson TSX-3225 (DigiKey) |
| SMD aluminium electrolytic | Case 4.3 × 4.3, 5.3 × 5.3, 6.6 × 6.6, 8.3 × 8.3, 10.3 × 10.3 mm (depending on manufacturer) | | Wikipedia |
| Tantalum | 3216 (A) 3.2 × 1.6; 3528 (B) 3.5 × 2.8; 6032 (C) 6.0 × 3.2; 7343 (D) 7.3 × 4.3 mm | | Wikipedia |
| M3 mounting hole | Hole Ø3.2 mm, copper pad Ø6.4 mm, courtyard radius 3.45 mm | | KiCad `MountingHole_3.2mm_M3_Pad` (that 3.2 mm corresponds to the ISO 273 "fine" series is general knowledge; the standard's table could not be opened) |
| ESP32-WROOM-32E | 18.0 × 25.5 × 3.1 mm | | Espressif datasheet |

### 3.2 mm/pixel calculation procedure

1. **Choose a reference:** Use the **longest** known distance possible in the image. Order of preference: (a) a dimension line or known board size in the image, (b) a multi-pin header/IC row (e.g. on a 10-pin header the centres of pins 1–10 = 9 × 2.54 = 22.86 mm), (c) the centres of the first and last pins on a SOIC/TSSOP, (d) the pad span of a single passive (least preferred).
2. **Measure pixels:** Use pad **centres** (edges are blurred by antialiasing). Find the pixel distance `P` between the two ends (Pythagoras if it is not horizontal/vertical).
3. **Scale:** `s = D_mm / P` (mm/pixel).
4. **Error margin:** Assume ±1 pixel centre uncertainty at each end → relative error ≈ `2 / P`. Add the footprint tolerance as well (negligible for pitch, ±5–10% for pad size).
   - Example: 22.86 mm = 450 px → s = 0.0508 mm/px; relative error ≈ 2/450 = 0.44%.
   - Example: 0603 outside-to-outside 2.45 mm = 25 px → s = 0.098 mm/px; relative error ≈ 2/25 = 8% + footprint difference → usable but weak.
5. **Cross-check with a second reference:** A different known item should give the same scale within ±5%; if it does not, the image is in perspective/skewed or the footprint is non-standard.
6. **Calculate what you want to measure:** `length_mm = pixels × s`. Uncertainty: `± (1 px × s)` absolute + relative scale error.
7. **Resolution threshold:** To make a numeric judgement about a feature (trace width, clearance) that feature must be **at least 3–4 pixels** wide. So:
   - To assess a 0.2 mm clearance you need s ≤ 0.05–0.067 mm/px.
   - For a 0.1 mm (≈4 mil) clearance you need s ≤ 0.025–0.033 mm/px.
   - If this threshold is not met, write "Needs verification — request a DRC report or a zoomed-in image" instead of a numeric violation ([GOR-003]).
8. **Distorting effects:** JPEG compression edge artefacts (±1–2 px), display scaling (Windows 125%/150% → one "pixel" may not be a real pixel), perspective in 3D images (switch to orthographic mode in the KiCad 3D viewer), lens distortion and tilt in photos. In photos, only measure when the board was shot straight from above and the reference is close to the thing being measured.

### 3.3 Quick reasoning rules of thumb (without scale)

- If a trace is close to the width of an adjacent 0603 pad (0.8 mm), it is ≈ 0.8 mm; if it is half of a 0402 pad, it is ≈ 0.25–0.3 mm.
- If a single trace can pass between QFN pads, the trace is ≤ ~0.2 mm (0.5 mm pitch).
- The gap between TSSOP pins is around ~0.3–0.35 mm (0.65 mm pitch − pad width); this is a good eyeball ruler for comparing clearances (Likely).

---

## 4. Analysis order

The image audit goes **from large to small** and **from serious errors to aesthetics**. At each step look only at that step's rule files; this way a critical power error does not get lost among silkscreen comments.

| Step | What to do | What to look at in the image | Rule files to apply |
|---|---|---|---|
| **0. Identify the image** | Tool, theme, layer visibility, scale, fill state | Background colour, layer panel/legend, is there `In*.Cu`, are there ratsnest/DRC markers, are the pours filled | `GOR` (this file), [01 STK](01-stackup.md) |
| **1. Blocks** | Split the board into functional blocks: input/protection, power conversion, MCU, RF, analog, connectors, motor/power stage | Component clusters, connector positions, silkscreen labels; whether the blocks are arranged in signal-flow order | [02 PLC](02-placement.md), [15 MEC](15-mechanical.md) |
| **2. Power path** | Follow the current path from the connector to the load | Trace/pour width, bottlenecks, number of vias in the current path, bulk capacitor position, proximity of regulator input/output capacitors, switching power loop area (Cin–FET–GND), SW node area, area under the inductor | [03 PWR](03-power-distribution.md), [08 SMPS](08-switching-power.md), [10 THM](10-thermal.md), [11 VIA](11-vias.md) |
| **3. GND integrity** | Check that the return path is uninterrupted | Slots/islands in the plane, rows of traces cutting the plane, "fences" formed by via rows, stitching vias, pour islands connected to nothing, thermal reliefs | [04 GND](04-grounding.md), [01 STK](01-stackup.md), [11 VIA](11-vias.md) |
| **4. Critical signals** | High speed, RF, clock, sensitive analog | Differential pair matching and reference plane, crossing over a slot, crystal–MCU distance and signals under the crystal, antenna keepout, proximity of the ESD part to the connector, decoupling capacitor–pin distance | [05 HS](05-high-speed-signals.md), [06 RF](06-rf-antenna.md), [07 XTL](07-crystal-oscillator.md), [09 ESD](09-esd-protection.md) |
| **5. DFM / DFA** | Manufacturability and assembly | Trace/clearance/annular ring if the scale allows; open via in pad, copper-to-board-edge distance, tombstone risk (asymmetric pad connection), part spacing, polarity markings, fiducials | [12 DFM](12-dfm.md), [13 DFA](13-dfa.md), [11 VIA](11-vias.md) |
| **6. Test and mechanical** | Testability, mounting | Test points, access to the programming connector, mounting holes and the keepout around them, connectors at the edge, height clashes (3D) | [16 TST](16-testability.md), [15 MEC](15-mechanical.md) |
| **7. Silkscreen and aesthetics** | Readability, order | Silkscreen on pads, unreadable/mirrored text, inconsistent orientation, board name/revision/date, needlessly wiggly traces, irregular alignment | [14 SLK](14-silkscreen.md), [17 EST](17-aesthetics.md) |

**Practical tips:**

- At each step write the finding into the report draft **immediately** (location + rule ID + confidence).
- If the image needed to assess a step is missing, do not skip the step silently; note "Could not be assessed — this image is needed" ([GOR-010], Section 7).
- In the power and GND steps you need to see **each copper layer separately**; in a combined image, overlapping pours hide slots.
- The root cause of a problem seen in step 4 is often the placement in step 1; give the fix recommendation at the placement level.

---

## 5. Limits of the image

### 5.1 Certain – likely – guess distinction

| Topic | What can be said from the image | Why it is limited |
|---|---|---|
| Presence and position of a component | **Certain** (if visible) | — |
| Component value / part number | Mostly **no**; Likely if written in the silkscreen or 3D | 3D models are generic; the value is only in the schematic |
| Layer mapping (colour → layer) | **Likely** | The theme can be changed; net colours can override the layer colour |
| Trace/clearance dimension | **Likely** (if scale and resolution are sufficient), otherwise **Needs verification** | Pixel limit, JPEG, display scaling |
| Net identity | **Likely** (Certain if the net name is visible) | No netlist; two copper areas of the same colour may be different nets |
| Broken connection | **Needs verification** | The connection may come from another layer or from an invisible pour; the ratsnest may be hidden |
| Plane continuity | **Likely** if that layer is shown on its own | Overlapping layers hide slots |
| Pour (zone) content | Belongs to the moment of the image; **may be stale** | KiCad does not refill zones automatically; in Altium the polygon may be shelved or not repoured |
| Current capacity | **Needs verification** | Current, copper thickness (oz) and temperature rise target are unknown |
| Impedance | **No** (without a stackup) | Dielectric thickness, εr and reference plane are unknown |
| Thermal behaviour | **Partly** (copper area and thermal vias can be seen) | Power dissipation and ambient are unknown |
| Hidden/inner layer | **No** | If it is not in the image, you cannot say it is "absent" |

### 5.2 Typical traps

1. **A single-layer image hides the other layers.** Saying "no trace reaches this pad" in an F.Cu-only image may be wrong; the connection may be made from B.Cu or from an inner plane through a via ([GOR-002]).
2. **Unfilled or stale pour.** If a zone edge is hatched but the inside is empty, or a pour runs over a trace without leaving a clearance, the pour is not up to date ([GOR-001]).
3. **The ratsnest may be hidden.** Its absence does not prove that all connections are complete; ask for the DRC "unconnected items" count ([GOR-005], [GOR-006]).
4. **The netlist is unknown.** Two pours that look the same may be different nets (e.g. GND and PGND). If there is no net name, say "probably GND" ([GOR-008]).
5. **Resolution:** Clearances below 0.2 mm are 2–4 pixels in a typical screenshot; do not build a numeric violation claim on them ([GOR-003]).
6. **Colour customisation and net colours:** KiCad and Altium net/net class colours can make the trace colour independent of the layer colour ([GOR-004]).
7. **3D renders** do not show inner layers or trace details under the mask; 3D models may be missing or wrong ([GOR-007]).
8. In **dimming / high-contrast** mode inactive layers appear pale; do not interpret them as "missing traces".
9. **Scale distortion:** The screenshot may have been resized or cropped; calculate the scale separately for each image.
10. **Altium inner planes** (Internal Plane) are shown in negative: the visible lines are where copper is **absent** (general knowledge, Needs verification).

### 5.3 Confidence level wording

Give every finding **exactly** one of these three labels:

| Label | When | Example wording |
|---|---|---|
| **Certain** | Seen directly and indisputably in the image (net name readable, ratsnest/DRC marker present, copper clearly cut, silkscreen on top of the pad) | "Certain: U3's thermal pad has no vias at all (in both the F.Cu and B.Cu images)." |
| **Likely** | There is a strong visual clue but it relies on an assumption (colour mapping, net type guess, scale estimate) | "Likely: the USB D+/D− pair (two parallel traces leaving the connector pins) crosses the slot in the GND pour on B.Cu." |
| **Needs verification** | The image is insufficient; additional data is needed | "Needs verification: the VIN trace appears to be ~0.4 mm; if the input current is 3 A it may be insufficient — the current value and copper thickness are needed." |

**Rules:**
- For a claim that needs a netlist (connection, net identity), use the "Certain" label **only** if the net name can be read in the image.
- When giving a numeric value, state the scale source and the uncertainty: "~0.25 mm (±0.05 mm; scale: J2 header pitch 2.54 mm)".
- Severity and confidence are separate axes: a finding of Critical severity that you are not sure about is written as "Critical / Needs verification", not downgraded.

### 5.4 Information to request from the user

| Missing information | Why it is needed | Request sentence (example) |
|---|---|---|
| Separate images of the other copper layers | GND integrity, connection verification | "Please share screenshots that show B.Cu and (if present) In1/In2 on their own." |
| Image with refilled pours | Stale pour misreading | "Could you refill all zones in KiCad with `B` and take the image again?" |
| Stackup / layer count / copper thickness | Impedance, current, layer mapping | "Please share the Board Setup → Physical Stackup screen and the copper thickness (1 oz / 2 oz)." |
| Currents and voltages | Trace width, thermal | "What are the VIN, main output and motor/load currents (continuous and peak)?" |
| DRC report | Numeric violations, broken connections | "Please run DRC and share the error/warning and 'unconnected' counts." |
| Schematic (PDF) | Net identity, part values, function | "Could you share the schematic as a PDF? Especially the power and USB sections." |
| Part numbers of critical parts | Comparison with the recommended layout in the datasheet | "What are the part numbers of U1 (buck) and U2 (MCU)?" |
| Manufacturer and price class | DFM limits | "Which manufacturer and which class (e.g. PCBWay standard)?" |
| Mechanical constraints | Connector/hole position | "Is there an enclosure drawing or any connector position constraints?" |

---

## 6. Suggested report format

### 6.1 Template

```markdown
# PCB Visual Audit Report — <board name / revision>

## Summary
- Images reviewed: <"1) All layers, KiCad 8, pours filled; 2) F.Cu only; 3) 3D top">
- Tool / theme: <KiCad Default / Altium / EasyEDA; theme verified?>
- Layer count: <2 / 4 / unknown> (source: <layer panel / estimate>)
- Scale: <s = 0.051 mm/px, reference: J1 1x10 header, ±0.5%>
- Finding count: Critical <n>, High <n>, Medium <n>, Low <n>, Cosmetic <n>
- Areas that could not be assessed: <e.g. inner layers, impedance>

## Findings

### Critical
| # | Rule | Location (in the image) | Finding | Confidence | Recommended fix |
|---|---|---|---|---|---|
| C1 | <RULE-ID> | Bottom left, between the J1 USB-C connector and U2 | ... | Certain | ... |

### High
(same table)

### Medium
### Low
### Cosmetic

## Requested from the user
1. ...

## Assumptions
- Colours were interpreted according to the KiCad Default theme.
```

**Location wording rules:**
- Think of the image as a 3×3 grid: *top left / top centre / top right / middle left / centre / middle right / bottom left / bottom centre / bottom right*.
- Combine the location with an **anchor**: "top right, between U1 (QFN) and inductor L1", "bottom edge, immediately left of the J3 screw terminal".
- If there are several images, add the image number: "Image 2 (B.Cu), centre, under U4".
- If possible, give the reference designator and pin number: "U2 pin 7 (left row, 3rd from the top)".
- Do not invent absolute coordinates from the image; if needed, ask the designer for the coordinate from the KiCad status bar.

**Severity levels (the handbook's common scale):**

| Severity | Meaning |
|---|---|
| **Critical** | The board does not work, gets damaged, or there is a safety risk (short circuit, broken power, reverse polarity, thermal runaway) |
| **High** | Very likely a functional/EMC/reliability problem (broken return path, large switching loop, antenna keepout violation) |
| **Medium** | Loss of performance/margin, or lowers manufacturing yield |
| **Low** | Outside good practice, small risk |
| **Cosmetic** | Appearance, readability, order |

### 6.2 Short example report (fictional)

> *This example was made up to show the format; it does not belong to a real board. The rule IDs are real rules from the handbook.*
>
> **Severity and confidence are separate:** The severity of a finding is the same as the **Severity** field of the rule; do not lower or raise it based on your own opinion. If you are not sure, still write the finding under the rule's severity heading, but put "Likely" or "Needs verification" in the confidence column. The severity changes only if the rule's **Exceptions** field clearly applies; in that case write the justification.

```markdown
# PCB Visual Audit Report — ESP32 sensor board v0.1

## Summary
- Images reviewed: 1) All layers (KiCad 8, Default theme, pours filled), 2) B.Cu on its own, 3) 3D top view
- Layer count: 2 (only F.Cu/B.Cu in the Appearance panel — Certain)
- Scale: 0.048 mm/px (J4 1x6 header, pin1–pin6 = 12.7 mm = 265 px; ±0.8%)
- Findings: Critical 4, Medium 1, Cosmetic 1
- Could not be assessed: USB impedance (no stackup)

## Findings

### Critical
| # | Rule | Location | Finding | Confidence | Fix |
|---|---|---|---|---|---|
| C1 | GOR-005 | Image 1, middle right, between U3 (LDO) and C7 | Pale cyan ratsnest line: the U3 output – C7 connection is unrouted | Certain | Complete the trace; check until DRC shows "unconnected = 0" |
| C2 | RF-001 | Image 2 (B.Cu), top edge, under the antenna end of the U1 ESP32 module | The B.Cu GND pour extends under the antenna area | Certain | Keep the area under the antenna free of copper on all layers (rule area); move the antenna to the board edge (RF-002) |
| C3 | GND-002, HS-003 | Image 2, centre, under the J2 USB-C → U2 path | A 5 V trace on B.Cu splits the GND pour in two; the USB D+/D− pair above crosses this slot | Likely | Move 5 V to the top layer or close the slot; leave uninterrupted GND under the pair |
| C4 | PWR-001 | Image 1, bottom left, J1 (DC jack) → U3 | VIN trace ~0.30 mm (±0.05); current unknown | Needs verification | Report the input current; if insufficient according to the IPC-2221 table, widen the trace or use a pour |

### Medium
| # | Rule | Location | Finding | Confidence | Fix |
|---|---|---|---|---|---|
| M1 | SLK-001 | Image 3, bottom right | The R12 label overlaps a pad | Certain | Move the label off the pad |

### Cosmetic
| # | Rule | Location | Finding | Confidence | Fix |
|---|---|---|---|---|---|
| CO1 | EST-001 | Image 1, bottom centre, signals going to the J4 header | 90° corners on low-speed GPIO traces | Certain | Optional: change to 45° corners (not an electrical problem) |

## Requested from the user
1. Input and 3V3 rail currents.
2. DRC report (especially "unconnected items").
3. Schematic PDF (to verify whether U2 is a USB-UART or native USB).
```

---

## 7. Which images to request

### 7.1 Ideal screenshot set

| # | Image | How to take it (KiCad) | What for |
|---|---|---|---|
| 1 | **All layers, pours filled**, board full screen | Fill all zones with `B`; *Zoom to Fit*; high-resolution screenshot or SVG/PNG export | Overall layout, blocks |
| 2 | **Each copper layer on its own** (F.Cu, In1.Cu, In2.Cu, …, B.Cu) | Only the relevant layer + Edge.Cuts enabled in the *Appearance* panel | GND integrity, power path, slots |
| 3 | Close-up(s) with **net names on** | *Preferences → PCB Editor → Display Options → Net names: on pads and tracks* | Net identity (instead of a netlist) |
| 4 | All-layer image with **ratsnest on** | *Appearance → Objects → Ratsnest* visible | Unrouted connections |
| 5 | **3D top and bottom** (orthographic) | 3D viewer → orthographic projection; from the top and the bottom | Placement, mechanical clashes, silkscreen, polarity |
| 6 | **Close-ups of critical areas** | Switching power stage, USB/differential pairs, crystal, antenna, motor/power stage | Detailed check at ≤ 0.03 mm/px scale |
| 7 | **Silkscreen + Fab + Courtyard** view | Only F.Silkscreen, F.Fab, F.Courtyard, Edge.Cuts | SLK/DFA check |
| 8 | **Stackup screen** | *Board Setup → Physical Stackup* | Layer count, thicknesses |
| 9 | **DRC result** | *Inspect → Design Rules Checker* or the `kicad-cli pcb drc` report | Numeric violations |
| 10 | **Schematic PDF** | *File → Plot* | Net and part identity |

### 7.2 Image quality requirements

- **Format:** PNG (lossless). JPEG produces artefacts in fine clearances.
- **Resolution:** In the full-board image the long side ≥ 2000 px; in detail checks the smallest target feature should be ≥ 4 px (Section 3.2, step 7).
- **No resizing:** If the image is cropped, keep at least one known item (header, IC) in the frame.
- **Interface elements:** If the layer panel/legend stays visible, the colour mapping can be verified; it is preferable not to crop it out.
- **Altium:** Single layer mode (Shift+S, "Hide Other Layers"); polygons "Solid" and repoured (Tools → Polygon Pours → Repour All), no shelved polygons.
- **EasyEDA:** Hide the other layers in the *Layers* panel; rebuild the copper pours (Rebuild Copper Area).

### 7.3 Minimum set (if the user will send few images)

1. All layers, pours filled, ratsnest on.
2. Each copper layer on its own.
3. 3D top view.
4. Currents + layer count + schematic (even as text).

---

## 8. GOR rules

### [GOR-001] Pour (zone) looks unfilled or stale — ask for a refill first

- **Severity:** High
- **Detectable from image:** Partly
- **How it looks in the image:** There is a zone boundary (a polygon whose edge is hatched with short diagonal lines) but the inside is empty; or the pour runs over a trace/pad without leaving a clearance; or the pour keeps the old shape of a part that was deleted or moved. In Altium the polygon is outline-only (None/Outlines Only) or shelved.
- **Why it matters:** Comments on GND integrity, short circuits or isolation made from a stale or empty pour will be wrong. KiCad does not refill pours automatically; it warns before DRC and output generation.
- **Recommended fix:** Ask for the image again after `B` (fill all zones) in KiCad, *Repour All* in Altium, *Rebuild Copper Area* in EasyEDA. Until then mark findings that rely on the pour as "Needs verification".
- **Exceptions:** If the user deliberately provided an image in "outline only" mode and a filled image is also available.
- **Example:** —
- **Source:** [KiCad 8 PCB Editor — Working with zones](https://docs.kicad.org/8.0/en/pcbnew/pcbnew.html); [Altium — Polygon Pour](https://www.altium.com/documentation/cstu/polygon-pour-0)

### [GOR-002] Do not conclude "no connection" from a single-layer image

- **Severity:** Medium
- **Detectable from image:** No (netlist needed)
- **How it looks in the image:** On the displayed layer no trace reaches a pad; the pad is alone or has a via next to it.
- **Why it matters:** The connection may be made from another layer, an inner plane or a pour. A false "broken connection" finding lowers the credibility of the report.
- **Recommended fix:** Ask for every copper layer one by one and an image with the ratsnest on; ask for the DRC "unconnected items" count. Write the finding as "Needs verification" at most.
- **Exceptions:** If a ratsnest line is visible ([GOR-005]), or if all copper layers were shown and the pad is connected on none of them → "Likely".
- **Example:** —
- **Source:** [KiCad 8 PCB Editor — Appearance panel](https://docs.kicad.org/8.0/en/pcbnew/pcbnew.html)

### [GOR-003] Do not claim a numeric violation before verifying scale and resolution

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** The clearance between two copper features or a trace width is only a few pixels; the image is JPEG or downscaled.
- **Why it matters:** A 0.2 mm clearance is 2 pixels at 0.1 mm/px; antialiasing and compression add ±1–2 px error. A numeric DFM violation claim may be wrong.
- **Recommended fix:** Calculate mm/px with the procedure in Section 3.2; if the measured feature is narrower than 4 pixels, write "Needs verification" instead of a number and ask for a close-up PNG or a DRC report. When you give a number, state the scale reference and the uncertainty.
- **Exceptions:** If the difference is very large (e.g. copper features clearly touching each other), "Certain" may be written.
- **Example:** —
- **Source:** [List of integrated circuit packaging types (Wikipedia)](https://en.wikipedia.org/wiki/List_of_integrated_circuit_packaging_types) (reference dimensions); [KiCad footprint R_0603_1608Metric](https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/master/Resistor_SMD.pretty/R_0603_1608Metric.kicad_mod)

### [GOR-004] Verify the colour → layer mapping; state the theme assumption explicitly

- **Severity:** Low
- **Detectable from image:** Partly
- **How it looks in the image:** The layer panel/legend is not visible; the colours do not match the default theme (e.g. green bottom copper; differently coloured traces on the same layer).
- **Why it matters:** In KiCad, Altium and EasyEDA the theme and net colour can be changed; in KiCad Classic B.Cu is green, in KiCad Default In1.Cu is green, in EasyEDA Inner2 is green. A wrong mapping leads to looking for errors on the wrong layer.
- **Recommended fix:** Write the mapping used in the "Assumptions" section of the report; ask for an image with the layer panel visible.
- **Exceptions:** If the layer panel or legend can be clearly read in the image.
- **Example:** —
- **Source:** [KiCad builtin_color_themes.h (8.0)](https://gitlab.com/kicad/code/kicad/-/raw/8.0/common/settings/builtin_color_themes.h); [EasyEDA PCB File Format](https://docs.easyeda.com/en/DocumentFormat/3-EasyEDA-PCB-File-Format/); [Altium — PCB Editor Layer Colors](https://www.altium.com/documentation/altium-designer/pcb-editor-layer-colors-preferences)

### [GOR-005] A visible ratsnest (airwire) is an unrouted connection

- **Severity:** Critical
- **Detectable from image:** Yes
- **How it looks in the image:** In KiCad Default a thin, semi-transparent cyan straight line between two pads (RGB 0, 248, 255, α0.35); white in Classic; `#6464FF` lavender blue in EasyEDA; a thin connection line in Altium.
- **Why it matters:** That connection will not exist on the manufactured board.
- **Recommended fix:** Route the connection or connect it with a pour; verify "unconnected items = 0" in DRC.
- **Exceptions:** If zones are not filled, the ratsnest also shows connections that the pour will close — handle [GOR-001] first. Intentional net-tie/jumper cases.
- **Example:** —
- **Source:** [KiCad builtin_color_themes.h (master)](https://gitlab.com/kicad/code/kicad/-/raw/master/common/settings/builtin_color_themes.h); [EasyEDA PCB File Format](https://docs.easyeda.com/en/DocumentFormat/3-EasyEDA-PCB-File-Format/)

### [GOR-006] Report the DRC markers in the image and ask for the DRC report

- **Severity:** High
- **Detectable from image:** Yes
- **How it looks in the image:** In KiCad Default red-pink (error) or yellow (warning) markers, a white marker = excluded violation; red/green in Classic; in Altium the violating objects are highlighted **green**.
- **Why it matters:** It directly shows that design rules are violated; but the image does not tell the type of the violation.
- **Recommended fix:** Report the positions of the markers; ask for the DRC report for the violation types. For white (exclusion) markers, ask for the justification.
- **Exceptions:** In Altium the DRC colour may have been changed; a green-highlighted object is not always a violation ([GOR-004]).
- **Example:** [Fedevel forum — Learn Altium Essentials](https://fedevel.com/forum/your-projects/17183-course-learn-altium-essentials-second-edition) — an Altium discussion where placed parts appear green because of a rule violation.
- **Source:** [KiCad builtin_color_themes.h (master)](https://gitlab.com/kicad/code/kicad/-/raw/master/common/settings/builtin_color_themes.h); [Altium — PCB Editor Layer Colors (DRC Error Markers)](https://www.altium.com/documentation/altium-designer/pcb-editor-layer-colors-preferences)

### [GOR-007] Do not judge copper continuity / inner layers from a 3D render or photo

- **Severity:** Medium
- **Detectable from image:** Partly
- **How it looks in the image:** A realistic image with green mask, white silkscreen and gold pads; traces can be made out only as a slight tone difference; inner layers are not visible at all; the perspective may be angled.
- **Why it matters:** Trace breaks under the mask, fine clearances and inner planes cannot be read from 3D; perspective distorts the scale.
- **Recommended fix:** Use the 3D image for placement, mechanical clashes, polarity and silkscreen; ask for 2D layer images for copper analysis. If measurement is needed, ask for an orthographic view.
- **Exceptions:** In backlit high-resolution photos outer-layer traces may be visible (still "Likely").
- **Example:** —
- **Source:** [KiCad builtin_color_themes.h — LAYER_3D_* values](https://gitlab.com/kicad/code/kicad/-/raw/master/common/settings/builtin_color_themes.h); [MCL — PCB Surface Finishes: HASL, OSP and ENIG](https://www.mclpcb.com/blog/pcb-surface-finishes-hasl-osp-enig)

### [GOR-008] If no net name is visible, a net type guess does not go above "Likely"

- **Severity:** Low
- **Detectable from image:** Partly
- **How it looks in the image:** The net name layer is off; there are wide traces, parallel trace pairs and large pours but no labels.
- **Why it matters:** A wide trace may be high-voltage isolation, a parallel pair may be two signals that happen to run side by side, a large pour may be a power rail rather than GND. A wrong net identity leads to applying the wrong rule set.
- **Recommended fix:** Use the clues in Section 2.3 and write the confidence as "Likely"; ask for an image with net names on or for the schematic.
- **Exceptions:** If the net name can be read on the pad/trace, or the silkscreen labels it clearly (`GND`, `VBUS` and directly connected to the connector pin).
- **Example:** —
- **Source:** [KiCad Forum — net names display](https://forum.kicad.info/t/how-to-control-net-names-on-traces-spacing-display-threshold/47608)

### [GOR-009] Limit impedance and return path judgements when the stackup is unknown

- **Severity:** Medium
- **Detectable from image:** No (stackup needed)
- **How it looks in the image:** Differential pairs or high-speed traces are visible, but there is no layer count/dielectric information; or vias seem to go to an inner layer.
- **Why it matters:** The trace width–impedance relationship depends on dielectric thickness and the reference plane; the same width gives very different impedance on a 2-layer 1.6 mm board and on a 4-layer board.
- **Recommended fix:** Estimate the layer count with Section 2.4 and ask for the stackup screen; write impedance findings as "Needs verification". Focus on what can be checked visually: symmetry of the pair, whether there is a slot in the reference plane, a nearby GND via at a layer change.
- **Exceptions:** If the stackup screen is in the image.
- **Example:** [Fedevel — USB Controlled Impedance on 4-Layer PCB](https://fedevel.com/forum/schematic-design-pcb-layout/11347-usb-controlled-impedance-on-4-layer-pcb-routing-on-l3) — the reviewer states that without a solid reference plane above and below the USB pair, the impedance calculation will not be correct.
- **Source:** [Fedevel — USB Controlled Impedance on 4-Layer PCB](https://fedevel.com/forum/schematic-design-pcb-layout/11347-usb-controlled-impedance-on-4-layer-pcb-routing-on-l3)

### [GOR-010] If an image is missing, do not skip the step — write "Could not be assessed" and request it

- **Severity:** Low
- **Detectable from image:** Yes
- **How it looks in the image:** There is only one image (e.g. 3D top); no bottom layer, inner layers, net names or schematic.
- **Why it matters:** A silently skipped analysis step (e.g. GND integrity) gives the user the impression that "there is no problem".
- **Recommended fix:** In the report, under the heading "Areas that could not be assessed", state the step and the image needed (Section 7.1). Prioritise the requests: copper layers first, then current/stackup, then the schematic.
- **Exceptions:** —
- **Example:** [Fedevel — Buck converter Layout Review](https://fedevel.com/forum/schematic-design-pcb-layout/16381-buck-converter-layout-review) — the reviewer asks for screenshots to be attached to posts to speed up the review.
- **Source:** [Fedevel — Buck converter Layout Review](https://fedevel.com/forum/schematic-design-pcb-layout/16381-buck-converter-layout-review)

---

## 9. Sources

All sources were accessed on 2026-10-13. Those labelled "(search result only)" were taken from search results and their content was verified with the search summary; the others were opened directly. Detailed notes are in the Turkish working files of the PCBDesignWClaude repository.

**KiCad**
- [KiCad builtin_color_themes.h — master](https://gitlab.com/kicad/code/kicad/-/raw/master/common/settings/builtin_color_themes.h)
- [KiCad builtin_color_themes.h — 8.0](https://gitlab.com/kicad/code/kicad/-/raw/8.0/common/settings/builtin_color_themes.h)
- [KiCad builtin_color_themes.h — 7.0](https://gitlab.com/kicad/code/kicad/-/raw/7.0/common/settings/builtin_color_themes.h)
- [KiCad builtin_color_themes.h — 9.0](https://gitlab.com/kicad/code/kicad/-/raw/9.0/common/settings/builtin_color_themes.h)
- [KiCad 8.0 PCB Editor documentation](https://docs.kicad.org/8.0/en/pcbnew/pcbnew.html)
- [KiCad Forum — How to control NET NAMES on traces](https://forum.kicad.info/t/how-to-control-net-names-on-traces-spacing-display-threshold/47608) (search result only)
- KiCad footprint files: [R_0402_1005Metric](https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/master/Resistor_SMD.pretty/R_0402_1005Metric.kicad_mod), [R_0603_1608Metric](https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/master/Resistor_SMD.pretty/R_0603_1608Metric.kicad_mod), [R_0805_2012Metric](https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/master/Resistor_SMD.pretty/R_0805_2012Metric.kicad_mod), [SOT-23](https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/master/Package_TO_SOT_SMD.pretty/SOT-23.kicad_mod), [SOT-223-3_TabPin2](https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/master/Package_TO_SOT_SMD.pretty/SOT-223-3_TabPin2.kicad_mod), [TO-252-2](https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/master/Package_TO_SOT_SMD.pretty/TO-252-2.kicad_mod), [TO-220-3_Vertical](https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/master/Package_TO_SOT_THT.pretty/TO-220-3_Vertical.kicad_mod), [MountingHole_3.2mm_M3_Pad](https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/master/MountingHole.pretty/MountingHole_3.2mm_M3_Pad.kicad_mod)

**Altium**
- [Altium — PCB Editor Layer Colors Preferences](https://www.altium.com/documentation/altium-designer/pcb-editor-layer-colors-preferences)
- [Altium — Board Layers and Colors](https://www.altium.com/documentation/cstu/board-layers-and-colors)
- [Altium — Your View of the PCB](https://www.altium.com/documentation/altium-designer/pcb/your-view-of-the-board)
- [Altium — Polygon Pour](https://www.altium.com/documentation/cstu/polygon-pour-0) (search result only)
- [Altium — Shelve Polygons](https://altium.com/documentation/altium-designer/pcb-cmd-shelvepolygonsshelvepolygons-ad) (search result only)
- [Fedevel forum — Learn Altium Essentials](https://fedevel.com/forum/your-projects/17183-course-learn-altium-essentials-second-edition)

**EasyEDA**
- [EasyEDA PCB File Format](https://docs.easyeda.com/en/DocumentFormat/3-EasyEDA-PCB-File-Format/)
- [EasyEDA Layer Manager](https://docs.easyeda.com/en/PCB/Layer-Manager/index.html)
- [EasyEDA Pro Layer Manager](https://prodocs.easyeda.com/en/pcb/tools-layer-manager/) (search result only)

**Package and connector dimensions**
- [Wikipedia — List of integrated circuit packaging types](https://en.wikipedia.org/wiki/List_of_integrated_circuit_packaging_types)
- [Wikipedia — USB-C](https://en.wikipedia.org/wiki/USB-C)
- [Wikipedia — USB hardware](https://en.wikipedia.org/wiki/USB_hardware)
- [Wikipedia — TO-220](https://en.wikipedia.org/wiki/TO-220)
- [Wikipedia — TO-252](https://en.wikipedia.org/wiki/TO-252)
- [Wikipedia — JST connector](https://wikipedia.com/wiki/JST_connector) (search result only)
- [HQ Online — GCT USB4105-GF-A](https://hqonline.com/product-detail/usb-connectors-gct-usb4105-gf-a-2500389379) (search result only, secondary)
- [RS Components — QANTEK HC-49/U-S crystal](https://uk.rs-online.com/web/p/crystal-units/1734305) (search result only)
- [DigiKey — Epson TSX-3225](https://azcus.digikey.com/en/products/detail/epson/TSX-3225-25-0000MF10P-C0/7430946) (search result only)
- [Espressif — ESP32-WROOM-32E/32UE Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.pdf) (search result only)
- [ISO 273:1979 — Clearance holes for bolts and screws](https://www.iso.org/standard/4183.html) (search result only; table values could not be seen in the source)

**Surface finish**
- [MCL — PCB Surface Finishes: HASL, OSP and ENIG](https://www.mclpcb.com/blog/pcb-surface-finishes-hasl-osp-enig)

**Real review examples**
- [Fedevel — Buck converter Layout Review](https://fedevel.com/forum/schematic-design-pcb-layout/16381-buck-converter-layout-review)
- [Fedevel — USB Controlled Impedance on 4-Layer PCB](https://fedevel.com/forum/schematic-design-pcb-layout/11347-usb-controlled-impedance-on-4-layer-pcb-routing-on-l3)
