---
name: powerlab-board-requirements
description: Collect a new board's requirements before designing it, the METU Power Lab way. Use when the user starts a board, schematic or project from scratch ("design a new board", "start a PCB for…", "make me a converter / sensor / driver board", "new project"), asks to set, review or change the board's requirements, spec or brief, or attaches a sketch, enclosure drawing or block diagram for a new design. Covers size, layers and layout, working temperature, cost, mechanics, and special environments (altitude, EMI/EMC, humidity, safety standards), saving them to design-requirements.md, and turning them into design rules.
---

# Board requirements first

A board designed without its requirements gets redesigned: the outline doesn't fit the enclosure, a part isn't rated for the temperature, the clearances are wrong for the altitude, or it costs twice the budget. Ask before you draw anything. **This is a rule for every new board:** no `create_project`, schematic sheet, outline or placement until the requirements are agreed, unless the user says to skip them.

## 0. What's already known
- Read `design-requirements.md` in the project folder if it exists. If it does, show a 3-5 line summary, ask only about what's missing or marked "assumed", and skip to step 3.
- Read what the user already said or attached, and the schematic if one exists (parts, power nets, voltages in net names). Never ask again for something you were already told.

## 1. Ask in short rounds
Go round by round and wait for each answer. Ask only the rounds that apply; a small logic board needs fewer questions than a 400 V inverter. Put the questions with clear answers in a `<choices>` block (2-4 options, the lab default first and marked "(Recommended)"). The panel adds an **Other…** button with a text box to every question, so the user can always write their own answer or a value (a size, a price); never add "Other" or "I'll type it" options yourself. Ask the open questions in plain text, in a round of their own, so the answer buttons never hide them.

Tell the user once, at the start, that they can:
- **attach anything they have** with 📎 or by pasting: a hand sketch (a phone photo is fine), an enclosure drawing, a block diagram, a reference design, datasheets, a photo of the space the board goes into;
- **write extra notes in their own words** at any point ("the heatsink is on the left", "it goes on a drone");
- **answer "don't know" or "use the lab defaults"** to anything. You then use the default and record it as *assumed*.

**Round 1: what it is (plain text).**
- What does the board do? Inputs and outputs: voltages, currents, power, switching frequency.
- Main parts or interfaces already chosen (MCU, gate driver, sensors, USB, CAN…).
- What does it connect to, and how (cables, connectors, a mating board)?

**Round 2: size, layers, temperature, cost (choices).** For example:
```
<choices>
Board size?
- As small as practical (Recommended)
- Must fit an enclosure
- Fixed size
Layers?
- 2 layers (Recommended)
- 4 layers
- Decide from the design
Working temperature (ambient around the board)?
- Lab / indoor, 0 to 40 °C (Recommended)
- Industrial, -40 to 85 °C
- Hot or extended, up to 105-125 °C
Cost and quantity?
- Prototype, a few boards at standard price (Recommended)
- Small batch, 10-100, keep the cost down
- I have a target price
</choices>
```

**Round 3: mechanics and layout (choices; if an answer needs details, like the enclosure drawing, the size or the price, and the user didn't write them in Other…, ask for them next).**
- Mounting: 4× M3 at the corners (Recommended) / match the enclosure / none. Plated + GND or NPTH (§3.1 asks).
- Parts on: top only (Recommended) / both sides.
- Height limits, keep-outs, heatsink or fan, board thickness (1.6 mm is standard).
- Where things go: which edge each connector sits on, where power comes in, which sections must be apart. A sketch answers this best, so ask for one.
- Assembly: hand-soldered (Recommended) / PCBWay assembly / mixed.

**Round 4: special environment (one choices question first).**
```
<choices>
Any special environment or standard?
- No, normal indoor use (Recommended)
- Yes, there is one
</choices>
```
If yes, ask only what applies, in plain text or choices:
- **Altitude** (above 2000 m, aircraft, drones, high-altitude sites).
- **EMI/EMC:** the target standard and class (e.g. CISPR 11 or 32 Class A/B, CISPR 25 automotive, MIL-STD-461), immunity (ESD, surge, burst), and nearby sensitive equipment.
- **Moisture and dirt:** humidity, condensation, dust, pollution degree, conformal coating, IP rating of the enclosure.
- **Vibration and shock** (vehicles, motors, drones), and the weight limit.
- **Safety and isolation:** mains or not, insulation class (functional / basic / reinforced), isolation voltage, standard (IEC 62368-1, IEC 61010-1, IEC 60335…).
- **Other:** lifetime and duty cycle, cooling airflow, test points and programming headers, RoHS, how it will be tested.

## 2. Save the requirements
Write them to `design-requirements.md` in the project folder with the Write tool, so they survive a cleared chat and other sessions can read them. Use these sections, one line per item, each marked **given** (from the user or their files) or **assumed** (a lab default because they didn't know):
1. Function and electrical (inputs, outputs, power, frequencies, interfaces)
2. Size and outline (and the source: sketch, enclosure drawing, typed)
3. Layers and layout (layer count, part sides, where sections and connectors go)
4. Temperature
5. Cost, quantity, fab and assembly
6. Mechanics (mounting, heights, keep-outs, heatsink, thickness)
7. Environment and standards (only what applies)
8. User notes, in their words, and a list of the attached files
9. **Design decisions:** what the requirements mean for the design (step 3)

Then show a short summary and confirm:
```
<choices>
Start the design with these requirements?
- Yes, start (Recommended)
- Change something
</choices>
```
When a requirement changes later, update the file and say which decisions it changes.

## 3. Turn the requirements into design decisions
Apply them with the `powerlab-pcb-design-rules` skill. The section numbers below are from it. Write each decision under "Design decisions", and tell the user about any that costs extra (§2.0) before using it.
- **Size:** the outline comes first (§3.1), with ≥ 0.3 mm loose mechanical fits (§2.1). Price scales with area, so keep it compact unless the size is fixed.
- **Layers:** 2 unless routing, EMI or the power stage really needs 4 (§2.0, §3.1). A strict EMI target with fast switching edges is a good reason for 4 with a solid GND plane; say so.
- **Temperature:**
  - Every part must be rated for the maximum ambient plus its own heating (0-70 °C commercial, -40-85 °C industrial, -40-125 °C automotive grade 1). Electrolytic capacitor life halves for every 10 °C hotter.
  - Track sizing uses ΔT = 10 °C (§3.3). The hottest copper (ambient + ΔT + nearby hot parts) should stay well below the board's ~130 °C limit. Above about 105 °C, standard FR-4 TG150 is marginal: propose high-TG material (costs extra).
- **Cost:** stay inside the standard-price spec (§2.0). List anything outside it with the requirement that forces it. Fewer unique parts and one-sided assembly cut assembly cost.
- **Mechanics:** mounting holes and keep-outs (§3.1), connectors at the edge facing out and locked, height-limited areas recorded as notes, heatsinked parts placed where the heatsink fits.
- **Keep-out areas:** for each one, write down its shape and size, **which sides** it covers (top, bottom or both) and what it keeps out (all parts, copper, or only switching parts and power copper) and what may go inside (e.g. small passives under an encoder ring). Don't narrow it to the side the user mentioned: a magnetic encoder or a sensor is disturbed through the board, so ask whether the other side may hold parts, and record the answer. At placement, draw an area that keeps out all parts as a rule area on those sides (footprints, and tracks or pours where copper is kept out). An area that lets some parts in gets no footprint rule area (DRC would flag those parts): pass it to `check_part_spacing` as a keep-out with `allow` (the reference prefixes allowed inside, e.g. `["R", "C"]`), and keep copper out with a tracks/pours rule area where needed.
- **Voltage and environment:**
  - Clearances come from the IPC-2221B table (§3.3) for the highest voltage between nets.
  - **Altitude:** air insulates less in thin air. IPC-2221B has its own column for uncoated outer layers above 3050 m, with much larger values. For IEC 60664-1 designs, multiply the clearances by its altitude factor (about 1.14 at 3000 m, 1.29 at 4000 m, 1.48 at 5000 m).
  - **Mains, isolation or a safety standard:** creepage and clearance come from that standard, the insulation class and the pollution degree, not from IPC-2221 (§3.3). Ask the user to confirm those values before layout.
  - **Humidity, condensation, dirt:** a higher pollution degree, so larger creepage; conformal coating if the user plans it; slots under isolation barriers if creepage is short.
  - **EMI/EMC:** input filter footprints, a small switching loop, a solid GND return, stitching vias, and a spot for a common-mode choke and Y capacitors on the input. Put them in the schematic as `LAYOUT:` notes (§1.7), so placement and routing pick them up.
  - **Vibration:** no tall unsupported parts; glue or clamp heavy parts; locking connectors; mounting holes near heavy parts.

## Afterwards
Before any later schematic, placement or routing step, read `design-requirements.md`. If a change would break a requirement (the board grows past the enclosure, a part isn't rated for the temperature), stop and say which one.

You can make mistakes, and the standards' values depend on their edition and the product: tell the user to check the clearance, creepage and altitude numbers against the standard they design to.
