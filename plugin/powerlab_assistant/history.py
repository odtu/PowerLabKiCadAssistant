"""The panel's chat, kept per project so it survives closing the panel, the editor or KiCad.

One panel serves both editors, so each project folder has one chat: Claude Code's session
id, so the next message continues the same conversation (`--resume`), and the messages shown
in the panel, so they can be shown again. Stored in %APPDATA%\\PowerLabKiCadAssistant\\chats.
Nothing here is ever sent anywhere or put in problem reports.
"""

import hashlib
import json
import os

from . import config

FOLDER = os.path.join(config.CONFIG_DIR, "chats")
KINDS = ("user", "text", "tool", "tool_done", "meta", "image")  # panel events that make up a chat
MAX_EVENTS = 600  # older messages are dropped from the panel (Claude still has them)
EDITORS = ("pcb", "schematic")  # before 0.6 each editor had its own panel and chat file


def _key(cwd):
    return hashlib.sha256(os.path.normcase(os.path.abspath(cwd)).encode("utf-8")).hexdigest()[:16]


def chat_path(cwd, folder=None):
    return os.path.join(folder or FOLDER, f"chat-{_key(cwd)}.json")


def _old_paths(cwd, folder=None):
    return [os.path.join(folder or FOLDER, f"{editor}-{_key(cwd)}.json") for editor in EDITORS]


def stored(kind, data):
    """The part of a panel event worth keeping (images by path, not their data)."""
    event = {k: v for k, v in data.items() if k != "src"}
    event["kind"] = kind
    return event


def load(cwd, folder=None):
    """(session_id or None, events) of the last chat for this project, empty if none."""
    path = chat_path(cwd, folder)
    found = []
    for p in [path] if os.path.exists(path) else _old_paths(cwd, folder):
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        if isinstance(data, dict):
            found.append((data, os.path.getmtime(p)))
    if not found:
        return None, []
    # Of the two old per-editor chats, keep the longer one: the real work, not a quick "hi".
    data = max(found, key=lambda d: (len(d[0].get("events") or []), d[1]))[0]
    events = [e for e in data.get("events") or [] if isinstance(e, dict) and e.get("kind") in KINDS]
    return data.get("session_id") or None, events


def save(cwd, session_id, events, folder=None):
    path = chat_path(cwd, folder)
    try:
        if not session_id and not events:
            if os.path.exists(path):
                os.remove(path)
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"cwd": cwd, "session_id": session_id, "events": events[-MAX_EVENTS:]}, f)
            os.replace(tmp, path)  # a crash mid-write never leaves a half-written chat
        for old in _old_paths(cwd, folder):
            if os.path.exists(old):
                os.remove(old)  # carried over into this chat (or cleared with +)
    except OSError:
        pass  # the chat still works; it just won't be there next time
