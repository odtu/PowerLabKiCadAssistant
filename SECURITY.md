# Security policy

## Reporting a vulnerability

Please don't report security problems in a public issue or pull request.

Report them privately with **Report a vulnerability** on the repository's [Security tab](https://github.com/odtu/PowerLabKiCadAssistant/security). Only you and the maintainers see the report. We'll answer there, work on a fix with you if you like, and publish an advisory, if one is needed, after the fixed version is released.

Please include what an attacker could do, the steps to reproduce it, and the version (shown in the panel's update bar and in `plugin/powerlab_assistant/config.py`).

## What counts

The assistant runs Claude Code with access to your KiCad projects, so these matter most:

- Claude or the panel running commands, or reaching files, beyond what the panel allows (`ALLOWED_TOOLS` in `panel.py`).
- A KiCad project, library, web page or datasheet that makes the panel or Claude do something the user didn't ask for.
- Project data, names, file contents or tokens getting into problem reports (they're meant to go through `report.scrub`), or anywhere else they shouldn't.
- The installers or the Update button downloading or running something other than the pinned, hash-checked files.

Bugs in [KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server), KiCad or Claude Code themselves should also go to those projects. If they affect the assistant, tell us too.

## Supported versions

Only the latest release on `main` gets security fixes. The panel offers each new release within about 10 minutes of it.
