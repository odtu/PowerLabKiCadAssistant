"""Files the user attaches to a message (picked, pasted or dropped into the panel).

Pasted and dropped files arrive from the page as data URLs; they're saved to a private
temp folder so Claude can open them with its Read tool (images and PDFs included).
Nothing here leaves the computer except through Claude itself.
"""

import base64
import os
import re
import tempfile
import time

FOLDER = os.path.join(tempfile.gettempdir(), "PowerLabAssistant", "attachments")
MAX_BYTES = 20 * 1024 * 1024
KEEP_DAYS = 7


def safe_name(name):
    base = re.split(r"[\\/]", name or "")[-1].strip() or "pasted"
    base = re.sub(r"[^\w.\- ]+", "_", base)[:80].strip(" .") or "pasted"
    return base


def save_data(name, data_url, folder=FOLDER):
    """Save a data: URL to the attachments folder; returns the path, or raises ValueError."""
    head, _, payload = (data_url or "").partition(",")
    if not head.startswith("data:") or ";base64" not in head:
        raise ValueError("not a file")
    data = base64.b64decode(payload, validate=False)
    if len(data) > MAX_BYTES:
        raise ValueError(f"larger than {MAX_BYTES // (1024 * 1024)} MB")
    if not os.path.splitext(name or "")[1]:
        ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/gif": ".gif", "image/webp": ".webp",
               "application/pdf": ".pdf"}.get(head[5:].split(";")[0], "")
        name = (name or "pasted") + ext
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, time.strftime("%Y%m%d-%H%M%S-") + safe_name(name))
    with open(path, "wb") as f:
        f.write(data)
    return path


def clean_old(folder=FOLDER, days=KEEP_DAYS):
    """Delete pasted files older than `days` (only ever inside our own folder)."""
    if not os.path.isdir(folder):
        return
    limit = time.time() - days * 86400
    for entry in os.scandir(folder):
        if entry.is_file() and entry.stat().st_mtime < limit:
            try:
                os.remove(entry.path)
            except OSError:
                pass


def prompt_suffix(paths):
    """Text appended to the user's message so Claude knows where the files are."""
    if not paths:
        return ""
    lines = "\n".join(f"- {p}" for p in paths)
    return f"\n\nAttached files (open them with the Read tool):\n{lines}"


def folders(paths):
    """Folders Claude needs read access to (--add-dir), without duplicates."""
    seen = []
    for p in paths:
        d = os.path.dirname(os.path.abspath(p))
        if d not in seen:
            seen.append(d)
    return seen
