"""The user's git clone of odtu/PowerLabKiCadLibraries: sync and contribute.

Sync is a read-only, anonymous `git fetch` from the public repo. Contributions go
out only when the user presses Share and confirms; they become a pull request from
the user's own GitHub fork, made with the user's own GitHub login (gh). Only files
under symbols/, footprints/ and 3dmodels/ are ever included.
"""

import json
import os
import re
import tempfile
import time

from . import config
from .common import find_gh, run_quiet

LIBRARY_DIRS = ("symbols", "footprints", "3dmodels")
STANDARDS = os.path.join("HowToCreateNewDesign", "DesignRules.md")
CHECKER = os.path.join("tools", "check_library.py")
KICAD_CONFIG = os.path.join(os.environ.get("APPDATA", ""), "kicad", "10.0")


def git(path, *args, env=None, timeout=120):
    return run_quiet(["git", "-C", path, *args], timeout=timeout, extra_env=env)


def library_context():
    """Instructions for Claude whenever it works on library parts."""
    path = config.library_path()
    if not path:
        return ""
    return "\n".join([
        f"The METU PowerLab KiCad library is a git clone at: {path}",
        f"Before creating or changing any library symbol, footprint or 3D model, read "
        f"{os.path.join(path, STANDARDS)} and follow it exactly (naming, fields, reference "
        "prefixes, footprint pad and drawing rules, symbol style).",
        "Put new or changed parts in that clone: symbols/<Library>.kicad_sym, "
        "footprints/<Library>.pretty/<Footprint>.kicad_mod, 3D models under "
        "3dmodels/powerlab.3dshapes/<Category>/<Subcategory>/, referenced as "
        "${METUPOWERLAB_3D}/<Category>/<Subcategory>/<file>.step.",
        "Register a new library in KiCad's global tables with the path variables, e.g. "
        "${METUPOWERLAB_SYMBOLS}/<Library>.kicad_sym and ${METUPOWERLAB_FOOTPRINTS}/<Library>.pretty, "
        "never with an absolute path.",
        "Don't commit, push or open pull requests yourself: the user shares library changes "
        "with the panel's Share button, which runs the lab's standards check first.",
    ])


class Status:
    def __init__(self, ok=True, behind=0, changes=None, error=""):
        self.ok, self.behind, self.changes, self.error = ok, behind, changes or [], error

    def as_dict(self):
        return {"ok": self.ok, "behind": self.behind, "changes": self.changes, "error": self.error}


def changed_files(path):
    """Library files that differ from the last synced version (added, modified, deleted)."""
    # -z: NUL-separated and never quoted; a rename is "R  new\0old\0".
    code, out = git(path, "status", "--porcelain=v1", "-z", "-uall", "--", *LIBRARY_DIRS)
    if code != 0:
        return []
    files, entries = [], out.split("\0")
    i = 0
    while i < len(entries):
        entry = entries[i]
        i += 1
        if len(entry) < 4:
            continue
        status = entry[:2]
        if status[0] in "RC":
            i += 1  # skip the rename's original path
        files.append({"status": status.strip() or "?", "path": entry[3:]})
    return files


def status(fetch=True):
    """Compare the clone with GitHub. Runs git (network) — call from a worker thread."""
    path = config.library_path()
    if not path:
        return Status(ok=False, error="no library clone configured")
    if fetch:
        code, out = git(path, "fetch", "--quiet", "origin")
        if code != 0:
            return Status(ok=False, changes=changed_files(path), error="couldn't reach GitHub")
    code, out = git(path, "rev-list", "--count", "HEAD..origin/main")
    behind = int(out) if code == 0 and out.isdigit() else 0
    return Status(behind=behind, changes=changed_files(path))


def update():
    """Fast-forward the clone to GitHub's main. Local edits that GitHub already has
    (e.g. your own merged contribution) are dropped first; other local edits block it."""
    path = config.library_path()
    for item in changed_files(path):
        code, _ = git(path, "diff", "--quiet", "origin/main", "--", item["path"])
        exists_upstream = git(path, "cat-file", "-e", f"origin/main:{item['path']}")[0] == 0
        if code == 0 and exists_upstream:  # identical to what GitHub has now
            git(path, "checkout", "--", item["path"])
            full = os.path.join(path, item["path"])
            if item["status"] == "??" and os.path.isfile(full):
                os.remove(full)
    code, out = git(path, "pull", "--ff-only", "--quiet", "origin", "main")
    if code != 0:
        return False, ("Couldn't update: you have library changes that aren't on GitHub yet. "
                       "Share them first, or ask Claude to help resolve it.")
    added = register_new_libraries(path)
    return True, added


def _table_names(table):
    try:
        with open(table, encoding="utf-8") as f:
            return set(re.findall(r'\(name\s+"([^"]+)"\)', f.read())), True
    except OSError:
        return set(), False


def _append_entries(table, entries):
    with open(table, encoding="utf-8") as f:
        text = f.read().rstrip()
    if not text.endswith(")"):
        return
    body = "".join(f'  (lib (name "{n}")(type "KiCad")(uri "{u}")(options "")(descr "METU PowerLab"))\n'
                   for n, u in entries)
    with open(table, "w", encoding="utf-8") as f:
        f.write(text[:-1].rstrip() + "\n" + body + ")\n")


def register_new_libraries(path):
    """Add libraries that exist in the clone but not in KiCad's global tables.
    KiCad picks them up after a restart. Returns the names added."""
    added = []
    for kind, folder, suffix, var, table in (
        ("sym", "symbols", ".kicad_sym", "METUPOWERLAB_SYMBOLS", "sym-lib-table"),
        ("fp", "footprints", ".pretty", "METUPOWERLAB_FOOTPRINTS", "fp-lib-table"),
    ):
        table_path = os.path.join(KICAD_CONFIG, table)
        names, ok = _table_names(table_path)
        if not ok:
            continue
        entries = []
        for item in sorted(os.listdir(os.path.join(path, folder))):
            if item.endswith(suffix):
                name = item[: -len(suffix)]
                if name not in names:
                    entries.append((name, "${%s}/%s" % (var, item)))
        if entries:
            _append_entries(table_path, entries)
            added += [n for n, _ in entries]
    return added


def path_variables_ok():
    """True if KiCad's METUPOWERLAB_* path variables point into the clone."""
    path = config.library_path()
    try:
        with open(os.path.join(KICAD_CONFIG, "kicad_common.json"), encoding="utf-8") as f:
            env = json.load(f).get("environment", {}).get("vars", {}) or {}
    except (OSError, ValueError):
        return False
    norm = lambda p: os.path.normcase(os.path.normpath(p or ""))
    return norm(env.get("METUPOWERLAB_SYMBOLS")) == norm(os.path.join(path, "symbols"))


# ---- contributing --------------------------------------------------------

def gh_login():
    gh = find_gh()
    if not gh:
        return None
    code, out = run_quiet([gh, "api", "user", "--jq", ".login"], timeout=20)
    return out.strip() if code == 0 and out.strip() else None


def run_checker(path, files):
    """The library repo's own standards check on the changed files, if it has one."""
    checker = os.path.join(path, CHECKER)
    targets = sorted({_check_target(f["path"]) for f in files if f["status"] != "D"} - {""})
    if not os.path.isfile(checker) or not targets:
        return None
    python = os.path.join(config.kicad_bin(), "python.exe")
    code, out = run_quiet([python, checker, *targets], cwd=path, timeout=300)
    return {"passed": code == 0, "output": out[-6000:]}


def _check_target(rel):
    if rel.endswith(".kicad_sym") or rel.endswith(".kicad_mod"):
        return rel
    return ""


def build_commit(path, paths, message, login):
    """A commit = HEAD + exactly `paths` from the working tree, built in a private index,
    so the user's checkout, branch and staged changes are untouched. Returns (ok, sha-or-error)."""
    index = os.path.join(tempfile.gettempdir(), f"powerlab-share-{os.getpid()}-{time.time_ns()}.index")
    env = {"GIT_INDEX_FILE": index}
    try:
        if git(path, "read-tree", "HEAD", env=env)[0] != 0:
            return False, "Couldn't prepare the commit (read-tree failed)."
        code, out = git(path, "add", "-A", "--", *paths, env=env)
        if code != 0:
            return False, f"Couldn't stage the files: {out[-300:]}"
        code, tree = git(path, "write-tree", env=env)
        if code != 0:
            return False, "Couldn't prepare the commit (write-tree failed)."
    finally:
        if os.path.exists(index):
            os.remove(index)
    identity = None
    if git(path, "config", "user.email")[0] != 0:  # no git identity: use the GitHub noreply one
        email = f"{login}@users.noreply.github.com"
        identity = {"GIT_AUTHOR_NAME": login, "GIT_COMMITTER_NAME": login,
                    "GIT_AUTHOR_EMAIL": email, "GIT_COMMITTER_EMAIL": email}
    code, commit = git(path, "commit-tree", tree.strip(), "-p", "HEAD", "-m", message, env=identity)
    if code != 0:
        return False, f"Couldn't create the commit: {commit[-300:]}"
    return True, commit.strip()


def error_line(output):
    """The line that says what went wrong. gh prints the error first and its usage text
    after it, so the end of the output (what this used to show) is just usage."""
    for line in output.splitlines():
        line = line.strip()
        if line and not line.startswith(("Usage:", "Flags:", "-", "Create a fork")):
            return line[:300]
    return output.strip()[:300] or "unknown error"


def contribute(title, description, files, login):
    """Open a PR to the lab library with exactly `files`. Runs git + gh (network):
    call from a worker thread. Returns (ok, url-or-error)."""
    path = config.library_path()
    gh = find_gh()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    branch = f"library/{login}-{stamp}"
    paths = [f["path"] for f in files]

    # No --remote flag: gh rejects it whenever a repository argument is given (issue #2).
    code, out = run_quiet([gh, "repo", "fork", config.LIBRARY_REPO, "--clone=false"], timeout=120)
    if code != 0 and "already exists" not in out:
        return False, f"Couldn't create your fork: {error_line(out)}"
    repo_name = config.LIBRARY_REPO.split("/")[1]
    fork_url = f"https://github.com/{login}/{repo_name}.git"

    ok, commit = build_commit(path, paths, f"{title}\n\n{description}".strip(), login)
    if not ok:
        return False, commit

    # gh's credentials for this one push only; the user's git config isn't changed.
    helper = "!\"%s\" auth git-credential" % gh.replace("\\", "/")
    code, out = git(path, "-c", "credential.helper=", "-c", f"credential.helper={helper}",
                    "push", fork_url, f"{commit}:refs/heads/{branch}", timeout=300)
    if code != 0:
        return False, f"Couldn't push to your fork: {error_line(out)}"

    body = (f"{description}\n\n**Files**\n" + "\n".join(f"- `{p}`" for p in paths) +
            "\n\nShared from PowerLab KiCad Assistant. Please check against "
            "`HowToCreateNewDesign/DesignRules.md`.")
    code, out = run_quiet([gh, "pr", "create", "-R", config.LIBRARY_REPO, "--base", "main",
                           "--head", f"{login}:{branch}", "--title", title, "--body", body], timeout=120)
    if code != 0:
        return False, f"Pushed, but couldn't open the pull request: {error_line(out)}"
    url = out.strip().splitlines()[-1]
    return True, url
