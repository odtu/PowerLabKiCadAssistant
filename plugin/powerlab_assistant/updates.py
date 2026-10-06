"""Plugin update check: is there a newer release of PowerLab KiCad Assistant?

At most once an hour the panel asks GitHub for the latest release of the public
repository. The request is anonymous and carries nothing about the user or their
projects (GitHub sees an IP address, like any download).
"""

import json
import os
import re
import time
import urllib.request

from . import config
from .common import open_console

# A day was too long: a fix released right after a check stayed invisible until
# the next day (a 0.1.1 panel cached "latest = 0.1.1" and missed 0.1.2).
CHECK_EVERY = 60 * 60  # seconds: once an hour
LATEST_URL = f"https://api.github.com/repos/{config.REPORT_REPO}/releases/latest"
RELEASES_URL = f"https://github.com/{config.REPORT_REPO}/releases"


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


def fetch_latest(timeout=10):
    request = urllib.request.Request(LATEST_URL, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "PowerLabKiCadAssistant",  # GitHub requires one; no user data
    })
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def check(settings, force=False, fetch=fetch_latest):
    """Return {'available', 'version', 'summary', 'url'} for the latest release,
    reusing the last answer if GitHub was asked less than CHECK_EVERY ago. Network: call
    from a worker thread. Updates `settings` (caller saves it)."""
    cached = settings.get("update_cache") or {}
    if force or time.time() - settings.get("update_checked", 0) >= CHECK_EVERY or not cached:
        release = fetch()
        cached = {"version": release.get("tag_name", ""), "summary": summary(release.get("body", "")),
                  "url": release.get("html_url") or RELEASES_URL}
        settings["update_checked"] = time.time()
        settings["update_cache"] = cached
    latest = parse_version(cached.get("version"))
    return {
        "available": bool(latest) and latest > parse_version(config.VERSION),
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
