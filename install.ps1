<#
.SYNOPSIS
  Installs PowerLab KiCad Assistant (KiCad 10, Windows).

.DESCRIPTION
  Asks before every change. Installs nothing that sends your project data to
  METU Power Lab. Your Claude and GitHub logins stay on this computer.

  Steps:
    1. Checks KiCad 10, git and Node.js.
    2. Claude Code (official installer) if missing.
    3. KiCad MCP server (mixelpixx/KiCAD-MCP-Server, pinned version) and its
       Python packages in KiCad's own Python.
    4. The panel plugins into your KiCad 10 folder.
    5. The METU Power Lab library as a git clone, and KiCad pointed at it.
    6. Optionally GitHub CLI, for sharing libraries and filing reports.

  -Update (used by the panel's Update button) asks nothing: it refreshes the
  plugin files and, only if its pinned version changed, the KiCad MCP server.
  The library, KiCad settings and GitHub setup are left alone.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File install.ps1
  powershell -ExecutionPolicy Bypass -File install.ps1 -LibraryPath D:\Work\PowerLabKiCadLibraries
  powershell -ExecutionPolicy Bypass -File install.ps1 -Update
#>
param(
    [string]$LibraryPath = "",
    [switch]$SkipLibrary,
    [switch]$SkipMcp,
    [switch]$Update,
    [string]$McpCommit = "ac716d1"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppData = Join-Path $env:APPDATA "PowerLabKiCadAssistant"
$LocalData = Join-Path $env:LOCALAPPDATA "PowerLabKiCadAssistant"
$McpRepo = "https://github.com/mixelpixx/KiCAD-MCP-Server.git"
$LibraryRepo = "https://github.com/odtu/PowerLabKiCadLibraries.git"

function Say($text) { Write-Host $text -ForegroundColor Cyan }
function Ok($text) { Write-Host "  OK  $text" -ForegroundColor Green }
function Warn($text) { Write-Host "  !   $text" -ForegroundColor Yellow }
function Fail($text) { Write-Host "  X   $text" -ForegroundColor Red; exit 1 }
function Ask($question, $default = "Y") {
    $hint = if ($default -eq "Y") { "[Y/n]" } else { "[y/N]" }
    $answer = Read-Host "  ?   $question $hint"
    if ([string]::IsNullOrWhiteSpace($answer)) { $answer = $default }
    return $answer.Trim().ToUpper().StartsWith("Y")
}
function Probe($exe, [string[]]$arguments) {
    # Runs a check whose output we don't need and returns its exit code. Windows
    # PowerShell 5.1 turns redirected stderr into a terminating error under "Stop",
    # and tools like gh/claude report "not signed in / not found" on stderr.
    $saved = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try { & $exe @arguments *> $null; return $LASTEXITCODE }
    catch { return 1 }
    finally { $ErrorActionPreference = $saved }
}
function Save-Config {
    # Written after each step, so an interrupted install still leaves usable settings.
    New-Item -ItemType Directory -Force $AppData | Out-Null
    $path = Join-Path $AppData "config.json"
    $config = @{}
    if (Test-Path $path) {
        (Get-Content $path -Raw | ConvertFrom-Json).PSObject.Properties | ForEach-Object { $config[$_.Name] = $_.Value }
    }
    if ($script:KiCadBin) { $config["kicad_bin"] = $script:KiCadBin }
    if ($script:McpReady) { $config["mcp_path"] = $script:McpDir }
    if ($script:Library) { $config["library_path"] = $script:Library }
    $config["source_path"] = $script:Root  # where the panel's Update button pulls from
    if (-not $config.ContainsKey("extra_dirs")) { $config["extra_dirs"] = @() }
    $config | ConvertTo-Json | Set-Content -Encoding UTF8 $path
    return $path
}
function Run($exe, [string[]]$arguments, $where = $null) {
    # Runs a native command; stops the install if it fails.
    if ($where) { Push-Location $where }
    try {
        & $exe @arguments
        if ($LASTEXITCODE -ne 0) { Fail "$exe $($arguments -join ' ') failed (exit $LASTEXITCODE)" }
    } finally { if ($where) { Pop-Location } }
}

Write-Host ""
Write-Host ("PowerLab KiCad Assistant - " + $(if ($Update) { "update" } else { "installer" })) -ForegroundColor White
Write-Host "Uses Claude Code. AI can make mistakes: always check its work before ordering boards." -ForegroundColor DarkGray
Write-Host ""

# ---- 1. Requirements -------------------------------------------------------
Say "1. Checking requirements"
$KiCadBin = $null
$uninstall = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*", "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*" -ErrorAction SilentlyContinue |
    Where-Object { $_.DisplayName -like "KiCad 10*" } | Select-Object -First 1
if ($uninstall -and $uninstall.InstallLocation) { $KiCadBin = Join-Path $uninstall.InstallLocation "bin" }
if (-not $KiCadBin -or -not (Test-Path (Join-Path $KiCadBin "kicad-cli.exe"))) { $KiCadBin = "C:\Program Files\KiCad\10.0\bin" }
$KiCadPython = Join-Path $KiCadBin "python.exe"
if (-not (Test-Path (Join-Path $KiCadBin "kicad-cli.exe"))) { Fail "KiCad 10 not found. Install it from https://www.kicad.org/download/windows/" }
Ok "KiCad 10 at $KiCadBin"

# KiCad's documents folder for 10.0 = three levels above its Python user site.
$userSite = (& $KiCadPython -c "import site; print(site.USER_SITE)").Trim()
$KiCadDocs = Split-Path (Split-Path (Split-Path $userSite -Parent) -Parent) -Parent
Ok "KiCad 10 user folder: $KiCadDocs"

foreach ($tool in @("git", "node", "npm")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        $pkg = @{ git = "Git.Git"; node = "OpenJS.NodeJS.LTS"; npm = "OpenJS.NodeJS.LTS" }[$tool]
        Fail "$tool is missing. Install it with:  winget install --id $pkg -e   then open a new PowerShell and run this again."
    }
}
$nodeMajor = [int]((node --version).TrimStart("v").Split(".")[0])
if ($nodeMajor -lt 18) { Fail "Node.js 18 or newer is needed (found $(node --version))." }
Ok "git, Node.js $(node --version)"

$running = Get-Process kicad, eeschema, pcbnew -ErrorAction SilentlyContinue
if ($running -and -not $Update) {  # updating only replaces plugin files; KiCad settings aren't touched
    Warn "KiCad is running. Close it now: KiCad rewrites its settings when it exits."
    Read-Host "  Press Enter once KiCad is closed" | Out-Null
    if (Get-Process kicad, eeschema, pcbnew -ErrorAction SilentlyContinue) { Fail "KiCad is still running." }
}

# ---- 2. Claude Code --------------------------------------------------------
Say "2. Claude Code"
$Claude = (Get-Command claude -ErrorAction SilentlyContinue).Source
if (-not $Claude -and (Test-Path "$env:USERPROFILE\.local\bin\claude.exe")) { $Claude = "$env:USERPROFILE\.local\bin\claude.exe" }
if (-not $Claude -and $Update) { Fail "Claude Code is missing. Run install.ps1 without -Update." }
if (-not $Claude) {
    if (Ask "Claude Code is not installed. Install it with Anthropic's official installer now?") {
        Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression
        $Claude = "$env:USERPROFILE\.local\bin\claude.exe"
        if (-not (Test-Path $Claude)) { Fail "Claude Code install did not finish. See https://docs.claude.com/claude-code" }
    } else { Fail "Claude Code is required." }
}
Ok "Claude Code at $Claude"

# ---- 3. KiCad MCP server ---------------------------------------------------
$McpDir = Join-Path $LocalData "KiCAD-MCP-Server"
$mcpCurrent = $false
if ($Update -and (Test-Path (Join-Path $McpDir "dist\index.js"))) {
    $head = (& git -C $McpDir rev-parse HEAD).Trim()
    $mcpCurrent = $head.StartsWith($McpCommit)
}
if ($mcpCurrent) {
    Say "3. KiCad tools for Claude"
    Ok "Already at the pinned version ($McpCommit)"
    $McpReady = $true
} elseif (-not $SkipMcp) {
    Say "3. KiCad tools for Claude (KiCAD-MCP-Server @ $McpCommit)"
    New-Item -ItemType Directory -Force $LocalData | Out-Null
    if (-not (Test-Path (Join-Path $McpDir ".git"))) { Run git @("clone", "--quiet", $McpRepo, $McpDir) }
    Run git @("-C", $McpDir, "fetch", "--quiet", "origin")
    Run git @("-C", $McpDir, "checkout", "--quiet", $McpCommit)
    Run npm @("ci", "--no-audit", "--no-fund", "--loglevel=error") $McpDir
    Run npm @("run", "build", "--silent") $McpDir
    Ok "MCP server built"
    # KiCad's Python puts --user packages in its own 3rdparty folder; no admin rights needed.
    Run $KiCadPython @("-m", "pip", "install", "--user", "--quiet", "--disable-pip-version-check", "-r", (Join-Path $McpDir "requirements.txt"))
    Ok "Python packages installed into KiCad's Python"
    $McpReady = $true

    $exists = ((Probe $Claude @("mcp", "get", "kicad")) -eq 0)
    if (-not $exists -or (-not $Update -and (Ask "Claude Code already has a 'kicad' tool server. Replace it with this one?"))) {
        if ($exists) { & $Claude mcp remove kicad -s user | Out-Null }
        $sitePackages = Join-Path $KiCadBin "Lib\site-packages"
        $entry = Join-Path $McpDir "dist\index.js"
        # Start-Process passes the argument string as-is (PowerShell 5.1 would drop the bare --).
        $argLine = "mcp add kicad -s user -e `"PYTHONPATH=$sitePackages`" -e `"KICAD_PYTHON=$KiCadPython`" -- node `"$entry`""
        $p = Start-Process -FilePath $Claude -ArgumentList $argLine -NoNewWindow -Wait -PassThru
        if ($p.ExitCode -ne 0) { Fail "Couldn't register the KiCad tools with Claude Code." }
        Ok "KiCad tools registered with Claude Code (for your user only)"
    }
} else { Warn "Skipped the KiCad MCP server (-SkipMcp)." }

# ---- 4. Plugins ------------------------------------------------------------
Say "4. Panel plugins"
$PanelDest = Join-Path $KiCadDocs "scripting\plugins\powerlab_assistant"
$ButtonDest = Join-Path $KiCadDocs "plugins\powerlab-assistant"
foreach ($legacy in @((Join-Path $KiCadDocs "scripting\plugins\claude_launcher"), (Join-Path $KiCadDocs "plugins\metu-powerlab-claude"))) {
    if ((Test-Path $legacy) -and -not $Update -and (Ask "Remove the old prototype plugin at $legacy ?")) { Remove-Item -Recurse -Force $legacy }
}
foreach ($pair in @(@("plugin\powerlab_assistant", $PanelDest), @("plugin\powerlab-assistant-button", $ButtonDest))) {
    if (Test-Path $pair[1]) { Remove-Item -Recurse -Force $pair[1] }
    New-Item -ItemType Directory -Force $pair[1] | Out-Null
    Copy-Item -Recurse -Force (Join-Path $Root "$($pair[0])\*") $pair[1]
}
Ok "PCB editor panel   -> $PanelDest"
Ok "Schematic button   -> $ButtonDest"
$null = Save-Config

if ($Update) {
    $version = (Select-String -Path (Join-Path $PanelDest "config.py") -Pattern '^VERSION = "([^"]+)"').Matches[0].Groups[1].Value
    Write-Host ""
    Write-Host "Updated to PowerLab KiCad Assistant $version." -ForegroundColor White
    Write-Host "  Restart KiCad to load it. The schematic panel restarts by itself on its next button click."
    exit 0
}

# ---- 5. Library ------------------------------------------------------------
$Library = ""
if (-not $SkipLibrary) {
    Say "5. METU Power Lab library (git clone, kept in sync by the panel)"
    if (-not $LibraryPath) { $LibraryPath = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "PowerLabKiCadLibraries" }
    if (Test-Path (Join-Path $LibraryPath ".git")) {
        $origin = (git -C $LibraryPath remote get-url origin).Trim()
        if ($origin -notmatch "odtu/PowerLabKiCadLibraries") { Fail "$LibraryPath is a git repo, but not odtu/PowerLabKiCadLibraries ($origin)." }
        Run git @("-C", $LibraryPath, "fetch", "--quiet", "origin")
        Ok "Using your existing clone at $LibraryPath"
    } elseif (Ask "Clone the library to $LibraryPath ?") {
        Run git @("clone", "--quiet", $LibraryRepo, $LibraryPath)
        Ok "Cloned to $LibraryPath"
    }
    if (Test-Path (Join-Path $LibraryPath ".git")) { $Library = (Resolve-Path $LibraryPath).Path }
    $null = Save-Config
}

$configure = @((Join-Path $Root "tools\configure_kicad.py"), "--kicad-bin", $KiCadBin)
$explain = @()
if ($Library -and (Ask "Point KiCad's METUPOWERLAB_* paths and library tables at this clone? (backed up first)")) {
    $configure += @("--library", $Library); $explain += "library paths"
}
if (Ask "Turn on KiCad's API server and set its plugin Python to KiCad 10? (needed for the schematic panel)") {
    $configure += "--enable-api"; $explain += "API server"
}
if ($explain.Count -gt 0) {
    Run $KiCadPython $configure
    if ($Library) {
        Warn "If you installed the library from KiCad's Plugin and Content Manager before, you can uninstall that package now; KiCad uses the git clone instead."
    }
}

# ---- 6. GitHub (optional) --------------------------------------------------
Say "6. GitHub (optional: share libraries, file problem reports with your account)"
$Gh = (Get-Command gh -ErrorAction SilentlyContinue).Source
if (-not $Gh -and (Test-Path "$env:ProgramFiles\GitHub CLI\gh.exe")) { $Gh = "$env:ProgramFiles\GitHub CLI\gh.exe" }
if (-not $Gh -and (Ask "Install GitHub CLI (gh) with winget?" "N")) {
    winget install --id GitHub.cli -e --source winget
    $Gh = "$env:ProgramFiles\GitHub CLI\gh.exe"
}
if ($Gh -and (Test-Path $Gh)) {
    if ((Probe $Gh @("auth", "status", "--hostname", "github.com")) -eq 0) { Ok "GitHub CLI ready and signed in" }
    elseif (Ask "Sign in to GitHub now? (opens your browser)" "N") { & $Gh auth login --hostname github.com --web }
} else { Warn "No GitHub CLI: reports open as a pre-filled form in your browser instead. You can connect later from the panel." }

# ---- Settings (local only) -------------------------------------------------
$configPath = Save-Config
Ok "Settings saved to $configPath (stays on this computer)"

Write-Host ""
Write-Host "Done. Next:" -ForegroundColor White
Write-Host "  1. Sign in to Claude Code once: run  claude  in a terminal, follow the login, then type /exit"
Write-Host "  2. Start KiCad. PCB editor: the PowerLab Assistant button is on the top toolbar."
Write-Host "  3. Schematic editor: Preferences > Preferences > Schematic Editor > Toolbars,"
Write-Host "     add 'IPC/Scripting plugins' to the Top main toolbar, then click the PowerLab button."
Write-Host "  Problems? Use the bug button in the panel, or https://github.com/odtu/PowerLabKiCadAssistant/issues"
