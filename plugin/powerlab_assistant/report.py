"""Problem reports, filed as public GitHub issues on the assistant's repository.

A report is only ever sent when the user presses Submit after seeing its exact
content. It holds versions, the error and the panel's own stack trace — never
project, board or sheet names, part references, net names, file contents, the
user's messages, Claude's replies, the selection or the clipboard. Paths are
replaced with placeholders.
"""

import collections
import os
import platform
import re
import tempfile
import traceback
import urllib.parse

from . import config
from .common import find_claude, find_gh, run_quiet

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

# What the panel did recently, as event types only (no text, names or paths).
recent = collections.deque(maxlen=25)


def note_event(kind, detail=""):
    recent.append(f"{kind} {detail}".strip())


def scrub(text):
    """Remove paths, the Windows user name and e-mail addresses."""
    if not text:
        return ""
    known = [
        (PLUGIN_DIR, "<plugin>"),
        (config.library_path(), "<library>"),
        (config.kicad_bin(), "<kicad>"),
        (os.environ.get("LOCALAPPDATA", ""), "<localappdata>"),
        (os.environ.get("APPDATA", ""), "<appdata>"),
        (os.path.expanduser("~"), "<home>"),
    ]
    for path, label in sorted(known, key=lambda kv: -len(kv[0])):
        if path:
            for variant in {path, path.replace("\\", "/")}:
                text = re.sub(re.escape(variant), label, text, flags=re.IGNORECASE)
    # Whatever follows a private folder (project and file names) goes too; the plugin's
    # and KiCad's own file names stay, they're what a bug fix needs.
    text = re.sub(r"<(home|appdata|localappdata|library)>[\\/][^\s\"'<>|,;)]*", r"<\1>/…", text)
    text = re.sub(r"(?<![<\w])[A-Za-z]:[\\/][^\s\"'<>|,;)]*", "<path>", text)  # other drive paths
    text = re.sub(r"\\\\[^\s\"'<>|]+", "<path>", text)  # UNC paths
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "<email>", text)
    user = os.environ.get("USERNAME", "")
    if len(user) > 2:
        text = re.sub(re.escape(user), "<user>", text, flags=re.IGNORECASE)
    return text


def plugin_traceback(exc_type, exc, tb):
    """Only the frames from this plugin, so other code's details stay out."""
    frames = [f for f in traceback.extract_tb(tb) if f.filename.startswith(PLUGIN_DIR)]
    lines = [f'  {os.path.basename(f.filename)}:{f.lineno} in {f.name}' for f in frames[-12:]]
    return f"{exc_type.__name__}: {scrub(str(exc))[:300]}\n" + "\n".join(lines)


def _version(args):
    code, out = run_quiet(args, timeout=15)
    return scrub(out.splitlines()[0]) if code == 0 and out else "unknown"


def diagnostics(editor, model, kicad_version, error=None, extra=()):
    claude = find_claude()
    mcp = config.mcp_path()
    lines = [
        f"assistant: {config.VERSION}",
        f"editor: {editor}",
        f"kicad: {kicad_version or 'unknown'}",
        f"windows: {platform.platform()}",
        f"python: {platform.python_version()}",
        f"claude_code: {_version([claude, '--version']) if claude else 'not found'}",
        f"mcp_server: {_version(['git', '-C', mcp, 'rev-parse', '--short', 'HEAD']) if mcp else 'unknown'}",
        f"model: {model or 'default'}",
        *[scrub(line) for line in extra],
    ]
    if error:
        lines += ["", f"error: {scrub(error.get('kind', ''))}", scrub(error.get("detail", ""))]
    if recent:
        lines += ["", "recent panel events:"] + [f"  {scrub(e)}" for e in recent]
    return "\n".join(lines).strip()


def gh_ready():
    gh = find_gh()
    return bool(gh) and run_quiet([gh, "auth", "status", "--hostname", "github.com"], timeout=20)[0] == 0


def issue_body(description, diag):
    return (f"### What happened\n\n{description.strip() or '_No description given._'}\n\n"
            f"### Diagnostics\n\n```text\n{diag}\n```\n\n"
            "_Sent from PowerLab KiCad Assistant. No project data is included._")


def submit_with_gh(title, description, diag):
    """File the issue with the user's own GitHub login. Returns (ok, url-or-error)."""
    path = os.path.join(tempfile.gettempdir(), "powerlab-assistant-report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(issue_body(description, diag))
    try:
        code, out = run_quiet([find_gh(), "issue", "create", "-R", config.REPORT_REPO,
                               "--title", title, "--body-file", path, "--label", "bug"], timeout=60)
    finally:
        os.remove(path)
    return (True, out.strip().splitlines()[-1]) if code == 0 else (False, scrub(out)[-300:])


def prefilled_url(title, description, diag):
    """The repo's bug-report form with fields filled in; the user submits it in the browser."""
    base = f"https://github.com/{config.REPORT_REPO}/issues/new"
    for budget in (6000, 3000, 1200):  # GitHub rejects very long URLs
        query = urllib.parse.urlencode({
            "template": "bug_report.yml", "title": title,
            "what": description[:1500], "diagnostics": diag[:budget],
        })
        if len(query) < 7000:
            break
    return f"{base}?{query}"
