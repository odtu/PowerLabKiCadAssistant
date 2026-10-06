"""The PowerLab Assistant panel: a WebView chat UI that runs Claude Code headlessly.

Each message runs `claude -p` in the project folder with the KiCad context attached.
The same panel is used inside the PCB editor (PcbSource) and as a standalone window
for the schematic editor (SchematicSource).
"""

import base64
import json
import os
import subprocess
import sys
import threading
import time

import wx
import wx.html2

from . import config, library, report
from .common import find_gh, open_console, open_terminal, clean_env
from .sources import PcbSource

# Tools Claude may use without asking. Headless runs can't show permission
# prompts, so anything else (including shell rm/del/mkdir) is denied.
ALLOWED_TOOLS = [
    "mcp__kicad", "Read", "Glob", "Grep", "Edit", "Write", "WebSearch", "WebFetch",
    "PowerShell(kicad-cli:*)", "Bash(kicad-cli:*)",
]

IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
               ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml"}
MAX_IMAGE_BYTES = 8 * 1024 * 1024
LIBRARY_CHECK_EVERY = 10 * 60  # seconds between GitHub checks for library updates

PANEL_NOTE = (
    "You are running in a narrow command panel docked beside KiCad, one headless "
    "command at a time. Keep replies to a few short lines. You cannot ask for permission "
    "mid-run; if you need a decision from the user, stop and ask in your reply.\n"
    "Images you open with the Read tool are shown to the user in the panel automatically, "
    "so never try to open them in another program.\n"
    "kicad-cli is already on PATH. Run it by name as a single plain command, e.g. "
    "`kicad-cli sch export pdf -o out.pdf design.kicad_sch` - never locate it first, and never "
    "use variables, `&`, `;`, pipes or its full path: the panel only allows a plain "
    "`kicad-cli ...` command and blocks everything else. It creates missing output folders "
    "itself. Write outputs inside the project folder.\n"
    "Each message ends with a <kicad_state> block giving the live KiCad selection at the "
    "moment it was sent. Words like 'this', 'that', 'it' or 'selected' refer to that selection. "
    "Change designs only through the kicad MCP tools (board tools edit KiCad live when its "
    "API server is on); never hand-edit .kicad_pcb or .kicad_sch files. Never delete files or "
    "folders unless the user names them explicitly; if a request is ambiguous, ask.\n"
    "You can make mistakes: for anything that ends up in hardware (footprints, pinouts, "
    "ratings, design rules), say what the user should double-check against the datasheet."
)

# Model picker: (id passed to --model, menu label, short button label, hint).
# "" means Claude Code's own default.
MODELS = [
    ("", "Default", "Default model", "Claude Code's default model"),
    ("claude-opus-5-5", "Opus 5.5", "Opus 5.5", "Most capable for complex work"),
    ("claude-sonnet-5-5", "Sonnet 5.5", "Sonnet 5.5", "Fast and capable for everyday tasks"),
    ("claude-haiku-4-5-20251001", "Haiku 4.5", "Haiku 4.5", "Fastest for quick answers"),
    ("claude-fable-5-1", "Fable 5.1", "Fable 5.1", "May need usage credits on your account"),
]
HTML_PATH = os.path.join(os.path.dirname(__file__), "panel.html")
DETAIL_KEYS = ("name", "symbol_name", "footprint_name", "library", "reference", "net",
               "file_path", "path", "pattern", "query", "url", "command")

_live_panel = None  # the panel that receives reports of this plugin's own exceptions


def kicad_frame():
    frame = wx.FindWindowByName("PcbFrame")
    if frame:
        return frame
    return next((w for w in wx.GetTopLevelWindows() if w.IsShown()), None)


def describe_tool(name, args):
    if name.startswith("mcp__kicad__"):
        name = name[len("mcp__kicad__"):].replace("_", " ").capitalize()
    detail = ""
    if isinstance(args, dict):
        for key in DETAIL_KEYS:
            if args.get(key):
                detail = str(args[key])
                if key in ("file_path", "path"):
                    detail = os.path.basename(detail.rstrip("\\/")) or detail
                break
    return name, detail[:120]


def tool_kind(name):
    """Tool name for the anonymous event log (no arguments)."""
    return name.replace("mcp__kicad__", "kicad:")


def install_excepthook():
    """Offer a report for exceptions raised by this plugin; leave others to KiCad."""
    previous = sys.excepthook
    if getattr(previous, "_powerlab", False):
        return

    def hook(exc_type, exc, tb):
        frames = []
        t = tb
        while t:
            frames.append(t.tb_frame.f_code.co_filename)
            t = t.tb_next
        if any(f.startswith(report.PLUGIN_DIR) for f in frames) and _live_panel:
            detail = report.plugin_traceback(exc_type, exc, tb)
            wx.CallAfter(_live_panel.safe, _live_panel.problem, "error",
                         "Something went wrong in the panel.", "panel exception", detail)
        previous(exc_type, exc, tb)

    hook._powerlab = True
    sys.excepthook = hook


class ClaudePanel(wx.Frame):
    _instance = None

    @classmethod
    def toggle(cls, claude):
        panel = cls._instance
        if panel and panel.IsShown():
            panel.Hide()
            return
        if not panel:
            panel = cls._instance = ClaudePanel(kicad_frame(), claude, PcbSource())
        panel.present()

    def present(self):
        self.Show()
        self.Raise()
        self.web.SetFocus()

    def __init__(self, parent, claude, source):
        global _live_panel
        style = wx.DEFAULT_FRAME_STYLE | wx.FRAME_TOOL_WINDOW
        # Inside the PCB editor the panel floats over its window; standalone it floats over everything.
        style |= wx.FRAME_FLOAT_ON_PARENT if parent else wx.STAY_ON_TOP
        super().__init__(parent, title="PowerLab Assistant", style=style)
        self.claude = claude
        self.source = source
        self.proc = None
        self.session_id = None
        self.watched = {}
        self.started = 0.0
        self.last_text = ""
        self.got_result = False
        self.held_text = ""
        self.capturing = False
        self.sending = False
        self.settings = config.settings()
        self.ready = False
        self.pending = []
        self.context_items = None
        self.image_reads = {}
        self.problems = {}  # id -> error details offered for reporting
        self.share_files = []
        self.library_checked = 0.0
        _live_panel = self
        install_excepthook()

        self.web = wx.html2.WebView.New(self, backend=wx.html2.WebViewBackendEdge)
        self.web.AddScriptMessageHandler("wx")
        self.web.EnableAccessToDevTools(False)
        self.web.Bind(wx.html2.EVT_WEBVIEW_SCRIPT_MESSAGE_RECEIVED, self.on_message)
        self.web.Bind(wx.html2.EVT_WEBVIEW_NAVIGATING, self.on_navigating)
        self.web.Bind(wx.html2.EVT_WEBVIEW_NEWWINDOW, self.on_new_window)
        self.load_page()

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, lambda evt: self.push_context())
        self.Bind(wx.EVT_SHOW, self.on_show)
        self.Bind(wx.EVT_ACTIVATE, self.capture_on_activate)
        self.Bind(wx.EVT_CLOSE, lambda evt: self.Hide())
        self.parent_id = parent.GetId() if parent else None
        if parent:
            parent.Bind(wx.EVT_CLOSE, self.on_parent_close)
            parent.Bind(wx.EVT_WINDOW_DESTROY, self.on_parent_destroy)

        width = 380
        if parent:
            rect = parent.GetScreenRect()
            self.SetSize(width, max(rect.height - 160, 460))
            self.SetPosition((rect.right - width - 30, rect.top + 110))
        else:
            # The display the user just clicked the toolbar button on.
            index = wx.Display.GetFromPoint(wx.GetMousePosition())
            area = wx.Display(max(index, 0)).GetClientArea()
            self.SetSize(width, max(area.height - 200, 460))
            self.SetPosition((area.right - width - 30, area.top + 120))

    # ---- page bridge -------------------------------------------------------

    def load_page(self):
        self.ready = False
        self.context_items = None
        with open(HTML_PATH, encoding="utf-8") as f:
            self.web.SetPage(f.read(), "")

    def emit(self, kind, **data):
        data["kind"] = kind
        if not self.ready:
            self.pending.append(data)
            return
        self.web.RunScript(f"app.event({json.dumps(data)})")

    def in_background(self, work, done):
        """Run work() off the GUI thread (network, git, subprocesses), then done(result)."""
        def runner():
            try:
                result = work()
            except Exception as exc:  # report, don't lose it in a thread
                result = exc
            wx.CallAfter(self.safe, done, result)

        threading.Thread(target=runner, daemon=True).start()

    def on_message(self, evt):
        try:
            msg = json.loads(evt.GetString())
        except ValueError:
            return
        kind = msg.get("type")
        handler = getattr(self, "msg_" + str(kind), None)
        if handler:
            handler(msg)

    def msg_ready(self, msg):
        self.ready = True
        for data in self.pending:
            self.web.RunScript(f"app.event({json.dumps(data)})")
        self.pending = []
        self.emit("suggestions", items=[{"label": l, "text": t} for l, t in self.source.suggestions])
        self.emit("models", current=self.model,
                  items=[{"id": i, "label": l, "short": s, "hint": h} for i, l, s, h in MODELS])
        if self.settings.get("notice_version", 0) < config.NOTICE_VERSION:
            self.emit("notice")
        self.push_context()
        self.check_library(force=True)

    def msg_notice_ok(self, msg):
        self.settings["notice_version"] = config.NOTICE_VERSION
        config.save_settings(self.settings)

    def msg_send(self, msg):
        self.run(msg.get("text", "").strip())

    def msg_stop(self, msg):
        if self.proc:
            self.proc.terminate()

    def msg_new(self, msg):
        if self.proc:
            self.proc.terminate()
        self.session_id = None
        self.load_page()

    def msg_open(self, msg):
        if os.path.isfile(msg.get("path", "")):
            os.startfile(msg["path"])

    def msg_reload(self, msg):
        if self.source.can_reload:
            self.reload_editor()

    def msg_model(self, msg):
        if msg.get("id") in [m[0] for m in MODELS]:
            self.settings["model"] = msg["id"]
            config.save_settings(self.settings)
            self.emit("model", current=self.model)

    def msg_save_send(self, msg):
        if self.held_text:
            self.save_then_send()

    def msg_terminal(self, msg):
        snap = self.snapshot()
        cwd = snap.cwd if snap else os.path.expanduser("~")
        open_terminal(self.claude, cwd, snap.context if snap else "", self.session_id)

    def on_navigating(self, evt):
        url = evt.GetURL()
        if url.startswith(("http://", "https://")):
            evt.Veto()
            wx.LaunchDefaultBrowser(url)

    def on_new_window(self, evt):
        wx.LaunchDefaultBrowser(evt.GetURL())

    def on_show(self, evt):
        if evt.IsShown():
            self.push_context()
            self.timer.Start(1000)
            self.check_library()
        else:
            self.timer.Stop()
        evt.Skip()

    def on_parent_close(self, evt):
        # Stop polling the board before KiCad frees it; resume if the close is cancelled.
        self.timer.Stop()
        evt.Skip()
        wx.CallAfter(self.safe, self.resume_polling)

    def resume_polling(self):
        if self.IsShown() and self.GetParent():
            self.timer.Start(1000)

    def on_parent_destroy(self, evt):
        global _live_panel
        evt.Skip()
        if evt.GetId() != self.parent_id:
            return  # a child of the editor, not the editor itself
        # wx destroys this panel along with the editor; just stop everything that
        # could call back into it, and let the next toolbar click build a new one.
        self.timer.Stop()
        if self.proc:
            self.proc.terminate()
        ClaudePanel._instance = None
        if _live_panel is self:
            _live_panel = None

    def snapshot(self):
        try:
            return self.source.snapshot()
        except Exception:  # e.g. KiCad's API server is off or KiCad closed
            return None

    def push_context(self):
        snap = self.snapshot()
        items = snap.chips if snap else ["Not connected to KiCad (is its API server on?)"]
        if items != self.context_items and self.ready:
            self.context_items = items
            self.emit("context", items=items)

    def safe(self, fn, *args, **kwargs):
        if self:  # panel may have been destroyed with KiCad
            fn(*args, **kwargs)

    # ---- problems and reports ---------------------------------------------

    def problem(self, level, text, kind, detail=""):
        """Show a problem with a Report button. Nothing is sent unless the user submits."""
        pid = str(len(self.problems) + 1)
        self.problems[pid] = {"kind": kind, "detail": detail}
        report.note_event("problem", kind)
        self.emit("note", level=level, text=text,
                  action={"label": "Report", "type": "report", "id": pid})

    def msg_report(self, msg):
        error = self.problems.get(msg.get("id", ""))
        editor, model = self.source.editor, self.model
        kicad = self.source.kicad_version() if hasattr(self.source, "kicad_version") else ""
        title = f"[{editor}] " + (error["kind"] if error else "Problem report")

        def work():
            return report.diagnostics(editor, model, kicad, error), report.gh_ready()

        def done(result):
            if isinstance(result, Exception):
                result = (report.diagnostics(editor, model, kicad, error), False)
            diag, gh = result
            self.emit("report_sheet", title=title, diagnostics=diag, gh=gh)

        self.in_background(work, done)

    def msg_report_submit(self, msg):
        title = msg.get("title", "").strip() or "Problem report"
        what = msg.get("what", "")
        diag = msg.get("diagnostics", "")
        if msg.get("via") == "gh":
            def done(result):
                ok, info = result if not isinstance(result, Exception) else (False, str(result))
                if ok:
                    self.emit("note", level="info", text=f"Report filed: {info} Thank you!")
                else:
                    self.emit("note", level="warn", text="Couldn't file it with GitHub; opening the form instead.")
                    wx.LaunchDefaultBrowser(report.prefilled_url(title, what, diag))

            self.in_background(lambda: report.submit_with_gh(title, what, diag), done)
        else:
            wx.LaunchDefaultBrowser(report.prefilled_url(title, what, diag))
            self.emit("note", level="info", text="The report form is open in your browser. "
                                                 "Check it and press Submit there.")

    def msg_gh_connect(self, msg):
        """Connect GitHub (the user's own account) with GitHub's CLI, in a visible console."""
        gh = find_gh()
        if gh:
            open_console([gh, "auth", "login", "--hostname", "github.com", "--web"])
        else:
            script = ("Write-Host 'Installing GitHub CLI (winget)...'; "
                      "winget install --id GitHub.cli -e --source winget; "
                      "& \"$env:ProgramFiles\\GitHub CLI\\gh.exe\" auth login --hostname github.com --web; "
                      "Write-Host 'Done. You can close this window.'")
            open_console(["powershell", "-NoProfile", "-NoExit", "-Command", script])
        self.emit("note", level="info", text="Finish signing in to GitHub in the console window, "
                                             "then press Check again.")

    def msg_gh_check(self, msg):
        self.in_background(report.gh_ready, lambda ok: self.emit("gh_status", ok=ok is True))

    # ---- library sync and sharing -------------------------------------------

    def check_library(self, force=False):
        if not config.library_path():
            self.emit("library", configured=False)
            return
        if not force and time.time() - self.library_checked < LIBRARY_CHECK_EVERY:
            return
        self.library_checked = time.time()

        def done(result):
            if isinstance(result, Exception):
                return
            data = result.as_dict()
            data["vars_ok"] = library.path_variables_ok()
            self.emit("library", configured=True, **data)

        self.in_background(library.status, done)

    def msg_lib_update(self, msg):
        report.note_event("library update")

        def done(result):
            ok, info = result if not isinstance(result, Exception) else (False, str(result))
            if ok and info:
                self.emit("note", level="info", text="Library updated. New libraries: "
                          + ", ".join(info[:8]) + (" …" if len(info) > 8 else "")
                          + ". Restart KiCad to see them.")
            elif ok:
                self.emit("note", level="info", text="Library updated. If a changed part doesn't "
                                                     "look updated yet, restart KiCad.")
            else:
                self.problem("warn", info, "library update failed")
            self.check_library(force=True)

        self.in_background(library.update, done)

    def msg_lib_share(self, msg):
        path = config.library_path()

        def work():
            files = library.changed_files(path)
            return {"files": files, "check": library.run_checker(path, files) if files else None,
                    "login": library.gh_login()}

        def done(result):
            if isinstance(result, Exception):
                self.problem("error", "Couldn't prepare the library changes.", "library share prepare",
                             report.plugin_traceback(type(result), result, result.__traceback__))
                return
            self.share_files = result["files"]
            self.emit("share_sheet", **result)

        self.in_background(work, done)

    def msg_share_submit(self, msg):
        chosen = set(msg.get("paths", []))
        files = [f for f in self.share_files if f["path"] in chosen]
        login = msg.get("login", "")
        if not files or not login:
            return
        title = msg.get("title", "").strip() or "Add library parts"
        report.note_event("library share", f"{len(files)} files")

        def done(result):
            ok, info = result if not isinstance(result, Exception) else (False, str(result))
            if ok:
                self.emit("note", level="info", text=f"Pull request opened: {info} — the lab will "
                                                     "review it. The automatic checks run there too.")
            else:
                self.problem("warn", info, "library share failed")
            self.check_library(force=True)

        self.in_background(lambda: library.contribute(title, msg.get("description", ""), files, login), done)

    # ---- running claude ----------------------------------------------------

    @property
    def model(self):
        return self.settings.get("model", "")

    def has_unsaved(self):
        check = getattr(self.source, "unsaved", None)
        return bool(check and check())

    def save_then_send(self):
        text, self.held_text = self.held_text, ""
        if not self.source.save():
            self.problem("error", "Couldn't save from here. Press Ctrl+S in KiCad, then send again.",
                         "save via menu failed")
            return
        deadline = time.time() + 8

        def wait():
            if not self.has_unsaved():
                self.run(text)
            elif time.time() < deadline:
                wx.CallLater(200, self.safe, wait)
            else:
                self.problem("error", "KiCad didn't finish saving. Save it there, then send again.",
                             "save timed out")

        wx.CallLater(200, self.safe, wait)

    def reload_editor(self):
        def done(ok):
            report.note_event("reload", "ok" if ok else "failed")
            if ok:
                self.emit("note", level="info", text="Reloaded the schematic in KiCad.")
            else:
                self.problem("warn", "Couldn't reload automatically. Use File → Revert in KiCad.",
                             "automatic reload failed")

        self.source.reload(lambda ok: self.safe(done, ok))

    def run(self, text):
        if not text or self.proc or self.sending:
            return
        if self.has_unsaved():
            # Claude edits the files on disk; unsaved editor changes would be stale for
            # Claude and lost when the panel reloads the editor afterwards.
            self.held_text = text
            self.emit("note", level="warn",
                      text="The schematic has unsaved changes. Save first so Claude works on the "
                           "latest version and the reload afterwards doesn't lose anything.",
                      action={"label": "Save & send", "type": "save_send"})
            return
        capture = getattr(self.source, "capture_selection", None)
        if capture:  # schematic: read the live selection right before sending
            self.sending = True  # blocks a second send while the selection is read
            capture(self.GetHandle(), lambda: self.safe(self.launch, text))
        else:
            self.launch(text)

    def capture_on_activate(self, evt):
        evt.Skip()
        capture = getattr(self.source, "capture_selection", None)
        if evt.GetActive() and capture and not self.proc and not self.sending and not self.capturing:
            self.capturing = True

            def done():
                self.capturing = False
                self.push_context()

            capture(self.GetHandle(), lambda: self.safe(done))

    def launch(self, text):
        self.sending = False
        snap = self.snapshot()
        if snap is None:
            self.problem("error", "Can't reach KiCad. Turn on Preferences → Plugins → Enable KiCad API, "
                                  "then reopen the panel.", "kicad not reachable")
            return
        args = [
            self.claude, "-p",
            "--output-format", "stream-json", "--verbose",
            "--append-system-prompt", snap.context + "\n" + PANEL_NOTE,
        ]
        for d in config.work_dirs():
            args += ["--add-dir", d]
        if self.session_id:
            args += ["--resume", self.session_id]
        if self.model:
            args += ["--model", self.model]
        args += ["--allowedTools", ",".join(ALLOWED_TOOLS)]

        self.emit("user", text=text)
        report.note_event("send", self.source.editor)
        self.watched = {p: os.path.getmtime(p) for p in snap.watch if os.path.isfile(p)}
        self.started = time.time()
        self.last_text = ""
        self.got_result = False
        try:
            self.proc = subprocess.Popen(
                args, cwd=snap.cwd, env=clean_env(),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                encoding="utf-8", errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except OSError as exc:
            self.problem("error", f"Could not start Claude Code: {exc}", "claude failed to start",
                         type(exc).__name__)
            return
        self.proc.stdin.write(f"{text}\n\n<kicad_state>\n{snap.state}\n</kicad_state>")
        self.proc.stdin.close()
        self.emit("busy", value=True)
        threading.Thread(target=self.read_stream, args=(self.proc,), daemon=True).start()

    def read_stream(self, proc):
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except ValueError:
                wx.CallAfter(self.safe, self.emit, "note", level="info", text=line)
                continue
            wx.CallAfter(self.safe, self.handle, msg)
        proc.wait()
        wx.CallAfter(self.safe, self.finished, proc.returncode)

    def handle(self, msg):
        kind = msg.get("type")
        if kind == "system" and msg.get("subtype") == "init":
            self.session_id = msg.get("session_id")
        elif kind == "assistant":
            for block in msg.get("message", {}).get("content", []):
                if block.get("type") == "text" and block.get("text", "").strip():
                    self.last_text = block["text"].strip()
                    self.emit("text", text=self.last_text)
                elif block.get("type") == "tool_use":
                    args = block.get("input") or {}
                    name, detail = describe_tool(block.get("name", ""), args)
                    self.emit("tool", id=block.get("id"), name=name, detail=detail)
                    self.image_reads[block.get("id")] = (
                        tool_kind(block.get("name", "")),
                        args.get("file_path", "") if block.get("name") == "Read" else "")
        elif kind == "user":
            content = msg.get("message", {}).get("content", [])
            for block in content if isinstance(content, list) else []:
                if block.get("type") != "tool_result":
                    continue
                detail = ""
                failed = bool(block.get("is_error"))
                if failed:
                    detail = block.get("content")
                    if isinstance(detail, list):
                        detail = " ".join(b.get("text", "") for b in detail if isinstance(b, dict))
                    detail = str(detail)[:200]
                self.emit("tool_done", id=block.get("tool_use_id"), error=failed, text=detail)
                name, image = self.image_reads.pop(block.get("tool_use_id"), ("tool", ""))
                report.note_event("tool", f"{name} {'error' if failed else 'ok'}")
                if image and not failed and os.path.splitext(image)[1].lower() in IMAGE_TYPES:
                    self.show_image(image)
        elif kind == "result":
            self.got_result = True
            result = str(msg.get("result") or msg.get("subtype"))
            report.note_event("result", f"{msg.get('subtype', '')} error={bool(msg.get('is_error'))}")
            if "Not logged in" in result:
                self.emit("note", level="warn", text="Claude Code isn't signed in yet.",
                          action={"label": "Sign in", "type": "terminal"})
            elif msg.get("is_error") and result.strip() != self.last_text:
                # Claude's own error text can mention the project, so it isn't put in reports.
                self.emit("note", level="error", text=result,
                          action={"label": "Report", "type": "report", "id": self._remember(
                              f"claude result {msg.get('subtype', 'error')}")})
            turns = msg.get("num_turns") or 0
            secs = time.time() - self.started
            labels = {i: l for i, l, _, _ in MODELS if i}
            used = [labels.get(m, m) for m in (msg.get("modelUsage") or {})]
            self.emit("meta", text=f"{secs:.0f}s" + (f" · {turns} steps" if turns > 1 else "")
                      + (f" · {', '.join(used)}" if used else ""))

    def _remember(self, kind, detail=""):
        pid = str(len(self.problems) + 1)
        self.problems[pid] = {"kind": kind, "detail": detail}
        return pid

    def show_image(self, path):
        try:
            if os.path.getsize(path) > MAX_IMAGE_BYTES:
                return
            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode("ascii")
        except OSError:
            return
        mime = IMAGE_TYPES[os.path.splitext(path)[1].lower()]
        self.emit("image", src=f"data:{mime};base64,{data}", name=os.path.basename(path), path=path)

    def finished(self, returncode):
        self.proc = None
        self.emit("busy", value=False)
        if not self.got_result and returncode not in (0, None, 1, 15, -15):
            self.problem("error", f"Claude Code stopped unexpectedly (exit code {returncode}).",
                         "claude exited without a result", f"exit code {returncode}")
        changed = [p for p, t in self.watched.items() if os.path.isfile(p) and os.path.getmtime(p) != t]
        if not changed:
            return
        if self.source.can_reload and not self.has_unsaved():
            self.reload_editor()  # nothing in the editor to lose: show Claude's change live
            return
        action = None
        if self.source.can_reload:
            action = {"label": "Reload (drops unsaved edits)", "type": "reload"}
        self.emit("note", level="warn", text=self.source.changed_note, action=action)
