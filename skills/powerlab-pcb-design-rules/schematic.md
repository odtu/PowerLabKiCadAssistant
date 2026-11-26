## 1. Schematic rules

Follow these steps in order when starting a new schematic.

### 1.1 Page setup and title block

- Every sheet is **A4** (landscape).
- Keep the drawing sheet the user or project already uses. Don't replace it.
- Fill in Title, Revision and Date on every sheet. If the title block uses text variables (`${...}`), define them in Schematic Setup → Project → Text Variables so they don't print raw.

### 1.2 Sheet structure

- Always use **hierarchical sheets**, one per functional block. Examples: Power Supply, MCU Core, RF Section, Gate Drive, Power Stage, Current Sensing, Communication. Repeated blocks (e.g. three inverter phases) reuse the same sub-sheet.
- The **root sheet is the main page.** It holds general info and images:
  - project name, revision, and a short description of the board
  - key specs (input voltage range, output/phase current, power, switching frequency, MCU, interfaces)
  - images: a block diagram, board render or photo (placed as images in the schematic)
  - the hierarchical sheet symbols for all sub-sheets, arranged as a block diagram
  - revision history, if the project keeps one
- **Connections between sheets use global net labels.** Inside a sheet, connect with wires (§1.4); use a local label only where a wire would be too long. Power rails use power symbols (§1.5).

### 1.3 Components: PowerLabKiCadLibraries only

- **Every** symbol and footprint comes from https://github.com/odtu/PowerLabKiCadLibraries. Don't use KiCad's stock libraries or project-local libraries.
- **Exception: power symbols come from KiCad's built-in `power` library** (Place → Power Symbols): `power:GND`, `power:+3V3`, `power:+5V`, `power:VBUS`, `power:PWR_FLAG` and so on. They are net markers, not parts. Never make a lab or project library of power symbols.
- If a part isn't in the repo, **stop and tell the user**. The part is added to PowerLabKiCadLibraries first (symbol + footprint + 3D model), then used. Never silently substitute a "similar" part or a stock-library part.
- **Place the library part as it is.** Each lab symbol is one orderable part: its name says which one (`22 µF 100V`), its Value is the plain value (`22 µF`), and its ratings, MPN, manufacturer and distributor numbers are fields of their own. When placing it, don't pass a value or footprint: the part keeps the library's Value and every library field. Never type a rating, package or tolerance into the Value, and never make a project or new library symbol for a part the library already has. A different value or rating is a different lab symbol: pick that one, or replace the part with it.
- After placing, Symbol Properties must list the library's fields (Manufacturer Number, Voltage Rating, …). If a placed part shows only Reference, Value, Footprint, Datasheet and Description, update it from the library (KiCad: Tools → Update Symbols from Library; kicad MCP: `update_symbol_from_library`): that adds the missing fields and puts back the library's Value.
- **Large ICs are split into units.** A microcontroller, DSP, FPGA or any IC with more than about 40 pins is a multi-unit symbol, one unit per function, e.g. power and ground, clock and reset, debug, analog inputs, comparators/PGAs, and GPIO/peripheral banks. Place each unit next to the circuit it serves, on its sheet. If the library symbol is one big block, stop and tell the user: it is split into units in PowerLabKiCadLibraries first, then used. Smaller ICs such as a gate driver stay one unit.

### 1.4 Wiring

- **Never connect a pin directly to another pin, or put a pin end directly on a junction.** Each pin gets its own wire segment to the junction. At a 4-way node, all four pins reach the junction dot through wires, like a plus sign of wires, not four legs touching.
- **Never put a power symbol directly on a pin.** Draw a wire of at least one grid step (2.54 mm) from the pin to the GND or supply symbol, so the connection is visible and the wire takes its net-class colour and width (§1.6).
- **Draw it like a normal schematic: wires, not net labels, inside a sheet.** Place parts that connect next to each other and join them with wires, so the circuit can be read without searching for matching names. Decoupling capacitors, pull-ups, dividers, RC filters, gate resistors and bootstrap parts sit beside the pin they serve and are wired to it, with a short wire to their own GND or supply symbol. Never put a label at both ends of a connection that a short wire could make.
- **Use a net label only where a wire would hurt readability:**
  - the net goes to another sheet (global label, §1.2);
  - the wire would be long (more than about 10 grid steps, 25 mm) or would cross other wires or symbols;
  - the net goes to many places across the sheet, such as an I²C or SPI bus.
- Keep wires short and direct. If a wire gets long, first move the part closer; only if that doesn't work, label both ends instead.
- A wired net that needs a name (for net classes, test points or simulation) gets **one** label on its wire, not a label at every pin.
- Put a junction dot on every T and cross connection. Wires only cross without a dot when they are not connected.
- Use the **2.54 mm (100 mil)** schematic grid. Every symbol, pin, wire, label and junction sits on it.
- Signal flow runs left to right, and power runs top to bottom (higher voltage at the top).

### 1.5 Net naming and power symbols

- **Never use bare `VCC` / `VDD`.** Name each rail by voltage *and* domain: `+5V_DDR`, `+3V3_RF`, `+3V3_MCU`, `+3V3_A`, `+12V_GD`, `+48V_DC` / `VBUS`.
- Grounds get separate names only when they really are separate domains: `GND`, `PGND`, `AGND`, `GND_ISO1`.
- Why: layout rules (net classes, widths, clearances) are assigned by net name, so the names must say what the net is.
- Signal nets are UPPER_SNAKE_CASE and describe the function: `PHASE_A`, `GATE_AH`, `ISENSE_A_P` / `ISENSE_A_N`, `PWM_AH`, `NFAULT` (active-low prefix `N`).
- **Place rails with KiCad's `power` symbols** (§1.3). A power symbol's Value is its net name, so for a rail with no stock symbol, place the closest one and change its Value: `power:+3V3` → `+3V3_MCU`, `power:+5V` → `+5V_SYS`, `power:GND` → `PGND`.
- **GND symbols always point down. VCC and other supply symbols always point up.** Never rotate them sideways.

### 1.6 Net classes and power-net styling

Set these up in Schematic Setup → Net Classes, so every wire picks up its style automatically from its net name. Don't style wires one by one.

- **GND nets are drawn thicker and blue. Supply nets are drawn thicker and red.**

| Net class | Pattern(s) | Schematic wire colour | Schematic wire width |
|---|---|---|---|
| GND | `*GND*` | Blue (0, 0, 255) | 0.3 mm (default wire is 0.15 mm) |
| Power | `+*`, `-*`, `VBUS*` | Red (255, 0, 0) | 0.3 mm |

- These are the same net classes as §2.6, so the PCB rules stay attached. Give the GND class the Power track/clearance values.
- The patterns rely on the net names in §1.5.
- **Set them up when the project is created, before drawing any wire.** With the kicad MCP, `create_netclass` with `projectPath` does it without a board: `name: "GND", patterns: ["*GND*"], schematicColor: "#0000FF", wireWidth: 0.3` and `name: "Power", patterns: ["+*", "-*", "VBUS*"], schematicColor: "#FF0000", wireWidth: 0.3`, plus the track and clearance values from §2.6; then reopen the schematic (File → Revert) so KiCad reads them. Check that a GND wire is blue and thick.

### 1.7 Layout notes on the schematic

- Write layout requirements **as text notes next to the parts they concern**, and start each one with `LAYOUT:` so it's easy to find. Examples:
  - `LAYOUT: Place C5 as close as possible to U1 pin 6`
  - `LAYOUT: 50 Ω impedance` (high-speed / RF traces)
  - `LAYOUT: Kelvin connection to R12 pads, route ISENSE_A_P/N as diff pair`
  - `LAYOUT: C20–C22 directly across Q1 drain / Q2 source (hot loop)`
  - `LAYOUT: Keep away from PHASE_A switch node`
- Before starting a PCB layout, collect every `LAYOUT:` note and treat them as requirements alongside §3.

### 1.8 Clean text

- Show **Reference**, **Value** and the key ratings the library symbol already shows (a capacitor's voltage rating, a resistor's power and tolerance, an inductor's current…). Keep every other field (Footprint, MPN, Manufacturer, Datasheet, …) in the symbol but hidden. Visibility comes from the library: don't hide its ratings and don't show other fields.
- **Ratings are fields, never part of the Value.** A 100 V DC-link capacitor reads `22 µF` with `100V` under it from its Voltage Rating field, not `22 µF 100V`. A generic 10 k pull-up is just `10 kOhm`.
- No overlapping text. References and values never cross each other, wires or symbol bodies. Autoplace the fields, then check visually.
- All text reads horizontally. Keep reference and value on the same side of each symbol, consistently.

### 1.9 Schematic done-checklist

- [ ] A4 on every sheet; title block filled, no raw `${...}`
- [ ] Hierarchical structure, main page with info and images, global labels between sheets
- [ ] Inside each sheet, parts are wired to each other (decoupling caps, pull-ups, dividers beside their pins); labels only between sheets, on buses, or where a wire would be long
- [ ] All parts come from PowerLabKiCadLibraries, placed with all their library fields and the library's Value (no ratings typed into the Value)
- [ ] MCUs and other large ICs (> ~40 pins) placed as multi-unit symbols, each unit beside the circuit it serves
- [ ] No pin-to-pin, pin-on-junction or pin-on-power-symbol connections
- [ ] Power symbols from KiCad's `power` library; no bare VCC/VDD; every rail named by voltage and domain; GND symbols point down, supplies up
- [ ] GND and Power net classes set with their patterns: GND wires blue and 0.3 mm, supply wires red and 0.3 mm (look at a rendered sheet)
- [ ] `LAYOUT:` notes on every placement- or impedance-critical part
- [ ] Clean text: Reference, Value and the library's visible ratings only, no overlaps
- [ ] Every unused pin has `no_connect`, PWR_FLAGs placed, annotation complete, **ERC 0 errors**
