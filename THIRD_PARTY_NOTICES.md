# Third-party software

The PowerLab KiCad Assistant's own code is licensed under CERN-OHL-S-2.0 (see [LICENSE](LICENSE)). It builds on the projects below, which keep their own licenses. Licenses were checked on 2026-10-08 against each project's license file or package metadata.

## Included in this repository

| What | Where | From | License |
|---|---|---|---|
| Changes to KiCAD-MCP-Server | `patches/kicad-mcp.patch` | Changes code from [mixelpixx/KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server), © 2024 mixelpixx | MIT, the same license as the code it changes. The notice is at the top of the patch. |

## Downloaded by `install.ps1`

The installer downloads these from their official sources into `%LOCALAPPDATA%\PowerLabKiCadAssistant` (or into KiCad's Python). This repository doesn't contain or redistribute them, and nothing is modified except the KiCAD-MCP-Server patch above.

| Software | Used for | License |
|---|---|---|
| [KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server) (pinned commit, see `install.ps1`) | KiCad tools for Claude | MIT |
| …its npm dependencies (94 packages, e.g. [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk), [zod](https://github.com/colinhacks/zod), [express](https://github.com/expressjs/express)) | | MIT, ISC, BSD-2-Clause, BSD-3-Clause. The MCP SDK is moving from MIT to Apache-2.0. |
| …its Python dependencies, installed into KiCad's Python | | |
| [kicad-python (kipy)](https://pypi.org/project/kicad-python/) | KiCad IPC API | MIT |
| [sexpdata](https://pypi.org/project/sexpdata/) | | BSD-2-Clause |
| [kicad-skip](https://pypi.org/project/kicad-skip/) | | LGPL-2.0-or-later |
| [Pillow](https://pypi.org/project/pillow/) | | MIT-CMU |
| [PyMuPDF](https://pypi.org/project/PyMuPDF/) | rendering board views | **AGPL-3.0** or an Artifex commercial license |
| [CairoSVG](https://pypi.org/project/CairoSVG/) | | LGPL-3.0-or-later |
| [colorlog](https://pypi.org/project/colorlog/), [pydantic](https://pypi.org/project/pydantic/) | | MIT |
| [requests](https://pypi.org/project/requests/) | | Apache-2.0 |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | | BSD-3-Clause |
| [Freerouting 2.4.1](https://github.com/freerouting/freerouting) | autorouting | GPL-3.0. Official release jar, run as a separate program; source on GitHub. |
| [Eclipse Temurin 25.0.4.1 JRE](https://adoptium.net/) | runs Freerouting | GPL-2.0 WITH Classpath-exception-2.0. Its notices are in the installed `legal/` folder. |

## Installed by you

| Software | License |
|---|---|
| [KiCad 10](https://www.kicad.org/) (the panel runs inside it and uses its Python, `pcbnew` and the bundled wxPython) | GPL-3.0; wxPython: wxWindows Library Licence |
| [Claude Code](https://docs.claude.com/claude-code) | Anthropic proprietary; used under your own Claude account and Anthropic's terms |
| [Node.js](https://nodejs.org/), [Git](https://git-scm.com/), [GitHub CLI](https://cli.github.com/) (optional) | MIT; GPL-2.0 (Git); MIT |

## Used by this repository's GitHub workflows

| Action | License |
|---|---|
| [actions/checkout](https://github.com/actions/checkout), [actions/setup-python](https://github.com/actions/setup-python), [actions/upload-artifact](https://github.com/actions/upload-artifact), [actions/github-script](https://github.com/actions/github-script) | MIT |
| [anthropics/claude-code-action](https://github.com/anthropics/claude-code-action) | MIT |

When you add a dependency, add it here with its license.
