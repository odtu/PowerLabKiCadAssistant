#!/bin/bash
# Installs PowerLab KiCad Assistant (KiCad 10, macOS). The macOS twin of install.ps1.
#
# Asks before every change. Installs nothing that sends your project data to METU Power
# Lab. Your Claude and GitHub logins stay on this computer.
#
# Steps:
#   1. Checks KiCad 10, git and Node.js.
#   2. Claude Code (official installer) if missing.
#   3. KiCad MCP server (mixelpixx/KiCAD-MCP-Server, the version install.ps1 pins) and
#      its Python packages in KiCad's own Python (plus NumPy, which KiCad for macOS
#      lacks); numba for the PowerLab router in a folder of its own (pinned wheels).
#   4. The panel plugins into your KiCad 10 documents folder.
#   5. The METU Power Lab library as a git clone, and KiCad pointed at it.
#   6. Optionally GitHub CLI (Homebrew), for sharing libraries and filing reports.
#
# --update (used by the panel's Update button) asks nothing: it refreshes the plugin
# files and, only if its pinned version or the patch changed, the KiCad MCP server.
#
#   /bin/bash install.sh
#   /bin/bash install.sh --library ~/Work/PowerLabKiCadLibraries
#   /bin/bash install.sh --kicad-app /Volumes/Apps/KiCad/KiCad.app
#   /bin/bash install.sh --update
#
# Runs on macOS's own bash 3.2: no associative arrays, no case-changing expansions.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUPPORT="$HOME/Library/Application Support/PowerLabKiCadAssistant"  # config, MCP server, numba
MCP_DIR="$SUPPORT/KiCAD-MCP-Server"
PYLIB="$SUPPORT/pylib"
SKILLS_DIR="$HOME/.claude/skills"
KICAD_DOCS="$HOME/Documents/KiCad/10.0"
LIBRARY_REPO="https://github.com/odtu/PowerLabKiCadLibraries.git"
# One pin for both installers: install.ps1's (tools/mcp_patch.py reads it from there too).
MCP_REPO="$(sed -n 's/^\$McpRepo = "\(.*\)"$/\1/p' "$ROOT/install.ps1")"
MCP_COMMIT="$(sed -n 's/.*\[string\]\$McpCommit = "\([0-9a-f]*\)".*/\1/p' "$ROOT/install.ps1")"

# KiCad 10 for macOS ships Python 3.9, which has no NumPy. NumPy 2.0 and numba 0.60 are the
# last releases for 3.9. name version arch sha256, from PyPI (cp39 wheels).
PINNED_WHEELS="
numpy 2.0.2 arm64 423e89b23490805d2a5a96fe40ec507407b8ee786d66f7328be214f9679df6dd
numpy 2.0.2 x86_64 9059e10581ce4093f735ed23f3b9d283b9d517ff46009ddd485f1747eb22653c
numba 0.60.0 arm64 819a3dfd4630d95fd574036f99e47212a1af41cbcb019bf8afac63ff56834449
numba 0.60.0 x86_64 01ef4cd7d83abe087d644eaa3d95831b777aa21d441a23703d649e06b8e06b74
llvmlite 0.43.0 arm64 18e9953c748b105668487b7c81a3e97b046d8abf95c4ddc0cd3c94f4e4651ae8
llvmlite 0.43.0 x86_64 9cd2a7376f7b3367019b664c21f0c61766219faa3b03731113ead75107f3b66c
"

LIBRARY_PATH=""
KICAD_APP=""
UPDATE=0
SKIP_LIBRARY=0
SKIP_MCP=0
YES=0
while [ $# -gt 0 ]; do
    case "$1" in
        --library) LIBRARY_PATH="$2"; shift 2 ;;
        --kicad-app) KICAD_APP="$2"; shift 2 ;;
        --update) UPDATE=1; shift ;;
        --skip-library) SKIP_LIBRARY=1; shift ;;
        --skip-mcp) SKIP_MCP=1; shift ;;
        --yes) YES=1; shift ;;  # answer every question with its default
        -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
        *) echo "Unknown option: $1" >&2; exit 2 ;;
    esac
done

if [ -t 1 ]; then C=$'\033[36m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; D=$'\033[2m'; N=$'\033[0m'
else C=""; G=""; Y=""; R=""; D=""; N=""; fi
say() { echo "${C}$*${N}"; }
ok() { echo "${G}  OK  $*${N}"; }
warn() { echo "${Y}  !   $*${N}"; }
fail() { echo "${R}  X   $*${N}" >&2; exit 1; }
ask() {  # ask "question" [Y|N]: returns 0 for yes
    local default="${2:-Y}" hint="[Y/n]" answer
    [ "$default" = "N" ] && hint="[y/N]"
    if [ "$YES" = 1 ] || [ "$UPDATE" = 1 ]; then answer="$default"
    else read -r -p "  ?   $1 $hint " answer || answer=""; fi
    [ -z "$answer" ] && answer="$default"
    case "$answer" in [Yy]*) return 0 ;; *) return 1 ;; esac
}
sha256() { shasum -a 256 "$1" | cut -d' ' -f1; }

echo
if [ "$UPDATE" = 1 ]; then echo "PowerLab KiCad Assistant - update"; else echo "PowerLab KiCad Assistant - installer"; fi
echo "${D}Uses Claude Code. AI can make mistakes: always check its work before ordering boards.${N}"
echo
[ "$(uname -s)" = "Darwin" ] || fail "install.sh is for macOS. On Windows, run install.ps1."
[ -n "$MCP_COMMIT" ] && [ -n "$MCP_REPO" ] || fail "Couldn't read the KiCad MCP server's pin from install.ps1."

# ---- 1. Requirements -------------------------------------------------------
say "1. Checking requirements"
config_value() {  # a key from config.json, if the installer wrote one before
    [ -f "$SUPPORT/config.json" ] || return 0
    /usr/bin/python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8-sig")).get(sys.argv[2], ""))' \
        "$SUPPORT/config.json" "$1" 2>/dev/null || true
}
kicad_version() { /usr/bin/defaults read "$1/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null || true; }
if [ -z "$KICAD_APP" ]; then
    previous="$(config_value kicad_bin)"
    candidates=""
    [ -n "$previous" ] && candidates="${previous%/Contents/MacOS}"
    candidates="$candidates
/Applications/KiCad/KiCad.app
$HOME/Applications/KiCad/KiCad.app
$(/usr/bin/mdfind "kMDItemCFBundleIdentifier == 'org.kicad.kicad'" 2>/dev/null || true)"
    while IFS= read -r app; do
        [ -n "$app" ] || continue
        case "$(kicad_version "$app")" in 10.*) KICAD_APP="$app"; break ;; esac
    done <<EOF
$candidates
EOF
fi
[ -n "$KICAD_APP" ] && [ -x "$KICAD_APP/Contents/MacOS/kicad-cli" ] ||
    fail "KiCad 10 not found. Install it from https://www.kicad.org/download/macos/ (or pass --kicad-app /path/to/KiCad.app)"
case "$(kicad_version "$KICAD_APP")" in 10.*) ;; *) fail "$KICAD_APP is KiCad $(kicad_version "$KICAD_APP"), not KiCad 10." ;; esac
KICAD_BIN="$KICAD_APP/Contents/MacOS"
KICAD_PYTHON="$KICAD_APP/Contents/Frameworks/Python.framework/Versions/Current/bin/python3"
[ -x "$KICAD_PYTHON" ] || fail "KiCad's Python wasn't found in $KICAD_APP."
"$KICAD_PYTHON" -c "import wx, pcbnew" 2>/dev/null || fail "KiCad's Python can't load wx and pcbnew."
PY_VERSION="$("$KICAD_PYTHON" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
PY_ARCH="$("$KICAD_PYTHON" -c 'import platform; print(platform.machine())')"
ok "KiCad $(kicad_version "$KICAD_APP") at $KICAD_APP (Python $PY_VERSION, $PY_ARCH)"
mkdir -p "$KICAD_DOCS"
ok "KiCad 10 user folder: $KICAD_DOCS"

# A program KiCad starts gets launchd's PATH, so the MCP server is registered with node's
# full path, and Homebrew's folders are looked in here too.
PATH="$PATH:/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin"
for tool in git node npm; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        if [ "$tool" = git ]; then fail "git is missing. Install it with:  xcode-select --install   then run this again."; fi
        fail "$tool is missing. Install Node.js 18 or newer (https://nodejs.org, or: brew install node), then run this again."
    fi
done
NODE="$(command -v node)"
node_major="$(node --version | sed 's/^v//; s/\..*//')"
[ "$node_major" -ge 18 ] || fail "Node.js 18 or newer is needed (found $(node --version))."
ok "git, Node.js $(node --version)"

kicad_running() { /usr/bin/pgrep -f "KiCad.app/Contents/MacOS/kicad" >/dev/null 2>&1 || /usr/bin/pgrep -x kicad >/dev/null 2>&1; }
if kicad_running && [ "$UPDATE" = 0 ]; then  # updating only replaces plugin files
    warn "KiCad is running. Quit it now (KiCad > Quit KiCad): KiCad rewrites its settings when it exits."
    if [ "$YES" = 0 ]; then read -r -p "  Press Enter once KiCad is closed " _ || true; fi
    kicad_running && fail "KiCad is still running."
fi

# ---- 2. Claude Code --------------------------------------------------------
say "2. Claude Code"
CLAUDE="$(command -v claude || true)"
[ -z "$CLAUDE" ] && [ -x "$HOME/.local/bin/claude" ] && CLAUDE="$HOME/.local/bin/claude"
if [ -z "$CLAUDE" ]; then
    [ "$UPDATE" = 1 ] && fail "Claude Code is missing. Run install.sh without --update."
    if ask "Claude Code is not installed. Install it with Anthropic's official installer now?"; then
        curl -fsSL https://claude.ai/install.sh | bash
        CLAUDE="$HOME/.local/bin/claude"
        [ -x "$CLAUDE" ] || fail "Claude Code install did not finish. See https://docs.claude.com/claude-code"
    else fail "Claude Code is required."; fi
fi
ok "Claude Code at $CLAUDE"

# ---- 3. KiCad MCP server ---------------------------------------------------
PATCH="$ROOT/patches/kicad-mcp.patch"
patch_hash() { sha256 "$PATCH"; }
build_stamp() { [ -f "$MCP_DIR/dist/.powerlab-patch" ] && head -n 1 "$MCP_DIR/dist/.powerlab-patch" | tr -d '\r\n ' | tr 'A-F' 'a-f' || true; }
save_build_stamp() { patch_hash > "$MCP_DIR/dist/.powerlab-patch"; }
remove_patch_new_files() {
    # Files the patch adds aren't in the pinned commit, so the checkout leaves an older
    # patch's copies behind and git apply refuses to create them again (#105).
    local prev="" line file
    while IFS= read -r line || [ -n "$line" ]; do
        if [ "$prev" = "--- /dev/null" ]; then
            case "$line" in
                "+++ b/"*) file="$MCP_DIR/${line#+++ b/}"; file="${file%"${file##*[![:space:]]}"}"
                           [ -f "$file" ] && rm -f -- "$file" ;;
            esac
        fi
        prev="$line"
    done < "$PATCH"
}
update_mcp_patch() {  # returns 0 when it changed the checkout (rebuild needed)
    if git -C "$MCP_DIR" apply --check -R "$PATCH" >/dev/null 2>&1; then return 1; fi
    git -C "$MCP_DIR" checkout --quiet --force "$MCP_COMMIT"
    git -C "$MCP_DIR" clean -fdq -- python src
    remove_patch_new_files
    git -C "$MCP_DIR" apply --whitespace=nowarn "$PATCH"
    return 0
}
build_mcp() { (cd "$MCP_DIR" && npm run build --silent >/dev/null) && save_build_stamp; }
wheel() {  # wheel NAME: "version sha256" of the pinned cp39 wheel for this Mac, or nothing
    echo "$PINNED_WHEELS" | awk -v n="$1" -v a="$PY_ARCH" '$1 == n && $3 == a { print $2, $4 }'
}
requirement() {  # requirement NAME: a pip requirement line with its hash
    local pin; pin="$(wheel "$1")"
    [ -n "$pin" ] && echo "$1==${pin% *} --hash=sha256:${pin#* }"
}
install_numpy() {
    "$KICAD_PYTHON" -c "import numpy" 2>/dev/null && return 0
    if [ "$PY_VERSION" = "3.9" ] && [ -n "$(wheel numpy)" ]; then
        local req; req="$(mktemp -t powerlab-numpy)"
        requirement numpy > "$req"
        "$KICAD_PYTHON" -m pip install --user --quiet --disable-pip-version-check --no-warn-script-location \
            --only-binary=:all: --require-hashes -r "$req"
        rm -f "$req"
    else
        "$KICAD_PYTHON" -m pip install --user --quiet --disable-pip-version-check --no-warn-script-location "numpy<3"
    fi
}
install_pylib() {  # numba and llvmlite into $PYLIB; never into KiCad's site-packages
    PYLIB_READY=0
    if [ "$PY_VERSION" != "3.9" ] || [ -z "$(wheel numba)" ]; then
        warn "No pinned numba for Python $PY_VERSION ($PY_ARCH). The PowerLab router runs slower without it."
        return 0
    fi
    local numba_v llvm_v; numba_v="$(wheel numba)"; llvm_v="$(wheel llvmlite)"
    if [ -d "$PYLIB/numba-${numba_v% *}.dist-info" ] && [ -d "$PYLIB/llvmlite-${llvm_v% *}.dist-info" ]; then
        ok "numba for the PowerLab router already installed"; PYLIB_READY=1; return 0
    fi
    mkdir -p "$PYLIB"
    rm -rf "$PYLIB"/numba* "$PYLIB"/llvmlite* "$PYLIB"/bin/numba*  # pip --target won't replace them
    local req; req="$(mktemp -t powerlab-pylib)"
    { requirement numba; requirement llvmlite; } > "$req"
    if "$KICAD_PYTHON" -m pip install --quiet --disable-pip-version-check --no-deps --only-binary=:all: \
            --require-hashes --target "$PYLIB" -r "$req" &&
       "$KICAD_PYTHON" -c "import sys; sys.path.insert(0, sys.argv[1]); import numba" "$PYLIB" 2>/dev/null; then
        ok "numba for the PowerLab router -> $PYLIB"; PYLIB_READY=1
    else
        warn "numba not installed. The PowerLab router runs slower without numba."
    fi
    rm -f "$req"
}
register_mcp() {
    local entry="$MCP_DIR/dist/index.js" exists=1
    "$CLAUDE" mcp get kicad >/dev/null 2>&1 || exists=0
    if [ "$exists" = 1 ]; then
        [ "$UPDATE" = 1 ] && return 0
        ask "Claude Code already has a 'kicad' tool server. Replace it with this one?" || return 0
        "$CLAUDE" mcp remove kicad -s user >/dev/null 2>&1 || true
    fi
    "$CLAUDE" mcp add kicad -s user -e "KICAD_PYTHON=$KICAD_PYTHON" -e "KICAD_CLI=$KICAD_BIN/kicad-cli" \
        -e "POWERLAB_PYLIB=$PYLIB" -- "$NODE" "$entry" >/dev/null || fail "Couldn't register the KiCad tools with Claude Code."
    ok "KiCad tools registered with Claude Code (for your user only)"
}

MCP_READY=0
mcp_current=0
if [ "$UPDATE" = 1 ] && [ -f "$MCP_DIR/dist/index.js" ]; then
    case "$(git -C "$MCP_DIR" rev-parse HEAD)" in "$MCP_COMMIT"*) mcp_current=1 ;; esac
fi
if [ "$mcp_current" = 1 ]; then
    say "3. KiCad tools for Claude"
    ok "Already at the pinned version ($MCP_COMMIT)"
    if update_mcp_patch; then build_mcp; ok "PowerLab fixes applied and rebuilt"
    elif [ "$(build_stamp)" != "$(patch_hash)" ]; then build_mcp; ok "PowerLab fixes already applied; rebuilt for the current patch"
    else ok "PowerLab fixes already applied"; fi
    MCP_READY=1
elif [ "$SKIP_MCP" = 0 ]; then
    say "3. KiCad tools for Claude (KiCAD-MCP-Server @ $MCP_COMMIT)"
    mkdir -p "$SUPPORT"
    [ -d "$MCP_DIR/.git" ] || git clone --quiet "$MCP_REPO" "$MCP_DIR"
    git -C "$MCP_DIR" fetch --quiet origin
    git -C "$MCP_DIR" checkout --quiet --force "$MCP_COMMIT"
    update_mcp_patch || true
    ok "PowerLab fixes applied"
    (cd "$MCP_DIR" && npm ci --no-audit --no-fund --loglevel=error >/dev/null)
    build_mcp
    ok "MCP server built"
    # --user: KiCad's Python puts them in ~/Library/Python/<version>; no admin rights needed.
    "$KICAD_PYTHON" -m pip install --user --quiet --disable-pip-version-check --no-warn-script-location \
        -r "$MCP_DIR/requirements.txt"
    install_numpy
    ok "Python packages installed into KiCad's Python"
    MCP_READY=1
    register_mcp
else warn "Skipped the KiCad MCP server (--skip-mcp)."; fi
PYLIB_READY=0
if [ "$MCP_READY" = 1 ]; then
    install_numpy
    install_pylib
fi

# ---- settings (local only) -------------------------------------------------
save_config() {
    # Written after each step, so an interrupted install still leaves usable settings.
    mkdir -p "$SUPPORT"
    local mcp="" pylib=""
    [ "$MCP_READY" = 1 ] && mcp="$MCP_DIR"
    [ "$PYLIB_READY" = 1 ] && pylib="$PYLIB"
    "$KICAD_PYTHON" - "$SUPPORT/config.json" "$KICAD_BIN" "$KICAD_PYTHON" "$mcp" "${LIBRARY:-}" "$pylib" "$ROOT" <<'PY'
import json, os, sys
path, kicad_bin, python, mcp, library, pylib, root = sys.argv[1:]
try:
    with open(path, encoding="utf-8-sig") as f:
        config = json.load(f)
except (OSError, ValueError):
    config = {}
config["kicad_bin"], config["kicad_python"] = kicad_bin, python
for key, value in (("mcp_path", mcp), ("library_path", library), ("pylib_path", pylib)):
    if value:
        config[key] = value
config["source_path"] = root  # where the panel's Update button pulls from
config.setdefault("extra_dirs", [])
with open(path, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)
PY
}

# ---- 4. Plugins ------------------------------------------------------------
say "4. Panel plugins"
PANEL_DEST="$KICAD_DOCS/scripting/plugins/powerlab_assistant"
BUTTON_DEST="$KICAD_DOCS/plugins/powerlab-assistant"
for pair in "powerlab_assistant|$PANEL_DEST" "powerlab-assistant-button|$BUTTON_DEST"; do
    src="$ROOT/plugin/${pair%%|*}"; dest="${pair#*|}"
    rm -rf "$dest"; mkdir -p "$dest"
    cp -R "$src/." "$dest/"
    find "$dest" -name "__pycache__" -type d -prune -exec rm -rf {} +
done
ok "Panel, PCB button -> $PANEL_DEST"
ok "Schematic button  -> $BUTTON_DEST"
LIBRARY="$(config_value library_path)"
save_config

# ---- 4b. Skills ------------------------------------------------------------
say "4b. Skills"
mkdir -p "$SKILLS_DIR"
shipped=""
for skill in "$ROOT"/skills/*/; do
    name="$(basename "$skill")"
    rm -rf "${SKILLS_DIR:?}/$name"; cp -R "$skill" "$SKILLS_DIR/$name"
    shipped="$shipped $name"
done
for old in "$SKILLS_DIR"/powerlab-*/; do  # skills we shipped before but no longer do
    [ -d "$old" ] || continue
    case " $shipped " in *" $(basename "$old") "*) ;; *) rm -rf "$old" ;; esac
done
ok "Skills:$shipped -> $SKILLS_DIR"

if [ "$UPDATE" = 1 ]; then
    version="$(sed -n 's/^VERSION = "\(.*\)".*/\1/p' "$PANEL_DEST/config.py")"
    echo
    echo "Updated to PowerLab KiCad Assistant $version."
    echo "  Restart KiCad to load it. An open panel restarts by itself on its next button click."
    exit 0
fi

# ---- 5. Library ------------------------------------------------------------
if [ "$SKIP_LIBRARY" = 0 ]; then
    say "5. METU Power Lab library (git clone, kept in sync by the panel)"
    [ -n "$LIBRARY_PATH" ] || LIBRARY_PATH="${LIBRARY:-$HOME/Documents/PowerLabKiCadLibraries}"
    LIBRARY_PATH="${LIBRARY_PATH/#\~/$HOME}"
    if [ -d "$LIBRARY_PATH/.git" ]; then
        origin="$(git -C "$LIBRARY_PATH" remote get-url origin)"
        case "$origin" in *odtu/PowerLabKiCadLibraries*) ;; *) fail "$LIBRARY_PATH is a git repo, but not odtu/PowerLabKiCadLibraries ($origin)." ;; esac
        git -C "$LIBRARY_PATH" fetch --quiet origin
        ok "Using your existing clone at $LIBRARY_PATH"
    elif ask "Clone the library to $LIBRARY_PATH ?"; then
        git clone --quiet "$LIBRARY_REPO" "$LIBRARY_PATH"
        ok "Cloned to $LIBRARY_PATH"
    fi
    [ -d "$LIBRARY_PATH/.git" ] && LIBRARY="$(cd "$LIBRARY_PATH" && pwd)"
    save_config
fi

configure=("$ROOT/tools/configure_kicad.py" --kicad-bin "$KICAD_BIN" --python "$KICAD_PYTHON")
explain=0
if [ -n "${LIBRARY:-}" ] && ask "Point KiCad's METUPOWERLAB_* paths and library tables at this clone? (backed up first)"; then
    configure+=(--library "$LIBRARY"); explain=1
fi
if ask "Turn on KiCad's API server and set its plugin Python to KiCad 10's? (the panel needs it)"; then
    configure+=(--enable-api); explain=1
fi
if [ "$explain" = 1 ]; then
    [ -f "$HOME/Library/Preferences/kicad/10.0/kicad_common.json" ] ||
        fail "KiCad 10 has no settings yet. Start KiCad once, quit it, then run this again."
    "$KICAD_PYTHON" "${configure[@]}"
fi

# ---- 6. GitHub (optional) --------------------------------------------------
say "6. GitHub (optional: share libraries, file problem reports with your account)"
GH="$(command -v gh || true)"
if [ -z "$GH" ] && command -v brew >/dev/null 2>&1 && ask "Install GitHub CLI (gh) with Homebrew?" N; then
    brew install gh && GH="$(command -v gh || true)"
fi
if [ -n "$GH" ]; then
    if "$GH" auth status --hostname github.com >/dev/null 2>&1; then ok "GitHub CLI ready and signed in"
    elif ask "Sign in to GitHub now? (opens your browser)" N; then "$GH" auth login --hostname github.com --web; fi
else warn "No GitHub CLI: reports open as a pre-filled form in your browser instead. You can connect later from the panel."; fi

save_config
ok "Settings saved to $SUPPORT/config.json (stays on this computer)"

echo
echo "Done. Next:"
echo "  1. Sign in to Claude Code once: run  claude  in Terminal, follow the login, then type /exit"
echo "  2. Start KiCad. PCB editor: the PowerLab Assistant button is on the top toolbar."
echo "  3. Schematic editor: KiCad > Settings > Schematic Editor > Toolbars,"
echo "     add 'IPC/Scripting plugins' to the Top main toolbar, then click the PowerLab button."
echo "  4. The first time the panel saves or reloads the schematic, macOS asks to let KiCad"
echo "     control your computer (Accessibility). Allow it: that's how the panel clicks"
echo "     File > Save and File > Revert in the schematic editor."
echo "  Problems? Use the bug button in the panel, or https://github.com/odtu/PowerLabKiCadAssistant/issues"
