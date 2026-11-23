#!/bin/bash
# Removes PowerLab KiCad Assistant on macOS (the twin of uninstall.ps1). Asks before each
# step. Your library clone, projects, Claude Code and GitHub CLI are left alone.

SUPPORT="$HOME/Library/Application Support/PowerLabKiCadAssistant"
KICAD_DOCS="$HOME/Documents/KiCad/10.0"

ask() {
    local answer
    read -r -p "  ?   $1 [y/N] " answer || answer=""
    case "$answer" in [Yy]*) return 0 ;; *) return 1 ;; esac
}

for dir in "$KICAD_DOCS/scripting/plugins/powerlab_assistant" "$KICAD_DOCS/plugins/powerlab-assistant"; do
    if [ -d "$dir" ] && ask "Remove plugin folder $dir ?"; then rm -rf "$dir"; fi
done

skills=""
for skill in "$HOME"/.claude/skills/powerlab-*/; do
    [ -d "$skill" ] && skills="$skills $(basename "$skill")"
done
if [ -n "$skills" ] && ask "Remove the assistant's Claude skills ($skills )?"; then
    rm -rf "$HOME"/.claude/skills/powerlab-*/
fi

CLAUDE="$(command -v claude || true)"
[ -z "$CLAUDE" ] && CLAUDE="$HOME/.local/bin/claude"
if [ -x "$CLAUDE" ] && ask "Remove the 'kicad' tool server from Claude Code?"; then
    "$CLAUDE" mcp remove kicad -s user
fi

for part in KiCAD-MCP-Server pylib; do
    if [ -d "$SUPPORT/$part" ] && ask "Delete $SUPPORT/$part ?"; then rm -rf "${SUPPORT:?}/$part"; fi
done
if [ -d "$SUPPORT" ] && ask "Delete settings, chats and KiCad config backups in $SUPPORT ? (copy the backup folder first if you may want to restore it)"; then
    rm -rf "$SUPPORT"
fi

echo
echo "Done. KiCad's METUPOWERLAB_* paths still point at your library clone; change them in"
echo "KiCad > Settings > Configure Paths if you delete the clone. Backups of the KiCad settings the"
echo "installer changed are in $SUPPORT/backup (unless you deleted that folder)."
echo "NumPy and the KiCad MCP server's Python packages stay in ~/Library/Python/<version>."
