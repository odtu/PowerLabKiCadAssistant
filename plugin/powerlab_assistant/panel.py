"""The PowerLab Assistant panel: a WebView chat UI that runs Claude Code headlessly.

Each message runs `claude -p` in the project folder with the KiCad context attached.
One standalone window serves both the PCB and the schematic editor (KiCadSource).
"""

import base64
import json
import os
import re
import subprocess
import sys
import threading
import time

import wx
import wx.html2

from . import attachments, config, history, library, report, updates, usage
from .common import find_gh, open_console, open_terminal, clean_env

# Tools Claude may use without asking. Headless runs can't show permission
# prompts, so anything else (including shell rm/del/mkdir) is denied.
ALLOWED_TOOLS = [
    "mcp__kicad", "Skill", "Read", "Glob", "Grep", "Edit", "Write", "WebSearch", "WebFetch",
    "PowerShell(kicad-cli:*)", "Bash(kicad-cli:*)",
    # Zip outputs for PCBWay (issue #24) with Windows' tar, create only. Compress-Archive
    # doesn't work: Claude Code blocks it as a file write unless all edits are auto-accepted,
    # which would also allow Remove-Item.
    "PowerShell(tar -a -cf:*)",
]

IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
               ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml"}
MAX_IMAGE_BYTES = 8 * 1024 * 1024
VIEWS_DIR = os.path.join(os.path.dirname(attachments.FOLDER), "views")  # board renders for review
LIBRARY_CHECK_EVERY = 10 * 60  # seconds between GitHub checks for library updates

PANEL_NOTE = (
    "You are running in a narrow command panel docked beside KiCad, one headless "
    "command at a time. Keep replies to a few short lines. You cannot ask for permission "
    "mid-run; if you need a decision from the user, stop and ask in your reply.\n"
    "The AskUserQuestion tool doesn't work here. Instead, when a question has a few clear "
    "answers, end your reply with a <choices> block: each question on a line of its own, "
    "followed by its 2-4 short options as '- ' lines, the one you recommend first, marked "
    "' (Recommended)'. The panel shows the options as buttons and sends the user's pick as "
    "their next message (they can still type their own answer), so don't also list the "
    "questions in the text above it. Example:\n"
    "<choices>\nKeep 25.4 mm row spacing?\n- Yes, 25.4 mm (Recommended)\n- No, use 28 mm\n"
    "Mounting holes?\n- None\n- Four M3 holes\n</choices>\n"
    "This one panel serves both KiCad's PCB editor and its schematic editor: the toolbar "
    "button in either shows or hides it, and closing KiCad closes it; the chat is kept and "
    "continues when the panel is opened again on this project. Work on both the schematic and "
    "the board from here with the kicad MCP tools. Each message's <kicad_state> says which "
    "editor the user is working in and what is selected in each. The panel saves the schematic "
    "before each message and reloads it in the schematic editor after you change a sheet, so "
    "don't tell the user to save or revert the schematic. "
    "Never ask the user to close the PCB or schematic editor or KiCad. Board tools "
    "edit the open board live; after you change a file on disk, ask the user to use "
    "File > Revert instead.\n"
    "Some board tools (e.g. get_design_rules) only work on the saved board file. If one "
    "says \"No board is loaded\" while KiCad has the board open, call open_board with the "
    "'Board file' path above, then retry the tool once.\n"
    "Images you open with the Read tool are shown to the user in the panel automatically, "
    "so never try to open them in another program.\n"
    "kicad-cli is already on PATH. Run it by name as a single plain command, e.g. "
    "`kicad-cli sch export pdf -o out.pdf design.kicad_sch` - never locate it first, and never "
    "use variables, `&`, `;`, pipes or its full path: the panel only allows a plain "
    "`kicad-cli ...` command and blocks everything else. It creates missing output folders "
    "itself. Write outputs inside the project folder.\n"
    "To zip outputs (e.g. Gerbers and drill files for PCBWay), run one plain command with the "
    "PowerShell tool: `tar -a -cf fab\\gerbers.zip -C fab\\gerbers *` (the zip first, then -C "
    "and the folder whose files go in). It is the only other shell command the panel allows; "
    "Compress-Archive is blocked.\n"
    "Read, list and search files only with the Read, Grep and Glob tools, never with shell "
    "commands such as cd, grep, cat, ls, dir or Select-String: the panel blocks them.\n"
    "Each message ends with a <kicad_state> block giving the live KiCad selection at the "
    "moment it was sent. Words like 'this', 'that', 'it' or 'selected' refer to that selection. "
    "It is for you only: never repeat it in your reply. "
    "Change designs only through the kicad MCP tools (board tools edit KiCad live when its "
    "API server is on); never hand-edit .kicad_pcb or .kicad_sch files. Never delete files or "
    "folders unless the user names them explicitly; if a request is ambiguous, ask.\n"
    "For any schematic or PCB design, placement, routing, design-rule or review work, load "
    "the powerlab-pcb-design-rules skill first and follow it.\n"
    "For any placement or routing work, also load the powerlab-visual-review skill: render the "
    "board and look at it after every step, fix what you see, and show the user the views. "
    "Save renders in the views folder named below (kicad-cli may write there too).\n"
    "You can make mistakes: for anything that ends up in hardware (footprints, pinouts, "
    "ratings, design rules), say what the user should double-check against the datasheet."
)

# Model picker: (id passed to --model, menu label, short button label, hint).
# "" means Claude Code's own default.
MODELS = [
    ("claude-opus-5-5", "Opus 5.5", "Opus 5.5", "Most capable for complex work (panel default)"),
    ("claude-sonnet-5-5", "Sonnet 5.5", "Sonnet 5.5", "Fast and capable for everyday tasks"),
    ("claude-haiku-4-5-20251001", "Haiku 4.5", "Haiku 4.5", "Fastest for quick answers"),
    ("claude-fable-5-1", "Fable 5.1", "Fable 5.1", "May need usage credits on your account"),
    ("", "Claude Code default", "Default model", "Whatever Claude Code itself is set to"),
]
DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_EFFORT = "high"  # --effort; settings.json "effort" overrides (low, medium, high, xhigh, max)
EFFORTS = ("low", "medium", "high", "xhigh", "max")
HTML_PATH = os.path.join(os.path.dirname(__file__), "panel.html")
DETAIL_KEYS = ("name", "symbol_name", "footprint_name", "library", "reference", "net",
               "file_path", "path", "pattern", "query", "url", "command")
BOARD_CHANGED = ("Board changed on disk. Use File → Revert in KiCad to load it "
                 "(unsaved KiCad edits will be lost).")
SCHEMATIC_CHANGED = ("Claude changed the schematic, but you have unsaved edits in KiCad, so it "
                     "wasn't reloaded automatically. Reloading drops those edits.")

_live_panel = None  # the panel that receives reports of this plugin's own exceptions


STATE_BLOCK = re.compile(r"\s*<kicad_state>.*?(</kicad_state>|$)", re.S)


def strip_state(text):
    """Claude sometimes echoes the message's <kicad_state> block; don't show it."""
    return STATE_BLOCK.sub("", text).strip()


CHOICES_BLOCK = re.compile(r"\s*<choices>(.*?)(</choices>|$)", re.S)
MAX_OPTIONS = 6


def split_choices(text):
    """(text, questions): Claude's <choices> block (see PANEL_NOTE) becomes answer buttons.

    Each question is {"question": str, "options": [str, ...]}; questions without options
    are dropped."""
    questions = []
    for block in CHOICES_BLOCK.findall(text):
        for line in block[0].splitlines():
            line = line.strip()
            option = re.match(r"^[-*•]\s+(.+)", line)
            if option and questions and len(questions[-1]["options"]) < MAX_OPTIONS:
                questions[-1]["options"].append(option.group(1).strip())
            elif line and not option:
                questions.append({"question": re.sub(r"^\d+[.)]\s*", "", line), "options": []})
    return CHOICES_BLOCK.sub("", text).strip(), [q for q in questions if q["options"]]


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


def views_note():
    """Tell Claude where board renders go (a private temp folder, cleaned after a week)."""
    os.makedirs(VIEWS_DIR, exist_ok=True)
    return f"\nViews folder for board renders: {VIEWS_DIR}\n"


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
    def present(self):
        self.Show()
        self.Raise()
        self.web.SetFocus()

    def __init__(self, claude, source):
        global _live_panel
        # A window of its own (not KiCad's), so it floats over both editors.
        style = wx.DEFAULT_FRAME_STYLE | wx.FRAME_TOOL_WINDOW | wx.STAY_ON_TOP
        super().__init__(None, title="PowerLab Assistant", style=style)
        self.claude = claude
        self.source = source
        self.proc = None
        self.session_id = None
        self.chat_cwd = None  # project folder of the chat shown (one saved chat per project)
        self.events = []  # the chat's messages, saved so they come back after a restart
        self.retry = None  # (text, files) of the last message sent into a resumed session
        self.stale_session = False
        self.watched = {}
        self.started = 0.0
        self.last_text = ""
        self.got_result = False
        self.held_text = ""
        self.attached = []  # files attached to the next message
        self.limits = []  # plan limits from Claude Code's last rate_limit_event
        self.capturing = False
        self.sending = False
        self.settings = config.settings()
        self.ready = False
        self.pending = []
        self.context_items = None
        self.image_reads = {}
        self.problems = {}  # id -> error details offered for reporting
        self.share_files = []
        self.sharing = False
        self.update_loop = False
        self.unreachable_text = "Not connected to KiCad (is its API server on?)"
        self.unreachable_at = 0.0
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

        # The display the user just clicked the toolbar button on.
        width = 380
        index = wx.Display.GetFromPoint(wx.GetMousePosition())
        area = wx.Display(max(index, 0)).GetClientArea()
        self.SetSize(width, max(area.height - 200, 460))
        self.SetPosition((area.right - width - 30, area.top + 120))

    # ---- page bridge -------------------------------------------------------

    def load_page(self):
        self.ready = False
        self.context_items = None
        # Messages still waiting for the old page belong to the chat being cleared.
        self.pending = [d for d in self.pending if d["kind"] not in history.KINDS + ("note", "busy")]
        with open(HTML_PATH, encoding="utf-8") as f:
            self.web.SetPage(f.read(), "")

    def emit(self, kind, **data):
        data["kind"] = kind
        if not self.ready:
            self.pending.append(data)
            return
        self.web.RunScript(f"app.event({json.dumps(data)})")

    def say(self, kind, **data):
        """Emit a chat message and keep it in the saved chat."""
        self.events.append(history.stored(kind, data))
        self.emit(kind, **data)

    def save_chat(self):
        if self.chat_cwd:
            history.save(self.chat_cwd, self.session_id, self.events)

    def open_chat(self, cwd):
        """Switch to the project's chat, continuing the last one if it was saved."""
        self.save_chat()
        if self.events:
            self.load_page()
        self.chat_cwd = cwd
        self.session_id, self.events = history.load(cwd)
        for event in self.events:
            if event["kind"] == "image":
                self.show_image(event.get("path", ""), record=False)
            else:
                self.emit(**event)
        if self.events:
            self.emit("busy", value=False)  # tools cut off last time stop spinning
            self.emit("note", level="info", text="Continuing your last chat on this project. "
                                                 "Press + for a new one.")

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
        self.emit_attached()
        if self.limits:
            text, tip = usage.summary(self.limits, 0, 0)
            self.emit("usage", text=text, tip=tip)
        self.in_background(lambda: (attachments.clean_old(), attachments.clean_old(VIEWS_DIR)),
                           lambda result: None)
        self.push_context()
        self.check_library(force=True)
        self.check_updates()

    def msg_attach(self, msg):
        with wx.FileDialog(self, "Attach files for Claude", wildcard="All files (*.*)|*.*",
                           style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.attached += [p for p in dlg.GetPaths() if p not in self.attached]
        self.emit_attached()

    def msg_attach_data(self, msg):
        try:
            self.attached.append(attachments.save_data(msg.get("name", ""), msg.get("data", "")))
        except ValueError as exc:
            self.emit("note", level="warn", text=f"Couldn't attach {msg.get('name') or 'that'}: {exc}.")
        self.emit_attached()

    def msg_attach_remove(self, msg):
        index = msg.get("index")
        if isinstance(index, int) and 0 <= index < len(self.attached):
            del self.attached[index]
        self.emit_attached()

    def emit_attached(self):
        self.emit("attachments", items=[os.path.basename(p) for p in self.attached])

    def msg_notice_ok(self, msg):
        self.settings["notice_version"] = config.NOTICE_VERSION
        config.save_settings(self.settings)

    def msg_send(self, msg):
        text = msg.get("text", "").strip()
        if not text and self.attached:
            text = "Have a look at the attached files."
        self.run(text)

    def msg_stop(self, msg):
        if self.proc:
            self.proc.terminate()

    def msg_new(self, msg):
        if self.proc:
            self.proc.terminate()
        self.session_id = None
        self.events = []
        self.save_chat()
        self.load_page()

    def msg_open(self, msg):
        if os.path.isfile(msg.get("path", "")):
            os.startfile(msg["path"])

    def msg_reload(self, msg):
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
            if self.ready:
                self.check_updates()  # cached: asks GitHub only if the last check is over CHECK_EVERY old
        else:
            self.timer.Stop()
        evt.Skip()

    def snapshot(self):
        try:
            return self.source.snapshot()
        except Exception:  # e.g. KiCad's API server is off or KiCad closed
            return None

    def push_context(self):
        snap = self.snapshot()
        if snap:
            items = snap.chips
        else:
            # Say why, refreshed at most every 15 s (it lists running processes).
            status = getattr(self.source, "unreachable_status", None)
            if status and time.time() - self.unreachable_at > 15:
                self.unreachable_text = status()
                self.unreachable_at = time.time()
            items = [self.unreachable_text]
        if snap and snap.cwd != self.chat_cwd and not self.proc and not self.sending:
            self.open_chat(snap.cwd)
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
        processes = getattr(self.source, "process_summary", None)

        def work():
            extra = [f"kicad_processes: {processes()}"] if processes else []
            return report.diagnostics(editor, model, kicad, error, extra), report.gh_ready()

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

    # ---- plugin updates -------------------------------------------------------

    def check_updates(self):
        """Ask GitHub (anonymously, at most every CHECK_EVERY) whether a newer stable
        version exists. Also re-checks that often while the panel stays open."""
        if not self.update_loop:
            self.update_loop = True

            def periodic():
                self.check_updates()
                wx.CallLater(updates.CHECK_EVERY * 1000, self.safe, periodic)

            wx.CallLater(updates.CHECK_EVERY * 1000, self.safe, periodic)

        def done(result):
            if isinstance(result, Exception):
                return  # offline or GitHub unreachable: try again next time
            config.save_settings(self.settings)
            if result["available"]:
                result["self_update"] = updates.can_self_update()
                self.emit("update", **result)

        self.in_background(lambda: updates.check(self.settings), done)

    def msg_plugin_update(self, msg):
        report.note_event("plugin update")
        if updates.start_update():
            self.emit("note", level="info", text="Updating in the console window. Restart KiCad when it says done.")
        else:
            wx.LaunchDefaultBrowser(msg.get("url") or updates.RELEASES_URL)
            self.emit("note", level="info", text="This copy wasn't installed from a git clone, so the release "
                                                 "page is open in your browser: download it and run install.ps1 -Update.")

    def msg_whats_new(self, msg):
        wx.LaunchDefaultBrowser(msg.get("url") or updates.RELEASES_URL)

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
        if self.sharing:
            self.emit("note", level="info", text="A pull request is already being opened; wait for it to finish.")
            return
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
        if not files or not login or self.sharing:
            return  # nothing chosen, or a share is already running (pressing twice made duplicate PRs)
        self.sharing = True
        title = msg.get("title", "").strip() or "Add library parts"
        report.note_event("library share", f"{len(files)} files")
        self.emit("note", level="info", text="Opening the pull request… (forking and uploading can take a minute)")

        def done(result):
            self.sharing = False
            ok, info = result if not isinstance(result, Exception) else (False, str(result))
            if ok:
                self.emit("note", level="info", text=f"Pull request opened: {info}. It merges automatically "
                                                     "once the library checks pass (lab members), then "
                                                     "everyone gets it with Update.")
            else:
                self.problem("warn", info, "library share failed")
            self.check_library(force=True)

        self.in_background(lambda: library.contribute(title, msg.get("description", ""), files, login), done)

    # ---- running claude ----------------------------------------------------

    @property
    def model(self):
        return self.settings.get("model", DEFAULT_MODEL)

    @property
    def effort(self):
        effort = self.settings.get("effort", DEFAULT_EFFORT)
        return effort if effort in EFFORTS else DEFAULT_EFFORT

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

    def launch(self, text, files=None):
        """Start Claude on a message. files is given only when resending (see finished)."""
        self.sending = False
        self.stale_session = False
        snap = self.snapshot()
        if snap is None:
            reason = getattr(self.source, "unreachable_reason", None)
            text = reason() if reason else ("Can't reach KiCad. Turn on Preferences → Plugins → "
                                            "Enable KiCad API, then reopen the panel.")
            self.problem("error", text, "kicad not reachable")
            return
        if snap.cwd != self.chat_cwd:
            self.open_chat(snap.cwd)
        args = [
            self.claude, "-p",
            "--output-format", "stream-json", "--verbose",
            "--append-system-prompt", snap.context + "\n" + PANEL_NOTE + views_note(),
        ]
        resend = files is not None
        if not resend:
            files, self.attached = self.attached, []
        extra = attachments.folders(files) + [VIEWS_DIR]
        for d in config.work_dirs() + [f for f in extra if f not in config.work_dirs()]:
            args += ["--add-dir", d]
        if self.session_id:
            args += ["--resume", self.session_id]
        if self.model:
            args += ["--model", self.model]
        args += ["--effort", self.effort]
        args += ["--allowedTools", ",".join(ALLOWED_TOOLS)]
        args += ["--disallowedTools", "AskUserQuestion"]  # no one to answer it; see <choices>

        if not resend:
            self.say("user", text=text, files=[os.path.basename(p) for p in files])
            self.emit_attached()
            self.save_chat()
        self.retry = (text, files) if self.session_id else None
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
            self.attached = files + self.attached
            self.emit_attached()
            self.problem("error", f"Could not start Claude Code: {exc}", "claude failed to start",
                         type(exc).__name__)
            return
        self.proc.stdin.write(f"{text}{attachments.prompt_suffix(files)}\n\n<kicad_state>\n{snap.state}\n</kicad_state>")
        self.proc.stdin.close()
        self.emit("busy", value=True)
        threading.Thread(target=self.read_stream, args=(self.proc,), daemon=True).start()

    def read_stream(self, proc):
        for line in proc.stdout:
            line = line.strip()
            if not line or line.startswith("No conversation found"):
                continue  # an expired session; handled with the result
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
            self.save_chat()
        elif kind == "rate_limit_event":
            self.limits = usage.limits(msg) or self.limits
            text, tip = usage.summary(self.limits, 0, 0)
            self.emit("usage", text=text, tip=tip)
        elif kind == "assistant":
            for block in msg.get("message", {}).get("content", []):
                text = strip_state(block.get("text", "")) if block.get("type") == "text" else ""
                text, choices = split_choices(text)
                if text or choices:
                    self.last_text = text
                    self.say("text", text=text, **({"choices": choices} if choices else {}))
                elif block.get("type") == "tool_use":
                    args = block.get("input") or {}
                    name, detail = describe_tool(block.get("name", ""), args)
                    self.say("tool", id=block.get("id"), name=name, detail=detail)
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
                self.say("tool_done", id=block.get("tool_use_id"), error=failed, text=detail)
                name, image = self.image_reads.pop(block.get("tool_use_id"), ("tool", ""))
                report.note_event("tool", f"{name} {'error' if failed else 'ok'}")
                if image and not failed and os.path.splitext(image)[1].lower() in IMAGE_TYPES:
                    self.show_image(image)
        elif kind == "result":
            self.got_result = True
            if msg.get("is_error") and any("No conversation found" in str(e) for e in msg.get("errors") or []):
                self.stale_session = True  # Claude Code deleted the saved session; resent in finished
                return
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
            tokens, window = usage.context(msg)
            self.say("meta", text=f"{secs:.0f}s" + (f" · {turns} steps" if turns > 1 else "")
                      + (f" · {', '.join(used)} · {self.effort} effort" if used else ""))
            text, tip = usage.summary(self.limits, tokens, window)
            self.emit("usage", text=text, tip=tip)

    def _remember(self, kind, detail=""):
        pid = str(len(self.problems) + 1)
        self.problems[pid] = {"kind": kind, "detail": detail}
        return pid

    def show_image(self, path, record=True):
        try:
            if os.path.getsize(path) > MAX_IMAGE_BYTES:
                return
            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode("ascii")
        except OSError:
            return
        mime = IMAGE_TYPES[os.path.splitext(path)[1].lower()]
        (self.say if record else self.emit)("image", src=f"data:{mime};base64,{data}",
                                            name=os.path.basename(path), path=path)

    def finished(self, returncode):
        self.proc = None
        if self.stale_session and self.retry:
            text, files = self.retry
            self.session_id = None
            self.emit("note", level="info", text="Claude Code no longer has the earlier conversation "
                                                 "(it deletes old chats), so this starts a new one.")
            self.launch(text, files)
            if self.proc:
                return
        self.emit("busy", value=False)
        self.save_chat()
        if not self.got_result and returncode not in (0, None, 1, 15, -15):
            self.problem("error", f"Claude Code stopped unexpectedly (exit code {returncode}).",
                         "claude exited without a result", f"exit code {returncode}")
        changed = [p for p, t in self.watched.items() if os.path.isfile(p) and os.path.getmtime(p) != t]
        if any(p.endswith(".kicad_pcb") for p in changed):
            self.emit("note", level="warn", text=BOARD_CHANGED)
        if not any(p.endswith(".kicad_sch") for p in changed) or not self.source.schematic_open():
            return
        if not self.has_unsaved():
            self.reload_editor()  # nothing in the editor to lose: show Claude's change live
            return
        self.emit("note", level="warn", text=SCHEMATIC_CHANGED,
                  action={"label": "Reload (drops unsaved edits)", "type": "reload"})
