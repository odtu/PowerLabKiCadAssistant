"""Plugin update check: is there a newer stable version of PowerLab KiCad Assistant?

`main` is the stable branch: changes land on `test` first and reach `main` only when
they are released. Every few minutes the panel reads VERSION from `main` on
raw.githubusercontent.com, which, unlike the GitHub API, has no 60-requests-an-hour
limit per IP that a lab behind one address would share. Only when that version is
newer does it ask the API for the release notes, once per version. Both requests are
anonymous and carry nothing about the user or their projects (GitHub sees an IP
address, like any download).
"""

import json
import os
import re
import time
import urllib.request

from . import config
from .common import open_console

# Stable releases should reach users right away. raw.githubusercontent.com caches for
# up to 5 minutes too, so a release shows within about 10 minutes.
CHECK_EVERY = 5 * 60  # seconds
STABLE_BRANCH = "main"
VERSION_URL = (f"https://raw.githubusercontent.com/{config.REPORT_REPO}/{STABLE_BRANCH}"
               "/plugin/powerlab_assistant/config.py")
LATEST_URL = f"https://api.github.com/repos/{config.REPORT_REPO}/releases/latest"
RELEASES_URL = f"https://github.com/{config.REPORT_REPO}/releases"
HEADERS = {"User-Agent": "PowerLabKiCadAssistant"}  # GitHub requires one; no user data


def parse_version(text):
    """'v0.1.1' / '0.1.1' -> (0, 1, 1); 'v0.2' -> (0, 2, 0); unparsable -> ()."""
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", text or "")
    return tuple(int(n or 0) for n in match.groups()) if match else ()


def summary(notes):
    """First non-heading line of the release notes, for the one-line bar."""
    for line in (notes or "").splitlines():
        line = line.strip().lstrip("-*").strip()
        if line and not line.startswith("#"):
            return line[:160]
    return ""


def version_in(source):
    """VERSION = "0.5.1" in config.py's text -> '0.5.1' ('' if missing)."""
    match = re.search(r'^VERSION\s*=\s*"([^"]+)"', source or "", re.M)
    return match.group(1) if match else ""


def fetch_stable_version(timeout=10):
    request = urllib.request.Request(VERSION_URL, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return version_in(response.read().decode("utf-8", "replace"))


def fetch_latest(timeout=10):
    request = urllib.request.Request(LATEST_URL, headers={**HEADERS, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def check(settings, force=False, fetch_version=fetch_stable_version, fetch_release=fetch_latest):
    """Return {'available', 'version', 'summary', 'url'} for the stable version,
    reusing the last answer if GitHub was asked less than CHECK_EVERY ago. Network: call
    from a worker thread. Updates `settings` (caller saves it)."""
    cached = settings.get("update_cache") or {}
    if force or time.time() - settings.get("update_checked", 0) >= CHECK_EVERY or not cached.get("version"):
        version = fetch_version()
        if parse_version(version) != parse_version(cached.get("version")):
            cached = {"version": version}  # notes of an older version don't describe this one
        settings["update_checked"] = time.time()
        settings["update_cache"] = cached
    latest = parse_version(cached.get("version"))
    available = bool(latest) and latest > parse_version(config.VERSION)
    if available and "summary" not in cached:
        # `main` can move a moment before its release is published: until the latest
        # release is this version, show the bar without notes and ask again next time.
        try:
            release = fetch_release()
        except Exception:
            release = {}
        if parse_version(release.get("tag_name")) == latest:
            cached["summary"] = summary(release.get("body", ""))
            cached["url"] = release.get("html_url") or RELEASES_URL
    return {
        "available": available,
        "version": cached.get("version", "").lstrip("v"),
        "current": config.VERSION,
        "summary": cached.get("summary", ""),
        "url": cached.get("url", RELEASES_URL),
    }


def can_self_update():
    source = config.source_path()
    return bool(source) and os.path.isdir(os.path.join(source, ".git")) and \
        os.path.isfile(os.path.join(source, "install.ps1"))


def start_update():
    """Pull the latest code into the folder install.ps1 ran from and re-run it in
    update mode, in a console the user can watch. Returns False if the install
    wasn't made from a git clone (then the release page is the way to update)."""
    if not can_self_update():
        return False
    source = config.source_path()
    script = (
        f"Set-Location -LiteralPath '{source}'; "
        "Write-Host 'Updating PowerLab KiCad Assistant...' -ForegroundColor Cyan; "
        "git pull --ff-only; "
        "if ($LASTEXITCODE -ne 0) { Write-Host 'git pull failed: see above.' -ForegroundColor Red; return }; "
        "powershell -NoProfile -ExecutionPolicy Bypass -File .\\install.ps1 -Update; "
        "Write-Host ''; Write-Host 'Restart KiCad to finish the update. You can close this window.' -ForegroundColor Green"
    )
    open_console(["powershell", "-NoProfile", "-NoExit", "-Command", script], cwd=source)
    return True
