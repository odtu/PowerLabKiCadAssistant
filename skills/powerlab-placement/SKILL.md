---
name: powerlab-placement
description: Place the parts of a KiCad PCB the METU Power Lab way, starting from a block plan the user approves. Use when the user asks to place the parts, do or redo the placement, lay out or arrange the board or a block ("do placement", "place the components", "place the power stage", "where should the parts go"), or moves from the schematic to the layout. Covers the block plan drawn on the board outline and the early review with the user before any part is placed, which connections decide where each block goes (gate drive before the MCU), placing block by block, and the design review that follows.
---

# Placement starts with a block plan

Most placement mistakes are block mistakes: the gate driver on the wrong side of the legs, the MCU in the place the driver needed, a connector across the board from its circuit. Found after 150 parts are placed, they mean starting again. So **plan the blocks first, show the plan, and ask the user before placing any part.**

Example: on TestPCB2 the DRV8323 sat between legs A and B, so its gate lines were 8–12 mm to leg A, 20–24 mm to leg B and 37–40 mm to leg C. One of the lab's own motor drivers has the same parts on a round board: the three MOSFETs are on the bottom about 21° apart, the DRV8323 is on top right behind the middle leg, and the MCU went round the board to where there was room.

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
- Write the plan as an SVG in the views folder, e.g. `00-block-plan.svg`, in board millimetres (viewBox from the outline's extents; `get_board_extents`, `get_component_list` for the fixed parts):
  - the outline, holes, keep-outs and fixed parts as they are on the board;
  - each block as a labelled box (or ring sector on a round board) of about its real size, at its planned place and angle; top side solid, bottom side dashed, and a legend saying so;
  - the top-ranked links as lines with their expected length in mm (e.g. "gate A 14 mm"), thickest for gate drive and hot loops;
  - a dark background (`#001023`), light lines and text, like the board views.
- Open it with the Read tool so the panel shows it. Then, in a few short lines: where each main block goes and on which side, the expected lengths of the top-ranked links (gate lines to every leg), and the trade-offs you made. End with the question:

  ```
  <choices>
  Is this block plan good, or do I need to move a part or block?
  - Good, place it (Recommended)
  - Move a block
  </choices>
  ```

- **Stop and wait for the answer.** Don't place parts before the user agrees. If they move a block, redraw the plan and ask again.
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
