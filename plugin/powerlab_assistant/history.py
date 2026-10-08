"""The panel's chat, kept per project so it survives closing the panel, the editor or KiCad.

Each editor (pcb, schematic) keeps one chat per project folder: Claude Code's session id,
so the next message continues the same conversation (`--resume`), and the messages shown
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


def chat_path(editor, cwd, folder=None):
    folder = folder or FOLDER
    key = hashlib.sha256(os.path.normcase(os.path.abspath(cwd)).encode("utf-8")).hexdigest()[:16]
    return os.path.join(folder, f"{editor}-{key}.json")


def stored(kind, data):
    """The part of a panel event worth keeping (images by path, not their data)."""
    event = {k: v for k, v in data.items() if k != "src"}
    event["kind"] = kind
    return event


def load(editor, cwd, folder=None):
    """(session_id or None, events) of the last chat for this project, empty if none."""
    try:
        with open(chat_path(editor, cwd, folder), encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None, []
    if not isinstance(data, dict):
        return None, []
    events = [e for e in data.get("events", []) if isinstance(e, dict) and e.get("kind") in KINDS]
    return data.get("session_id") or None, events


def save(editor, cwd, session_id, events, folder=None):
    path = chat_path(editor, cwd, folder)
    try:
        if not session_id and not events:
            if os.path.exists(path):
                os.remove(path)
            return
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"cwd": cwd, "session_id": session_id, "events": events[-MAX_EVENTS:]}, f)
        os.replace(tmp, path)  # a crash mid-write never leaves a half-written chat
    except OSError:
        pass  # the chat still works; it just won't be there next time
