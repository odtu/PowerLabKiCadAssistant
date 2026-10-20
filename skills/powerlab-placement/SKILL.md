---
name: powerlab-placement
description: Place the parts of a KiCad PCB the METU Power Lab way, starting from a block plan the user approves. Use when the user asks to place the parts, do or redo the placement, lay out or arrange the board or a block ("do placement", "place the components", "place the power stage", "where should the parts go"), or moves from the schematic to the layout. Covers the block plan drawn on the board outline and the early review with the user before any part is placed, which connections decide where each block goes (gate drive before the MCU), placing block by block, and the design review that follows.
---

# Placement starts with a block plan

Most placement mistakes are block mistakes: the gate driver on the wrong side of the legs, the MCU in the place the driver needed, a connector across the board from its circuit. Found after 150 parts are placed, they mean starting again. So **plan the blocks first, show the plan, and ask the user before placing any part.**

For example, on TestPCB2 the DRV8323 sat between legs A and B, so its gate lines were 8–12 mm to leg A, 20–24 mm to leg B and 37–40 mm to leg C. One of the lab's own motor drivers has the same parts on a round board: the three MOSFETs are on the bottom about 21° apart, the DRV8323 is on top right behind the middle leg, and the MCU went round the board to where there was room.

## 1. Collect
- `design-requirements.md`, the design rules (`powerlab-pcb-design-rules` §3.1, §3.2), and the schematic's `LAYOUT:` notes.
- The outline, the keep-outs and the fixed parts: connectors, mounting holes (§3.1: ask plated + GND or NPTH), switches, anything the enclosure decides.
- The functional blocks, by schematic sheet and function: power input, each half-bridge leg, gate driver, each converter, MCU, sensors, communication, debug. For each, write down:
  - its anchor part (the IC or switch the rest gathers round);
  - its rough size (footprint areas plus room for its passives);
  - which pins face which way: with `get_component_pads` on the anchor, which side of the IC each pin group is on (gate outputs, PWM/SPI, ADC, supply). That decides the anchor's angle.
  - the blocks it connects to, with how many nets and what kind.

## 2. Rank the connections
The links between blocks don't matter equally. Give the shortest distances to the top of this list; lower ones get the room that's left.
1. **Hot loops:** input caps across the switches, converter input loops. Inside the block, on one side, with no via.
2. **Gate drive and switch sensing:** driver → each gate, source/Kelvin return and current-sense pair. **Put the driver in the middle of the switches it drives**, so every leg gets the same short lines: behind the middle leg, and on the other side of the board when it has parts on both (stacked, a via long). Equal and short to every leg beats very short to one and long to another.
3. **Converter control:** feedback, bootstrap, compensation, at their IC.
4. **Analog sense** to the ADC pins: short, away from the switch nodes.
5. **MCU ↔ driver** (PWM, SPI, enable, fault): digital and slow next to the gate lines. A few centimetres is fine. **The MCU moves, not the driver:** put it in the free space the power stage leaves, still near the driver, with its PWM/SPI side facing it and without crossing the power stage. Its crystal and decaps stay inside the MCU block.
6. **Connectors, debug and test points:** at the edge, near the block they serve.

Also keep: power flowing one way (input connector → protection → bulk → legs), analog and sensors away from switching parts, keep-outs on both sides.

When two blocks want the same place, the one with the higher-ranked links gets it and the other moves.

## 3. Draw the plan and ask
- Write the plan to `placement\block-plan.json` in the project folder. The panel shows it as soon as the file is written: a card with the board, each block on it, and a list of the blocks. When the user hovers a block, it lights up. When they click it, KiCad selects the block's parts in the PCB editor, and the schematic editor shows them too. So every block lists its parts in `refs`, and every part on the board belongs to one block.
- Everything is in board millimetres, in KiCad's coordinates (y down). Angles are degrees clockwise from +x, as they look on the board. Take the holes and fixed parts from the board (`get_component_list`, `get_component_pads`).
- **Outline:** `"outline": "board"` draws the board's own Edge.Cuts, whatever its shape (arcs, notches, rounded corners, cutouts), so use it whenever the board has an outline. The panel reads the saved `.kicad_pcb` in the project folder; if there are several, name it with `"board": "<file>.kicad_pcb"`. Save the board first. Only before the outline exists, draw the planned one yourself (`circle`, `rect` or `polygon`).
- Shapes: `{"circle": {"center": [x, y], "diameter": d}}`, `{"ring": {"center": [x, y], "inner": d1, "outer": d2}}`, `{"sector": {"center": [x, y], "r": [r0, r1], "angle": [a0, a1]}}` (ring sectors, for round boards), `{"rect": {"center": [x, y], "size": [w, h], "angle": a}}`, `{"polygon": [[x, y], ...]}`. Size each block to about its real area (footprints plus room for their passives).
- The file:

  ```json
  {
    "title": "<board> block plan",
    "outline": {"circle": {"center": [100, 100], "diameter": 91.25}},
    "cutouts": [{"circle": {"center": [100, 100], "diameter": 20}}],
    "holes": [{"circle": {"center": [140, 100], "diameter": 4}}],
    "keepouts": [{"name": "Encoder area", "sides": ["top"], "circle": {"center": [100, 100], "diameter": 47}}],
    "blocks": [
      {"id": "legB", "name": "Leg B", "detail": "Q2 · shunt · caps", "side": "top", "kind": "power",
       "refs": ["Q2", "R10", "R11", "C28", "C29"], "sector": {"center": [100, 100], "r": [29, 42], "angle": [333, 355]}},
      {"id": "u3", "name": "U3", "detail": "DRV8323", "side": "bottom", "kind": "gate",
       "refs": ["U3", "C20", "C21"], "sector": {"center": [100, 100], "r": [20, 28], "angle": [335, 353]}}
    ],
    "links": [{"from": "u3", "to": "legB", "label": "gate B ~6 mm", "kind": "gate"}],
    "notes": ["**U3 sits under leg B**, so all three legs get the same short gate lines."]
  }
  ```

  - `kind` sets the colour: `power`, `gate`, `mcu`, `supply`, `comms`, `sensor`, `analog`, `connector`, `debug`, `other`, and `text` / `logo` for silkscreen (below).
  - **Board texts and logos** go on the plan too, so the user can place them: the board-info line (§3.6), the "Designed with PowerLab KiCad Assistant and Claude" text, company or lab text the requirements ask for, and logos. One block each, `kind` `text` or `logo`, `name` the text itself (short) or the logo's name, sized to how big it will print, on its side. Board text has no reference: leave `refs` out, and a click shows KiCad what lies at the block's centre. A logo footprint gets its reference in `refs`. Reference designators aren't blocks; they stay with their parts. Like all silkscreen, put them in place after the parts (§3.6): move logos with `move_component`, and board text with `edit_board_text` once that tool exists (#70); until then, tell the user which texts to move by hand.
  - `side`: `top` (solid) or `bottom` (hatched).
  - `links`: the top-ranked connections between blocks for this board (gate drive, hot loops, sense lines, buses: whatever ranks highest here), with their expected length as the label, e.g. `gate A ~14 mm`. `kind`: `gate`, `power`, `signal` or `analog`. The panel measures the edge-to-edge gap between the two blocks itself (shown on hover and while the user drags); the label is your estimate of the track length.
  - Block shapes follow the board: on a rectangular board, `rect` blocks at 0/90/180/270° (§3.2); on a round board, `sector` blocks that follow the circle; along an odd edge, a `polygon` that follows it.
  - `notes`: two to four short lines: the trade-offs, and what changed from the last plan.
- Then, in a few short lines: where each main block goes and on which side, the expected lengths of the top-ranked links (gate lines to every leg), and the trade-offs you made. End with the question:

  ```
  <choices>
  Is this block plan good, or do I need to move a part or block?
  - Good, place it (Recommended)
  - Move a block
  </choices>
  ```

- **Stop and wait for the answer.** Don't place parts before the user agrees. If they want a block moved, change the file (the panel shows the new plan) and ask again.
- **The user can move blocks on the card themselves:** drag a block (a ring sector turns round its centre and moves in or out; other shapes move in x and y), turn a box or polygon (↻ 90°, ↻ 45°, ↺ 45°, or any angle typed in), or switch its side ("Move to bottom side" / "Move to top side"). While they drag, the links of that block follow it and show the measured gap between the two blocks. After the drop, those links keep a label like `gate A · 7.5 mm gap` until you measure them again. The panel writes each move into `block-plan.json` at once. "Send moves to Claude" then sends you a list of the moves. Read the file again: the shapes and sides there are the user's. Keep their positions; measure the links again, update `links` and `notes`, and write the file (the panel shows the new card). Then say what their moves change (gate-line lengths, rules, blocks that now overlap) and ask again. Don't move their blocks back without asking.
- Skip the plan only when the user says so, or when you add one small block to an existing placement (then say in one line where it goes and why).

## 4. Place
- Follow §3.2: fixed parts → power stage and hot loops → gate driver → each IC with its decoupling caps, then its other pin passives → the rest. Put each block's anchor at its planned place first.
- Finish each block before the next: passives by their connections (§3.2), `get_ratsnest` / `estimate_airwire_lengths`, `check_part_spacing`, and a close-up (`powerlab-visual-review`). Write one short line per block.
- If a block doesn't fit where the plan put it and moving it changes a top-ranked link (gate drive, hot loop), don't just put it elsewhere: show the changed plan and ask.
- Lab footprints may have their origin at a pad or a corner, not the centre: place from the pad positions (`get_component_pads`) and check them after the move.
- An exposed pad with thermal vias can be copper on both sides: on a bottom part, nothing on top may sit on it.
- Plated mounting holes on GND: `add_mounting_hole` with `plated` and `net`, or `edit_component` with `padNets: {"*": "GND"}` for holes already on the board.

## 5. Review
Go on with `powerlab-design-review` when the placement is done. Compare the result with the plan: the lengths of the top-ranked links, and every block still where the user agreed.
