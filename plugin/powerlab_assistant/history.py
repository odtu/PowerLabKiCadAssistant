"""The panel's chat, kept per project so it survives closing the panel, the editor or KiCad.

One panel serves both editors, so each project folder has one chat: Claude Code's session
id, so the next message continues the same conversation (`--resume`), and the messages shown
in the panel, so they can be shown again. A chat reopened later isn't resumed: resuming sends
the whole conversation again, every tool result and render, with each message. It continues
in a new session told the user's last prompts, with the chat so far in a file (write_earlier)
that Claude reads only if it needs to. Stored in %APPDATA%\\PowerLabKiCadAssistant\\chats.
Nothing here is ever sent anywhere or put in problem reports.
"""

import hashlib
import json
import os

from . import config

FOLDER = os.path.join(config.CONFIG_DIR, "chats")
KINDS = ("user", "text", "thought", "tool", "tool_done", "meta", "image", "review", "plan")  # panel events that make up a chat
MAX_EVENTS = 600  # older messages are dropped from the panel (Claude still has them)
EDITORS = ("pcb", "schematic")  # before 0.6 each editor had its own panel and chat file


def _key(cwd):
    return hashlib.sha256(os.path.normcase(os.path.abspath(cwd)).encode("utf-8")).hexdigest()[:16]


def chat_path(cwd, folder=None):
    return os.path.join(folder or FOLDER, f"chat-{_key(cwd)}.json")


def _old_paths(cwd, folder=None):
    return [os.path.join(folder or FOLDER, f"{editor}-{_key(cwd)}.json") for editor in EDITORS]


def stored(kind, data):
    """The part of a panel event worth keeping (images, reviews and plans by path, not their data)."""
    event = {k: v for k, v in data.items() if k not in ("src", "body", "svg", "blocks", "notes", "links")}
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


def last_prompts(events, count=3):
    """The user's last few messages (what they asked, not what Claude did)."""
    return [e.get("text", "") for e in events if e.get("kind") == "user" and e.get("text")][-count:]


def earlier_path(cwd, folder=None):
    return os.path.join(folder or FOLDER, "earlier", _key(cwd), "earlier-chat.md")


def write_earlier(cwd, events, folder=None):
    """The chat so far as a short text file (prompts, replies, the steps' names), for a chat
    continued in a new session: Claude reads it only when the last prompts aren't enough.
    Returns its path, or "" if it couldn't be written."""
    lines, steps = ["# Earlier chat on this project", ""], []

    def flush():
        if steps:
            lines.extend([f"(steps: {', '.join(dict.fromkeys(steps))})", ""])
            steps.clear()

    for e in events:
        kind, text = e.get("kind"), (e.get("text") or "").strip()
        if kind == "tool":
            steps.append(e.get("name", ""))
            continue
        if kind == "user":
            flush()
            lines.extend(["## User", text, ""])
        elif kind == "text" and text:
            flush()
            lines.extend(["Claude: " + text, ""])
        elif kind in ("review", "plan") and e.get("path"):
            flush()
            lines.extend([f"({'Design review' if kind == 'review' else 'Block plan'}: {e['path']})", ""])
    flush()
    path = earlier_path(cwd, folder)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except OSError:
        return ""
    return path


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
