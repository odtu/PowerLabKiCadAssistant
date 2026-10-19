"""The lab's fixes to the KiCad MCP server, patches/kicad-mcp.patch (CLAUDE.md > Fixes to
the KiCad MCP server).

    python tools/mcp_patch.py checkout DIR   # the pinned commit with the patch applied
    python tools/mcp_patch.py regen [DIR]    # write DIR's changes back into the patch

DIR defaults to %LOCALAPPDATA%\\PowerLabKiCadAssistant\\KiCAD-MCP-Server, the checkout
install.ps1 makes. The pin and the repository come from install.ps1. `regen` keeps the
license header (everything before the first `diff --git`) and leaves the patch alone when
only git's abbreviated `index` lines differ, so a different clone doesn't count as a change.
"""

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATCH = os.path.join(ROOT, "patches", "kicad-mcp.patch")


def pin():
    """(repository, commit) from install.ps1."""
    with open(os.path.join(ROOT, "install.ps1"), encoding="utf-8") as f:
        text = f.read()
    return (re.search(r'\$McpRepo = "([^"]+)"', text).group(1),
            re.search(r'\$McpCommit = "([0-9a-f]+)"', text).group(1))


def git(where, *args):
    return subprocess.run(["git", "-C", where, *args], check=True, stdout=subprocess.PIPE).stdout


def checkout(where):
    repo, commit = pin()
    if not os.path.isdir(os.path.join(where, ".git")):
        subprocess.run(["git", "clone", "--quiet", repo, where], check=True)
    git(where, "checkout", "--quiet", "--force", commit)
    git(where, "clean", "-fdq")
    git(where, "apply", "--whitespace=nowarn", PATCH)


def _body(patch):
    """The diff without its header or `index` lines."""
    start = patch.find(b"diff --git")
    return [line for line in patch[start:].splitlines() if not line.startswith(b"index ")]


def regen(where):
    """Returns True when the patch file changed."""
    _repo, commit = pin()
    new = [f for f in git(where, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0") if f]
    if new:
        git(where, "add", "-N", "--", *[f.decode() for f in new])
    try:
        diff = git(where, "diff", commit)
    finally:
        if new:
            git(where, "reset", "-q", "--", *[f.decode() for f in new])
    with open(PATCH, "rb") as f:
        old = f.read()
    if _body(old) == _body(diff):
        return False
    with open(PATCH, "wb") as f:
        f.write(old[:old.find(b"diff --git")] + diff)
    return True


def main(argv):
    if len(argv) < 2 or argv[1] not in ("checkout", "regen") or (argv[1] == "checkout" and len(argv) < 3):
        print(__doc__)
        return 2
    where = argv[2] if len(argv) > 2 else os.path.join(
        os.environ.get("LOCALAPPDATA", ""), "PowerLabKiCadAssistant", "KiCAD-MCP-Server")
    if argv[1] == "checkout":
        checkout(where)
        print(f"{where}: {pin()[1]} with patches/kicad-mcp.patch applied")
    else:
        print("patches/kicad-mcp.patch " + ("updated" if regen(where) else "unchanged"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
