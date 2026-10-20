# PowerLab KiCad Assistant

A side panel for **KiCad 10** that lets you ask Claude to do things in your design: create symbol and footprint libraries to the METU Power Lab standard, run ERC/DRC and explain the results, render 3D views, export fabrication files, and edit schematics and boards.

It runs [Claude Code](https://docs.claude.com/claude-code) on your computer with your own Claude account, and gives it KiCad tools through [KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server).

> **Early version.** Windows and KiCad 10 only. Expect rough edges and please [report problems](#reporting-problems).

![The PowerLab Assistant panel: suggestions and library updates; autorouting with a rendered board view; checking a footprint against an attached datasheet](docs/images/panel-overview.png)

<sub>Example sessions (illustrative). Left: start screen with suggestions and a library update. Middle: Claude routes the board, then renders and checks it. Right: a question about an attached datasheet, with another file ready to send. The board is the lab's open-source [Voltage Sensor Card](https://github.com/odtu/Powerlab/tree/master/Hardware/Voltage-Sensor-Board).</sub>

---

## ⚠️ Read this first

**AI makes mistakes.** Claude can get pinouts, footprints, pad sizes, ratings or connections wrong while sounding certain. Treat everything it produces as a draft:

- Check parts against the manufacturer datasheet.
- Run ERC and DRC yourself.
- Review the 3D view and the fabrication outputs before you order a board.

**It edits your files.** Claude changes schematic, board and library files directly. Keep your projects in git (or keep backups) so you can undo.

**Your design data goes to Anthropic.** Your messages, and any project files Claude reads, are processed by Anthropic under *your* Claude account and its terms. Don't use the assistant on designs that your NDA, employer or customer doesn't allow you to share with an AI service.

## Privacy: what goes where

| Data | Where it goes | When |
|---|---|---|
| Your messages and the project files Claude reads | Anthropic, under your Claude account | Every time you send a message |
| Library parts you choose to share | A pull request to [odtu/PowerLabKiCadLibraries](https://github.com/odtu/PowerLabKiCadLibraries), from your GitHub account | Only when you press **Share** and confirm the file list |
| Problem reports | A **public** issue on this repository | Only when you press **Submit** after reviewing the report |
| Library updates | Anonymous read from GitHub (`git fetch`) | When the panel opens, at most every 10 minutes |
| Plugin update check | Anonymous read from GitHub of the version number on this repository's stable branch; when it's newer, of that release's notes | When the panel opens or is shown, at most every 5 minutes |

**Nothing else is sent to METU Power Lab.** The panel has no analytics, telemetry or tracking.

Problem reports contain versions, the error and the panel's own stack trace. They **never** contain:

- project, board or sheet names
- part references or values, net names
- file contents or paths (replaced with placeholders)
- your messages or Claude's replies
- your selection or clipboard

**Stays on your computer:**

- your Claude login and your GitHub login (if you use one)
- the panel's settings (`%APPDATA%\PowerLabKiCadAssistant`)
- your conversation history (`%USERPROFILE%\.claude`, and the panel's copy in `%APPDATA%\PowerLabKiCadAssistant\chats`)
- design reviews and their PDFs (`design-review\` in your project; Microsoft Edge prints the PDF on your computer, offline)

The repository contains no API keys or tokens. Each user signs in with their own accounts.

## Requirements

- Windows 10 or 11
- [KiCad 10](https://www.kicad.org/download/windows/)
- A Claude account with Claude Code access (a paid Claude plan or an Anthropic API account)
- [Git](https://git-scm.com/download/win): `winget install --id Git.Git -e`
- [Node.js](https://nodejs.org/) 18 or newer: `winget install --id OpenJS.NodeJS.LTS -e`
- Optional: a GitHub account, to share library parts and file reports with one click

## Install

1. Close KiCad.
2. Download this repository (green **Code** button → **Download ZIP**, then unzip) or `git clone https://github.com/odtu/PowerLabKiCadAssistant`.
3. In PowerShell, in that folder:

   ```powershell
   powershell -ExecutionPolicy Bypass -File install.ps1
   ```

   The installer asks before every step. It will:

   - Install Claude Code with Anthropic's official installer, if you don't have it yet.
   - Download KiCAD-MCP-Server at a tested version, build it, and install its Python packages into KiCad's own Python. No admin rights are needed.
   - Copy the panel into your KiCad 10 folder.
   - Clone the METU Power Lab library and point KiCad's `METUPOWERLAB_*` paths at it. Your KiCad settings are backed up first.
   - Turn on KiCad's API server, which the panel needs.
   - Optionally install GitHub CLI and sign you in.

   If you already have a clone of the library, add `-LibraryPath D:\path\to\PowerLabKiCadLibraries`.

4. Sign in to Claude Code once: run `claude` in a terminal, follow the login, then type `/exit`.
5. In the **Schematic Editor**, go to **Preferences → Preferences → Schematic Editor → Toolbars**. Add **IPC/Scripting plugins** to the **Top main** toolbar. KiCad doesn't show plugin buttons there by default.

To remove it later, run `uninstall.ps1`.

## Updating

Changes are tried on the `test` branch first. When they're released to `main`, the stable branch, the panel shows a bar like *PowerLab Assistant 0.1.2 is available: …* within about 10 minutes, with **What's new** and **Update** buttons.

- **Update**, if you installed from a `git clone` of this repository: a console window pulls the new version and runs `install.ps1 -Update`. Restart KiCad when it says done.
  - `-Update` asks no questions and only replaces the panel's files. It also rebuilds the KiCad tools, but only if their pinned version or the lab's fixes to them (`patches/kicad-mcp.patch`) changed.
  - Your library, KiCad settings and GitHub setup aren't touched.
- **Update**, if you installed from a ZIP download: the release page opens in your browser. Download it and run `install.ps1 -Update`.

To be notified by e-mail as well, use **Watch → Custom → Releases** on this repository.

## Use

Click the **PowerLab Assistant** button on the toolbar of the PCB Editor or the Schematic Editor. Type a short request and press Enter. For example:

- *Create a symbol and footprint library for the LMR38020*
- *Run DRC and summarize the violations*
- *What is this part connected to?* (select it first)
- *Render the top side and show it to me*

The panel shows each step Claude takes, plus any images it renders.

- **Models:** the model picker under the input box switches between Claude models. The default is **Opus 5.5 at high effort**. To change the effort, set `"effort"` (`low`, `medium`, `high`, `xhigh` or `max`) in `%APPDATA%\PowerLabKiCadAssistant\settings.json`.
- **Attachments:** attach screenshots, datasheets (PDF) or other files with the 📎 button, or paste or drop them into the input box. Pasted and dropped files are kept for a week in `%TEMP%\PowerLabAssistant\attachments`.
- **Usage:** the corner under the input box shows how much of your Claude plan's limit is used (e.g. *5h 49%*) and how full this chat's context is. Hover for the reset time. Start a new chat (**+**) when the context gets full.
- **One panel for both editors:** the button in the PCB Editor and the one in the Schematic Editor show or hide the same panel, with one chat per project. Ask about either side from wherever you are: Claude sees the board and the schematic, which editor you're working in, and what is selected in each.
- **One panel per KiCad:** with two KiCad windows open (two projects), each one's button opens a panel of its own, titled with its project, and Claude works only on that KiCad. KiCad 10 on Windows gives an API connection only to the first KiCad, so the panel leaves an empty `%TEMP%\kicad\api.sock` file that makes every KiCad started afterwards open its own. If a panel says to restart its KiCad, that KiCad was started before the file existed: save, close it and start it again.
- **Chats are kept:** closing the panel, the editor or KiCad doesn't lose the chat. Reopen the panel on the same project and it continues where you left off. **+** starts a new chat.

**Board:**

- Some board edits (move, rotate, delete and others) apply live through KiCad's API server.
- When Claude changes the board file instead, the panel tells you to use **File → Revert**.

**Schematic:**

- Before each message, the panel makes sure the schematic is saved.
- After Claude changes a sheet, the panel reloads it in the Schematic Editor for you.

## Skills

Skills teach Claude how the lab does specific jobs. The installer copies them to your Claude skills folder (`%USERPROFILE%\.claude\skills\powerlab-*`). Claude uses one automatically when your request matches it, both in the panel and in a terminal session started from the panel.

| Skill | What it does | Try |
|---|---|---|
| `powerlab-board-requirements` | Before a new board is started, Claude asks for its requirements in a few short rounds of answer buttons (every question also has **Other…**, a box for your own answer): what it does, size, layers and layout, working temperature, cost and quantity, mounting and mechanics, and, if you need them, special conditions like altitude, EMI/EMC targets, humidity, vibration or a safety standard. You can attach a hand sketch, an enclosure drawing or a block diagram, add notes in your own words, or answer "use the lab defaults". The answers go into `design-requirements.md` in your project, with what they mean for the design (clearances, layers, part ratings, outline), and Claude keeps to them in later steps. | *Start a new board from scratch* |
| `powerlab-pcb-design-rules` | The lab's [PCB design rules](https://github.com/odtu/Powerlab/blob/master/KiCAD/PCB_DESIGN_RULES.md) (without the lab's drawing sheet, logo and QR code: boards get a small "Designed with PowerLab KiCad Assistant and Claude" silkscreen text instead). It covers the PCBWay standard-price spec, DRC constraints, net classes, schematic rules, and placement, routing, via and pour rules. It also carries a **review handbook** of 233 layout rules, collected from manufacturer application notes, fab capability pages and expert reviews of real boards, each with a severity, what it looks like on a board, the fix and its sources. Claude follows it for any schematic or PCB design work. | *Set up the design rules for this board* |
| `powerlab-placement` | Before placing any part, Claude shows a block plan in the panel: the board with each functional block where it would go, top side solid and bottom side hatched, and how long the important connections will be. Hover a block to light it up; click it and KiCad selects its parts in the PCB editor and the schematic. Drag blocks to where you want them, or move one to the other side with **Move to bottom side** / **Move to top side**, then press **Send moves to Claude**: Claude checks your plan and updates it. Gate drive and hot loops get the shortest distances: the gate driver sits in the middle of the MOSFETs it drives, and the MCU moves to the free space near it. It shows you the plan and asks whether to move anything; only then does it place the parts, block by block, and run the design review. | *Do the placement* |
| `powerlab-visual-review` | Claude renders the board (2D layer views in colour, plus 3D) after every placement or routing step. It looks at each view against the design rules, fixes what it sees, and shows you the views in the panel. Renders go to `%TEMP%\PowerLabAssistant\views` and are cleaned after a week. | *Show me the routing* |
| `powerlab-design-review` | When Claude finishes placing or routing a board, it reviews its own work: DRC (zones refilled, every track error, schematic parity), rendered views, the lab rules and the review handbook. It fixes what it can on its own, checks again, and repeats until nothing it can fix is left (at most 5 rounds). What needs your decision or information (a connector to move, a current it doesn't know, a track only you can delete in KiCad) goes on a *Needs you* list. The final review shows in the panel: the verdict, open findings by severity, what was fixed, and the board views. Click any place in it (marked ⌖) and KiCad selects those parts or that net in the PCB editor and zooms there; the schematic editor follows, on the right sheet. It is also saved as `design-review\design-review.pdf` in your project (**Open PDF**). | *Review the board* |
| `powerlab-autoroute` | Routes the board. Claude first asks how: with the **PowerLab router** (recommended), or by hand. Either way it first sets the lab design rules and net classes (power tracks sized for their current) and keeps hand-routed, locked copper. The PowerLab router runs on your computer in KiCad's Python and applies the lab rules while it routes: power rails first, then a copper pour round each rail; GND pours kept whole, with thermal reliefs; no tracks under inductors; escape room at fine-pitch pins; buses as parallel runs; few corners and vias; pads entered at their centres; a net's later tracks join its earlier ones instead of running beside them; and GND stitching vias at the end. With the board open in KiCad, you watch the tracks appear while it routes. Claude then routes whatever the router left by hand, fixes the DRC errors, and runs the design review without asking. | *Route the board* |

A run takes about 10–15 minutes on a 2-layer board with ~50 connections; it runs in the background and the panel stays usable. Each run keeps the board from before it, so Claude can undo it. Routed power-electronics boards always need a human review: loop areas, return paths, and track widths on high-current nets.

## The METU Power Lab library

The panel keeps your library clone up to date. When new parts are merged on GitHub, a bar offers **Update**.

Claude creates library parts in your clone, following [`HowToCreateNewDesign/DesignRules.md`](https://github.com/odtu/PowerLabKiCadLibraries/blob/main/HowToCreateNewDesign/DesignRules.md). When you have new or changed parts, the bar offers **Share**. Share:

1. Runs the lab's standards check on your changes.
2. Shows exactly which library files will be sent.
3. Opens a pull request from your GitHub account.

The same checks run on the pull request. For lab members (write access), it **merges automatically once they pass**, and everyone gets the parts with the next **Update**. Pull requests from others wait for a maintainer.

The checks can't confirm that pinouts or pad sizes match the datasheet, so verify that before you share. On GitHub, the `hold` label keeps a pull request open for review. Only files under `symbols/`, `footprints/` and `3dmodels/` are ever shared.

## Reporting problems

Use the **bug button** in the panel header, or **Report** on an error message. You'll see the full report before anything is sent:

- **GitHub connected (recommended):** **Submit** files the issue with your account, and you get notified about the fix. The panel can set up the connection for you (**Connect GitHub**).
- **Not connected:** **Open in browser** opens a pre-filled form here. Check it and press *Submit new issue*.

Reports are public, so don't add confidential details to the description.

## Known limitations

- **KiCad 10's schematic API is limited.** It can't report the selection, save or reload. The panel works around this by using the editor's own **Edit → Copy**, **File → Save** and **File → Revert**. Your clipboard is restored afterwards. This needs KiCad's menus in **English**.
- **Claude's permissions are limited.** Inside the panel, Claude can only use the KiCad tools, read and write files, search the web, run `kicad-cli`, and zip outputs with `tar -a -cf`. Other shell commands are blocked, because the panel can't ask you for permission mid-run. Use the terminal button to continue a conversation in a full Claude Code session.
- **The KiCad tools get small fixes from this repository.** `patches/kicad-mcp.patch` keeps 3D models when parts are rotated (kipy 0.8 drops them), and adds the PowerLab router. The installer applies it on top of the pinned KiCad MCP server.
- **Windows only, KiCad 10 only.**

## Contributing

Bug reports and pull requests are welcome. Open pull requests against the `test` branch: `main` only changes when a tested version is released. The panel's code is in `plugin/powerlab_assistant` (Python + an HTML/JS UI in `panel.html`). The schematic toolbar button is in `plugin/powerlab-assistant-button`.

## License

[CERN Open Hardware Licence Version 2 - Strongly Reciprocal](LICENSE), like the METU Power Lab libraries.

Claude and Claude Code are products of Anthropic. This project is not affiliated with or endorsed by Anthropic.

It builds on other open-source projects, which keep their own licenses:
- **KiCad tools:** KiCAD-MCP-Server (MIT), with a small MIT-licensed patch from this repository.
- **Board views:** PyMuPDF (AGPL-3.0).
- **KiCad** itself (GPL-3.0).

The installer downloads these from their official sources; this repository doesn't redistribute them. The full list, with links and licenses, is in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
