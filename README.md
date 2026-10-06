# PowerLab KiCad Assistant

A side panel for **KiCad 10** that lets you ask Claude to do things in your design: create symbol and footprint libraries to the METU Power Lab standard, run ERC/DRC and explain the results, render 3D views, export fabrication files, and edit schematics and boards.

It runs [Claude Code](https://docs.claude.com/claude-code) on your computer with your own Claude account, and gives it KiCad tools through [KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server).

> **Early version.** Windows and KiCad 10 only. Expect rough edges and please [report problems](#reporting-problems).

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
- your conversation history (`%USERPROFILE%\.claude`)

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
   - Turn on KiCad's API server, which the schematic panel needs.
   - Optionally install GitHub CLI and sign you in.

   If you already have a clone of the library, add `-LibraryPath D:\path\to\PowerLabKiCadLibraries`.

4. Sign in to Claude Code once: run `claude` in a terminal, follow the login, then type `/exit`.
5. In the **Schematic Editor**, go to **Preferences → Preferences → Schematic Editor → Toolbars**. Add **IPC/Scripting plugins** to the **Top main** toolbar. KiCad doesn't show plugin buttons there by default.

To remove it later, run `uninstall.ps1`.

## Use

Click the **PowerLab Assistant** button on the toolbar of the PCB Editor or the Schematic Editor. Type a short request and press Enter. For example:

- *Create a symbol and footprint library for the LMR38020*
- *Run DRC and summarize the violations*
- *What is this part connected to?* (select it first)
- *Render the top side and show it to me*

The panel shows each step Claude takes, plus any images it renders. The model picker under the input box switches between Claude models.

**PCB Editor:**

- Claude sees the footprints you have selected.
- Some board edits (move, rotate, delete and others) can apply live through KiCad's API server.
- When Claude changes the board file instead, the panel tells you to use **File → Revert**.

**Schematic Editor:**

- Claude sees the sheet you're on and the items you have selected.
- Before each message, the panel makes sure the schematic is saved.
- After Claude changes a sheet, the panel reloads it in KiCad for you.

## The METU Power Lab library

The panel keeps your library clone up to date. When new parts are merged on GitHub, a bar offers **Update**.

Claude creates library parts in your clone, following [`HowToCreateNewDesign/DesignRules.md`](https://github.com/odtu/PowerLabKiCadLibraries/blob/main/HowToCreateNewDesign/DesignRules.md). When you have new or changed parts, the bar offers **Share**. Share:

1. Runs the lab's standards check on your changes.
2. Shows exactly which library files will be sent.
3. Opens a pull request from your GitHub account.

The lab reviews it, and the same checks run automatically on the pull request. Only files under `symbols/`, `footprints/` and `3dmodels/` are ever shared.

## Reporting problems

Use the **bug button** in the panel header, or **Report** on an error message. You'll see the full report before anything is sent:

- **GitHub connected (recommended):** **Submit** files the issue with your account, and you get notified about the fix. The panel can set up the connection for you (**Connect GitHub**).
- **Not connected:** **Open in browser** opens a pre-filled form here. Check it and press *Submit new issue*.

Reports are public, so don't add confidential details to the description.

## Known limitations

- **KiCad 10's schematic API is limited.** It can't report the selection, save or reload. The panel works around this by using the editor's own **Edit → Copy**, **File → Save** and **File → Revert**. Your clipboard is restored afterwards. This needs KiCad's menus in **English**.
- **Claude's permissions are limited.** Inside the panel, Claude can only use the KiCad tools, read and write files, search the web, and run `kicad-cli`. Other shell commands are blocked, because the panel can't ask you for permission mid-run. Use the terminal button to continue a conversation in a full Claude Code session.
- **Windows only, KiCad 10 only.**

## Contributing

Bug reports and pull requests are welcome. The panel's code is in `plugin/powerlab_assistant` (Python + an HTML/JS UI in `panel.html`). The schematic toolbar button is in `plugin/powerlab-assistant-button`.

## License

[CERN Open Hardware Licence Version 2 - Strongly Reciprocal](LICENSE), like the METU Power Lab libraries.

Claude and Claude Code are products of Anthropic. This project is not affiliated with or endorsed by Anthropic. KiCAD-MCP-Server is MIT-licensed by its authors and is downloaded at install time, not redistributed here.
