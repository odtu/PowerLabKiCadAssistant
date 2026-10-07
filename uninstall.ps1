<#
.SYNOPSIS
  Removes PowerLab KiCad Assistant. Asks before each step.
  Your library clone, projects, Claude Code and GitHub CLI are left alone.
#>
$ErrorActionPreference = "Continue"
$AppData = Join-Path $env:APPDATA "PowerLabKiCadAssistant"
$LocalData = Join-Path $env:LOCALAPPDATA "PowerLabKiCadAssistant"

function Ask($question) {
    $answer = Read-Host "  ?   $question [y/N]"
    return $answer.Trim().ToUpper().StartsWith("Y")
}

$python = "C:\Program Files\KiCad\10.0\bin\python.exe"
$configPath = Join-Path $AppData "config.json"
if (Test-Path $configPath) {
    $bin = (Get-Content $configPath -Raw | ConvertFrom-Json).kicad_bin
    if ($bin) { $python = Join-Path $bin "python.exe" }
}
$userSite = (& $python -c "import site; print(site.USER_SITE)").Trim()
$KiCadDocs = Split-Path (Split-Path (Split-Path $userSite -Parent) -Parent) -Parent

foreach ($dir in @((Join-Path $KiCadDocs "scripting\plugins\powerlab_assistant"), (Join-Path $KiCadDocs "plugins\powerlab-assistant"))) {
    if ((Test-Path $dir) -and (Ask "Remove plugin folder $dir ?")) { Remove-Item -Recurse -Force $dir }
}

$skills = @(Get-ChildItem (Join-Path $env:USERPROFILE ".claude\skills") -Directory -Filter "powerlab-*" -ErrorAction SilentlyContinue)
if ($skills.Count -and (Ask "Remove the assistant's Claude skills ($(($skills | ForEach-Object Name) -join ', '))?")) {
    $skills | ForEach-Object { Remove-Item -Recurse -Force $_.FullName }
}

$claude = (Get-Command claude -ErrorAction SilentlyContinue).Source
if (-not $claude) { $claude = "$env:USERPROFILE\.local\bin\claude.exe" }
if ((Test-Path $claude) -and (Ask "Remove the 'kicad' tool server from Claude Code?")) { & $claude mcp remove kicad -s user }

if ((Test-Path $LocalData) -and (Ask "Delete the KiCad MCP server, Java and Freerouting copies in $LocalData ?")) { Remove-Item -Recurse -Force $LocalData }
if ((Test-Path $AppData) -and (Ask "Delete settings and KiCad config backups in $AppData ? (copy the backup folder first if you may want to restore it)")) {
    Remove-Item -Recurse -Force $AppData
}

Write-Host ""
Write-Host "Done. KiCad's METUPOWERLAB_* paths still point at your library clone; change them in"
Write-Host "KiCad > Preferences > Configure Paths if you delete the clone. Backups of the KiCad settings the"
Write-Host "installer changed are in $AppData\backup (unless you deleted that folder)."
