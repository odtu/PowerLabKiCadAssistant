"""Run with KiCad's Python (it has wx and pcbnew):

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" -m unittest discover -s tests -v
"""

import base64
import os
import subprocess
import sys
import tempfile
import time
import types
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Outside KiCad (e.g. GitHub Actions) there's no pcbnew or wx. The code under test
# only needs them at import time, so stand-ins are enough.
try:
    import pcbnew  # noqa: F401
except ImportError:
    pcbnew = types.ModuleType("pcbnew")
    pcbnew.ActionPlugin = type("ActionPlugin", (), {"register": lambda self: None})
    sys.modules["pcbnew"] = pcbnew
try:
    import wx  # noqa: F401
except ImportError:
    wx = types.ModuleType("wx")
    wx.FindWindowByName = lambda *args: None
    wx.Frame = object
    wx.html2 = types.ModuleType("wx.html2")
    sys.modules["wx"] = wx
    sys.modules["wx.html2"] = wx.html2
os.environ["POWERLAB_ASSISTANT_STANDALONE"] = "1"  # don't register the PCB plugin
sys.path.insert(0, os.path.join(ROOT, "plugin"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from powerlab_assistant import config, library, report, sources, updates  # noqa: E402
import configure_kicad  # noqa: E402


def sh(cwd, *args):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


class ScrubTests(unittest.TestCase):
    def test_removes_paths_user_and_email(self):
        home = os.path.expanduser("~")
        text = (f"failed reading {home}\\Projects\\SecretBoard\\board.kicad_pcb and D:\\Work\\Customer\\x.kicad_sch "
                f"user {os.environ.get('USERNAME', 'someone')} mail jane.doe@example.com")
        out = report.scrub(text)
        self.assertNotIn("SecretBoard", out)
        self.assertNotIn("board.kicad_pcb", out)
        self.assertIn("<home>/…", out)
        self.assertNotIn("Customer", out)
        self.assertNotIn("example.com", out)
        self.assertIn("<path>", out)
        if len(os.environ.get("USERNAME", "")) > 2:
            self.assertNotIn(os.environ["USERNAME"].lower(), out.lower())

    def test_plugin_traceback_keeps_only_plugin_frames(self):
        try:
            sources.parse_selection(None)  # raises inside the plugin
        except Exception as exc:  # noqa: BLE001
            tb = report.plugin_traceback(type(exc), exc, exc.__traceback__)
        self.assertIn("sources.py", tb)
        self.assertNotIn("test_assistant.py", tb)
        self.assertNotIn(ROOT, tb)

    def test_prefilled_url_stays_short(self):
        url = report.prefilled_url("t", "x" * 5000, "diag line\n" * 2000)
        self.assertLess(len(url), 8000)
        self.assertIn("template=bug_report.yml", url)


class SelectionParserTests(unittest.TestCase):
    def test_symbols_labels_and_power_symbols(self):
        clip = '''(kicad_sch
  (symbol
    (lib_id "Device:R")
    (property "Reference" "R12" (at 0 0 0))
    (property "Value" "10k" (at 0 0 0))
  )
  (symbol
    (lib_id "power:GND")
    (property "Reference" "#PWR03" (at 0 0 0))
  )
  (label "EN" (at 1 1 0))
)'''
        self.assertEqual(sources.parse_selection(clip), ["R12 (10k)", "label EN"])


class UnreachableHintTests(unittest.TestCase):
    """Issue #7: a windowless leftover kicad.exe holds the API connection."""

    def test_stale_background_kicad_is_named(self):
        hint = sources.unreachable_hint([(11884, False), (28252, True)])
        self.assertIn("11884", hint)
        self.assertIn("Task Manager", hint)
        self.assertNotIn("28252", hint)  # the KiCad the user is working in

    def test_single_kicad_points_to_api_setting(self):
        self.assertIn("Enable KiCad API", sources.unreachable_hint([(28252, True)]))

    def test_no_kicad_running(self):
        self.assertIn("isn't running", sources.unreachable_hint([]))

    def test_status_chip_names_the_blocking_process(self):
        self.assertIn("11884", sources.unreachable_chip([(11884, False), (5976, True)]))
        self.assertEqual(sources.unreachable_chip([]), "Not connected: KiCad isn't running")
        self.assertIn("API server", sources.unreachable_chip([(5976, True)]))

    def test_report_includes_process_counts(self):
        diag = report.diagnostics("schematic", "", "10.0.5", extra=["kicad_processes: 2 running, 1 without a window"])
        self.assertIn("kicad_processes: 2 running, 1 without a window", diag)


class SkillToolsEnvTests(unittest.TestCase):
    """The panel's Claude sessions must find the private Java 25 before any system Java,
    and the Freerouting jar, so the kicad MCP server's autoroute tool works."""

    def test_java_first_on_path_and_jar_exported(self):
        from powerlab_assistant import common
        with tempfile.TemporaryDirectory() as tmp:
            java_home = os.path.join(tmp, "jdk-25-jre")
            os.makedirs(os.path.join(java_home, "bin"))
            open(os.path.join(java_home, "bin", "java.exe"), "w").close()
            jar = os.path.join(tmp, "freerouting-2.4.1.jar")
            open(jar, "w").close()
            saved = config.config
            config.config = lambda: {"java_home": java_home, "freerouting_jar": jar}
            try:
                env = common.clean_env()
            finally:
                config.config = saved
        self.assertEqual(env["PATH"].split(os.pathsep)[0], os.path.join(java_home, "bin"))
        self.assertEqual(env["JAVA_HOME"], java_home)
        self.assertEqual(env["FREEROUTING_JAR"], jar)

    def test_windows_tar_before_git_tar(self):
        # Issue #24: Git's GNU tar can't write zips; Windows' own tar in System32 can.
        from powerlab_assistant import common
        system32 = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")
        if not os.path.isfile(os.path.join(system32, "tar.exe")):
            self.skipTest("no Windows tar.exe")
        saved = os.environ["PATH"]
        os.environ["PATH"] = os.pathsep.join([r"C:\Program Files\Git\usr\bin", saved])
        try:
            path = common.clean_env()["PATH"].split(os.pathsep)
        finally:
            os.environ["PATH"] = saved
        self.assertLess(path.index(system32), path.index(r"C:\Program Files\Git\usr\bin"))

    def test_shipped_skills_have_frontmatter(self):
        skills = os.path.join(ROOT, "skills")
        names = sorted(os.listdir(skills))
        self.assertIn("powerlab-autoroute", names)
        for name in names:
            with open(os.path.join(skills, name, "SKILL.md"), encoding="utf-8") as f:
                head = f.read().split("---")
            self.assertIn(f"name: {name}", head[1])
            self.assertIn("description:", head[1])

    def test_design_rules_skill_is_public_safe_and_used_by_autoroute(self):
        skills = os.path.join(ROOT, "skills")
        with open(os.path.join(skills, "powerlab-pcb-design-rules", "SKILL.md"), encoding="utf-8") as f:
            rules = f.read()
        self.assertIn("### 2.6 KiCad setup", rules)
        self.assertNotIn(".kicad_wks", rules)  # the lab drawing-sheet rule stays out of the public panel
        with open(os.path.join(skills, "powerlab-autoroute", "SKILL.md"), encoding="utf-8") as f:
            self.assertIn("powerlab-pcb-design-rules", f.read())

    def test_routing_rules_from_issue_21_stay(self):
        # GND to the pours (no pad-to-pad tracks), power at class width, short paths:
        # the panel addition must survive a re-copy of the lab's rules file
        skills = os.path.join(ROOT, "skills")
        with open(os.path.join(skills, "powerlab-pcb-design-rules", "SKILL.md"), encoding="utf-8") as f:
            rules = f.read()
        self.assertIn("Never route a pour net between pads", rules)
        self.assertIn("Power rails are copper areas, not traces", rules)
        self.assertIn("Enter a pad straight and end at its centre", rules)
        self.assertIn("No copper islands or slivers next to pads", rules)
        self.assertIn("Shortest path, fewest corners", rules)
        with open(os.path.join(skills, "powerlab-autoroute", "SKILL.md"), encoding="utf-8") as f:
            route = f.read()
        self.assertIn("Freerouting 2.4.1 ignores the net-class width", route)
        # No GND fan-out vias up front: pads reach the pour, vias only after routing
        self.assertIn("No GND fan-out before routing", route)
        self.assertIn("Never fan out GND pads with vias up front", rules)
        # Copper before routing, magnetics, switching layers, fast-signal vias
        self.assertIn("### 3.3 Copper pours and high-current copper", rules)
        self.assertIn("Power pads get their copper first", rules)
        self.assertIn("No tracks under inductors, transformers", rules)
        self.assertIn("Switching signals don't share a layer with high-current copper", rules)
        self.assertIn("Avoid vias on high-speed signals if you can", rules)


class AttachmentTests(unittest.TestCase):
    """Issue #10: images and documents can be attached to a message."""

    def test_pasted_image_is_saved_and_listed_for_claude(self):
        from powerlab_assistant import attachments
        png = "data:image/png;base64," + base64.b64encode(b"\x89PNG fake").decode()
        with tempfile.TemporaryDirectory() as tmp:
            path = attachments.save_data("", png, folder=tmp)
            self.assertTrue(path.endswith(".png"))
            with open(path, "rb") as f:
                self.assertEqual(f.read(), b"\x89PNG fake")
            self.assertEqual(attachments.folders([path, path]), [tmp])
        suffix = attachments.prompt_suffix([path])
        self.assertIn("Read tool", suffix)
        self.assertIn(path, suffix)
        self.assertEqual(attachments.prompt_suffix([]), "")

    def test_rejects_non_files_and_odd_names(self):
        from powerlab_assistant import attachments
        with self.assertRaises(ValueError):
            attachments.save_data("x.txt", "javascript:alert(1)")
        self.assertEqual(attachments.safe_name("..\\..\\evil<>.pdf"), "evil_.pdf")


class UsageTests(unittest.TestCase):
    """Issue #10: show plan limits and context use in the panel."""

    def test_limits_and_context(self):
        from powerlab_assistant import usage
        event = {"type": "rate_limit_event", "rate_limit_info": {
            "status": "allowed", "rateLimitType": "five_hour", "resetsAt": 1791408000,
            "unifiedWindows": {"five_hour": {"utilization": 0.49, "resetsAt": 1791408000},
                               "seven_day": {"utilization": 0.2, "resetsAt": 1791900000}}}}
        items = usage.limits(event, now=1791400000)
        self.assertEqual([(i["short"], i["pct"]) for i in items], [("5h", 49), ("week", 20)])
        result = {"usage": {"iterations": [{"input_tokens": 10, "cache_read_input_tokens": 20000,
                                            "cache_creation_input_tokens": 4000, "output_tokens": 990}]},
                  "modelUsage": {"claude-opus-5-5": {"contextWindow": 200000}}}
        self.assertEqual(usage.context(result), (25000, 200000))
        text, tip = usage.summary(items, 25000, 200000)
        self.assertEqual(text, "5h 49% · context 12%")
        self.assertIn("Weekly limit: 20% used", tip)
        self.assertEqual(usage.summary([], 0, 0), ("", ""))


class ChatHistoryTests(unittest.TestCase):
    """Closing the panel, the editor or KiCad must not forget the chat."""

    def setUp(self):
        from powerlab_assistant import history
        self.history = history
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.old_folder, history.FOLDER = history.FOLDER, self.tmp.name
        self.addCleanup(setattr, history, "FOLDER", self.old_folder)
        self.project = os.path.join(self.tmp.name, "project")

    def fake_panel(self):
        """The panel's chat methods on a plain object (no window, page or Claude process)."""
        try:
            from powerlab_assistant.panel import ClaudePanel
        except ImportError as exc:
            self.skipTest(f"panel needs wx.html2: {exc}")
        names = ("say", "save_chat", "open_chat", "handle", "finished", "show_image", "set_activity",
                 "show_review")

        class Fake:
            pass

        for name in names:
            setattr(Fake, name, getattr(ClaudePanel, name))
        panel = Fake()
        panel.source = types.SimpleNamespace(editor="pcb")
        panel.session_id, panel.chat_cwd, panel.events = None, None, []
        panel.retry, panel.stale_session, panel.proc = None, False, None
        panel.got_result, panel.watched, panel.image_reads = False, {}, {}
        panel.review_writes, panel.review_md = {}, None
        panel.last_text, panel.limits, panel.started, panel.effort = "", [], 0.0, "high"
        panel.activity, panel.activity_sent = ("waiting", ""), time.time()
        panel.thinking_tokens = 0
        panel.thought, panel.thought_started, panel.summaries_on = "", 0.0, False
        panel.emitted = []
        panel.emit = lambda kind, **data: panel.emitted.append(dict(data, kind=kind))
        panel.load_page = lambda: panel.emitted.clear()
        panel.SetTitle = lambda title: setattr(panel, "title", title)
        return panel

    def write_old(self, editor, session_id, events):
        """A chat saved by 0.5, when each editor had its own panel and chat."""
        import json
        name = os.path.basename(self.history.chat_path(self.project)).replace("chat-", editor + "-")
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"cwd": self.project, "session_id": session_id, "events": events}, f)
        return path

    def test_chat_is_kept_per_project(self):
        h = self.history
        image = h.stored("image", {"src": "data:image/png;base64,AAAA", "name": "v.png", "path": "C:\\v.png"})
        self.assertEqual(image, {"kind": "image", "name": "v.png", "path": "C:\\v.png"})
        h.save(self.project, "abc", [{"kind": "user", "text": "hi", "files": []}, image])
        self.assertEqual(h.load(self.project), ("abc", [{"kind": "user", "text": "hi", "files": []}, image]))
        self.assertEqual(h.load(self.project + "2"), (None, []))
        h.save(self.project, "abc", [{"kind": "text", "text": str(i)} for i in range(h.MAX_EVENTS + 5)])
        self.assertEqual(len(h.load(self.project)[1]), h.MAX_EVENTS)
        h.save(self.project, None, [])  # New chat
        self.assertEqual(os.listdir(self.tmp.name), [])

    def test_old_per_editor_chats_are_carried_over(self):
        h = self.history
        self.write_old("pcb", "old-pcb", [{"kind": "text", "text": "pcb"}] * 3)
        newer = self.write_old("schematic", "old-sch", [{"kind": "text", "text": "hi"}])
        os.utime(newer, (time.time() + 10, time.time() + 10))
        self.assertEqual(h.load(self.project)[0], "old-pcb")  # the longer one, not a newer "hi"
        self.write_old("schematic", "old-sch", [{"kind": "text", "text": "sch"}] * 3)
        os.utime(newer, (time.time() + 10, time.time() + 10))
        self.assertEqual(h.load(self.project)[0], "old-sch")  # as long: the newer one
        h.save(self.project, "old-sch", h.load(self.project)[1])
        self.assertEqual(os.listdir(self.tmp.name), [os.path.basename(h.chat_path(self.project))])

    def test_reopened_panel_continues_the_last_chat(self):
        first = self.fake_panel()
        first.open_chat(self.project)
        # With two KiCads open there are two panels: the title says whose this is.
        self.assertEqual(first.title, "PowerLab Assistant — " + os.path.basename(self.project))
        self.assertEqual(first.emitted, [])  # nothing saved yet
        first.say("user", text="Place the connectors", files=[])
        first.handle({"type": "system", "subtype": "init", "session_id": "s-1"})
        first.handle({"type": "assistant", "message": {"content": [
            {"type": "text", "text": "Done."},
            {"type": "tool_use", "id": "t1", "name": "mcp__kicad__move_component", "input": {"reference": "J1"}}]}})
        first.save_chat()  # KiCad closes; the panel opens again on the project, from either editor
        second = self.fake_panel()
        second.source.editor = "schematic"
        second.open_chat(self.project)
        self.assertEqual(second.session_id, "s-1")  # the next message resumes it
        kinds = [e["kind"] for e in second.emitted]
        self.assertEqual(kinds, ["user", "text", "tool", "busy", "note"])
        self.assertEqual(second.emitted[1]["text"], "Done.")
        self.assertIn("Continuing your last chat", second.emitted[-1]["text"])
        # Another project has its own chat.
        second.open_chat(self.project + "-other")
        self.assertEqual((second.session_id, second.events, second.emitted), (None, [], []))

    def test_requirements_skill_questions_become_buttons(self):
        # The intake rounds of powerlab-board-requirements must parse as answer buttons:
        # 2-4 options per question, the lab default first and recommended.
        from powerlab_assistant.panel import split_choices
        with open(os.path.join(ROOT, "skills", "powerlab-board-requirements", "SKILL.md"),
                  encoding="utf-8") as f:
            skill = f.read()
        import re
        blocks = re.findall(r"```\n(<choices>\n.*?</choices>)\n```", skill, re.S)
        self.assertGreaterEqual(len(blocks), 3)
        questions = [q for block in blocks for q in split_choices(block)[1]]
        self.assertGreaterEqual(len(questions), 6)
        for q in questions:
            self.assertTrue(2 <= len(q["options"]) <= 4, q)
            self.assertTrue(q["options"][0].endswith("(Recommended)"), q)
            for option in q["options"]:  # the panel adds its own Other… with a text box
                self.assertFalse(option.lower().startswith("other"), q)
                self.assertNotIn("type it", option, q)

    def test_echoed_kicad_state_is_not_shown(self):
        panel = self.fake_panel()
        state = "<kicad_state>\nOpen board: C:/p/b.kicad_pcb\nSelected footprints: U1\n</kicad_state>"
        panel.handle({"type": "assistant", "message": {"content": [
            {"type": "text", "text": "Which part do you mean?\n\n" + state},
            {"type": "text", "text": state}]}})
        self.assertEqual([e["text"] for e in panel.emitted], ["Which part do you mean?"])
        self.assertEqual(panel.last_text, "Which part do you mean?")

    def test_questions_become_answer_buttons(self):
        panel = self.fake_panel()
        panel.handle({"type": "assistant", "message": {"content": [{"type": "text", "text": (
            "Two things to confirm.\n\n<choices>\n1. Keep 25.4 mm row spacing?\n"
            "- Yes, 25.4 mm (Recommended)\n- No, use 28 mm\nMounting holes?\n* None\n* Four M3 holes\n"
            "A question without options\n</choices>")}]}})
        self.assertEqual(panel.emitted, [{"kind": "text", "text": "Two things to confirm.", "choices": [
            {"question": "Keep 25.4 mm row spacing?", "options": ["Yes, 25.4 mm (Recommended)", "No, use 28 mm"]},
            {"question": "Mounting holes?", "options": ["None", "Four M3 holes"]}]}])
        self.assertEqual(panel.events[0]["choices"][1]["options"], ["None", "Four M3 holes"])  # kept in the chat
        # Only the block (no text above it), and replies without one stay plain text.
        panel.emitted.clear()
        panel.handle({"type": "assistant", "message": {"content": [
            {"type": "text", "text": "<choices>\nRoute GND?\n- Pour\n- Tracks"},
            {"type": "text", "text": "Done."}]}})
        self.assertEqual(panel.emitted, [
            {"kind": "text", "text": "", "choices": [{"question": "Route GND?", "options": ["Pour", "Tracks"]}]},
            {"kind": "text", "text": "Done."}])

    def test_panel_shows_what_claude_is_doing(self):
        # A 12-minute think showed nothing at all, and looked like a hang.
        panel = self.fake_panel()

        def stream(event):
            panel.handle({"type": "stream_event", "event": event})

        def shown():
            done = [(e["phase"], e["name"]) for e in panel.emitted if e["kind"] == "activity"]
            panel.emitted.clear()
            return done

        stream({"type": "message_start"})
        stream({"type": "content_block_start", "content_block": {"type": "thinking"}})
        for _ in range(50):  # chunks of the same activity aren't each sent to the page
            stream({"type": "content_block_delta", "delta": {"type": "thinking_delta", "thinking": ""}})
        self.assertEqual(shown(), [("thinking", "")])
        panel.activity_sent -= 30  # a quiet think still tells the page Claude is alive
        stream({"type": "content_block_delta", "delta": {"type": "thinking_delta", "thinking": ""}})
        self.assertEqual(shown(), [("thinking", "")])
        panel.activity_sent -= 30  # how far the think has got
        panel.handle({"type": "system", "subtype": "thinking_tokens", "estimated_tokens": 4200})
        self.assertEqual(panel.emitted, [{"kind": "activity", "phase": "thinking", "name": "", "tokens": 4200}])
        panel.emitted.clear()
        # With summaries on, the thinking itself is shown while it streams...
        stream({"type": "content_block_delta", "delta": {"type": "thinking_delta", "thinking": "Checking U3 decoupling. "}})
        stream({"type": "content_block_delta", "delta": {"type": "thinking_delta", "thinking": "C5 is 9 mm away."}})
        panel.activity_sent -= 30
        stream({"type": "content_block_delta", "delta": {"type": "thinking_delta", "thinking": ""}})
        self.assertEqual(panel.emitted[-1]["thought"], "Checking U3 decoupling. C5 is 9 mm away.")
        panel.emitted.clear()
        # ...then kept in the chat, collapsed.
        panel.handle({"type": "assistant", "message": {"content": [
            {"type": "thinking", "thinking": "Checking U3 decoupling. C5 is 9 mm away.", "signature": "x"}]}})
        self.assertEqual([(e["kind"], e["text"]) for e in panel.emitted],
                         [("thought", "Checking U3 decoupling. C5 is 9 mm away.")])
        self.assertEqual(panel.events[-1]["kind"], "thought")
        panel.handle({"type": "assistant", "message": {"content": [{"type": "thinking", "thinking": ""}]}})
        self.assertEqual(len(panel.events), 1)  # omitted thinking (no summary) adds nothing
        panel.emitted.clear()

        stream({"type": "content_block_start", "content_block": {"type": "tool_use", "name": "mcp__kicad__get_pads"}})
        panel.handle({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "a", "name": "mcp__kicad__get_pads", "input": {}},
            {"type": "tool_use", "id": "b", "name": "Grep", "input": {"pattern": "x"}}]}})
        self.assertEqual(shown(), [("preparing", "Get pads"), ("tool", "Get pads"), ("tool", "Grep")])
        panel.handle({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "a"}]}})
        self.assertEqual(shown(), [])  # Grep is still running
        panel.handle({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "b"}]}})
        self.assertEqual(shown(), [("waiting", "")])
        panel.handle({"type": "system", "subtype": "api_retry", "attempt": 1})
        self.assertEqual(shown(), [("retry", "")])
        # Activity isn't part of the saved chat.
        self.assertFalse(any(e["kind"] == "activity" for e in panel.events))

    def test_expired_session_is_sent_again_as_a_new_chat(self):
        panel = self.fake_panel()
        panel.chat_cwd, panel.session_id = self.project, "gone"
        panel.retry = ("Run DRC", [])
        sent = []

        def launch(text, files=None):
            sent.append((text, files, panel.session_id))
            panel.proc = object()

        panel.launch = launch
        panel.handle({"type": "result", "subtype": "error_during_execution", "is_error": True,
                      "errors": ["No conversation found with session ID: gone"]})
        panel.finished(0)
        self.assertEqual(sent, [("Run DRC", [], None)])
        self.assertFalse(any(e["kind"] == "meta" or e.get("level") == "error" for e in panel.emitted))

    def test_design_review_is_shown_with_its_pdf(self):
        # The design-review skill writes design-review.md; when the run ends, the panel
        # shows the review in the chat and saves it as a PDF next to it.
        from powerlab_assistant import review
        panel = self.fake_panel()
        panel.in_background = lambda work, done: done(work())
        panel.chat_cwd = self.project
        md = os.path.join(self.project, "design-review", "design-review.md")
        os.makedirs(os.path.dirname(md))
        with open(md, "w", encoding="utf-8") as f:
            f.write("# Design review: board\n\n- **Verdict:** Ready to order\n")
        built = []
        saved = review.build
        review.build = lambda path: built.append(path) or dict(saved(path, edge=""), pdf=path[:-3] + ".pdf")
        self.addCleanup(setattr, review, "build", saved)
        panel.handle({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "w1", "name": "Write", "input": {"file_path": md, "content": "x"}},
            {"type": "tool_use", "id": "w2", "name": "Write", "input": {"file_path": md + ".txt"}}]}})
        panel.handle({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "w1"}, {"type": "tool_result", "tool_use_id": "w2"}]}})
        self.assertEqual(built, [])  # shown once the run ends, after Claude's last reply
        panel.finished(0)
        self.assertEqual(built, [md])
        card = panel.emitted[-1]
        self.assertEqual((card["kind"], card["title"], card["verdict"]), ("review", "Design review: board", "Ready to order"))
        self.assertTrue(card["pdf"].endswith("design-review.pdf"))
        self.assertIn("<strong>Verdict:</strong>", card["body"])
        self.assertNotIn("body", panel.events[-1])  # the chat keeps the path, not the HTML
        # Reopened later, the card is built again from the file.
        again = self.fake_panel()
        again.open_chat(self.project)
        shown = [e for e in again.emitted if e["kind"] == "review"]
        self.assertEqual(len(shown), 1)
        self.assertIn("<strong>Verdict:</strong>", shown[0]["body"])
        self.assertTrue(shown[0]["pdf"].endswith(".pdf"))
        # A failed write, or a run that wrote no review, shows nothing.
        panel.emitted.clear()
        panel.handle({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "w3", "name": "Edit", "input": {"file_path": md}}]}})
        panel.handle({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "w3", "is_error": True, "content": "no"}]}})
        panel.finished(0)
        self.assertFalse(any(e["kind"] == "review" for e in panel.emitted))

    def test_clicked_location_is_shown_in_kicad(self):
        from powerlab_assistant.panel import ClaudePanel
        panel = self.fake_panel()
        calls = []
        results =[(3, []), (1, ["U9"]), (0, ["net NOPE"]), ConnectionError("no board")]

        def locate(target):
            calls.append(target)
            result = results.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        panel.source = types.SimpleNamespace(locate=locate, show_pcb_editor=lambda: calls.append("front"))
        panel.in_background = lambda work, done: done(_run(work))

        def _run(work):
            try:
                return work()
            except Exception as exc:
                return exc

        for target in ("refs=U6", "refs=U6,U9", "net=NOPE", "refs=U1"):
            ClaudePanel.msg_locate(panel, {"type": "locate", "target": target})
        self.assertEqual(calls, ["refs=U6", "front", "refs=U6,U9", "front", "net=NOPE", "refs=U1"])
        notes = [(e["level"], e["text"]) for e in panel.emitted]
        self.assertEqual(notes[0], ("info", "Not found on the board: U9"))
        self.assertEqual(notes[1], ("warn", "Not found on the board: net NOPE"))
        self.assertIn("Open the board in the PCB editor", notes[2][1])
        self.assertEqual(len(notes), 3)


class DesignReviewTests(unittest.TestCase):
    """The review handbook, the design-review skill, and the review's HTML and PDF."""

    def setUp(self):
        from powerlab_assistant import review
        self.review = review
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = os.path.join(self.tmp.name, "design-review")
        os.makedirs(os.path.join(self.folder, "images"))
        png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg==")
        with open(os.path.join(self.folder, "images", "01-top.png"), "wb") as f:
            f.write(png)
        self.md = os.path.join(self.folder, "design-review.md")

    def skill(self, name):
        with open(os.path.join(ROOT, "skills", name, "SKILL.md"), encoding="utf-8") as f:
            return f.read()

    def test_handbook_ships_with_the_design_rules(self):
        import re
        folder = os.path.join(ROOT, "skills", "powerlab-pcb-design-rules", "handbook")
        names = os.listdir(folder)
        ids = []
        for name in names:
            with open(os.path.join(folder, name), encoding="utf-8") as f:
                text = f.read()
            if re.match(r"\d\d-", name) and name != "91-checklist.md":
                ids += re.findall(r"^### \[([A-Z]+-\d{3})\]", text, re.M)
            self.assertNotIn("_calisma/", text if name != "DECISIONS.md" else "")  # Turkish work notes stay out
        self.assertEqual(len(ids), 233)
        self.assertEqual(len(set(ids)), 233)
        with open(os.path.join(folder, "91-checklist.md"), encoding="utf-8") as f:
            checklist = f.read()
        for rule in ids:
            self.assertIn(f"**{rule}**", checklist)
        rules = self.skill("powerlab-pcb-design-rules")
        # Lab rules brought in line with the handbook (also in odtu/Powerlab's file)
        for rule in ("**0.5 A per 0.3 mm via**", "**Ø 8 mm keepout**", "place the hot loop first",
                     "TVS and ESD diodes go at the connector", "Power input protection sits at the input connector",
                     "Gate return is Kelvin", "Current-sense shunts use Kelvin connections",
                     "No copper on any layer under the antenna", "within about 2.5 mm of its pin"):
            self.assertIn(rule, rules)
        self.assertNotIn("0.4 mm via ≈ 1.5 A", rules)
        self.assertIn("## 4. Layout review handbook", rules)
        self.assertIn("handbook/91-checklist.md", rules)
        for name in re.findall(r"`(\d\d-[a-z0-9-]+\.md)`", rules):
            self.assertIn(name, names)

    def test_review_skill_loops_and_writes_the_report(self):
        import ast
        with open(os.path.join(ROOT, "plugin", "powerlab_assistant", "panel.py"), encoding="utf-8") as f:
            tree = ast.parse(f.read())
        note = next(ast.literal_eval(n.value) for n in tree.body
                    if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "PANEL_NOTE")
        self.assertIn("powerlab-design-review", note)
        self.assertIn(r"design-review\design-review.md", note)
        skill = self.skill("powerlab-design-review")
        for part in ("## When to stop", "Five rounds", "Needs the user", "--all-track-errors",
                     "handbook/91-checklist.md", r"design-review\design-review.md"):
            self.assertIn(part, skill)
        self.assertIn("powerlab-design-review", self.skill("powerlab-visual-review"))
        # The report template in the skill turns into the card the panel shows.
        import re
        template = re.search(r"```markdown\n(.*?)\n```", skill, re.S).group(1)
        with open(self.md, "w", encoding="utf-8") as f:
            f.write(template.replace("images/02-top.png", "images/01-top.png"))
        card = self.review.card(self.md)
        self.assertTrue(card["title"].startswith("Design review: "))
        self.assertTrue(card["verdict"].startswith("Ready to order after"))
        for heading in ("Summary", "Needs you", "Open findings", "Fixed during the review",
                        "Checked and fine", "Not checked", "Views"):
            self.assertIn(f"<h2>{heading}</h2>", card["body"])
        self.assertIn('<h3 class="sev sev-high">High</h3>', card["body"])
        self.assertIn("<td>N1</td><td>RF-006</td>", card["body"])
        self.assertIn('src="data:image/png;base64,', card["body"])
        self.assertIn("data-path=", card["body"])  # click opens the image
        self.assertIn("Image not found: images/01-placement.png", card["body"])

    def test_review_text_is_escaped(self):
        body = self.review.body_html(
            "# T\n\n<script>alert(1)</script> **b** [x](javascript:alert(1)) [ok](https://e.com)\n"
            "![a\" onerror=\"x](images/01-top.png)\n", self.folder)
        self.assertNotIn("<script>", body)
        self.assertNotIn('href="javascript', body)
        self.assertIn('<a href="https://e.com">ok</a>', body)
        self.assertNotIn('" onerror="', body)
        self.assertIn("&lt;script&gt;", body)
        self.assertFalse(self.review.is_review(os.path.join(self.folder, "notes.md")))
        self.assertTrue(self.review.is_review(self.md.upper()))

    def test_locations_are_parsed(self):
        parse = self.review.parse_location
        self.assertEqual(parse("refs=U6,Q2&net=GLC"), {"refs": ["U6", "Q2"], "nets": ["GLC"], "areas": []})
        self.assertEqual(parse("U1")["refs"], ["U1"])
        self.assertEqual(parse("net=Net-%28U1-Pad3%29&net=A%2CB")["nets"], ["Net-(U1-Pad3)", "A,B"])
        self.assertEqual(parse("area=20,30,10,5")["areas"], [(10, 5, 20, 30)])
        self.assertEqual(parse("at=100,50")["areas"], [(97.5, 47.5, 102.5, 52.5)])
        self.assertEqual(parse("at=x,1&area=1,2&bogus=3"), {"refs": [], "nets": [], "areas": []})

    def test_location_picks_board_items(self):
        from types import SimpleNamespace as NS

        def at(x, y):
            return NS(x=int(x * 1e6), y=int(y * 1e6))

        u6 = NS(reference_field=NS(text=NS(value="U6")), position=at(100, 50))
        q2 = NS(reference_field=NS(text=NS(value="Q2")), position=at(104, 52))
        track = NS(net=NS(name="GLC"), start=at(100, 50), end=at(160, 50))
        via = NS(net=NS(name="GLC"), position=at(160, 50))
        pad = NS(net=NS(name="GLC"), position=at(100, 50))
        other = NS(net=NS(name="GND"), start=at(0, 0), end=at(1, 1))
        board = ([u6, q2], [track, other], [via], [pad])
        pick = lambda target: self.review.pick_items(self.review.parse_location(target), *board)
        items, missing, small = pick("refs=u6,Q2,U9")
        self.assertEqual((items, missing, small), ([u6, q2], ["U9"], True))  # small: zoomed out once
        items, missing, small = pick("net=GLC")
        self.assertEqual((items, missing, small), ([track, via, pad], [], False))
        items, missing, _ = pick("at=160,50&net=NOPE")
        self.assertEqual((items, missing), ([track, via], ["net NOPE"]))
        self.assertEqual(pick("area=0,0,1,1")[0], [other])
        self.assertEqual(pick("at=500,500")[:2], ([], ["anything at (497.5, 497.5)–(502.5, 502.5) mm"]))

    def test_location_links_are_clickable_in_the_panel_only(self):
        body = self.review.body_html(
            '| F1 | [under L1](kicad:refs=L1&net=BUCK_PG) |\n|---|---|\n| x | [a"b](kicad:refs="><script>) |\n',
            self.folder)
        self.assertIn('<a class="loc" data-loc="refs=L1&amp;net=BUCK_PG" title="Show in KiCad">under L1</a>', body)
        self.assertNotIn("<script>", body)
        self.assertIn("a.loc { color: inherit;", self.review.CSS)  # plain text in the PDF
        with open(os.path.join(ROOT, "plugin", "powerlab_assistant", "panel.html"), encoding="utf-8") as f:
            page = f.read()
        self.assertIn("kicad:([^)\\s]+)", page)  # Claude's replies get the links too
        self.assertIn("post({ type: 'locate', target: loc.dataset.loc })", page)
        skill = self.skill("powerlab-design-review")
        self.assertIn("(kicad:refs=U6,Q2)", skill)
        self.assertIn("kicad:net=Net-%28U1-Pad3%29", skill)

    def test_without_edge_the_html_is_saved_instead(self):
        with open(self.md, "w", encoding="utf-8") as f:
            f.write("# Design review: b\n\n![Top](images/01-top.png)\n")
        data = self.review.build(self.md, edge="")
        self.assertNotIn("pdf", data)
        self.assertIn("Edge", data["error"])
        with open(data["html"], encoding="utf-8") as f:
            page = f.read()
        self.assertIn("data:image/png;base64,", page)  # works on its own
        self.assertNotIn("data-path", page)

    @unittest.skipUnless(sys.platform == "win32", "needs Microsoft Edge")
    def test_pdf_is_printed_with_edge(self):
        if not self.review.find_edge():
            self.skipTest("Microsoft Edge not found")
        with open(self.md, "w", encoding="utf-8") as f:
            f.write("# Design review: b\n\n## Summary\n- **Verdict:** Ready to order\n\n"
                    "| # | Rule |\n|---|---|\n| F1 | PWR-006 |\n\n![Top](images/01-top.png)\n")
        data = self.review.build(self.md)
        self.assertEqual(data.get("error"), None)
        with open(data["pdf"], "rb") as f:
            self.assertEqual(f.read(5), b"%PDF-")
        self.assertFalse(os.path.exists(os.path.join(self.folder, "design-review.html")))


class OnePanelTests(unittest.TestCase):
    """One panel serves both editors: Claude sees the board and the schematic from either."""

    def setUp(self):
        try:
            from kipy.board_types import FootprintInstance
            from kipy.errors import ApiError
            from kipy.proto.common.types.base_types_pb2 import DocumentSpecifier, DocumentType
        except ImportError as exc:
            self.skipTest(f"needs kicad-python: {exc}")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = self.tmp.name
        for name in ("esp.kicad_pro", "esp.kicad_sch", "power.kicad_sch", "esp.kicad_pcb"):
            open(os.path.join(self.project, name), "w").close()
        self.open = {"pcb", "schematic"}
        self.foreground = "esp — PCB Editor"
        self.footprints = ["U2", "C5"]

        def doc(doc_type, filename):
            d = DocumentSpecifier()
            d.type, d.board_filename, d.project.path = doc_type, filename, self.project
            return d

        def get_open_documents(doc_type):
            editor = "pcb" if doc_type == DocumentType.DOCTYPE_PCB else "schematic"
            if editor not in self.open:
                raise ApiError("KiCad returned error: no handler available for request")
            return [doc(doc_type, "esp.kicad_pcb" if editor == "pcb" else "esp.kicad_sch")]

        def selection():
            items = []
            for ref in self.footprints:
                fp = FootprintInstance()
                fp.reference_field.text.value = ref
                items.append(fp)
            return items

        kicad = types.SimpleNamespace(
            get_open_documents=get_open_documents,
            get_board=lambda: types.SimpleNamespace(get_selection=selection))
        self.source = sources.KiCadSource.__new__(sources.KiCadSource)
        self.source.editor, self.source.kicad, self.source.down_until = "schematic", kicad, 0.0
        self.source.pid = 0
        self.source.selected, self.source.clip_seq = ["R1 (10k)"], 0
        self.source.poll_clipboard = lambda: None
        window = types.SimpleNamespace(
            foreground_title=lambda pid=0: self.foreground,
            find_editor=lambda kind="Schematic Editor", pid=0: 1 if "schematic" in self.open else None,
            current_sheet=lambda hwnd: "esp/Power")
        old, sources.kicad_window = sources.kicad_window, window
        self.addCleanup(setattr, sources, "kicad_window", old)

    def test_sees_both_editors_and_follows_the_one_in_use(self):
        snap = self.source.snapshot()
        self.assertEqual(self.source.editor, "pcb")  # the PCB editor has the focus
        self.assertEqual(snap.cwd, self.project)
        self.assertEqual(snap.chips, ["esp.kicad_pcb", "Selected: C5, U2"])
        self.assertIn("The user is working in the PCB editor.", snap.state)
        self.assertIn("Selected footprints in the PCB editor: C5, U2", snap.state)
        self.assertIn("showing sheet esp/Power", snap.state)
        self.assertIn("Selected in the schematic editor: R1 (10k)", snap.state)
        self.assertIn("Root schematic: " + os.path.join(self.project, "esp.kicad_sch"), snap.context)
        self.assertIn("Board file: " + os.path.join(self.project, "esp.kicad_pcb"), snap.context)
        self.assertEqual(sorted(os.path.basename(p) for p in snap.watch),
                         ["esp.kicad_pcb", "esp.kicad_sch", "power.kicad_sch"])
        # The user clicks into the schematic editor; the panel itself having the focus changes nothing.
        self.foreground = "esp [esp/Power] — Schematic Editor"
        self.assertEqual(self.source.snapshot().chips, ["Sheet: Power", "Selected: R1"])
        self.foreground = "PowerLab Assistant"
        self.assertIn("working in the schematic editor", self.source.snapshot().state)

    def test_works_with_only_one_editor_open(self):
        self.open = {"schematic"}
        snap = self.source.snapshot()
        self.assertEqual(snap.cwd, self.project)
        self.assertIn("PCB editor: not open", snap.state)
        self.assertIn("Board file: " + os.path.join(self.project, "esp.kicad_pcb"), snap.context)
        self.open = {"pcb"}
        snap = self.source.snapshot()
        self.assertIn("Schematic editor: not open", snap.state)
        self.assertIn("Root schematic:", snap.context)
        self.open = set()
        self.assertEqual(self.source.snapshot().chips, ["No schematic or board open"])


class TwoKiCadsTests(unittest.TestCase):
    """A second KiCad gets a panel of its own, connected to that KiCad and no other."""

    def setUp(self):
        self.shared = sources.instances.SHARED.lower()
        self.own = sources.instances.own_socket(2344).lower()

    def test_each_kicad_finds_its_own_socket(self):
        find = sources.instances.find_socket
        # The first KiCad has api.sock; one started later has api-<pid>.sock.
        self.assertEqual(find(11632, {self.shared, self.own}, lambda path: 11632),
                         "ipc://" + sources.instances.SHARED)
        self.assertEqual(find(2344, {self.shared, self.own}, lambda path: 11632),
                         "ipc://" + sources.instances.own_socket(2344))
        # A KiCad started before the placeholder, while another held api.sock, has none:
        # it must never be handed the other KiCad's.
        self.assertIsNone(find(2344, {self.shared}, lambda path: 11632))
        self.assertEqual(sources.instances.shared_holder(2344, {self.shared}, lambda path: 11632), 11632)
        self.assertEqual(sources.instances.shared_holder(11632, {self.shared}, lambda path: 11632), 0)

    def test_placeholder_makes_later_kicads_use_their_own_socket(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = sources.instances.SOCKET_DIR, sources.instances.SHARED
            self.addCleanup(lambda: setattr(sources.instances, "SHARED", old[1]))
            self.addCleanup(lambda: setattr(sources.instances, "SOCKET_DIR", old[0]))
            sources.instances.SOCKET_DIR = os.path.join(tmp, "kicad")
            sources.instances.SHARED = os.path.join(tmp, "kicad", "api.sock")
            sources.instances.ensure_placeholder()
            self.assertTrue(os.path.isfile(sources.instances.SHARED))
            sources.instances.ensure_placeholder()  # already there: left alone

    def test_kicad_without_its_own_socket_is_not_connected_to_another(self):
        try:
            import kipy  # noqa: F401
        except ImportError as exc:
            self.skipTest(f"needs kicad-python: {exc}")
        window = types.SimpleNamespace(pipe_names=lambda: {self.shared},
                                       pipe_server=lambda path: 11632,
                                       kicad_processes=lambda: [(11632, True), (2344, True)])
        old, sources.kicad_window = sources.kicad_window, window
        self.addCleanup(setattr, sources, "kicad_window", old)
        source = sources.KiCadSource("pcb", pid=2344)
        self.assertIsNone(source.kicad)
        with self.assertRaises(ConnectionError):
            source.call(lambda k: k.get_open_documents(0))
        # Claude's kicad tools get a socket nothing listens on, so they work on the files.
        self.assertEqual(source.api_env(), {"KICAD_API_SOCKET": "ipc://" + sources.instances.own_socket(2344),
                                            "KICAD_API_TOKEN": ""})
        self.assertEqual(source.unreachable_reason(), sources.RESTART_HINT)
        self.assertIn("restart this KiCad", source.unreachable_status())

    def test_kicad_with_its_own_socket_connects_there(self):
        try:
            import kipy  # noqa: F401
        except ImportError as exc:
            self.skipTest(f"needs kicad-python: {exc}")
        window = types.SimpleNamespace(pipe_names=lambda: {self.shared, self.own},
                                       pipe_server=lambda path: 11632)
        old, sources.kicad_window = sources.kicad_window, window
        self.addCleanup(setattr, sources, "kicad_window", old)
        source = sources.KiCadSource("pcb", pid=2344)
        self.assertEqual(source.socket, "ipc://" + sources.instances.own_socket(2344))
        self.assertEqual(source.api_env()["KICAD_API_SOCKET"], source.socket)

    @unittest.skipUnless(os.name == "nt", "Windows process helpers")
    def test_process_helpers(self):
        from powerlab_assistant import kicad_window

        self.assertTrue(kicad_window.process_running(os.getpid()))
        self.assertEqual(kicad_window.processes()[os.getpid()][1].lower(),
                         os.path.basename(sys.executable).lower())
        self.assertEqual(kicad_window.kicad_ancestor(os.getpid()), 0)  # not started by KiCad


class McpPatchTests(unittest.TestCase):
    """Issue #10: fixes shipped as a patch on the pinned KiCad MCP server."""

    def patch(self):
        with open(os.path.join(ROOT, "patches", "kicad-mcp.patch"), encoding="utf-8") as f:
            return f.read()

    def new_file(self, name):
        text = self.patch().split(f"+++ b/{name}\n", 1)[1]
        body = text.split("\ndiff --git", 1)[0].split("\n")[1:]  # skip the @@ header
        return "\n".join(line[1:] for line in body if line.startswith("+"))

    def test_rotation_keeps_3d_models(self):
        patch = self.patch()
        self.assertIn("models = list(target_fp.definition.models)", patch)
        self.assertIn("target_fp.definition.add_item(model)", patch)

    def test_pours_work_in_live_mode(self):
        """Issue #12: live add_copper_pour ignored "outline" and add_zone had no handler."""
        patch = self.patch()
        self.assertIn('points = params.get("outline") or params.get("points") or []', patch)
        self.assertIn("box = self.ipc_board_api.edge_cuts_box()", patch)
        self.assertIn('+        "add_zone": "_ipc_add_copper_pour",', patch)
        self.assertIn('+            "add_zone": self._handle_add_zone,', patch)

    def test_board_views_are_coloured_and_kept(self):
        """Visual review: colour 2D views, true aspect ratio, numbered output files."""
        patch = self.patch()
        self.assertIn('*([] if color else ["--black-and-white"])', patch)
        self.assertIn("zoom = min(width / page.rect.width, height / page.rect.height)", patch)
        self.assertIn("output_path = output_path_param or", patch)
        self.assertIn("outputPath,", patch)  # passed through by the TypeScript tool

    def test_stitching_vias_work_in_live_mode(self):
        """Issue #14: add_gnd_stitching_vias said "No board is loaded" with KiCad open."""
        patch = self.patch()
        self.assertIn('+        "add_gnd_stitching_vias": "_ipc_add_gnd_stitching_vias",', patch)
        self.assertIn("def _ipc_add_gnd_stitching_vias", patch)
        self.assertIn('plan_params["clearance"] = max(', patch)  # net-class clearance, not a fixed 0.2

    def test_footprint_text_moves_in_live_mode(self):
        """Issue #36: move_footprint_text edited the offline copy, and saves dropped the move."""
        patch = self.patch()
        self.assertIn('+        "move_footprint_text": "_ipc_move_footprint_text",', patch)
        self.assertIn("def _ipc_move_footprint_text", patch)
        self.assertIn("+            board.update_items([target_fp])\n+            board.push_commit(commit, f\"Moved {reference} {field} text\")", patch)

    def test_pour_nets_are_left_out_of_routing(self):
        module = types.ModuleType("pour_nets")
        exec(self.new_file("python/commands/pour_nets.py"), module.__dict__)
        dsn = """(pcb test
  (structure
    (layer F.Cu (type signal))
    (plane GND (polygon B.Cu 0 0 0 100 0 100 100 0 100))
    (plane VBUS (polygon F.Cu 0 0 0 10 0 10 10 0 10))
  )
  (network
    (net GND (pins U1-1 C1-2))
    (net SIG (pins U1-2 R1-1))
    (class kicad_default "" GND SIG
      (rule (width 200) (clearance 200))
    )
  )
  (wiring
    (wire (path B.Cu 500 0 0 10 0) (net GND) (type protect))
    (wire (path F.Cu 200 0 5 10 5) (net SIG))
  )
)"""
        out, dropped = module.leave_to_pours(dsn, ["GND"])
        self.assertEqual(dropped, 1)
        self.assertNotIn("(plane GND", out)
        self.assertIn("(plane VBUS", out)  # other pours stay
        self.assertNotIn("(net GND (pins", out)
        self.assertIn("(net SIG (pins U1-2 R1-1))", out)
        self.assertIn("(class kicad_default \"\" SIG", out)
        self.assertIn(f"(net {module.PLACEHOLDER_NET})", out)  # GND wire kept as an obstacle
        self.assertEqual(out.count("("), out.count(")"))

        # keepout pour nets: not routed, and their pours become keepouts
        out, dropped = module.leave_to_pours(dsn, ["GND"], ["VBUS"])
        self.assertNotIn("(plane VBUS", out)
        self.assertIn('(keepout "" (polygon F.Cu 0 0 0 10 0 10 10 0 10))', out)
        self.assertEqual(out.count("("), out.count(")"))

    def test_live_autoroute_copper(self):
        """Live autoroute: partial results replace each other in KiCad; locked copper stays."""
        try:
            import pcbnew
            from kipy.board_types import Track, Via
            from kipy.geometry import Vector2
            from kipy.proto.board.board_types_pb2 import BoardLayer
        except ImportError:
            self.skipTest("needs KiCad's Python with kipy")
        patch = self.patch()
        self.assertIn('"autoroute": self._handle_autoroute,', patch)
        self.assertIn("for idx in range(0 if live else attempts):", patch)
        self.assertIn("--api_server.authentication.enabled=false", patch)
        module = types.ModuleType("freerouting_live")
        exec(self.new_file("python/commands/freerouting_live.py"), module.__dict__)

        # The same track has the same key on both sides, whichever way round it's drawn
        board = pcbnew.BOARD()
        net = pcbnew.NETINFO_ITEM(board, "SIG")
        board.Add(net)
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(3000000, 1000000)); t.SetEnd(pcbnew.VECTOR2I(1000000, 1000000))
        t.SetWidth(200000); t.SetLayer(pcbnew.B_Cu); t.SetNet(net)
        board.Add(t)
        (key, spec), = module.pcbnew_copper(board).items()
        k = Track()
        k.start, k.end = Vector2.from_xy(1000000, 1000000), Vector2.from_xy(3000000, 1000000)
        k.width, k.layer = 200000, BoardLayer.BL_B_Cu
        self.assertEqual(module.kipy_key(k)[:-1], key[:-1])  # the kipy track has no net
        self.assertEqual(key[-1], "SIG")
        self.assertEqual(module.pcbnew_copper(board, ["SIG"]), {})

        class FakeBoard:
            def __init__(self):
                self.items, self.commits = [], 0
            def get_nets(self):
                return []
            def begin_commit(self):
                return object()
            def push_commit(self, commit, message):
                self.commits += 1
            def create_items(self, items):
                self.items += items
                return items
            def remove_items(self, items):
                self.items = [i for i in self.items if all(i is not r for r in items)]
            def get_tracks(self):
                return [i for i in self.items if isinstance(i, Track)]
            def get_vias(self):
                return [i for i in self.items if isinstance(i, Via)]

        def track(x):
            spec = {"kind": "track", "layer": "F.Cu", "start": (x, 0), "end": (x, 1000), "width": 200, "net": ""}
            return ("t", "F.Cu", x, 0, x, 1000, 200, ""), spec
        via = (("v", 5, 5, 600, 300, ""), {"kind": "via", "pos": (5, 5), "dia": 600, "drill": 300, "net": ""})
        fake = FakeBoard()
        locked = Track()
        locked.start, locked.end = Vector2.from_xy(9, 0), Vector2.from_xy(9, 1000)
        locked.width, locked.layer, locked.locked = 200, BoardLayer.BL_F_Cu, True
        fake.items.append(locked)
        copper = module.LiveCopper(fake)
        copper.show(dict([track(1), track(2)]))
        copper.show(dict([track(2), track(3), via]))
        self.assertEqual(sorted(copper.shown), sorted([track(2)[0], track(3)[0], via[0]]))
        self.assertEqual(len(fake.items), 4)  # the locked track and this run's three items
        copper.show(dict([track(2), track(3), via]))  # nothing new: no commit
        self.assertEqual(fake.commits, 2)
        result = copper.finish(dict([track(3), track(4)]))  # final result
        self.assertEqual(result, {"added": 1, "removed": 2, "locked_kept": 1})
        self.assertEqual(sorted(module.kipy_key(i) for i in fake.items),
                         sorted([track(3)[0], track(4)[0], track(9)[0]]))
        copper.clear()  # after finish there's nothing left to take back
        self.assertEqual(len(fake.items), 3)

    def test_session_vias_keep_their_annular_ring(self):
        self.assertIn("via_drills = _repair_via_drills(self.board)", self.patch())

    def test_powerlab_router_rules(self):
        """Milestone 1: clearance rules from .kicad_dru, last match wins, unknown terms only
        ever make the clearance larger."""
        module = types.ModuleType("rules")
        exec(self.new_file("python/commands/powerlab_router/rules.py"), module.__dict__)
        rules = module.Rules.parse('''(version 1)
(rule "Fine-pitch pads"
	(condition "A.Type == 'Pad' && (A.memberOfFootprint('U3') || A.memberOfFootprint('J*'))")
	(constraint clearance (min 0.15mm)))
(rule "Thin power tracks"
	(condition "A.Type == 'Track' && A.Width <= 0.25mm && A.hasNetclass('Power')")
	(constraint clearance (min 0.2mm)))
(rule "Pads of one part"
	(condition "A.Type == 'Pad' && B.Type == 'Pad'")
	(constraint clearance (min 0.1mm)))
(rule "HV inner" (layer inner)
	(condition "A.hasNetclass('HV') || B.hasNetclass('HV')")
	(constraint clearance (min 0.4mm)))
(rule "Fan-out areas"
	(condition "A.intersectsArea('FANOUT') && !(A.NetName == 'GND')")
	(constraint clearance (min 0.5mm)))
(rule "Ignored" (severity ignore)
	(condition "A.Type == 'Via'")
	(constraint clearance (min 3mm)))
''')
        track = {"Type": "Track", "NetClass": "Default", "NetName": "IO2", "Width": 0.2, "Footprint": None}
        u3 = {"Type": "Pad", "NetClass": "Power", "NetName": "+3V3", "Footprint": "U3"}
        j1 = {"Type": "Pad", "NetClass": "Default", "NetName": "CC1", "Footprint": "J1"}
        u1 = {"Type": "Pad", "NetClass": "Power", "NetName": "+3V3", "Footprint": "U1"}
        thin = {"Type": "Track", "NetClass": "Power", "NetName": "+3V3", "Width": 0.25, "Footprint": None}
        hv = {"Type": "Track", "NetClass": "HV", "NetName": "VBUS", "Width": 0.5, "Footprint": None}
        gnd = {"Type": "Track", "NetClass": "GND", "NetName": "GND", "Width": 0.3, "Footprint": None}
        self.assertEqual(rules.unsupported, ["Fan-out areas"])
        # the fan-out rule might match anything but GND, so it raises other clearances to 0.5
        self.assertEqual(rules.clearance(track, u3, "F.Cu", 0.3), 0.5)
        drop = module.Rules(r for r in rules.rules if r.name != "Fan-out areas")
        self.assertEqual(drop.clearance(track, u3, "F.Cu", 0.3), 0.15)  # wildcard and ||
        self.assertEqual(drop.clearance(track, j1, "F.Cu", 0.3), 0.15)
        self.assertEqual(drop.clearance(track, u1, "F.Cu", 0.3), 0.3)  # no rule: net classes
        self.assertEqual(drop.clearance(track, thin, "F.Cu", 0.3), 0.2)
        self.assertEqual(drop.clearance(u3, j1, "F.Cu", 0.3), 0.1)  # pad-pad, the later rule
        self.assertEqual(drop.clearance(track, hv, "F.Cu", 0.3), 0.3)  # layer clause
        self.assertEqual(drop.clearance(track, hv, "In1.Cu", 0.3), 0.4)
        self.assertEqual(rules.clearance(gnd, track, "F.Cu", 0.3), 0.5)  # B side may match
        self.assertEqual(rules.clearance(gnd, dict(gnd), "F.Cu", 0.3), 0.3)  # !(GND): can't match

    def test_powerlab_router_groups(self):
        """Milestone 1: nets sorted into the lab's routing order (§3.4)."""
        module = types.ModuleType("groups")
        exec(self.new_file("python/commands/powerlab_router/groups.py"), module.__dict__)
        classes = {"+3V3": "Power", "GND": "GND", "USB_DP": "USB", "USB_DN": "USB"}
        nets = ["+3V3", "GND", "VBUS", "/Gate Drive/GHA", "SPI_SCK", "CAN_H", "CAN_L", "USB_DP", "USB_DN",
                "/Sense/IBUS_SNS_P", "SENSOR_VP", "SENSOR_VN", "IO12", "Net-(SW1-Pad2)", "Net-(R5-Pad1)"]
        got = module.classify(nets, lambda n: classes.get(n, "Default"), {"IO12": "sensitive analog"})
        names = {n: module.GROUPS[g] for n, g in got.items()}
        self.assertEqual(names["+3V3"], "power")
        self.assertEqual(names["GND"], "power")
        self.assertEqual(names["VBUS"], "power")
        self.assertEqual(names["/Gate Drive/GHA"], "switching and clocks")
        self.assertEqual(names["SPI_SCK"], "switching and clocks")
        self.assertEqual(names["CAN_H"], "differential pairs")
        self.assertEqual(names["USB_DN"], "differential pairs")
        self.assertEqual(names["SENSOR_VP"], "sensitive analog")  # not a pair: VP/VN
        self.assertEqual(names["IO12"], "sensitive analog")  # the user's choice
        self.assertEqual(names["Net-(SW1-Pad2)"], "other")  # automatic names go by class only

    def test_powerlab_router_search(self):
        """docs/powerlab-router-plan.md milestone 0: 45 degree turns only, spaced apart,
        arrival straight along the goal pad's lane, and a via when one layer is walled off."""
        module = types.ModuleType("search")
        exec(self.new_file("python/commands/powerlab_router/search.py"), module.__dict__)
        nx = ny = 40

        def grid(wall=None):
            cells = bytearray(nx * ny)
            for i, j in wall or ():
                cells[j * nx + i] = 1
            return cells

        def check_turns(path, min_run):
            run = min_run
            for a, b in zip(path, path[1:]):
                if a[2] != b[2] or a[3] == module.FREE or b[3] == module.FREE:
                    run = min_run
                    continue
                turn = (b[3] - a[3]) % 8
                self.assertIn(turn, (0, 1, 7))  # never more than 45 degrees in one step
                if turn:
                    self.assertGreaterEqual(run, min_run)  # two bends never sit together
                    run = 1
                else:
                    run += 1

        costs = module.Costs(turn=0.4, via=2.0, min_run=2)
        # start heading east at (2, 2); the goal pad is entered heading south at (30, 30)
        wall = [(10, j) for j in range(0, 30)]  # a wall forces the path around
        path, stats = module.search([grid(wall)], grid(), nx, ny, 0.1, [(2, 2, 0, 0, 0.0)],
                                    {(30, 30, 0): (2, 0.0)}, (0, 0, nx - 1, ny - 1), costs)
        self.assertIsNotNone(path)
        self.assertEqual(path[-1][:4], (30, 30, 0, 2))
        check_turns(path, 2)
        self.assertTrue(all(i != 10 or j >= 30 for i, j, *_ in path))

        # layer 0 walled off completely: the path takes a via to layer 1 and arrives there
        wall = [(20, j) for j in range(ny)]
        vias_ok = bytes([1]) * (nx * ny)
        path, _ = module.search([grid(wall), grid()], vias_ok, nx, ny, 0.1, [(2, 20, 0, 0, 0.0)],
                                {(35, 20, 1): (0, 0.0)}, (0, 0, nx - 1, ny - 1), costs)
        self.assertIsNotNone(path)
        self.assertEqual({s[2] for s in path}, {0, 1})
        check_turns(path, 2)

        # no via allowed: no path
        path, _ = module.search([grid(wall), grid()], bytes(nx * ny), nx, ny, 0.1, [(2, 20, 0, 0, 0.0)],
                                {(35, 20, 1): (0, 0.0)}, (0, 0, nx - 1, ny - 1), costs)
        self.assertIsNone(path)

    def test_autoroute_can_be_undone(self):
        """File > Revert loads the routed file, so autoroute keeps the board from before it."""
        patch = self.patch()
        self.assertIn('result["backupPath"] = autoroute_backup.keep(before_path, board_path)', patch)
        self.assertIn('+            "undo_autoroute": self._handle_undo_autoroute,', patch)
        self.assertIn('"check_freerouting", "clean_up_routing", "undo_autoroute"]', patch)
        module = types.ModuleType("autoroute_backup")
        exec(self.new_file("python/commands/autoroute_backup.py"), module.__dict__)

        folder = tempfile.mkdtemp()
        board = os.path.join(folder, "b.kicad_pcb")
        before = os.path.join(folder, "staged.kicad_pcb")
        with open(before, "w") as f:
            f.write("unrouted")
        with open(board, "w") as f:
            f.write("routed")
        self.assertFalse(module.restore(board)["success"])  # no run yet
        self.assertEqual(module.keep(before, board), os.path.join(folder, "autoroute-backup", "b.kicad_pcb"))
        self.assertTrue(module.restore(board)["success"])
        with open(board) as f:
            self.assertEqual(f.read(), "unrouted")
        self.assertFalse(os.path.exists(os.path.join(folder, "autoroute-backup")))
        self.assertFalse(module.restore(board)["success"])  # once only

    def test_clean_up_routing(self):
        """Post-route clean-up: stubs, dead ends, net-class widths and 90 degree corners."""
        try:
            import pcbnew
        except ImportError:
            self.skipTest("needs KiCad's Python")
        cli = os.path.join(os.path.dirname(sys.executable), "kicad-cli.exe")
        if not os.path.isfile(cli):
            self.skipTest("needs kicad-cli")
        module = types.ModuleType("route_cleanup")
        exec(self.new_file("python/commands/route_cleanup.py"), module.__dict__)
        self.assertIn('"clean_up_routing": self._handle_clean_up_routing,', self.patch())

        mm, P = pcbnew.FromMM, lambda x, y: pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
        board = pcbnew.BOARD()
        net = pcbnew.NETINFO_ITEM(board, "SIG")
        board.Add(net)
        for a, b in (((0, 0), (40, 0)), ((40, 0), (40, 40)), ((40, 40), (0, 40)), ((0, 40), (0, 0))):
            edge = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
            edge.SetStart(P(*a)); edge.SetEnd(P(*b)); edge.SetLayer(pcbnew.Edge_Cuts); edge.SetWidth(mm(0.1))
            board.Add(edge)
        for x, y in ((10, 10), (25, 20)):
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(P(x, y)); via.SetWidth(mm(0.6)); via.SetDrill(mm(0.3)); via.SetNet(net)
            board.Add(via)
        path = [(10, 10), (20, 10), (20, 15), (20.05, 15.05), (25, 20)]  # 90 degree corner, 0.07 mm stub
        segments = list(zip(path, path[1:])) + [((25, 20), (30, 25)), ((20, 30), (20, 30))]  # dead end, zero length
        for a, b in segments:
            track = pcbnew.PCB_TRACK(board)
            track.SetStart(P(*a)); track.SetEnd(P(*b)); track.SetWidth(mm(0.15))
            track.SetLayer(pcbnew.F_Cu); track.SetNet(net)
            board.Add(track)
        folder = tempfile.mkdtemp()
        path = os.path.join(folder, "cleanup.kicad_pcb")
        board.Save(path)
        board = pcbnew.LoadBoard(path)
        class_width = board.GetDesignSettings().m_NetSettings.GetEffectiveNetClass("SIG").GetTrackWidth()

        report = module.clean_up(board, path, cli)
        self.assertEqual(report["stubs"], {"zero_length": 1, "merged_into_pad": 0, "joined": 1, "put_back": 0})
        self.assertEqual(report["dangling"]["removed"], 1)
        self.assertEqual(report["widths"]["full_width"], 3)
        self.assertEqual(report["miter"]["mitered"], 1)
        self.assertEqual(report["sharp_corners_left"]["count"], 0)
        self.assertEqual(report["thin_tracks_left"]["count"], 0)
        tracks = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
        self.assertEqual(len(tracks), 4)  # two legs, the chamfer and the diagonal
        self.assertTrue(all(t.GetWidth() == class_width for t in tracks))


class PanelDefaultsTests(unittest.TestCase):
    """panel.py needs wx.html2, so read its constants without importing it."""

    def constants(self):
        import ast
        with open(os.path.join(ROOT, "plugin", "powerlab_assistant", "panel.py"), encoding="utf-8") as f:
            tree = ast.parse(f.read())
        found = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
                try:
                    found[node.targets[0].id] = ast.literal_eval(node.value)
                except ValueError:
                    pass
        return found

    def test_default_is_opus_high_effort(self):
        c = self.constants()
        self.assertEqual(c["DEFAULT_MODEL"], "claude-opus-5-5")
        self.assertEqual(c["DEFAULT_EFFORT"], "high")
        self.assertIn(c["DEFAULT_EFFORT"], c["EFFORTS"])
        self.assertEqual(c["MODELS"][0][0], c["DEFAULT_MODEL"])
        self.assertIn("powerlab-pcb-design-rules", "".join(c["PANEL_NOTE"]))
        self.assertIn("Never ask the user to close", c["PANEL_NOTE"])  # issue #10
        self.assertIn("the chat is kept", c["PANEL_NOTE"])
        self.assertIn("powerlab-visual-review", c["PANEL_NOTE"])  # look at the board while working
        self.assertIn("powerlab-board-requirements", c["PANEL_NOTE"])  # ask before a new board
        self.assertIn("design-requirements.md", c["PANEL_NOTE"])
        self.assertIn("<choices>", c["PANEL_NOTE"])  # questions come back as answer buttons
        self.assertIn("never add an 'Other'", c["PANEL_NOTE"])  # the card has its own Other…
        # Issue #27: file-only tools (get_design_rules) say "No board is loaded" with KiCad open
        self.assertIn('says "No board is loaded"', c["PANEL_NOTE"])
        self.assertIn("call open_board with the 'Board file' path", c["PANEL_NOTE"])
        # Issue #53: the error still showed first; load the file before the first such call
        self.assertIn("Before the first get_design_rules call in a chat, call open_board",
                      c["PANEL_NOTE"])

    def test_board_views_get_the_board_path(self):
        # Issue #52: get_board_2d_view failed with "pcbPath required" when KiCad had the board
        # open: the tool process has no board loaded, so the path has to be passed.
        c = self.constants()
        self.assertIn("get_board_2d_view, always pass pcbPath: the 'Board file' path",
                      c["PANEL_NOTE"])

    def test_gerbers_can_be_zipped(self):
        # Issue #24: PCBWay wants the Gerbers zipped, but only kicad-cli was allowed in the shell.
        c = self.constants()
        # Compress-Archive is blocked by Claude Code as a file write; Windows' tar is not.
        self.assertIn("PowerShell(tar -a -cf:*)", c["ALLOWED_TOOLS"])
        self.assertNotIn("PowerShell(tar:*)", c["ALLOWED_TOOLS"])  # never extraction
        self.assertIn(r"tar -a -cf fab\gerbers.zip -C fab\gerbers *", c["PANEL_NOTE"])

    def test_files_are_read_with_tools_not_the_shell(self):
        # Issue #29: Claude ran `cd ...; grep ...` in Bash to search a project file, and the
        # panel blocked it. Shell grep/cat/cd aren't allowed, so it must use Read/Grep/Glob.
        c = self.constants()
        self.assertNotIn("Bash", c["ALLOWED_TOOLS"])
        self.assertIn("Read, Grep and Glob tools", c["PANEL_NOTE"])
        self.assertIn("never with shell commands", c["PANEL_NOTE"])

    def test_board_minimums_are_the_pcbway_floor(self):
        with open(os.path.join(ROOT, "skills", "powerlab-pcb-design-rules", "SKILL.md"), encoding="utf-8") as f:
            rules = f.read()
        self.assertIn("| Minimum track width | 0.15 mm |", rules)
        self.assertIn("| Default | 0.2 mm | 0.2 mm |", rules)  # lab default stays in the net class

    def test_page_scripts_never_run_synchronously(self):
        # A burst of tool events nested synchronous RunScript calls, each waiting in its
        # own event loop, until the panel froze at 100% CPU and outlived KiCad.
        import re
        with open(os.path.join(ROOT, "plugin", "powerlab_assistant", "panel.py"), encoding="utf-8") as f:
            source = f.read()
        self.assertIn(".RunScriptAsync(", source)
        self.assertEqual(re.findall(r"\.RunScript\(", source), [])

    def test_user_can_follow_the_work(self):
        c = self.constants()
        self.assertIn("one long silent think", c["PANEL_NOTE"])  # a running commentary instead
        self.assertIn(c["DEFAULT_MODEL"], c["SUMMARY_MODELS"])  # thinking shown live
        # Haiku 4.5 answers "400 adaptive thinking is not supported on this model".
        self.assertFalse(any("haiku-4" in m for m in c["SUMMARY_MODELS"]))

    def test_files_are_not_parsed_with_scripts(self):
        # Issue #30: Claude ran `python -c` to parse a saved get_pads result, which is blocked.
        c = self.constants()
        self.assertIn("Never run a script (python -c", c["PANEL_NOTE"])
        self.assertIn("Read tool in parts (offset and limit)", c["PANEL_NOTE"])
        self.assertFalse(any(t.startswith(("Bash(python", "PowerShell(python")) for t in c["ALLOWED_TOOLS"]))

    def test_grep_patterns_are_ripgrep_syntax(self):
        # Issue #34: Claude gave Grep a look-ahead `(?!...)`, which ripgrep rejects.
        c = self.constants()
        self.assertIn("Grep uses ripgrep", c["PANEL_NOTE"])
        self.assertIn("no look-ahead, look-behind", c["PANEL_NOTE"])


class LibraryCommitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        sh(self.repo, "git", "init", "-q", "-b", "main")
        sh(self.repo, "git", "config", "user.email", "test@example.com")
        sh(self.repo, "git", "config", "user.name", "Test")
        os.makedirs(os.path.join(self.repo, "symbols"))
        self.write("symbols/METUPowerLab_A.kicad_sym", "a")
        self.write("README.md", "readme")
        sh(self.repo, "git", "add", "-A")
        sh(self.repo, "git", "commit", "-q", "-m", "init")
        config.library_path = lambda: self.repo

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        with open(os.path.join(self.repo, rel), "w") as f:
            f.write(text)

    def git(self, *args):
        return subprocess.run(["git", "-C", self.repo, *args], capture_output=True, text=True).stdout.strip()

    def test_commit_has_only_chosen_files_and_checkout_untouched(self):
        self.write("symbols/METUPowerLab_B.kicad_sym", "b")  # new part to share
        self.write("README.md", "local edit, not shared")  # outside the library folders
        head = self.git("rev-parse", "HEAD")
        before = self.git("status", "--porcelain")

        changed = library.changed_files(self.repo)
        self.assertEqual([f["path"] for f in changed], ["symbols/METUPowerLab_B.kicad_sym"])

        ok, sha = library.build_commit(self.repo, ["symbols/METUPowerLab_B.kicad_sym"], "Add B", "someone")
        self.assertTrue(ok, sha)
        files = self.git("diff-tree", "--no-commit-id", "--name-only", "-r", sha).splitlines()
        self.assertEqual(files, ["symbols/METUPowerLab_B.kicad_sym"])
        self.assertEqual(self.git("rev-parse", f"{sha}^"), head)
        self.assertEqual(self.git("rev-parse", "HEAD"), head)  # branch not moved
        self.assertEqual(self.git("status", "--porcelain"), before)  # working copy untouched


class LibraryUpdateTests(unittest.TestCase):
    """Issue #4: after your shared parts are merged, Update must accept the local copies
    (an edited tracked file and a new untracked file) that equal what's on GitHub."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = self.tmp.name
        self.remote = os.path.join(root, "remote.git")
        self.mine = os.path.join(root, "mine")
        theirs = os.path.join(root, "theirs")
        sh(root, "git", "init", "-q", "--bare", "-b", "main", self.remote)
        sh(root, "git", "clone", "-q", self.remote, theirs)
        for repo in (theirs,):
            sh(repo, "git", "config", "user.email", "t@example.com")
            sh(repo, "git", "config", "user.name", "T")
        os.makedirs(os.path.join(theirs, "symbols"))
        os.makedirs(os.path.join(theirs, "footprints", "METUPowerLab_A.pretty"))
        self.write(theirs, "symbols/METUPowerLab_A.kicad_sym", "v1\n")
        sh(theirs, "git", "add", "-A"); sh(theirs, "git", "commit", "-q", "-m", "v1")
        sh(theirs, "git", "push", "-q", "origin", "main")
        sh(root, "git", "clone", "-q", self.remote, self.mine)
        # The user's shared change gets merged upstream...
        self.write(theirs, "symbols/METUPowerLab_A.kicad_sym", "v1\nnew part\n")
        self.write(theirs, "footprints/METUPowerLab_A.pretty/SOT-23-5.kicad_mod", "fp\n")
        sh(theirs, "git", "add", "-A"); sh(theirs, "git", "commit", "-q", "-m", "merged share")
        sh(theirs, "git", "push", "-q", "origin", "main")
        # ...while the user's clone still holds the same edits, uncommitted.
        self.write(self.mine, "symbols/METUPowerLab_A.kicad_sym", "v1\nnew part\n")
        self.write(self.mine, "footprints/METUPowerLab_A.pretty/SOT-23-5.kicad_mod", "fp\n")
        self.saved = (config.library_path, library.register_new_libraries)
        config.library_path = lambda: self.mine
        library.register_new_libraries = lambda path: []  # don't touch the real KiCad tables

    def tearDown(self):
        config.library_path, library.register_new_libraries = self.saved
        self.tmp.cleanup()

    def write(self, repo, rel, text):
        os.makedirs(os.path.dirname(os.path.join(repo, rel)), exist_ok=True)
        with open(os.path.join(repo, rel), "w", newline="\n") as f:
            f.write(text)

    def git(self, *args):
        return subprocess.run(["git", "-C", self.mine, *args], capture_output=True, text=True).stdout.strip()

    def test_update_after_own_share_was_merged(self):
        ok, info = library.update()
        self.assertTrue(ok, info)
        self.assertEqual(self.git("rev-parse", "HEAD"), self.git("rev-parse", "origin/main"))
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_update_keeps_edits_that_github_does_not_have(self):
        self.write(self.mine, "symbols/METUPowerLab_A.kicad_sym", "v1\nnew part\nmy unshared edit\n")
        ok, info = library.update()
        self.assertFalse(ok)
        with open(os.path.join(self.mine, "symbols/METUPowerLab_A.kicad_sym")) as f:
            self.assertIn("my unshared edit", f.read())  # never thrown away


class ContributeCommandTests(unittest.TestCase):
    """The Share flow's gh/git commands, with gh and the network mocked out."""

    def test_fork_push_and_pr_commands(self):
        calls = []

        def fake_run(args, cwd=None, timeout=60, extra_env=None):
            calls.append(args)
            if args[1:3] == ["pr", "create"]:
                return 0, "https://github.com/odtu/PowerLabKiCadLibraries/pull/99"
            return 0, ""

        saved = (library.run_quiet, library.find_gh, library.build_commit, config.library_path)
        library.run_quiet = fake_run
        library.find_gh = lambda: r"C:\Program Files\GitHub CLI\gh.exe"
        library.build_commit = lambda path, paths, message, login: (True, "abc123")
        config.library_path = lambda: "C:/lib"
        try:
            ok, url = library.contribute("Add X", "desc", [{"status": "??", "path": "symbols/METUPowerLab_X.kicad_sym"}], "someone")
        finally:
            library.run_quiet, library.find_gh, library.build_commit, config.library_path = saved

        self.assertTrue(ok, url)
        self.assertTrue(url.endswith("/pull/99"))
        fork = next(c for c in calls if c[1:3] == ["repo", "fork"])
        # gh rejects --remote together with a repository argument (issue #2).
        self.assertFalse(any(a.startswith("--remote") for a in fork), fork)
        self.assertIn("--clone=false", fork)
        push = next(c for c in calls if "push" in c)
        self.assertEqual(push[-2], "https://github.com/someone/PowerLabKiCadLibraries.git")
        self.assertTrue(push[-1].startswith("abc123:refs/heads/library/someone-"))
        pr = next(c for c in calls if c[1:3] == ["pr", "create"])
        self.assertIn("someone:" + push[-1].split("refs/heads/")[1], pr)

    def test_error_line_skips_usage_text(self):
        out = ("the `--remote` flag is unsupported when a repository argument is provided\n\n"
               "Usage:  gh repo fork [<repository>] [-- <gitflags>...] [flags]\n\nFlags:\n"
               "  --clone   Clone the fork\n  --remote  Add a git remote for the fork\n")
        self.assertEqual(library.error_line(out),
                         "the `--remote` flag is unsupported when a repository argument is provided")


class UpdateCheckTests(unittest.TestCase):
    def release(self, tag, body="## 0.9.0\n\n- Fixes library Share\n- Other things"):
        return lambda: {"tag_name": tag, "body": body, "html_url": f"https://example.invalid/{tag}"}

    def stable(self, version):
        return lambda: version

    def no_release(self):
        return self.fail("asked the GitHub API for release notes without a newer version")

    def test_newer_stable_version_is_offered_and_answer_cached_briefly(self):
        settings = {}
        result = updates.check(settings, fetch_version=self.stable("99.0.0"), fetch_release=self.release("v99.0.0"))
        self.assertTrue(result["available"])
        self.assertEqual(result["version"], "99.0.0")
        self.assertEqual(result["summary"], "Fixes library Share")
        self.assertEqual(result["url"], "https://example.invalid/v99.0.0")
        # Shortly after, the cached answer is reused: GitHub isn't asked again.
        again = updates.check(settings, fetch_version=lambda: self.fail("asked GitHub again within CHECK_EVERY"),
                              fetch_release=lambda: self.fail("asked for the notes again"))
        self.assertTrue(again["available"])
        self.assertEqual(again["summary"], "Fixes library Share")

    def test_stable_release_is_seen_within_minutes(self):
        self.assertLessEqual(updates.CHECK_EVERY, 5 * 60)
        settings = {}
        updates.check(settings, fetch_version=self.stable(config.VERSION), fetch_release=self.no_release)
        settings["update_checked"] -= updates.CHECK_EVERY + 1  # a few minutes later, main moved
        self.assertTrue(updates.check(settings, fetch_version=self.stable("99.0.0"),
                                      fetch_release=self.release("v99.0.0"))["available"])

    def test_version_is_read_from_stable_branch_without_the_api(self):
        self.assertIn("raw.githubusercontent.com", updates.VERSION_URL)
        self.assertIn("/main/plugin/powerlab_assistant/config.py", updates.VERSION_URL)
        with open(config.__file__, encoding="utf-8") as f:
            self.assertEqual(updates.version_in(f.read()), config.VERSION)
        self.assertEqual(updates.version_in('NOTICE_VERSION = 1\nVERSION = "1.2.3"  # bump\n'), "1.2.3")
        self.assertEqual(updates.version_in("nothing here"), "")

    def test_notes_wait_until_the_release_is_published(self):
        settings = {}
        # main has 99.0.0, but its GitHub release isn't out yet: the latest is the previous one.
        early = updates.check(settings, fetch_version=self.stable("99.0.0"), fetch_release=self.release("v0.1.0"))
        self.assertTrue(early["available"])
        self.assertEqual(early["summary"], "")  # not the previous release's notes
        self.assertTrue(early["url"].endswith("/releases"))
        # Within CHECK_EVERY the version is cached, but the notes are asked for again.
        later = updates.check(settings, fetch_version=lambda: self.fail("asked GitHub again within CHECK_EVERY"),
                              fetch_release=self.release("v99.0.0"))
        self.assertEqual(later["summary"], "Fixes library Share")

    def test_release_notes_failure_still_offers_the_update(self):
        def offline():
            raise OSError("no network")
        result = updates.check({}, fetch_version=self.stable("99.0.0"), fetch_release=offline)
        self.assertTrue(result["available"])
        self.assertEqual(result["summary"], "")

    def test_notes_of_an_older_version_are_dropped(self):
        settings = {"update_checked": 0, "update_cache": {"version": "v98.0.0", "summary": "Old notes", "url": "x"}}
        result = updates.check(settings, fetch_version=self.stable("99.0.0"), fetch_release=self.release("v98.0.0"))
        self.assertEqual(result["version"], "99.0.0")
        self.assertEqual(result["summary"], "")

    def test_same_or_older_version_is_not_offered(self):
        for version in (config.VERSION, "0.0.1", "", "not-a-version"):
            self.assertFalse(updates.check({}, fetch_version=self.stable(version),
                                           fetch_release=self.no_release)["available"], version)

    def test_version_order_is_numeric(self):
        self.assertGreater(updates.parse_version("v0.10.0"), updates.parse_version("v0.9.9"))
        self.assertEqual(updates.parse_version("v0.2"), (0, 2, 0))
        self.assertGreater(updates.parse_version("v0.2"), updates.parse_version("0.1.4"))


class LibTableTests(unittest.TestCase):
    def test_repoints_pcm_entries_and_adds_missing(self):
        with tempfile.TemporaryDirectory() as lib, tempfile.TemporaryDirectory() as cfg:
            os.makedirs(os.path.join(lib, "symbols"))
            for name in ("METUPowerLab_A", "METUPowerLab_B"):
                open(os.path.join(lib, "symbols", name + ".kicad_sym"), "w").close()
            table = os.path.join(cfg, "sym-lib-table")
            with open(table, "w") as f:
                f.write('(sym_lib_table\n  (version 7)\n'
                        '  (lib (name "METUPowerLab_A")(type "KiCad")(uri "${KICAD10_3RD_PARTY}/symbols/x/METUPowerLab_A.kicad_sym")(options "")(descr ""))\n'
                        '  (lib (name "Device")(type "KiCad")(uri "${KICAD10_SYMBOL_DIR}/Device.kicad_sym")(options "")(descr ""))\n)\n')
            text, repointed, missing = configure_kicad.update_table(
                table, lib, "symbols", ".kicad_sym", "METUPOWERLAB_SYMBOLS")
            self.assertEqual(repointed, 1)
            self.assertEqual(missing, ["METUPowerLab_B"])
            self.assertIn('(uri "${METUPOWERLAB_SYMBOLS}/METUPowerLab_A.kicad_sym")', text)
            self.assertIn('(uri "${KICAD10_SYMBOL_DIR}/Device.kicad_sym")', text)  # others untouched
            self.assertIn('(name "METUPowerLab_B")', text)
            self.assertTrue(text.rstrip().endswith(")"))


if __name__ == "__main__":
    unittest.main()
