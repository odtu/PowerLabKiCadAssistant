---
name: powerlab-component-research
description: Choose parts for a design the METU Power Lab way, from the lab library first, then the LCSC/JLCPCB catalogue and the distributors (Digi-Key, Mouser, Farnell), with every shortlisted value checked in its datasheet. Use when the user asks to find, choose, pick, select, suggest, recommend, compare or replace a component ("find me a 100 V MOSFET", "which buck converter for 48 V to 5 V 3 A", "suggest a gate driver", "cheaper alternative to…", "this part is out of stock, what else", "compare these three", "what should I use for the current sense"), asks what part fits a requirement, or needs a part the schematic doesn't have yet. Covers turning the need into hard requirements and margins, the lab library, catalogue search (parametric and free text), stock and price, datasheet checks, the comparison table, the recommendation, and getting the chosen part into the lab library and the design.
---

# Component research

The goal is a part the user can buy, place and trust: it meets the requirements with margin in its datasheet, it's in
stock, and its symbol and footprint exist or can be made from the datasheet. Never recommend a part from memory: every
rating in the answer comes from its datasheet (load `powerlab-datasheet-lookup` for how to get and read it).

Tools (kicad MCP): `search_symbols` (lab library: `library: "METUPowerLab"`), `search_lcsc_catalog` (catalogue),
`digikey_search_parts`, `mouser_search_parts`, `farnell_search_parts` (distributors' stock, price, lifecycle;
`digikey_test_connection` when Digi-Key reports a key problem),
`fetch_datasheet` / `read_datasheet`, `search_parts_registry` (ready-made KiCad parts when the lab has none),
`search_footprints`. Report progress part by part in short lines; the user watches.

## 1. Requirements

Write the need as a short list of **hard requirements** (must meet) and **preferences** (rank by), e.g. for a
high-side switch on a 48 V rail: Vds, continuous and pulse current at the board's temperature, Rds(on) at the gate
drive voltage, gate charge (switching frequency), package (thermal, hand soldering), logic-level or not.

- Take the numbers from the schematic, `design-requirements.md` and the user's words. Read the circuit around the part
  (`get_schematic_component`, the net's other parts) for voltages, currents and the gate drive.
- **Margins:** use the ones in `design-requirements.md` if it gives them. Otherwise say which margin you used and why
  (e.g. "Vds ≥ 1.5 × the 48 V rail for switching ringing: 75 V, so a 80–100 V part"), as your assumption, not as a
  lab rule; the lab rules don't set part derating.
- Ask only for what decides the choice and can't be read from the design (with `<choices>`), e.g. the load current
  when nothing gives it. Otherwise state the assumption and go on.

## 2. Lab library first

`search_symbols` with `library: "METUPowerLab"` and words from the description the lab uses (e.g. "N-CH MOSFET",
"Buck", "TVS", "Gate driver"; the libraries are by kind: Transistors_MOSFETs, Regulators_BuckConverters,
GateDrivers_LowSide, Amplifiers_CurrentSenses, Diodes_TVSDiodes, …). A lab part that meets the requirements wins
unless another is clearly better: its symbol, footprint and 3D model are made and checked, and the lab has used it.
Check it like any other candidate (§4).

## 3. Candidates from the catalogue

`search_lcsc_catalog`:
- **Parametric** where a table exists (`mode: "tables"` lists them; `table` + `mode: "tables"` gives its fields):
  `mosfets`, `diodes`, `capacitors`, `resistors`, `ldos`, `voltage_regulators`, `buck_boost_converters`,
  `boost_converters`, `fuses`, `microcontrollers`, `usb_c_connectors`, … Filters are `<field>_min` / `<field>_max` in
  SI units, plus `package`; `sortBy` `priceUsd` or a field. Read `ignoredByService`: the service skips some filters
  (booleans like `is_schottky`), the tool then only checks the rows it got, so widen with `mode: "search"`.
- **Free text** for the rest, and always for the kinds without a table (gate drivers, current-sense amplifiers, op-amps,
  inductors, eFuses). The service needs every word in one listing, so use few words, in the catalogue's terms: the
  kind, plus at most one number, e.g. "gate driver", "100V half-bridge", "current sense amplifier", "inductor 10uH".
  Check the other requirements in the results (`description`, `attributes`). If nothing matches all words, the tool
  drops words from the end and says what it searched for (`searchedFor`).
- **Makers' own selectors** (WebSearch: TI, Infineon, onsemi, ST, Nexperia, Vishay parametric search) when the
  catalogue is thin. A part found there still needs an LCSC or Digi-Key listing, or another buyable source.

**Distributors:** `digikey_search_parts`, `mouser_search_parts`, `farnell_search_parts` (store `tr.farnell.com` by
default). LCSC is strong on Chinese makers and JLCPCB assembly; the three on Western makers and new parts that
reach LCSC late:
- **Candidates:** a phrase in the distributor's terms, e.g. "MOSFET N-CH 100V", "gate driver half-bridge 100V",
  "current sense amplifier", "0402 100nF 50V X7R" (Digi-Key first, its parameters are the cleanest). Check the
  requirements in `parameters`; `productsCount` says how many more there are (`offset` pages them).
- **Every shortlisted part, by its part number,** wherever it was found, at all three: Digi-Key `keywords`,
  Mouser `keywords` (its `partNumber` wants Mouser's own number), Farnell `partNumber`. Digi-Key `preferPackaging:
  "CT"` (cut tape) for prototype quantities, `"TR"` for a reel. `active: false` (NRND, Obsolete, End of Life, Last
  Time Buy, no longer manufactured) drops the part like the datasheet's mark would. Mouser also lists parts it
  doesn't sell (`orderable: false`, no Mouser number or prices): that's "—" in its column, not stock 0. Farnell
  lists a part once per packing: for prototypes quote the cut-tape row, not `reeled: true` (order code …RL, a
  reeling charge on top); its `leadTimeDays` is the restocking time, given even when the part is in stock.
- **Their `datasheet` link is usually the maker's current copy:** pass it as `fetch_datasheet`'s `url` (§4).
- **Currencies differ:** Digi-Key and Mouser give the currency with each price, Farnell its store's. Compare in one
  currency only when the user asks, and say the rate and its date.
- **No keys:** if a search reports missing or rejected keys, say so in one line ("Mouser not searched: no API key in
  the server's .env") and go on with the others. Never leave a distributor out without saying it.
- **Turkish distributors** (Özdisan, Ekom) have no search the tools can use and give price and stock on request:
  when the user wants local supply, say they can ask for a quote with the part numbers.

Catalogue values are the distributors' parsed parameters: some are missing or wrong. Use them to shortlist, never to
decide. Drop parts with little stock for the quantity (stock below about 10 × the boards' need at every
distributor), and parts the maker marks not for new designs (NRND, obsolete: the datasheet's first page, the maker's
page or a distributor's lifecycle status).

Shortlist 3 to 5, different makers where possible. Say in one line why each made the list.

## 4. Check each shortlisted part in its datasheet

`fetch_datasheet` with `part`, `maker`, `url` when known (a distributor's `datasheet` link, usually the maker's file) and `lcsc`
(the catalogue's LCSC number, so the copy comes without the user). For each part read, with the page: every hard requirement (absolute maximum and recommended
operating conditions, the electrical characteristics at the design's conditions, not at 25 °C when it runs hot),
the package's thermal resistance, and what the preferences need (Qg, Coss, quiescent current, efficiency curve at the
load, …). Confirm table values on the rendered image (`read_datasheet` `render` with `clip`). A part that fails a
hard requirement leaves the list, with the reason.

## 5. Compare and recommend

A compact table, one row per part, a source in each cell (`p N` of its datasheet; the distributor's column for stock
and price):

| Part | Maker | Key ratings… | Package | LCSC | Digi-Key | Mouser | Farnell | Lab library | Datasheet |

- Each distributor cell: stock / price at the user's quantity with its currency (LCSC's `priceTiers`, the others'
  `pricing`; for Digi-Key say which packaging, cut tape or reel). "—" where the distributor doesn't list the part,
  "not searched" where its search wasn't available. JLCPCB `basic` / `preferred` parts cost less to assemble
  there; a part LCSC doesn't have must be sent to the assembler or soldered by hand: say so.
- **Lab library:** yes (name), no.
- **Datasheet:** which copy and its date ("LCSC's copy, June 2020").
- Then **one recommendation** with the reason in a sentence, and a runner-up (second source, or the cheaper part if
  the first has margin to spare). Say what still needs the user: a value you assumed, a marginal rating, a datasheet
  older than the maker's current one before ordering.
- For a kept record, write the comparison to `documents\component-research-<what>.md` (the panel makes it a PDF).

## 6. Into the design

- **In the lab library:** place it (`add_schematic_component` or `replace_schematic_component`), library fields and
  Value as the library has them (`powerlab-pcb-design-rules`).
- **Not in the lab library:** offer to make the symbol and footprint in the user's library clone, following
  `HowToCreateNewDesign/DesignRules.md` in that clone, with pins and pads from the datasheet's pin table and package
  drawing (and `search_parts_registry` for a verified ready-made footprint to compare against). The panel's **Share**
  sends new parts to the lab library for review; say that pinouts and pad sizes must be checked against the datasheet
  before sharing.
- Changing a part on a placed board: its footprint may differ; say what moves before replacing it.
