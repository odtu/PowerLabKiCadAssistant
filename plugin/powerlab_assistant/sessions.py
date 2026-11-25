"""Past conversations on a project, from Claude Code's own records, as readable transcripts.

Claude Code keeps every session it ran as JSON lines in ~/.claude/projects/<project>/
(CLAUDE_CONFIG_DIR moves it), panel runs included, and deletes them after about a month. The
panel lists them, and writes one as Markdown into the project's chat-history folder: the
user's prompts, Claude's replies, the steps it took (tool names and their file or part),
and at the end where it stopped (a usage limit, an error, or mid-step). Nothing is sent to
Claude for this, so it costs no tokens. The transcript can be summarised elsewhere and
attached to a new chat, or attached as it is ("Continue").
"""

import json
import os
import re
import time

STATE_TAGS = ("<kicad_state>", "<selection>")  # the panel's context after each prompt
DETAIL_KEYS = ("file_path", "path", "schematicPath", "pcbPath", "reference", "componentRef",
               "net", "netName", "name", "skill", "query", "pattern", "command", "url")
LAST_STEPS = 15  # steps listed under "Where it stopped"
FOLDER_NAME = "chat-history"


def claude_dir():
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")


def encoded(cwd):
    """Claude Code's folder name for a project: every character but letters and digits -> '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(cwd))


def session_folder(cwd, root=None):
    """Where Claude Code keeps this project's sessions, or "" if it has none."""
    projects = os.path.join(root or claude_dir(), "projects")
    folder = os.path.join(projects, encoded(cwd))
    if os.path.isdir(folder):
        return folder
    # Very long paths are shortened with a hash: find the folder whose sessions ran here.
    prefix = encoded(cwd)[:100]
    try:
        names = [n for n in os.listdir(projects) if n.startswith(prefix)]
    except OSError:
        return ""
    for name in names:
        for path in _jsonl(os.path.join(projects, name))[:1]:
            for entry in _entries(path, limit=30):
                if entry.get("cwd"):
                    if os.path.abspath(entry["cwd"]) == os.path.abspath(cwd):
                        return os.path.join(projects, name)
                    break
    return ""


def _jsonl(folder):
    try:
        paths = [os.path.join(folder, n) for n in os.listdir(folder) if n.endswith(".jsonl")]
    except OSError:
        return []
    return sorted(paths, key=os.path.getmtime, reverse=True)


def _entries(path, limit=None):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if limit is not None and i >= limit:
                    return
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if isinstance(entry, dict):
                    yield entry
    except OSError:
        return


def prompt_text(entry):
    """The user's own words in a user entry (without the panel's KiCad state), else None.
    Tool results, loaded skills and Claude Code's own notes aren't prompts."""
    if entry.get("type") != "user" or entry.get("isMeta") or entry.get("isSidechain"):
        return None
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, list):
        if any(isinstance(c, dict) and c.get("type") == "tool_result" for c in content):
            return None
        content = "\n".join(c.get("text", "") for c in content
                            if isinstance(c, dict) and c.get("type") == "text")
    if not isinstance(content, str):
        return None
    for tag in STATE_TAGS:
        if tag in content:
            content = content[:content.index(tag)]
    content = content.replace("\ufffc", "").strip()  # an attachment's placeholder
    if not content or content.startswith(("<local-command", "<command-", "Caveat:", "Base directory for this skill")):
        return None
    return content


def _detail(tool_input):
    if not isinstance(tool_input, dict):
        return ""
    for key in DETAIL_KEYS:
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            value = value.replace("\n", " ")
            return value if len(value) <= 90 else value[:87] + "…"
    return ""


def read(path):
    """A session as turns: [{"prompt", "time", "items": [("text", str) | ("step", name, detail)]}],
    plus how it ended: "limit", "error" (with its text), "mid-step" or "done"."""
    turns, ending, error = [], "done", ""
    pending_tool = False
    for entry in _entries(path):
        kind = entry.get("type")
        if entry.get("isSidechain"):
            continue  # a subagent's own steps
        prompt = prompt_text(entry)
        if prompt is not None:
            turns.append({"prompt": prompt, "time": entry.get("timestamp", ""), "items": []})
            ending, error, pending_tool = "done", "", False
            continue
        if kind != "assistant" or not turns:
            if kind == "user" and pending_tool:
                pending_tool = False  # the step's result came back
            continue
        message = entry.get("message") or {}
        if entry.get("isApiErrorMessage") or message.get("model") == "<synthetic>":
            text = " ".join(c.get("text", "") for c in message.get("content") or []
                            if isinstance(c, dict)).strip()
            ending = "limit" if entry.get("error") == "rate_limit" or "limit" in text.lower() else "error"
            error = text
            continue
        for block in message.get("content") or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and block.get("text", "").strip():
                turns[-1]["items"].append(("text", block["text"].strip()))
            elif block.get("type") == "tool_use":
                name = block.get("name", "")
                if name.startswith("mcp__kicad__"):
                    name = name[len("mcp__kicad__"):]
                turns[-1]["items"].append(("step", name, _detail(block.get("input"))))
                pending_tool = True
        ending = "mid-step" if message.get("stop_reason") == "tool_use" else "done"
    if ending == "done" and pending_tool:
        ending = "mid-step"
    return turns, ending, error


def summary(path):
    """One row of the history list, or None for a session with no prompt of the user's."""
    turns, ending, error = read(path)
    if not turns:
        return None
    steps = sum(1 for t in turns for i in t["items"] if i[0] == "step")
    return {
        "id": os.path.splitext(os.path.basename(path))[0],
        "first": turns[0]["prompt"][:160],
        "last": turns[-1]["prompt"][:160],
        "started": turns[0]["time"],
        "updated": time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(path))),
        "prompts": len(turns),
        "steps": steps,
        "ending": ending,
        "error": error[:200],
    }


def list_sessions(cwd, root=None, limit=50):
    folder = session_folder(cwd, root)
    rows = []
    for path in _jsonl(folder) if folder else []:
        row = summary(path)
        if row:
            rows.append(row)
        if len(rows) >= limit:
            break
    return rows


ENDINGS = {
    "limit": "It stopped at a usage limit, in the middle of the work.",
    "error": "It stopped with an error.",
    "mid-step": "It stopped in the middle of a step (closed, stopped, or cut off).",
    "done": "Claude had finished replying to the last message.",
}


def markdown(path, project="", cwd=""):
    """The session as Markdown, ending with where it stopped (paths relative to cwd)."""
    turns, ending, error = read(path)
    if cwd:
        base = os.path.abspath(cwd).rstrip(os.sep) + os.sep
        for turn in turns:
            turn["items"] = [(i[0], i[1], i[2].replace(base, "")) if i[0] == "step" else i
                             for i in turn["items"]]
    sid = os.path.splitext(os.path.basename(path))[0]
    lines = [f"# Conversation{' on ' + project if project else ''}", "",
             f"Claude Code session `{sid}`, {len(turns)} messages from the user. "
             "Written by PowerLab Assistant from Claude Code's own record (no tokens used).", ""]
    for n, turn in enumerate(turns, 1):
        lines += [f"## {n}. User ({turn['time'][:16].replace('T', ' ')} UTC)", "", turn["prompt"], ""]
        steps = []
        for item in turn["items"]:
            if item[0] == "step":
                steps.append(f"`{item[1]}`" + (f" {item[2]}" if item[2] else ""))
                continue
            if steps:
                lines += ["Steps: " + "; ".join(steps), ""]
                steps = []
            lines += ["**Claude:** " + item[1], ""]
        if steps:
            lines += ["Steps: " + "; ".join(steps), ""]
    lines += ["## Where it stopped", "", ENDINGS[ending]]
    if error:
        lines += ["", f"Message: {error}"]
    if turns:
        last = turns[-1]
        lines += ["", "Last request from the user:", "", "> " + last["prompt"].replace("\n", "\n> ")]
        texts = [i[1] for i in last["items"] if i[0] == "text"]
        if texts:
            lines += ["", "Claude's last words:", "", "> " + texts[-1].replace("\n", "\n> ")]
        steps = [i for i in last["items"] if i[0] == "step"][-LAST_STEPS:]
        if steps:
            lines += ["", f"Its last {len(steps)} steps:", ""]
            lines += [f"- `{s[1]}`" + (f" {s[2]}" if s[2] else "") for s in steps]
    lines += ["", "To continue: check the project's files for what was really done (the last "
              "steps may not have finished), then carry on with the last request.", ""]
    return "\n".join(lines)


def write_transcript(cwd, session_id, root=None):
    """Write the session's transcript into <project>/chat-history/ and return its path."""
    if not re.fullmatch(r"[0-9a-fA-F-]{8,64}", session_id or ""):
        raise ValueError("not a session id")
    folder = session_folder(cwd, root)
    path = os.path.join(folder, session_id + ".jsonl") if folder else ""
    if not os.path.isfile(path):
        raise FileNotFoundError("Claude Code no longer has this conversation")
    stamp = time.strftime("%Y-%m-%d_%H%M", time.localtime(os.path.getmtime(path)))
    out_dir = os.path.join(cwd, FOLDER_NAME)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{stamp}_{session_id[:8]}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(markdown(path, os.path.basename(os.path.abspath(cwd)), cwd))
    return out
