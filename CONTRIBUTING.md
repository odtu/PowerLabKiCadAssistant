# Contributing to PowerLab KiCad Assistant

Thank you for helping. Bug reports, fixes, new platforms, translations and testing are all welcome, from inside METU Power Lab or outside it.

## Ways to help

- **Report a problem** with the bug button in the panel header. The report is filled in for you and scrubbed of paths and names, and you see all of it before it's sent. Reports are public issues, so leave out anything confidential about your design.
- **Fix a bug or add a feature** with a pull request (below).
- **Translate.** The panel speaks 19 languages, and new texts often arrive in English first. Native speakers who check or improve a translation are a great help.
- **Test on your setup**, especially macOS (newer than Windows support) and KiCad versions or languages we haven't tried, and tell us what broke.

## Branches and pull requests

- **Open pull requests against `test`**, never `main`. `main` is what users run: the panel's Update button pulls it, and every change to `main` reaches every user. Changes land on `test`, get tried there, and reach `main` in a release.
- One topic per pull request. A small, focused PR is reviewed faster than a large one.
- In the description, say what changed, why, and **how you tested it**: which OS, KiCad version and KiCad language, and what you clicked through. Measurements (before/after timings, router results) make a review much easier.
- If a change touches code shared by Windows and macOS, say which platform you couldn't try. CI runs the tests on Windows, Ubuntu and macOS.
- The first CI run of a first-time contributor waits for a maintainer's approval. That's GitHub's rule, not a judgement.
- Don't bump `VERSION` or write release notes; maintainers do that at release time.
- Add yourself to [CONTRIBUTORS.md](CONTRIBUTORS.md) with your first pull request, if you like.

## Setting up

1. Fork the repository and clone your fork.
2. Switch to `test`: `git switch test`.
3. Install from that clone, so KiCad runs your copy of the panel:
   - **Windows:** close KiCad, then run `install.ps1` (or `install.ps1 -Update` after the first time) in PowerShell.
   - **macOS:** quit KiCad, then run `/bin/bash install.sh` (or `install.sh --update`).
4. Restart KiCad after each install to load your changes.

See the [README](README.md#requirements) for what the installer needs.

## Running the tests

Run them with KiCad's own Python, which has wx and pcbnew:

```powershell
& "C:\Program Files\KiCad\10.0\bin\python.exe" -m unittest discover -s tests
```

```bash
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 -m unittest discover -s tests
```

A plain Python 3 runs them too, skipping the tests that need KiCad. Add a test for every bug you fix: it should fail without your fix and pass with it.

## Where things are

| Path | What it is |
|---|---|
| `plugin/powerlab_assistant/` | The panel: Python (`panel.py`, `sources.py`, ...) and its HTML/JS page (`panel.html`) |
| `plugin/powerlab_assistant/kicad_window_win.py`, `kicad_window_mac.py` | Driving KiCad's windows and menus, one module per platform with the same functions |
| `plugin/powerlab_assistant/lang/` | The panel's translations, one JSON file per language |
| `plugin/powerlab-assistant-button/` | The schematic editor's toolbar button |
| `skills/` | Claude Code skills (`powerlab-*`) the installer copies into `~/.claude/skills` |
| `patches/kicad-mcp.patch` | The lab's fixes to [KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server), applied on top of its pinned commit |
| `install.ps1`, `install.sh` | The Windows and macOS installers (and their `uninstall` twins) |
| `tools/` | Developer scripts: translations, the MCP patch, router benchmarks |
| `tests/` | Unit tests |

## Guidelines

### Keep both platforms working

Windows and macOS share most of the code. Put platform-specific behaviour behind `config.IS_WINDOWS` / `config.IS_MAC`, or in the platform's `kicad_window_*` module, and leave the other platform's path as it was.

### Installers

- `install.ps1` and `uninstall.ps1` must stay plain ASCII and run on Windows PowerShell 5.1.
- `install.sh` and `uninstall.sh` must stay plain ASCII and run on macOS's own bash 3.2 (no associative arrays, no `${var,,}`).
- The KiCad MCP server's pinned commit lives only in `install.ps1`; `install.sh` reads it from there.
- Anything the installer downloads is pinned: an exact version and its SHA-256. Install it under the assistant's own folder, never into system-wide locations, and never change the system PATH.

### The KiCad MCP server

Most tool problems ("the board didn't change", "No board is loaded") are in the KiCad MCP server, not the panel. Don't edit `patches/kicad-mcp.patch` by hand:

```bash
python tools/mcp_patch.py checkout ../kicad-mcp   # the pinned commit with the patch applied
# edit and test the server in ../kicad-mcp
python tools/mcp_patch.py regen ../kicad-mcp      # write your changes back into the patch
```

Then check that the patch still applies to a clean checkout of the pin. If the bug is in the server itself and not specific to the lab, please also report it [upstream](https://github.com/mixelpixx/KiCAD-MCP-Server/issues).

### Translations

- Write new page text as `t('English text', { name })` in `panel.html`. Notes sent from `panel.py` need nothing extra.
- Run `python tools/i18n_strings.py` to update `lang/en.json` (the tests fail until you do).
- `python tools/i18n_strings.py --check` lists texts missing from each language. Translate the ones you can; maintainers fill in the rest before a release.
- Arabic and Persian lay the page out right to left, so use logical CSS (`margin-inline-start`, `text-align: start`), not left/right.
- Keep markers the panel parses in English in every language: ` (Recommended)`, `**Verdict:**`, `<choices>`.

### Privacy

The panel promises its users that nothing about their projects reaches METU Power Lab. Problem reports go through `report.scrub` and never include messages, Claude's replies, the selection, the clipboard, or project, part or net names. Keep it that way: anything new in a report must go through `report.scrub` too. The same goes for screenshots in pull requests and docs: blank out paths and design names that aren't yours to share.

### Dependencies and licenses

Every outside project the assistant contains, downloads or needs is listed with its license in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). If you add one (an installer download, a Python or npm package, a GitHub Action), check that its license allows it and add it there.

### Commits

- Stage only the files you changed (`git add <paths>`), not `git add -A`: KiCad leaves lock files in project folders that contain your computer and user name.
- Write commit messages that say what changed and why. Mention the issue a commit fixes (`Fixes #123`).

## AI-assisted contributions

This project is built with Claude, and AI-assisted pull requests are welcome. You are still the author: read and understand what you submit, run the tests, and say how you checked the change.

## Security

Please don't post details of a security problem in a public issue. Report it privately with **Report a vulnerability** on the repository's [Security tab](https://github.com/odtu/PowerLabKiCadAssistant/security): only you and the maintainers see it, and the details are published, if at all, after the fix is released.

## License

By contributing, you agree that your contribution is licensed under the repository's license, [CERN-OHL-S-2.0](LICENSE). Changes to `patches/kicad-mcp.patch` modify KiCAD-MCP-Server and stay under its MIT License, as the patch's header says.
