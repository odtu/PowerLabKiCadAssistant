# Notes for Claude (maintainers' sessions)

## Handling issues

Problem reports from the panel arrive as public issues on odtu/PowerLabKiCadAssistant.

1. Fix the problem, verify it, and push the fix with `Fixes #N` in the commit message.
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

Claude reproduces the bug with a test, fixes it and runs the tests. The workflow then opens a pull request (`Fixes #N`) and comments on the issue as `github-actions[bot]`. Its changes are limited to `plugin/`, `tests/`, `tools/`, `README.md` and the install scripts.

A maintainer still reviews and merges the PR, then releases (below) and replies with the version. Bugs that need the KiCad window can't be verified on the runner; Claude lists them under "Needs a human".

**Limits.** Runs use the maintainer's Claude subscription (the `CLAUDE_CODE_OAUTH_TOKEN` secret), so they count against the same usage limits as their own Claude use.
- **Model:** Opus 5.5 at high effort.
- **Per run:** up to 60 turns and 60 minutes.
- **Per day:** at most `DAILY_LIMIT` (3) successful or running Claude runs in 24 hours. Over the limit, the bot says so on the issue; re-add the `auto-fix` label later to retry.

## Releasing

Users only learn about fixes through releases: the panel offers an update when the latest GitHub release is newer than its `VERSION`.

1. Bump `VERSION` in `plugin/powerlab_assistant/config.py` (semantic: patch for fixes, minor for features).
2. Commit, push, then tag and publish:

   ```powershell
   gh release create vX.Y.Z -R odtu/PowerLabKiCadAssistant --title "X.Y.Z" --notes-file notes.md
   ```

   The first bullet of the notes appears in the panel's update bar ("PowerLab Assistant X.Y.Z is available: <first bullet>"). Make it a short, user-facing summary.
3. Issue replies name the version that contains the fix ("Fixed in 0.1.1 — update from the panel"), so reporters know which update brings it.
4. If the release changes the pinned KiCad MCP server commit, change `$McpCommit` in `install.ps1`. `install.ps1 -Update` rebuilds it only when that pin changed.

## Working on the code

- Stage only the files you changed (`git add <paths>`), never `git add -A` / `git add .`. Maintainers keep local KiCad test projects in the checkout (e.g. `tests/TestPCB/`), and KiCad lock files contain the user's computer and user name.

- Tests: `"C:\Program Files\KiCad\10.0\bin\python.exe" -m unittest discover -s tests` (KiCad's Python has wx and pcbnew).
- `install.ps1` / `uninstall.ps1` must stay plain ASCII and run on Windows PowerShell 5.1. Under `$ErrorActionPreference = "Stop"`, redirecting a native command's stderr (`*> $null`, `2>&1`) throws; run such checks through `Probe`.
- The panel promises users that nothing about their projects reaches METU Power Lab. Anything added to problem reports must go through `report.scrub`, and must never include messages, Claude's replies, selection, clipboard, or project/part/net names.
