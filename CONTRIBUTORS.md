# Contributors

Thank you to everyone who has helped build PowerLab KiCad Assistant.

## Maintainer

- **Ekrem Turan Fırat** ([@ekremturanfirat](https://github.com/ekremturanfirat)), METU Power Lab: created and maintains the assistant.

## Code

- **Selçuk DİNÇ** ([@selcukdinc](https://github.com/selcukdinc)): macOS support, with `install.sh`, the panel on macOS and KiCad's menus in any language ([#112](https://github.com/odtu/PowerLabKiCadAssistant/pull/112)); a faster panel on macOS and the permissions sheet ([#113](https://github.com/odtu/PowerLabKiCadAssistant/pull/113)).

## Problem reports

Everyone who has sent a problem report from the panel. Most fixes started with one of them.

## Built on

- [KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server) by mixelpixx (MIT License): the KiCad tools Claude uses. The lab's fixes to it are in `patches/kicad-mcp.patch`.
- METU Power Lab's [PCB design rules](https://github.com/odtu/Powerlab/blob/master/KiCAD/PCB_DESIGN_RULES.md) and the review handbook from [odtu/PCBDesignWClaude](https://github.com/odtu/PCBDesignWClaude): the design-rules skill.
- [Claude](https://www.anthropic.com/claude) and [Claude Code](https://docs.claude.com/claude-code) by Anthropic: co-author of most commits, and the auto-fix workflow that turns problem reports into pull requests.

The full list of outside software and its licenses is in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Adding yourself

When your first pull request is merged, add yourself under **Code** (in that pull request or a later one), or a maintainer will add you. One line: your name, your GitHub link and what you contributed. Translations, testing and documentation count too: add a heading for them when the first one arrives.
