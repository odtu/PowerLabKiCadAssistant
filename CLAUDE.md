# Notes for Claude (maintainers' sessions)

## Branches

- **`main` is stable.** Users' clones follow it, and the panel's Update button pulls it. Within about 10 minutes of `VERSION` changing on `main`, every panel shows the update bar. So `main` changes only through a release (below), never through a direct commit or a fix or feature PR.
- **`test` is where changes land first.** Work on `test` itself: commit there and push to `test` (`git push origin test`). Don't create feature branches or open PRs for your own changes, and don't leave work on a side branch. The flow is always `test` → `main`, through a release. GitHub's default branch stays `main`, so check you're on `test` before you commit.
- **To try `test` yourself:** in the clone `install.ps1` ran from, `git switch test`, `git pull`, close KiCad, `install.ps1 -Update`. The panel's Update button then pulls `test`. The bar only appears for a newer stable `VERSION`, not for new `test` commits. Switch back with `git switch main`.

## Handling issues

Problem reports from the panel arrive as public issues on odtu/PowerLabKiCadAssistant.

1. Fix the problem, verify it, and commit the fix to `test` and push it, with `Fixes #N` in the commit message. GitHub closes the issue when that commit reaches `main` in a release.
2. **Always reply on the issue** after a fix: what went wrong, which commit fixed it, how it was verified, and what the reporter must do to get it (usually: pull, close KiCad, rerun `install.ps1`).
3. **Post replies as `github-actions[bot]`, never under a maintainer's personal account.** Don't use a GitHub tool or `gh issue comment` that posts as the signed-in user. Write the reply to a file and run the `reply-to-issue.yml` workflow:

   ```powershell
   gh workflow run reply-to-issue.yml -R odtu/PowerLabKiCadAssistant -f issue=N -F body=@reply.md
   ```

   Add `-f close=true` to close the issue too. Use `-F body=@file`: Windows PowerShell 5.1 mangles quotes in inline arguments. After the run, check the comment author is `github-actions[bot]`.
4. Issues and replies are public. Never quote project, board, sheet or part names, net names or file contents from a user's design in a reply.

## Automatic issue fixing

`.github/workflows/auto-fix.yml` runs Claude (claude-code-action) on GitHub when:
- a member or collaborator opens an issue, or
- a maintainer adds the `auto-fix` label to anyone's issue.

Claude reproduces the bug with a test, fixes it and runs the tests. The workflow then opens a pull request into `test` (`Fixes #N`) and comments on the issue as `github-actions[bot]`. Its changes are limited to `plugin/`, `tests/`, `tools/`, `README.md` and the install scripts.

A maintainer still reviews and merges the PR, tests it on `test`, then releases (below) and replies with the version. The workflow file itself runs from `main`, so changes to it take effect once released. Bugs that need the KiCad window can't be verified on the runner; Claude lists them under "Needs a human".

**Limits.** Runs use the maintainer's Claude subscription (the `CLAUDE_CODE_OAUTH_TOKEN` secret), so they count against the same usage limits as their own Claude use.
- **Model:** Opus 5.5 at high effort.
- **Per run:** up to 60 turns and 60 minutes.
- **Per day:** at most `DAILY_LIMIT` (3) successful or running Claude runs in 24 hours. Over the limit, the bot says so on the issue; re-add the `auto-fix` label later to retry.

## Releasing

Users only learn about fixes through releases. Every panel reads `VERSION` from `main` every 5 minutes (`updates.py`), and offers an update when it is newer than its own. The bar's text comes from the GitHub release of that version.

1. On `test`, bump `VERSION` in `plugin/powerlab_assistant/config.py` (semantic: patch for fixes, minor for features).
2. Merge `test` into `main` with a merge commit, not a squash, so the two branches stay in step:

   ```powershell
   gh pr create -R odtu/PowerLabKiCadAssistant --base main --head test --title "Release X.Y.Z" --body-file notes.md
   gh pr merge <PR> -R odtu/PowerLabKiCadAssistant --merge
   ```

   Merging is the release: within about 10 minutes every panel shows the update bar.
3. Right away, tag and publish the release on `main`:

   ```powershell
   gh release create vX.Y.Z -R odtu/PowerLabKiCadAssistant --target main --title "X.Y.Z" --notes-file notes.md
   ```

   The first bullet of the notes appears in the panel's update bar ("PowerLab Assistant X.Y.Z is available: <first bullet>"). Make it a short, user-facing summary. Until the release exists, the bar shows without it.
4. Never commit to `main` directly, not even docs: anything on `main` reaches users with their next Update.
5. Issue replies name the version that contains the fix ("Fixed in 0.1.1 — update from the panel"), so reporters know which update brings it.
6. If the release changes the pinned KiCad MCP server commit, change `$McpCommit` in `install.ps1`. `install.ps1 -Update` rebuilds it only when that pin or `patches/kicad-mcp.patch` changed.

## Fixes to the KiCad MCP server

`patches/kicad-mcp.patch` holds the lab's fixes on top of the pinned `$McpCommit`. The installer checks whether it's applied (`git apply --check -R`); if not, it resets the checkout to the pin, applies the patch and rebuilds. Today it does these things:
- **Rotation keeps 3D models:** `move_component` puts them back, because kipy 0.8's orientation setter drops them (#10).
- **`pourNets` on `autoroute`:** those nets are left out of the DSN, so they connect through pours instead of tracks; their existing tracks are kept.
- **`keepoutPourNets` on `autoroute`:** left out like `pourNets`, but each pour's outline becomes a keepout on its layer, so Freerouting routes around outer-layer power pours instead of reading them as solid planes.
- **Freerouting analytics off:** the CLI and Docker commands pass `--usage_and_diagnostic_data.disable_analytics=true`, like the live API server.
- **Via drills after the SES import:** a session via whose annular ring is below the board minimum gets a smaller drill.
- **`clean_up_routing` (new tool):** after autorouting, removes router stubs and dead-end tracks, widens tracks to their net-class width, and chamfers 90° corners. Each change that adds copper is checked with kicad-cli DRC (zones refilled, `--all-track-errors`, because by default a track already in one error hides its others) and taken back if it adds an error. Ported from the post-route scripts in odtu/PCBDesignWClaude (`hardware/tools/pcb`).
- **Pours in live mode (#12):** the live `add_copper_pour` handler accepts the tool's `outline` (or `points`), and falls back to the board outline like the offline one. `add_zone` gets a handler in both modes.
- **Stitching vias in live mode (#14):** `add_gnd_stitching_vias` had no live-mode handler. With KiCad open, the tool process never loads the board, so it said "No board is loaded". The new handler plans on the saved board file with the largest net-class clearance, then places the vias live.
- **Footprint text in live mode (#36):** `move_footprint_text` had no live-mode handler, so it moved the text on the tool's offline copy and the next save wrote KiCad's live board over it. The new handler moves the reference, value or a user field/text in KiCad directly.
- **Live autorouting (`live` on `autoroute`, prototype):** with the board open and saved in KiCad, Freerouting runs as a local API server (`commands/freerouting_live.py`, authentication and analytics off). Every `liveInterval` seconds (default 2) its partial session is imported into a scratch copy of the board, and the new copper is pushed into KiCad over kipy in one commit, replacing the previous update; existing and locked copper isn't touched. At the end the normal SES import runs, KiCad's board is brought in line with it (locked copper kept) and saved there, so no File → Revert. One attempt only; not in Docker.
- **Undoing an autoroute run (`undo_autoroute`, new tool):** the run writes the routed board over the saved file, so File → Revert can't undo it. Each successful run keeps the saved board from before it in `autoroute-backup\` next to the board (`commands/autoroute_backup.py`); `undo_autoroute` copies it back, reloads the board and removes the copy, so it works once.
- **PowerLab router (`commands/powerlab_router/`, in progress, not a tool yet):** a router that applies the lab rules while routing; see `docs/powerlab-router-plan.md`. It reads the board's `.kicad_dru` clearance rules itself (`rules.py`), because KiCad's rule engine isn't available from Python. It rips up and reroutes blocked connections and straightens the result (`finish.py`). The lab rules are search costs (`costs.py`): pours kept whole, no tracks under magnetics, escape room at fine-pitch pins, switching nets off power-pour layers, clock spacing, escape vias at the pins. Like hand routing, a bus between two parallel pin rows is drawn as a river (`bus.py`), with escape vias in a column and a bundle on the other layer where one layer is full, and other runs are redrawn as simple 45° shapes (`patterns.py`). `tools/router_bench.py` runs it on a board and compares it with DRC; `tools/route_quality.py` measures routing quality (pour pieces, pad entries, corners, vias), e.g. against the hand-routed TestPCB.
- **Board views for review:** `get_board_2d_view` renders in layer colours on KiCad's dark background (it was black and white), keeps the board's aspect ratio, and takes an `outputPath`, so the `powerlab-visual-review` skill can keep a numbered series.

To change it:
1. Edit the files in `%LOCALAPPDATA%\PowerLabKiCadAssistant\KiCAD-MCP-Server`.
2. Regenerate the patch there with `git add -N <new files>; git diff > <repo>\patches\kicad-mcp.patch`, then `git reset`. Put back the MIT license header from the old patch: everything before the first `diff --git`, which `git apply` ignores.
3. Check that it applies to a clean checkout of the pin.

## Third-party licenses

`THIRD_PARTY_NOTICES.md` lists every outside project the assistant contains, downloads or needs, with its license. When you add a dependency (installer download, Python or npm package, GitHub Action), check its license and add it there. METU Power Lab / odtu content needs no entry, because it's the lab's own.

Report real bugs upstream too.

## Skills

- **Where they live:** each folder in `skills/` is a Claude Code skill (`SKILL.md` with `name` and `description` frontmatter). `install.ps1` (and `-Update`) copies them to `%USERPROFILE%\.claude\skills\`. Name them `powerlab-*`: the installer removes `powerlab-*` skills that no longer ship, and never touches the user's other skills.
- **Writing one:** the description decides when Claude uses it, so name the user phrasings. Keep the body to the lab's procedure and judgement; the kicad MCP tools do the work.
- **External tools:** a skill that needs one gets it from `install.ps1`. Pin the version and its SHA-256, install it under `%LOCALAPPDATA%\PowerLabKiCadAssistant`, record its path in `config.json`, and expose it to the panel's sessions in `common.clean_env()`. That's how Java 25 and Freerouting 2.4.1 are set up. Never change system-wide PATH or Java.
- **The `Skill` tool** is in the panel's `ALLOWED_TOOLS`.
- **`powerlab-pcb-design-rules`** is a copy of the lab's [PCB_DESIGN_RULES.md](https://github.com/odtu/Powerlab/blob/master/KiCAD/PCB_DESIGN_RULES.md). It differs in two ways:
  - it is renamed, with a `Source:` line under the title;
  - nothing lab-branded goes on other people's boards: the drawing-sheet template rule (§1.1, and its §1.9 checklist item) is removed, and §3.6 has no lab logo, website or QR code. Instead, every board gets the silkscreen text `Designed with PowerLab KiCad Assistant and Claude` (and its §3.7 checklist item).

  - it has a §4 that points to `handbook/`.

  When the source changes, copy it again with the same edits. Change rules in the lab's file too (a PR to odtu/Powerlab), so the two stay the same. §3.3 pours, §3.4 routing, §3.5 vias: other skills (autoroute, visual review) refer to these numbers, so check they still match. `PANEL_NOTE` tells Claude to load it for any design work.
- **The review handbook** (`skills/powerlab-pcb-design-rules/handbook/`) is a copy of `pcb-handbook/` in odtu/PCBDesignWClaude (233 rules from online reviews and app notes), without `PROGRESS.md` and without the links to the Turkish working notes in `90-visual-audit-guide.md` and `SOURCES.md`. Copy it again when the source changes; the tests count 233 unique rule IDs, so update that number with it.
- **`powerlab-design-review`** runs at the end of placement and routing: review, fix, check again, then write `design-review\design-review.md` in the project. When a run's Write or Edit of a file with that name succeeds, the panel (`review.py`) shows the review as a card after Claude's reply and prints it to `design-review.pdf` with headless Microsoft Edge (its own temporary profile, so it never touches the user's Edge). Without Edge, it saves `design-review.html` instead. Places in the review (and in Claude's replies) are `kicad:` links (`refs=`, `net=`, `area=`, `at=`; `review.parse_location`). A click selects them in the PCB editor over the API (`KiCadSource.locate`), runs KiCad's zoom-to-selection and, for nets, highlight-net actions, and KiCad's own cross-probing then selects them in the schematic editor. KiCad 10's schematic API has no selection, so this needs the PCB editor open.

## Working on the code

- Stage only the files you changed (`git add <paths>`), never `git add -A` / `git add .`. Maintainers keep local KiCad test projects in the checkout (e.g. `tests/TestPCB/`), and KiCad lock files contain the user's computer and user name.

- Tests: `"C:\Program Files\KiCad\10.0\bin\python.exe" -m unittest discover -s tests` (KiCad's Python has wx and pcbnew).
- `install.ps1` / `uninstall.ps1` must stay plain ASCII and run on Windows PowerShell 5.1. Under `$ErrorActionPreference = "Stop"`, redirecting a native command's stderr (`*> $null`, `2>&1`) throws; run such checks through `Probe`.
- The panel promises users that nothing about their projects reaches METU Power Lab. Anything added to problem reports must go through `report.scrub`, and must never include messages, Claude's replies, selection, clipboard, or project/part/net names.
