"""Run with KiCad's Python (it has wx and pcbnew):

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" -m unittest discover -s tests -v
"""

import base64
import math
import os
import re
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
    """The tools the panel's Claude sessions get, and the ones they don't."""

    def test_freerouting_is_gone(self):
        # Since 1.0 routing is the PowerLab router's or by hand: no Java or Freerouting
        # downloads, no Freerouting environment, and the MCP's Freerouting tools are blocked
        from powerlab_assistant import common, panel
        saved = config.config
        config.config = lambda: {"java_home": "C:/nowhere", "freerouting_jar": "C:/nowhere.jar"}
        try:
            env = common.clean_env()
        finally:
            config.config = saved
        self.assertNotIn("FREEROUTING_JAR", env)
        for tool in ("mcp__kicad__autoroute", "mcp__kicad__check_freerouting", "mcp__kicad__import_ses",
                     "AskUserQuestion"):
            self.assertIn(tool, panel.DISALLOWED_TOOLS)
        with open(os.path.join(ROOT, "install.ps1"), encoding="utf-8") as f:
            install = f.read()
        self.assertNotIn("freerouting-2.4.1.jar", install)
        self.assertNotIn("temurin", install.lower())
        self.assertIn('$_.Name -eq "freerouting"', install)  # old copies are removed
        self.assertIn("PowerLab router", panel.PANEL_NOTE)
        self.assertIn("never offer it", panel.PANEL_NOTE)

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
        self.assertIn("powerlab-placement", names)
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
        # the first question, then the review without asking; no Freerouting
        self.assertIn("## 0. Ask first: by hand or the PowerLab router", route)
        self.assertIn("PowerLab router, then I fix its DRC errors by hand (Recommended)", route)
        self.assertIn("Always run the design review next, without asking", route)
        self.assertIn("Never offer it.", route)
        self.assertNotIn("autoroute`", route.replace("undo_autoroute`", ""))
        # GND pours with thermal reliefs; solid only for high-current pours; power rails as pours
        self.assertIn("GND pours connect pads with thermal reliefs", route)
        self.assertIn("powerPours", route)
        self.assertIn("No duplicate tracks", rules)
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
                 "show_review", "show_plan")

        class Fake:
            pass

        for name in names:
            setattr(Fake, name, getattr(ClaudePanel, name))
        panel = Fake()
        panel.source = types.SimpleNamespace(editor="pcb")
        panel.session_id, panel.chat_cwd, panel.events = None, None, []
        panel.retry, panel.stale_session, panel.proc = None, False, None
        panel.got_result, panel.watched, panel.image_reads = False, {}, {}
        panel.review_writes, panel.review_md, panel.plan_writes = {}, None, {}
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

    def test_written_block_plan_shows_as_a_card(self):
        import json
        panel = self.fake_panel()
        path = os.path.join(self.tmp.name, "placement", "block-plan.json")
        os.makedirs(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"title": "Plan", "blocks": [{"id": "a", "name": "A", "refs": ["U1"],
                                                    "rect": {"center": [0, 0], "size": [5, 5]}}]}, f)
        panel.handle({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "w", "name": "Write", "input": {"file_path": path, "content": "{}"}}]}})
        panel.handle({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "w"}]}})
        plans = [e for e in panel.emitted if e["kind"] == "plan"]
        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0]["blocks"][0]["loc"], "refs=U1")
        self.assertNotIn("svg", panel.events[-1])  # the chat keeps the path, not the drawing
        self.assertEqual(panel.events[-1]["path"], path)

    def test_plans_and_reviews_open_in_their_own_window(self):
        # The chat looked crowded with a block plan and a whole review in it: they are rows
        # with Open, which shows the card in a window of its own (one per file).
        panel = self.fake_panel()  # skips without wx.html2
        from powerlab_assistant import panel as panel_module
        panel.chat_cwd = self.project
        panel.card_windows = {}
        opened = []

        class Window:
            def __init__(self, owner, kind, path):
                opened.append((kind, path))
                self.shown = 0

            def Show(self):
                self.shown += 1

            def Raise(self):
                pass

        saved = panel_module.CardWindow
        panel_module.CardWindow = Window
        self.addCleanup(setattr, panel_module, "CardWindow", saved)
        files = {}
        for kind, rel in (("plan", "placement\\block-plan.json"), ("review", "design-review\\design-review.md")):
            files[kind] = os.path.join(self.project, *rel.split("\\"))
            os.makedirs(os.path.dirname(files[kind]), exist_ok=True)
            open(files[kind], "w").close()
        open_card = panel_module.ClaudePanel.msg_open_card
        open_card(panel, {"card": "plan", "path": files["plan"]})
        open_card(panel, {"card": "plan", "path": files["plan"]})  # the same window again
        open_card(panel, {"card": "review", "path": files["review"]})
        self.assertEqual(opened, [("plan", files["plan"]), ("review", files["review"])])
        self.assertEqual(panel.card_windows[("plan", os.path.normcase(files["plan"]))].shown, 2)
        open_card(panel, {"card": "plan", "path": files["review"]})  # not a plan
        open_card(panel, {"card": "script", "path": files["plan"]})
        self.assertEqual([e["level"] for e in panel.emitted], ["warn", "warn"])
        other = os.path.join(self.tmp.name, "other", "placement", "block-plan.json")
        os.makedirs(os.path.dirname(other))
        open(other, "w").close()
        open_card(panel, {"card": "plan", "path": other})  # another project's
        self.assertEqual(len(opened), 2)

        # A window keeps up with the busy state and with its own file, nothing else.
        window = types.SimpleNamespace(kind="review", path=files["review"], sent=[],
                                       FOLLOW=saved.FOLLOW)
        window.send = window.sent.append
        window.card = lambda: {"kind": "review", "path": files["review"], "body": "<p>x</p>"}
        follow = saved.follow
        for data in ({"kind": "busy", "value": True}, {"kind": "text", "text": "hi"},
                     {"kind": "plan_update", "path": files["plan"]},
                     {"kind": "review", "path": files["review"], "title": "t"}):
            follow(window, data)
        self.assertEqual([d["kind"] for d in window.sent], ["busy", "review"])
        self.assertEqual(window.sent[1]["body"], "<p>x</p>")  # a review without its body is built again
        # The panel passes its events on to its windows.
        window.follow = lambda data: follow(window, data)
        real = types.SimpleNamespace(card_windows={"w": window}, ready=False, pending=[])
        window.sent.clear()
        panel_module.ClaudePanel.emit(real, "busy", value=False)
        self.assertEqual(window.sent, [{"kind": "busy", "value": False}])
        with open(os.path.join(ROOT, "plugin", "powerlab_assistant", "panel.html"), encoding="utf-8") as f:
            page = f.read()
        self.assertEqual(page.count("<body>"), 1)  # CardWindow marks it as a window
        self.assertIn("const WINDOW = document.body.classList.contains('window');", page)
        self.assertIn("post({ type: 'open_card', card: kind, path: e.path })", page)
        self.assertIn("if (!WINDOW) { add(docCard(e, 'review'));", page)

    def test_tool_steps_and_views_fold_into_one_line(self):
        # Every tool call and render was its own row in the chat. A run of them is one
        # collapsed line ("5 steps · 1 view — Move component, ...") that opens into a small box.
        with open(os.path.join(ROOT, "plugin", "powerlab_assistant", "panel.html"), encoding="utf-8") as f:
            page = f.read()
        self.assertIn("toolGroup.className = 'steps';", page)
        self.assertIn("stepsList().appendChild(row); refreshSteps(toolGroup);", page)
        self.assertIn("stepsList().appendChild(fig); refreshSteps(toolGroup);", page)  # renders too
        self.assertIn("details.steps .list {", page)
        self.assertIn("max-height: 260px; overflow-y: auto;", page)
        self.assertNotIn("toolGroup = add(div('tools'))", page)
        # A failed step's error stays in the chat, under the closed line.
        self.assertIn("toolGroup._errs = add(div('step-errs'));", page)
        self.assertIn("if (e.error) row.dataset.error = e.text || 'failed';", page)
        self.assertIn("${esc(r.dataset.error)}", page)

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
                     "No copper on any layer under the antenna", "about 2.5 mm as the target",
                     "Placement distances are targets, not limits", "Rotations follow the board"):
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


class BlockPlanTests(unittest.TestCase):
    """The block plan card (powerlab-placement): drawn from block-plan.json, a click on a
    block selects its parts in KiCad."""

    def setUp(self):
        import json
        from powerlab_assistant import history, plan
        self.plan, self.history = plan, history
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "placement", "block-plan.json")
        os.makedirs(os.path.dirname(self.path))
        self.data = {
            "title": "Board <b>plan</b>",
            "outline": {"circle": {"center": [100, 100], "diameter": 90}},
            "cutouts": [{"circle": {"center": [100, 100], "diameter": 20}}],
            "holes": [{"circle": {"center": [140, 100], "diameter": 4}}],
            "keepouts": [{"name": "Ring", "ring": {"center": [100, 100], "inner": 84, "outer": 90}}],
            "blocks": [
                {"id": "legB", "name": "Leg <B>", "detail": "Q2 & shunt", "side": "top", "kind": "power",
                 "refs": ["Q2", "R10", 'X" onclick="alert(1)'],
                 "sector": {"center": [100, 100], "r": [29, 42], "angle": [333, 355]}},
                {"id": "u3", "name": "U3", "side": "bottom", "kind": "gate", "refs": ["U3"],
                 "rect": {"center": [125, 95], "size": [7, 7], "angle": 30}},
                {"id": "x", "name": "Odd", "kind": "nope", "polygon": [[60, 60], [70, 60], [65, 70]]},
            ],
            "links": [{"from": "u3", "to": "legB", "label": "gate <6>", "kind": "gate"}],
            "notes": ["**U3** under [leg B](kicad:refs=Q2)"],
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f)

    def test_is_plan(self):
        self.assertTrue(self.plan.is_plan(self.path))
        self.assertTrue(self.plan.is_plan(r"C:\p\placement\Block-Plan.json"))
        self.assertFalse(self.plan.is_plan(r"C:\p\placement\notes.json"))

    def test_card_escapes_text_and_keeps_only_clean_refs(self):
        card = self.plan.card(self.path)
        self.assertNotIn("error", card)
        svg = card["svg"]
        self.assertTrue(svg.startswith("<svg"))
        for raw in ("<b>", "Leg <B>", "gate <6>", "onclick", "alert("):
            self.assertNotIn(raw, svg)
        self.assertIn("Leg &lt;B&gt;", svg)
        self.assertIn('data-loc="refs=Q2,R10"', svg)
        legb = next(b for b in card["blocks"] if b["id"] == "legB")
        self.assertEqual((legb["loc"], legb["count"], legb["side"]), ("refs=Q2,R10", 2, "top"))
        odd = next(b for b in card["blocks"] if b["id"] == "x")
        self.assertEqual((odd["kind"], odd["side"], odd["loc"]), ("other", "top", "at=65,63.333"))  # no parts: its place
        self.assertEqual(card["title"], "Board <b>plan</b>")  # the page escapes it

    def test_bottom_blocks_are_hatched_and_drawn_under_the_top(self):
        svg = self.plan.card(self.path)["svg"]
        self.assertIn('class="blk bottom"', svg)
        self.assertIn('fill="url(#h-gate)"', svg)
        self.assertLess(svg.index('data-id="u3"'), svg.index('data-id="legB"'))
        # the gate link and its pill: the line under the blocks, the pill over them
        self.assertLess(svg.index('class="link"'), svg.index('data-id="u3"'))
        self.assertGreater(svg.index('class="pill-g"'), svg.index('data-id="legB"'))

    def test_sector_spans_its_angles(self):
        s = self.plan.Shape({"sector": {"center": [0, 0], "r": [10, 20], "angle": [350, 10]}})
        self.assertAlmostEqual(math.hypot(*s.anchor), 15, places=6)
        self.assertAlmostEqual(math.degrees(math.atan2(s.anchor[1], s.anchor[0])), 0, places=6)
        self.assertIn(" A20 20 0 0 1 ", s.d)

    def test_a_broken_plan_shows_an_error(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("{not json")
        card = self.plan.card(self.path)
        self.assertIn("can't be read", card["error"])
        self.assertEqual(card["svg"], "")

    def test_chat_keeps_the_plan_by_path(self):
        card = dict(self.plan.card(self.path), kind="plan")
        kept = self.history.stored("plan", card)
        self.assertEqual(kept["path"], self.path)
        for key in ("svg", "blocks", "notes", "links"):
            self.assertNotIn(key, kept)
        self.assertIn("plan", self.history.KINDS)

    def test_drags_are_written_into_the_plan(self):
        import json
        lines = self.plan.move(self.path, [
            {"id": "legB", "da": -12, "dr": 1.5},          # a sector turns and moves outward
            {"id": "u3", "dx": 2, "dy": -1},               # a rect moves in x and y
            {"id": "x", "dx": 1, "dy": 1},                 # a polygon moves every point
            {"id": "u3", "side": "top"},                   # and a block changes side
            {"id": "nope", "dx": 5},                       # unknown blocks are ignored
            {"id": "legB", "da": 1e9},                     # huge numbers are clamped, not kept
        ])
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        blocks = {b["id"]: b for b in data["blocks"]}
        self.assertEqual(blocks["legB"]["sector"]["r"], [30.5, 43.5])
        self.assertEqual(blocks["legB"]["sector"]["angle"][0], (333 - 12 + 500) % 360)
        self.assertEqual(blocks["u3"]["rect"]["center"], [127, 94])
        self.assertEqual(blocks["u3"]["side"], "top")
        self.assertEqual(blocks["x"]["polygon"][0], [61, 61])
        self.assertIn("Leg <B>: turned 12.0° counter-clockwise, 1.5 mm outward", lines[0])
        self.assertIn("U3: moved +2.0 mm in x, -1.0 mm in y; centre now (127, 94)", lines[1])
        self.assertIn("U3: to the top side", lines)
        self.assertEqual(len(lines), 5)
        svg = self.plan.card(self.path)["svg"]
        self.assertIn('data-drag="sector" data-cx="100" data-cy="100"', svg)
        self.assertIn('data-drag="move"', svg)

    def test_boxes_turn_and_moved_links_show_the_measured_gap(self):
        import json
        g = self.plan.gap(self.plan.Shape({"rect": {"center": [0, 0], "size": [10, 10]}}),
                          self.plan.Shape({"rect": {"center": [20, 0], "size": [6, 6]}}))
        self.assertAlmostEqual(g, 12.0, places=6)  # edges at x = 5 and x = 17
        self.assertEqual(self.plan.gap(self.plan.Shape({"rect": {"center": [0, 0], "size": [10, 10]}}),
                                       self.plan.Shape({"circle": {"center": [4, 0], "diameter": 6}})), 0.0)
        lines = self.plan.move(self.path, [{"id": "u3", "rot": 90}, {"id": "u3", "dx": -10, "dy": 0}])
        self.assertEqual(lines[0], "U3: turned 90° clockwise")
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["blocks"][1]["rect"]["angle"], 120)
        label = data["links"][0]["label"]
        self.assertRegex(label, r"^gate <6> · (stacked|\d+\.\d mm gap)$")  # U3 is on the other side
        self.assertEqual(self.plan.NUMBER_AT_END.sub("", "gate A ~16 mm"), "gate A")  # old lengths go
        self.plan.move(self.path, [{"id": "u3", "dx": 1}])
        with open(self.path, encoding="utf-8") as f:
            again = json.load(f)["links"][0]["label"]
        self.assertEqual(again.count("·"), 1)  # measured again, not appended twice
        svg = self.plan.card(self.path)["svg"]
        self.assertIn('data-turn="1"', svg)  # boxes and polygons can turn
        self.assertRegex(svg, r'data-pts="[\d.]+,[\d.]+ ')
        self.assertIn('data-from="u3" data-to="legB"', svg)

    def test_drags_snap_to_the_board_edges_and_centre(self):
        svg = self.plan.card(self.path)["svg"]
        self.assertRegex(svg, r'<svg [^>]*data-board="-?[\d.]+ -?[\d.]+ [\d.]+ [\d.]+"')  # the board's box
        self.assertIn('<g class="snap"></g>', svg)  # where the guides go
        with open(os.path.join(ROOT, "plugin", "powerlab_assistant", "panel.html"), encoding="utf-8") as f:
            page = f.read()
        self.assertIn("const snapAxis = (d, lo, hi, b0, b1, tol)", page)
        self.assertIn("const snap = !ev2.altKey && guides;", page)  # Alt drags freely
        self.assertIn("Math.round(mid / 45) * 45", page)  # sectors snap to 45° steps

    def test_any_board_shape_comes_from_edge_cuts(self):
        import json
        project = os.path.dirname(os.path.dirname(self.path))
        edge = '(layer "Edge.Cuts")'
        with open(os.path.join(project, "odd.kicad_pcb"), "w", encoding="utf-8") as f:
            f.write("(kicad_pcb\n"
                    # a 40 x 20 board with a rounded top-left corner, drawn out of order
                    f'\t(gr_line (start 10 0) (end 40 0) (stroke (width 0.1)) {edge})\n'
                    f'\t(gr_line (start 40 20) (end 40 0) (stroke (width 0.1)) {edge})\n'
                    f'\t(gr_line (start 40 20) (end 0 20) (stroke (width 0.1)) {edge})\n'
                    f'\t(gr_arc (start 10 0) (mid 2.928932 2.928932) (end 0 10) (stroke (width 0.1)) {edge})\n'
                    f'\t(gr_line (start 0 10) (end 0 20) (stroke (width 0.1)) {edge})\n'
                    f'\t(gr_circle (center 30 10) (end 32 10) (stroke (width 0.1)) {edge})\n'
                    '\t(gr_line (start 0 0) (end 99 99) (stroke (width 0.1)) (layer "F.SilkS"))\n'
                    '\t(gr_text "a (layer \\"Edge.Cuts\\") in text" (at 5 5) (layer "F.SilkS"))\n)\n')
        loops = self.plan.edge_cuts(os.path.join(project, "odd.kicad_pcb"))
        self.assertEqual(len(loops), 2)
        self.assertAlmostEqual(self.plan._area(loops[0]), 800 - 100 + math.pi * 25, delta=0.5)
        self.assertAlmostEqual(self.plan._area(loops[1]), math.pi * 4, delta=0.05)
        self.data["outline"] = "board"
        self.data.pop("cutouts")
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f)
        card = self.plan.card(self.path)
        self.assertNotIn("error", card)
        self.assertIn('class="board"', card["svg"])
        self.assertIn('class="cut"', card["svg"])  # the round cutout
        os.remove(os.path.join(project, "odd.kicad_pcb"))
        self.assertIn("can't be read", self.plan.card(self.path)["error"])

    def test_board_text_and_logos_are_blocks_too(self):
        import json
        self.data["blocks"] += [
            {"id": "info", "name": "Board rev A", "kind": "text", "rect": {"center": [70, 110], "size": [20, 3]}},
            {"id": "logo", "name": "Logo", "kind": "logo", "refs": ["LOGO1"], "rect": {"center": [80, 120], "size": [8, 8]}}]
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f)
        card = self.plan.card(self.path)
        blocks = {b["id"]: b for b in card["blocks"]}
        self.assertEqual(blocks["info"]["loc"], "at=70,110")  # text has no reference: its place
        self.assertEqual(blocks["logo"]["loc"], "refs=LOGO1")
        self.assertIn('data-kind="text" data-loc="at=70,110"', card["svg"])
        self.plan.move(self.path, [{"id": "info", "dx": 5, "dy": -2}])
        self.assertIn('data-loc="at=75,108"', self.plan.card(self.path)["svg"])  # it follows the move

    def test_any_angle_turns_a_box(self):
        lines = self.plan.move(self.path, [{"id": "u3", "rot": -22.5}, {"id": "u3", "rot": 1000}])
        self.assertEqual(lines, ["U3: turned 22.5° counter-clockwise"])  # 1000° isn't a real turn

    def test_panel_moves_only_plans_of_its_project(self):
        try:
            from powerlab_assistant.panel import ClaudePanel
        except ImportError as exc:
            self.skipTest(f"panel needs wx.html2: {exc}")
        panel = types.SimpleNamespace(chat_cwd=self.tmp.name, emitted=[])
        panel.emit = lambda kind, **data: panel.emitted.append(dict(data, kind=kind))
        ClaudePanel.msg_plan_move(panel, {"path": self.path, "moves": [{"id": "u3", "side": "top"}]})
        self.assertEqual([e["kind"] for e in panel.emitted], ["plan_update"])
        self.assertEqual(panel.emitted[0]["lines"], ["U3: to the top side"])
        self.assertIn('class="blk top" data-id="u3"', panel.emitted[0]["svg"])
        other = tempfile.TemporaryDirectory()
        self.addCleanup(other.cleanup)
        panel.chat_cwd, panel.emitted = other.name, []
        ClaudePanel.msg_plan_move(panel, {"path": self.path, "moves": [{"id": "u3", "side": "bottom"}]})
        self.assertEqual(panel.emitted, [])  # not this chat's project
        panel.chat_cwd = self.tmp.name
        ClaudePanel.msg_plan_move(panel, {"path": self.path.replace("block-plan", "other"), "moves": []})
        self.assertEqual(panel.emitted, [])  # not a block plan

    def test_panel_shows_written_plans(self):
        with open(os.path.join(ROOT, "plugin", "powerlab_assistant", "panel.py"), encoding="utf-8") as f:
            panel = f.read()
        self.assertIn("plan.is_plan(args.get(\"file_path\"))", panel)
        self.assertIn("self.show_plan(plan_path)", panel)
        with open(os.path.join(ROOT, "plugin", "powerlab_assistant", "panel.html"), encoding="utf-8") as f:
            page = f.read()
        self.assertIn("if (!WINDOW) { add(docCard(e, 'plan'));", page)  # a row in the chat
        self.assertIn("else { add(planCard(e));", page)  # the drawing in its window
        self.assertIn("post({ type: 'locate', target: loc })", page)
        self.assertIn("post({ type: 'plan_move', path: e.path, moves: [move], undo: !!undo })", page)
        self.assertIn("'Move to bottom side ↓' : 'Move to top side ↑'", page)
        self.assertIn("case 'plan_update':", page)
        self.assertIn("Send moves to Claude", page)
        self.assertIn("[[90, '↻ 90°'], [45, '↻ 45°'], [-45, '↺ 45°']]", page)  # common angles first
        self.assertIn("inp.placeholder = 'any °'", page)  # then any angle
        self.assertIn("follow(id, tf);", page)  # links follow a drag, with the gap measured live
        with open(os.path.join(ROOT, "skills", "powerlab-placement", "SKILL.md"), encoding="utf-8") as f:
            skill = f.read()
        self.assertIn("placement\\block-plan.json", skill)
        self.assertIn("Stop and wait for the answer", skill)


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

    def test_patch_tool(self):
        """tools/mcp_patch.py (the auto-fix workflow's checkout) uses install.ps1's pin, and a
        regenerated patch that differs only in git's abbreviated index lines isn't a change."""
        import mcp_patch
        with open(os.path.join(ROOT, "install.ps1"), encoding="utf-8") as f:
            text = f.read()
        repo, commit = mcp_patch.pin()
        self.assertIn(f'$McpRepo = "{repo}"', text)
        self.assertIn(f'[string]$McpCommit = "{commit}"', text)
        old = self.patch().encode("utf-8")
        other_clone = re.sub(rb"(?m)^index \w+\.\.\w+", b"index 1234567890..abcdef1234", old)
        self.assertNotEqual(other_clone, old)
        self.assertEqual(mcp_patch._body(old), mcp_patch._body(other_clone))
        self.assertNotEqual(mcp_patch._body(old), mcp_patch._body(old + b"+# one more line\n"))

    def test_update_rebuilds_for_a_changed_patch(self):
        """A maintainer's checkout already has the new patch applied (CLAUDE.md: edit, then
        regen), so -Update saw nothing to do and kept the old build: padNets and
        edit_board_text were missing. Every build now records the patch it was made from."""
        with open(os.path.join(ROOT, "install.ps1"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn('"dist\\.powerlab-patch"', text)
        self.assertIn("elseif ((Get-McpBuildStamp) -ne (Get-PatchHash))", text)
        self.assertEqual(text.count("Save-McpBuildStamp"), 4)  # defined, and after each of the 3 builds

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

    def test_schematic_text_can_be_deleted_and_moved(self):
        """Issue #60: free text could be added and listed, but not deleted or moved."""
        patch = self.patch()
        for tool in ("delete_schematic_text", "move_schematic_text"):
            self.assertIn(f'+            "{tool}": self._handle_{tool},', patch)
            self.assertIn(f'+    "{tool}",', patch)  # the TypeScript tool
        self.assertIn("def delete_text(", patch)
        self.assertIn("def move_text(", patch)

    def test_open_board_resolves_symbol_libraries_once(self):
        """Issue #61: open_board took ~27 s with 300+ symbol libraries and timed out at 30 s."""
        patch = self.patch()
        self.assertIn('env_vars = getattr(self, "_uri_env_vars", None)', patch)
        self.assertIn('+  "open_board", // PowerLab patch (#61)', patch)

    def test_junctions_count_wires_running_through(self):
        """Issue #62: every wire edit dropped the junctions of T's drawn in KiCad."""
        patch = self.patch()
        self.assertIn("def _through_wire_counter(", patch)
        self.assertIn("return ends + 2 * through(iu) if ends else 0", patch)

    def test_live_board_edits_that_need_a_library_footprint(self):
        """Issues #63, #65, #67: these changed only the tool's copy with KiCad open."""
        patch = self.patch()
        self.assertIn("LIVE_VIA_FILE_COMMANDS = {", patch)
        for command in ("place_component", "add_mounting_hole", "sync_schematic_to_board",
                        "edit_component", "replace_component"):
            self.assertIn(f'+        "{command}",\n', patch)
        self.assertIn("kicad_board.revert()", patch)
        self.assertIn('"replace_component": self._handle_replace_component', patch)
        self.assertIn("cli_nets = self._kicad_cli_pad_net_map(schematic_path)", patch)
        self.assertIn("nets_renamed.append(", patch)
        self.assertIn('describe("Net for the pad of a plated hole', patch)

    def test_parts_flip_and_circles_draw_in_live_mode(self):
        """Issues #64, #66, #68."""
        patch = self.patch()
        self.assertIn("def flip_component(self, reference: str, layer: str)", patch)
        self.assertIn('self._kicad.run_action("pcbnew.InteractiveEdit.flip")', patch)
        self.assertIn("return self._ipc_add_outline_circle(params)", patch)
        self.assertIn("circle.radius_point = Vector2.from_xy(", patch)

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

    def test_live_deletes_reach_kicads_board(self):
        # Issue #56: with KiCad open, delete_trace changed only the tool's own copy and
        # said it worked; nothing could delete board-outline lines live
        patch = self.patch()
        self.assertNotIn("+        return self.routing_commands.delete_trace(params)", patch)
        self.assertIn('+        """IPC handler for delete_trace (PowerLab patch, #56).', patch)
        for handler in ("_ipc_delete_graphic", "_ipc_list_graphics", "_ipc_clear_board_outline"):
            self.assertIn(f"+    def {handler}(self, params", patch)
        for name in ("list_graphics", "delete_graphic", "clear_board_outline"):
            self.assertIn(f'+        "{name}": "_ipc_{name}",  # PowerLab patch (#56)', patch)
        self.assertIn("board.remove_items(found)", patch)

    def test_no_board_loaded_loads_kicads_board(self):
        # Issue #57: run_drc said "No board is loaded" while KiCad had the board open
        patch = self.patch()
        self.assertIn("+    def _board_path_to_load(self, params", patch)
        self.assertIn('and result.get("message") == "No board is loaded"', patch)

    def test_session_vias_keep_their_annular_ring(self):
        self.assertIn("via_drills = _repair_via_drills(self.board)", self.patch())

    def router_package(self):
        """The router's files from the patch, as an importable package in a temp folder.
        They need KiCad's own pcbnew, not the stand-in these tests use outside KiCad."""
        if not hasattr(sys.modules.get("pcbnew"), "BOARD"):
            self.skipTest("needs KiCad's Python")
        root = tempfile.mkdtemp()
        pkg = os.path.join(root, "commands", "powerlab_router")
        os.makedirs(pkg)
        open(os.path.join(root, "commands", "__init__.py"), "w").close()
        for name in re.findall(r"\+\+\+ b/python/commands/powerlab_router/(\w+\.py)", self.patch()):
            with open(os.path.join(pkg, name), "w", encoding="utf-8") as f:
                f.write(self.new_file(f"python/commands/powerlab_router/{name}") + "\n")
        return root

    def test_powerlab_router_river(self):
        """A bus between two parallel pin rows, drawn as by hand: every bend 45 degrees, the
        runs in the channel exactly one pitch apart, no two tracks crossing, and a track
        that doesn't fit its slot moves along the channel."""
        module = types.ModuleType("bus")
        exec(self.new_file("python/commands/powerlab_router/bus.py"), module.__dict__)
        # module row at x = 106.25 (1.27 mm pitch), header row at x = 101.3 (2.54 mm), header left
        pairs = [((106.25, 110 + 1.27 * i), (101.3, 108 + 2.54 * i)) for i in range(6)]
        shapes = module.plan(pairs, 0.4, 0.9, 1.0)
        self.assertEqual(sorted(shapes), list(range(6)))
        for i, pts in shapes.items():
            self.assertEqual((pts[0], pts[-1]), pairs[i])
            for a, b in zip(pts, pts[1:]):
                angle = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 45
                self.assertTrue(angle < 0.01 or angle > 44.99, (i, a, b))
        runs = sorted(round(pts[2][0], 3) for i, pts in shapes.items() if pairs[i][1][1] > pairs[i][0][1] + 0.05)
        self.assertTrue(all(abs((b - a) - 0.4) < 1e-6 for a, b in zip(runs, runs[1:])), runs)

        def crosses(p, q):
            def side(a, b, c):
                return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            for a, b in zip(p, p[1:]):
                for c, d in zip(q, q[1:]):
                    if side(a, b, c) * side(a, b, d) < -1e-9 and side(c, d, a) * side(c, d, b) < -1e-9:
                        return True
            return False
        for i in shapes:
            for j in shapes:
                if i < j:
                    self.assertFalse(crosses(shapes[i], shapes[j]), (i, j))

        # copper on the first downward track's slot: it steps past it, the next one a pitch beyond
        first = min(i for i in shapes if pairs[i][1][1] > pairs[i][0][1] + 0.05)
        x0 = shapes[first][2][0]
        blocked = lambda i, pts: not any(x0 - 0.05 <= p[0] <= x0 + 0.25 for p in pts[2:-2]) if i == first else True
        moved = module.plan(pairs, 0.4, 0.9, 1.0, clear=blocked)
        self.assertGreater(moved[first][2][0], x0 + 0.25)
        self.assertGreaterEqual(moved[first + 1][2][0], moved[first][2][0] + 0.4 - 1e-9)

        # step-in: once a track has turned off into its pin, the next moves into its slot
        down = sorted((i for i in shapes if pairs[i][1][1] > pairs[i][0][1] + 0.05), key=lambda i: pairs[i][0][1])
        def last_run(pts):
            return [u[0] for u, v in zip(pts[2:-1], pts[3:-1]) if abs(u[0] - v[0]) < 1e-9][-1]
        stepped = [(prev, i) for prev, i in zip(down, down[1:]) if len(shapes[i]) > 6]
        self.assertTrue(stepped)
        for prev, i in stepped:
            self.assertAlmostEqual(last_run(shapes[i]), last_run(shapes[prev]), places=6)

        # pins in a different order on the two rows would cross: no plan
        crossed = [pairs[1], (pairs[0][0], pairs[2][1]), (pairs[2][0], pairs[0][1])]
        self.assertEqual(module.plan(crossed, 0.4, 0.9, 1.0), {})

    def test_powerlab_router_shapes(self):
        """Hand-drawn shapes between two points: straight, one bend, Z; 45 degree bends only."""
        module = types.ModuleType("patterns")
        exec(self.new_file("python/commands/powerlab_router/patterns.py"), module.__dict__)
        found = module.shapes((0, 0), 0, (3, 1), 0, step=0.1)
        self.assertTrue(found)
        self.assertEqual(min(module.bends(s) for s in found), 1)
        for s in found:
            self.assertEqual(s[0], (0, 0))
            self.assertEqual(s[-1], (3, 1))
            for a, b in zip(s, s[1:]):
                angle = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 45
                self.assertTrue(angle < 0.01 or angle > 44.99)
        self.assertEqual(module.shapes((0, 0), 0, (3, 0), 0)[0], [(0, 0), (3, 0)])  # straight
        self.assertEqual(module.shapes((0, 0), 0, (-3, 0), 4, most=4), [])  # a U-turn: left to the search
        # a pad centre, its lane exit on the same line, one bend: one corner, not two
        self.assertEqual(module.bends([(0, 0), (0.5, 0), (2, 0), (3, 1), (4, 2)]), 1)

    def test_powerlab_router_shortcut(self):
        """Milestone 2: the shortcut pass straightens a staircase, keeps the pad lanes and
        never turns by more than 45 degrees."""
        module = types.ModuleType("finish")
        exec(self.new_file("python/commands/powerlab_router/finish.py"), module.__dict__)
        # pad centre, lane exit, a staircase, then the far lane exit and pad centre
        pts = [(0, 0), (1, 0), (1.5, 0.5), (2, 0.5), (2.5, 1), (3, 1), (3.5, 1.5), (5, 1.5), (6, 1.5)]
        out = module._shorten(lambda a, b: True, pts, 1, len(pts) - 2)
        self.assertEqual(out[:2], pts[:2])
        self.assertEqual(out[-2:], pts[-2:])
        self.assertLess(len(out), len(pts))
        self.assertLess(module._length(out), module._length(pts))
        dirs = [module._unit(a, b) for a, b in zip(out, out[1:])]
        self.assertTrue(all(module._turn_ok(u, v) for u, v in zip(dirs, dirs[1:])))
        for a, b in zip(out, out[1:]):
            self.assertTrue(module._octilinear(b[0] - a[0], b[1] - a[1]))
        # nothing is clear: nothing changes
        self.assertEqual(module._shorten(lambda a, b: False, pts, 1, len(pts) - 2), pts)

    def test_powerlab_router_shortcut_corners_and_pad_entry(self):
        """Corners cost something in the finishing pass, a pad that isn't fine pitch may be
        entered at 45 degrees instead of bending just before it, and a T-junction end never
        turns to run along the track it joins."""
        module = types.ModuleType("finish")
        exec(self.new_file("python/commands/powerlab_router/finish.py"), module.__dict__)
        # pad centre, lane exit to the left, a 45 degree corner, then down (the bend before the pad)
        pts = [(0, 0), (-1, 0), (-2, 1), (-2, 4)]
        kept = module._shorten(lambda a, b: True, pts, 1, len(pts) - 1, bend=module.BEND)
        self.assertEqual(kept[:2], pts[:2])  # lane kept: fine pitch
        free = module._shorten(lambda a, b: True, pts, 0, len(pts) - 1, bend=module.BEND)
        self.assertNotEqual(free[1], (-1, 0))  # straight from the pad centre, no lane bend
        self.assertLess(module._turns(free), module._turns(pts))
        for a, b in zip(free, free[1:]):
            self.assertTrue(module._octilinear(b[0] - a[0], b[1] - a[1]))
        # equal length, but a wiggle: only the corner cost straightens it
        wiggle = [(0, 0), (1, 0), (2, 0), (2.5, 0.5), (3.5, 0.5), (4, 0), (6, 0), (7, 0)]
        cost = lambda a, b: math.dist(a, b) + (0.6 * math.dist(a, b) if abs(a[1]) < 1e-9 and abs(b[1]) < 1e-9 else 0)
        self.assertGreater(module._turns(module._shorten(lambda a, b: True, wiggle, 1, len(wiggle) - 2, cost)), 0)
        straight = module._shorten(lambda a, b: True, wiggle, 1, len(wiggle) - 2, cost, bend=module.BEND)
        self.assertEqual(module._turns(module._corners(straight)), 0)
        # a T-junction end on a horizontal track: the last segment doesn't run along it
        tee = [(0, 3), (0, 2), (1, 1), (3, 1), (4, 0)]
        out = module._shorten(lambda a, b: True, tee, 1, len(tee) - 1, bend=module.BEND, forbid_end=(1.0, 0.0))
        u = module._unit(out[-2], out[-1])
        self.assertGreater(abs(u[1]), 1e-3)
        self.assertEqual(out[-1], tee[-1])

    def test_powerlab_router_search_joins_a_track(self):
        """The search may end on the net's own track (a set of directions), at an angle."""
        module = types.ModuleType("search")
        exec(self.new_file("python/commands/powerlab_router/search.py"), module.__dict__)
        nx, ny = 40, 20
        blocked = [bytes(nx * ny)]
        via_ok = bytes(nx * ny)
        starts = [(2, 10, 0, 0, 0.0)]
        goals = {(38, 10, 0): (0, 0.0)}  # the far pad, straight on
        along = frozenset(k for k in range(8) if k % 4 != 2)  # a vertical track at i = 15
        for j in range(ny):
            goals.setdefault((15, j, 0), (along, 0.0))
        path, stats = module.search(blocked, via_ok, nx, ny, 0.1, starts, goals, (0, 0, nx - 1, ny - 1),
                                    module.Costs(layer_factor=None))
        self.assertIsNotNone(path)
        self.assertEqual(path[-1][:2], (15, 10))  # joined the track, not the far pad
        self.assertIn(path[-1][3], along)

    def test_powerlab_router_rejects_loops(self):
        """A grid path that comes back to a cell it has been on, or changes layer twice at
        one spot (a loop through two vias, to turn where the corner rules don't allow it)."""
        try:
            import pcbnew  # noqa: F401
        except ImportError:
            self.skipTest("needs KiCad's Python")
        sys.path.insert(0, self.router_package())
        try:
            for m in [m for m in sys.modules if m == "commands" or m.startswith("commands.")]:
                del sys.modules[m]
            from commands.powerlab_router.model import _loops
        finally:
            sys.path.pop(0)
        straight = [(i, 5, 0, 0, 2) for i in range(10)]
        self.assertEqual(_loops(straight), [])
        via_loop = [(3, 5, 0, 0, 2), (4, 5, 0, 0, 2), (4, 5, 1, 8, 0), (5, 6, 1, 1, 1), (4, 7, 1, 3, 1),
                    (3, 6, 1, 5, 1), (4, 5, 1, 7, 1), (4, 5, 0, 8, 0), (5, 5, 0, 0, 1)]
        self.assertEqual(_loops(via_loop), [(4, 5)])

    def test_powerlab_router_keeps_out_of_footprint_keepouts(self):
        """A module's antenna keepout comes with its footprint, not the board: the router
        reads the footprints' rule areas too."""
        try:
            import pcbnew
        except ImportError:
            self.skipTest("needs KiCad's Python")
        sys.path.insert(0, self.router_package())
        try:
            for m in [m for m in sys.modules if m == "commands" or m.startswith("commands.")]:
                del sys.modules[m]
            from commands.powerlab_router.router import Router
        finally:
            sys.path.pop(0)
        mm, P = pcbnew.FromMM, lambda x, y: pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
        board = pcbnew.BOARD()
        for a, b in (((0, 0), (30, 0)), ((30, 0), (30, 20)), ((30, 20), (0, 20)), ((0, 20), (0, 0))):
            edge = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
            edge.SetStart(P(*a)); edge.SetEnd(P(*b)); edge.SetLayer(pcbnew.Edge_Cuts); edge.SetWidth(mm(0.1))
            board.Add(edge)
        net = pcbnew.NETINFO_ITEM(board, "SIG")
        board.Add(net)
        for ref, x in (("R1", 5), ("R2", 25)):
            fp = pcbnew.FOOTPRINT(board)
            fp.SetReference(ref)
            fp.SetPosition(P(x, 10))
            pad = pcbnew.PAD(fp)
            pad.SetShape(pcbnew.PAD_SHAPE_RECTANGLE)
            pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
            pad.SetLayerSet(pcbnew.PAD.SMDMask())
            pad.SetSize(pcbnew.F_Cu, P(1, 1))
            pad.SetPosition(P(x, 10))
            pad.SetNumber("1")
            pad.SetNet(net)
            fp.Add(pad)
            board.Add(fp)
        module = pcbnew.FOOTPRINT(board)
        module.SetReference("U1")
        module.SetPosition(P(15, 7))
        keepout = pcbnew.ZONE(module)
        keepout.SetIsRuleArea(True)
        keepout.SetDoNotAllowTracks(True)
        keepout.SetDoNotAllowVias(True)
        layers = pcbnew.LSET()
        layers.AddLayer(pcbnew.F_Cu)
        layers.AddLayer(pcbnew.B_Cu)
        keepout.SetLayerSet(layers)
        for x, y in ((12, 0), (18, 0), (18, 14), (12, 14)):
            keepout.AppendCorner(P(x, y), -1)
        module.Add(keepout)
        board.Add(module)
        report = Router(board).run(["SIG"])
        self.assertEqual(report["routed"], 1, report["left"])
        for t in board.GetTracks():
            a, e = t.GetStart(), t.GetEnd()
            for k in range(51):
                x = pcbnew.ToMM(a.x + (e.x - a.x) * k / 50)
                y = pcbnew.ToMM(a.y + (e.y - a.y) * k / 50)
                self.assertFalse(12 < x < 18 and y < 14, "a track in the footprint's keepout")

    def test_powerlab_router_bus_keeps_out_of_rule_areas(self):
        """A bus between a module row and a header row is drawn as a river (bus.py), placed
        with its own clearance check, not the search's grid. Its tracks and escape vias
        stayed out of other copper but ran straight through a rule area that keeps tracks
        and vias out."""
        try:
            import pcbnew
        except ImportError:
            self.skipTest("needs KiCad's Python")
        sys.path.insert(0, self.router_package())
        try:
            for m in [m for m in sys.modules if m == "commands" or m.startswith("commands.")]:
                del sys.modules[m]
            from commands.powerlab_router.router import Router
        finally:
            sys.path.pop(0)
        mm, P = pcbnew.FromMM, lambda x, y: pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
        board = pcbnew.BOARD()
        for a, b in (((0, 0), (30, 0)), ((30, 0), (30, 30)), ((30, 30), (0, 30)), ((0, 30), (0, 0))):
            edge = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
            edge.SetStart(P(*a)); edge.SetEnd(P(*b)); edge.SetLayer(pcbnew.Edge_Cuts); edge.SetWidth(mm(0.1))
            board.Add(edge)
        nets = []
        for i in range(4):
            net = pcbnew.NETINFO_ITEM(board, f"S{i}")
            board.Add(net)
            nets.append(net)
        # a module row (SMD, top only) and a header row (through-hole), facing each other
        for ref, x, pitch, smd in (("U1", 8, 1.27, True), ("J1", 22, 2.54, False)):
            fp = pcbnew.FOOTPRINT(board)
            fp.SetReference(ref)
            fp.SetPosition(P(x, 15))
            for i, net in enumerate(nets):
                pad = pcbnew.PAD(fp)
                pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD if smd else pcbnew.PAD_ATTRIB_PTH)
                pad.SetLayerSet(pcbnew.PAD.SMDMask() if smd else pcbnew.PAD.PTHMask())
                pad.SetShape(pcbnew.PAD_SHAPE_RECTANGLE if smd else pcbnew.PAD_SHAPE_CIRCLE)
                pad.SetSize(pcbnew.F_Cu, P(1.5, 0.6) if smd else P(1.6, 1.6))
                if not smd:
                    pad.SetDrillSize(P(1.0, 1.0))
                y = 15 + (i - 1.5) * pitch
                pad.SetPosition(P(x, y))
                pad.SetNumber(str(i + 1))
                pad.SetNet(net)
                fp.Add(pad)
            board.Add(fp)
        # a rule area across the middle of the channel; the way round is above or below it
        keepout = pcbnew.ZONE(board)
        keepout.SetIsRuleArea(True)
        keepout.SetDoNotAllowTracks(True)
        keepout.SetDoNotAllowVias(True)
        layers = pcbnew.LSET()
        layers.AddLayer(pcbnew.F_Cu)
        layers.AddLayer(pcbnew.B_Cu)
        keepout.SetLayerSet(layers)
        for x, y in ((13, 11), (17, 11), (17, 19), (13, 19)):
            keepout.AppendCorner(P(x, y), -1)
        board.Add(keepout)
        router = Router(board)
        conns = router.connections([n.GetNetname() for n in nets])
        router._buses(conns)
        self.assertTrue(all(c.bus for c in conns), "the test board should make a bus")
        router.run([n.GetNetname() for n in nets])
        tracks = list(board.GetTracks())
        self.assertTrue(tracks)
        for t in tracks:
            a, e = t.GetStart(), t.GetEnd()
            for k in range(101):
                x = pcbnew.ToMM(a.x + (e.x - a.x) * k / 100)
                y = pcbnew.ToMM(a.y + (e.y - a.y) * k / 100)
                self.assertFalse(13 < x < 17 and 11 < y < 19,
                                 f"{t.GetNetname()} {'via' if t.Type() == pcbnew.PCB_VIA_T else 'track'} "
                                 f"in the rule area at ({x:.2f}, {y:.2f})")

    def test_powerlab_router_routes_a_board(self):
        """Milestone 2, end to end: two pads with another net's pad between them. The track
        goes around it, starts and ends at the pad centres, and turns by 45 degrees at most."""
        try:
            import pcbnew
        except ImportError:
            self.skipTest("needs KiCad's Python")
        sys.path.insert(0, self.router_package())
        try:
            for m in [m for m in sys.modules if m == "commands" or m.startswith("commands.")]:
                del sys.modules[m]
            from commands.powerlab_router.router import Router
        finally:
            sys.path.pop(0)
        mm, P = pcbnew.FromMM, lambda x, y: pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
        board = pcbnew.BOARD()
        for a, b in (((0, 0), (30, 0)), ((30, 0), (30, 20)), ((30, 20), (0, 20)), ((0, 20), (0, 0))):
            edge = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
            edge.SetStart(P(*a)); edge.SetEnd(P(*b)); edge.SetLayer(pcbnew.Edge_Cuts); edge.SetWidth(mm(0.1))
            board.Add(edge)
        nets = {}
        for name in ("SIG", "OTHER"):
            nets[name] = pcbnew.NETINFO_ITEM(board, name)
            board.Add(nets[name])
        for ref, (x, y), size, net in (("R1", (5, 10), (1, 1), "SIG"), ("R2", (25, 10), (1, 1), "SIG"),
                                       ("U1", (15, 10), (2, 8), "OTHER")):
            fp = pcbnew.FOOTPRINT(board)
            fp.SetReference(ref)
            fp.SetPosition(P(x, y))
            pad = pcbnew.PAD(fp)
            pad.SetShape(pcbnew.PAD_SHAPE_RECTANGLE)
            pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
            pad.SetLayerSet(pcbnew.PAD.SMDMask())
            pad.SetSize(pcbnew.F_Cu, P(*size))
            pad.SetPosition(P(x, y))
            pad.SetNumber("1")
            pad.SetNet(nets[net])
            fp.Add(pad)
            board.Add(fp)
        # an inductor between them, off the straight line: no track under it (§3.4)
        coil = pcbnew.FOOTPRINT(board)
        coil.SetReference("L1")
        coil.SetPosition(P(10, 10))
        box = pcbnew.PCB_SHAPE(coil, pcbnew.SHAPE_T_RECTANGLE)
        box.SetStart(P(8, 4))
        box.SetEnd(P(12, 16))
        box.SetLayer(pcbnew.F_CrtYd)
        box.SetWidth(mm(0.05))
        coil.Add(box)
        board.Add(coil)
        report = Router(board).run(["SIG"])
        self.assertEqual(report["routed"], 1, report["left"])
        for t in board.GetTracks():
            a, e = t.GetStart(), t.GetEnd()
            for k in range(51):  # points along the track
                x = pcbnew.ToMM(a.x + (e.x - a.x) * k / 50)
                y = pcbnew.ToMM(a.y + (e.y - a.y) * k / 50)
                self.assertFalse(7.9 < x < 12.1 and 3.9 < y < 16.1, "a track under the inductor")
        tracks = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
        ends = {(round(pcbnew.ToMM(p.x), 3), round(pcbnew.ToMM(p.y), 3)) for t in tracks for p in (t.GetStart(), t.GetEnd())}
        self.assertIn((5.0, 10.0), ends)  # pad centres
        self.assertIn((25.0, 10.0), ends)
        for t in tracks:
            dx, dy = pcbnew.ToMM(t.GetEnd().x - t.GetStart().x), pcbnew.ToMM(t.GetEnd().y - t.GetStart().y)
            angle = math.degrees(math.atan2(dy, dx)) % 45
            self.assertTrue(angle < 0.5 or angle > 44.5, (dx, dy))
            # around U1's pad, never through it
            self.assertFalse(13.8 < pcbnew.ToMM(t.GetStart().x) < 16.2 and 5.8 < pcbnew.ToMM(t.GetStart().y) < 14.2)

    def _router_board(self, pads, nets):
        """A 30 x 20 mm board with 1 x 1 mm SMD pads: pads = [(ref, (x, y), net)]."""
        import pcbnew
        mm, P = pcbnew.FromMM, lambda x, y: pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
        board = pcbnew.BOARD()
        for a, b in (((0, 0), (30, 0)), ((30, 0), (30, 20)), ((30, 20), (0, 20)), ((0, 20), (0, 0))):
            edge = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
            edge.SetStart(P(*a)); edge.SetEnd(P(*b)); edge.SetLayer(pcbnew.Edge_Cuts); edge.SetWidth(mm(0.1))
            board.Add(edge)
        info = {}
        for name in nets:
            info[name] = pcbnew.NETINFO_ITEM(board, name)
            board.Add(info[name])
        for ref, (x, y), net in pads:
            fp = pcbnew.FOOTPRINT(board)
            fp.SetReference(ref)
            fp.SetPosition(P(x, y))
            pad = pcbnew.PAD(fp)
            pad.SetShape(pcbnew.PAD_SHAPE_RECTANGLE)
            pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
            pad.SetLayerSet(pcbnew.PAD.SMDMask())
            pad.SetSize(pcbnew.F_Cu, P(1, 1))
            pad.SetPosition(P(x, y))
            pad.SetNumber("1")
            pad.SetNet(info[net])
            fp.Add(pad)
            board.Add(fp)
        return board

    def _import_router(self):
        sys.path.insert(0, self.router_package())
        try:
            for m in [m for m in sys.modules if m == "commands" or m.startswith("commands.")]:
                del sys.modules[m]
            from commands.powerlab_router import router, pours
        finally:
            sys.path.pop(0)
        return router, pours

    def test_powerlab_router_squares_a_run_between_vias(self):
        """pad -> via -> other layer -> via -> pad, each piece one run, both pads off the
        grid: the vias slide along their runs so the middle run is a 45 degree multiple."""
        try:
            import pcbnew  # noqa: F401
        except ImportError:
            self.skipTest("needs KiCad's Python")
        sys.path.insert(0, self.router_package())
        try:
            for m in [m for m in sys.modules if m == "commands" or m.startswith("commands.")]:
                del sys.modules[m]
            from commands.powerlab_router.model import _square_middles
        finally:
            sys.path.pop(0)
        pieces = [(0, [(0.0, 0.0), (1.0, 0.0)]), (1, [(1.0, 0.0), (4.0, 3.05)]), (0, [(4.0, 3.05), (5.0, 3.05)])]
        vias = [(1.0, 0.0), (4.0, 3.05)]
        _square_middles(pieces, vias)
        (a, b) = pieces[1][1]
        self.assertAlmostEqual(abs(b[0] - a[0]), abs(b[1] - a[1]), places=6)  # 45 degrees
        self.assertEqual(pieces[0][1][-1], a)
        self.assertEqual(pieces[2][1][0], b)
        self.assertEqual(vias, [a, b])
        self.assertAlmostEqual(a[1], 0.0)  # each via stays on its own run
        self.assertAlmostEqual(b[1], 3.05)

    def test_powerlab_router_joins_a_nets_tracks(self):
        """Two connections of one net leave the same pad toward the same side: the second
        joins the first's track (or leaves by another lane) instead of running a second
        track beside or on top of it."""
        try:
            import pcbnew
        except ImportError:
            self.skipTest("needs KiCad's Python")
        router, _pours = self._import_router()
        board = self._router_board([("R1", (5, 10), "SIG"), ("R2", (16, 4), "SIG"), ("R3", (16, 16), "SIG")], ["SIG"])
        report = router.Router(board).run(["SIG"])
        self.assertEqual(report["routed"], 2, report["left"])
        T = pcbnew.ToMM
        segs = [((T(t.GetStart().x), T(t.GetStart().y)), (T(t.GetEnd().x), T(t.GetEnd().y)))
                for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
        for i, (a, b) in enumerate(segs):
            for c, d in segs[i + 1:]:
                u = (b[0] - a[0], b[1] - a[1])
                v = (d[0] - c[0], d[1] - c[1])
                if abs(u[0] * v[1] - u[1] * v[0]) > 1e-6:
                    continue  # not parallel
                gap = abs(u[0] * (c[1] - a[1]) - u[1] * (c[0] - a[0])) / math.hypot(*u)
                if gap > 1.0:
                    continue
                n = math.hypot(*u)
                s = sorted(((c[0] - a[0]) * u[0] + (c[1] - a[1]) * u[1], (d[0] - a[0]) * u[0] + (d[1] - a[1]) * u[1]))
                overlap = min(n * n, s[1]) - max(0.0, s[0])
                self.assertLess(overlap / n, 0.3, f"two tracks side by side: {(a, b)} {(c, d)}")

    def test_powerlab_router_power_pours_and_stitching(self):
        """After routing: a pour round a power rail's track (thermal reliefs, above the GND
        pour), and GND stitching vias where both GND pours are filled."""
        try:
            import pcbnew
        except ImportError:
            self.skipTest("needs KiCad's Python")
        router, pours = self._import_router()
        board = self._router_board([("C1", (5, 10), "+3V3"), ("C2", (25, 10), "+3V3")], ["+3V3", "GND"])
        P = lambda x, y: pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
        gnd = board.FindNet("GND")
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            z = pcbnew.ZONE(board)
            z.SetLayer(layer)
            z.SetNet(gnd)
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
            for x, y in ((0, 0), (30, 0), (30, 20), (0, 20)):
                z.AppendCorner(P(x, y), -1)
            board.Add(z)
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        r = router.Router(board)
        self.assertTrue(r.is_power("+3V3"))
        report = r.run(["+3V3"])
        self.assertEqual(report["routed"], 1, report["left"])
        made = pours.power_pours(r, ["+3V3"])
        self.assertEqual(made["added"], {"+3V3": ["F.Cu"]})
        rail = [z for z in board.Zones() if z.GetNetname() == "+3V3"]
        self.assertEqual(len(rail), 1)
        self.assertEqual(rail[0].GetPadConnection(), pcbnew.ZONE_CONNECTION_THERMAL)
        self.assertGreater(rail[0].GetAssignedPriority(), 0)
        stitched = pours.stitching_vias(r, 5.0)
        self.assertGreater(stitched["added"], 4)
        vias = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
        self.assertTrue(all(v.GetNetname() == "GND" for v in vias))
        self.assertTrue(all(not r.rb.violations("GND", [v]) for v in vias))

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

    def test_powerlab_router_zone_connection(self):
        """zone_connection rules: how a pad joins a pour, which decides whether the pour
        flows across it (solid) or leaves it a hole reached only by spokes."""
        module = types.ModuleType("rules")
        exec(self.new_file("python/commands/powerlab_router/rules.py"), module.__dict__)
        rules = module.Rules.parse('''(version 1)
(rule "Module and USB-C GND pads connect solid"
	(condition "A.Type == 'Pad' && (A.memberOfFootprint('U1') || A.memberOfFootprint('J1'))")
	(constraint zone_connection solid))
(rule "Test points off the pour"
	(condition "A.Type == 'Pad' && A.memberOfFootprint('TP*')")
	(constraint zone_connection none))
''')
        zone = {"Type": "Zone", "NetName": "GND", "NetClass": "GND", "Footprint": None}
        pad = lambda ref: {"Type": "Pad", "NetName": "GND", "NetClass": "GND", "Footprint": ref}
        self.assertEqual(rules.zone_connection(pad("U1"), zone, "F.Cu"), "solid")
        self.assertEqual(rules.zone_connection(pad("TP3"), zone, "B.Cu"), "none")
        self.assertIsNone(rules.zone_connection(pad("C4"), zone, "F.Cu"))  # the zone decides
        self.assertEqual(rules.unsupported, [])
        # rules without a clearance don't change clearances
        track = {"Type": "Track", "NetClass": "Default", "NetName": "IO2", "Width": 0.2, "Footprint": None}
        self.assertEqual(rules.clearance(track, pad("U1"), "F.Cu", 0.3), 0.3)

    def test_powerlab_router_net_name_patterns(self):
        """Rules that name nets: the patterns they compare NetName with, or None when a rule
        uses NetName another way (then each net needs grids of its own)."""
        module = types.ModuleType("rules")
        exec(self.new_file("python/commands/powerlab_router/rules.py"), module.__dict__)
        rules = module.Rules.parse('''(version 1)
(rule "HV" (layer outer)
	(constraint clearance (min 0.6mm))
	(condition "(A.NetName == '+48V' || A.NetName == 'SW_*') && !(B.NetName == '+48V' || B.NetName == 'SW_*')"))
''')
        self.assertEqual(module.net_name_patterns(rules), ["+48V", "SW_*"])
        same = module.Rules.parse('''(version 1)
(rule "Same net" (constraint clearance (min 0.3mm)) (condition "A.NetName == B.NetName"))
''')
        self.assertIsNone(module.net_name_patterns(same))

    def test_powerlab_router_patches(self):
        """A net's copper is kept as a patch round it, not a full-board array per net and
        layer (5.8 GB on a 4-layer board with 100 nets)."""
        try:
            import numpy  # noqa: F401
            import PIL  # noqa: F401
        except ImportError:
            self.skipTest("needs numpy and Pillow (KiCad's Python has both)")
        module = types.ModuleType("grid")
        exec(self.new_file("python/commands/powerlab_router/grid.py"), module.__dict__)
        g = module.Grid(0, 0, 30, 20, 0.1)
        polys = [([(5, 5), (8, 5), (8, 7), (5, 7)], []), ([(20, 12), (21, 12), (21, 15)], [])]
        full = g.raster(polys)
        p = g.raster_box(polys)
        self.assertTrue((p.full(g.ny, g.nx) == full).all())
        self.assertLess(g.raster_box(polys[:1]).a.size, full.size / 50)  # one part's copper: a small box
        self.assertIsNone(g.raster_box([]))
        a, b = g.raster_box(polys[:1]), g.raster_box(polys[1:])
        self.assertTrue((module.Patch.union(a, b).full(g.ny, g.nx) == full).all())

    def test_powerlab_router_groups_nets_the_rules_treat_alike(self):
        """Nets the rules can't tell apart share their grids: the 48 V nets of a rule that
        lists them by name are one group, every other net another."""
        try:
            import pcbnew  # noqa: F401
        except ImportError:
            self.skipTest("needs KiCad's Python")
        router, _pours = self._import_router()
        from commands.powerlab_router.model import RouterBoard
        from commands.powerlab_router.rules import Rules
        nets = ["+48V", "SW_A", "SW_B", "IO1", "IO2", "IO3"]
        board = self._router_board([(f"R{i}", (3 + 4 * i, 10), n) for i, n in enumerate(nets)], nets)
        rules = Rules.parse('''(version 1)
(rule "HV" (layer outer)
	(constraint clearance (min 0.6mm))
	(condition "(A.NetName == '+48V' || A.NetName == 'SW_A' || A.NetName == 'SW_B') && !(B.NetName == '+48V' || B.NetName == 'SW_A' || B.NetName == 'SW_B')"))
''')
        rb = RouterBoard(board, rules=rules)
        groups = {n: rb.net_group(n) for n in nets}
        self.assertEqual(len({groups[n] for n in ("+48V", "SW_A", "SW_B")}), 1)
        self.assertEqual(len({groups[n] for n in ("IO1", "IO2", "IO3")}), 1)
        self.assertNotEqual(groups["+48V"], groups["IO1"])
        self.assertEqual(len({rb.key(n) for n in nets}), 2)

    def test_powerlab_router_leaves_inner_planes_alone(self):
        """On a 4-layer board an inner layer covered by a zone is a plane: no tracks on it,
        vias pass through. An inner layer without one is routed."""
        try:
            import pcbnew
        except ImportError:
            self.skipTest("needs KiCad's Python")
        router, _pours = self._import_router()
        from commands.powerlab_router.model import RouterBoard
        board = self._router_board([("R1", (5, 10), "SIG"), ("R2", (25, 10), "SIG")], ["SIG", "GND"])
        board.SetCopperLayerCount(4)
        layers = board.GetEnabledLayers()
        layers.AddLayer(pcbnew.In1_Cu)
        layers.AddLayer(pcbnew.In2_Cu)
        board.SetEnabledLayers(layers)
        plane = pcbnew.ZONE(board)
        plane.SetLayer(pcbnew.In1_Cu)
        plane.SetNet(board.FindNet("GND"))
        for x, y in ((0, 0), (30, 0), (30, 20), (0, 20)):
            plane.AppendCorner(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)), -1)
        board.Add(plane)
        rb = RouterBoard(board)
        names = [rb.layer_names[L] for L in rb.layers]
        self.assertEqual(names, ["F.Cu", "In2.Cu", "B.Cu"])
        self.assertEqual([rb.layer_names[L] for L in rb.via_only_layers], ["In1.Cu"])
        self.assertEqual([rb.layer_names[L] for L in RouterBoard(board, layers=["F.Cu", "B.Cu"]).layers],
                         ["F.Cu", "B.Cu"])

    def test_powerlab_router_time_limit(self):
        """Past the time limit the connections left are reported for hand routing, and the
        run still finishes with what it has."""
        try:
            import pcbnew  # noqa: F401
        except ImportError:
            self.skipTest("needs KiCad's Python")
        router, _pours = self._import_router()
        board = self._router_board([("R1", (5, 10), "SIG"), ("R2", (25, 10), "SIG")], ["SIG"])
        report = router.Router(board, time_limit=1e-9).run(["SIG"])
        self.assertEqual(report["routed"], 0)
        self.assertEqual(report["time_limit_left"], 1)
        self.assertEqual([c["reason"] for c in report["left"]], ["time limit"])

    def test_part_spacing(self):
        """check_part_spacing: parts closer than the lab's 1 mm pad to pad, and parts in a
        keep-out area on either side, measured on the board (the lab parts have no courtyard)."""
        import pcbnew  # KiCad's, or the stand-in above (which has no BOARD)
        if not hasattr(pcbnew, "BOARD"):
            self.skipTest("needs KiCad's Python")
        module = types.ModuleType("part_spacing")
        exec(self.new_file("python/commands/part_spacing.py"), module.__dict__)
        board = self._router_board([("C1", (5, 10), "A"), ("C2", (6.5, 10), "A"), ("C3", (15, 10), "B")], ["A", "B"])
        c3 = [fp for fp in board.GetFootprints() if fp.GetReference() == "C3"][0]
        c3.Flip(c3.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        path = os.path.join(tempfile.mkdtemp(), "spacing.kicad_pcb")
        pcbnew.SaveBoard(path, board)
        out = module.check(path, {"keepouts": [{"name": "encoder", "center": {"x": 15, "y": 10}, "diameter": 6}]})
        self.assertEqual([s["refs"] for s in out["spacing"]], [["C1", "C2"]])
        self.assertAlmostEqual(out["spacing"][0]["gap_mm"], 0.5, places=2)
        self.assertEqual([(k["ref"], k["side"]) for k in out["in_keepouts"]], [("C3", "B")])
        top_only = module.check(path, {"keepouts": [{"center": {"x": 15, "y": 10}, "diameter": 6, "sides": ["F"]}]})
        self.assertEqual(top_only["in_keepouts"], [])
        # passives the requirements let in (e.g. under an encoder ring) aren't hits
        allowed = module.check(path, {"keepouts": [{"center": {"x": 15, "y": 10}, "diameter": 6, "allow": ["c"]}]})
        self.assertEqual(allowed["in_keepouts"], [])
        self.assertEqual(allowed["rules"]["keepout_areas"][-1]["allowed"], ["C"])
        loose = module.check(path, {"minGap": 0.4})
        self.assertEqual(loose["spacing"], [])
        # a through pad of a bottom part is copper on top too: a top pad on it is a short
        tht = pcbnew.FOOTPRINT(board)
        tht.SetReference("Q9")
        tht.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(5), pcbnew.FromMM(10)))
        via = pcbnew.PAD(tht)
        via.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        via.SetLayerSet(pcbnew.PAD.PTHMask())
        via.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        via.SetSize(pcbnew.F_Cu, pcbnew.VECTOR2I(pcbnew.FromMM(0.6), pcbnew.FromMM(0.6)))
        via.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.3), pcbnew.FromMM(0.3)))
        via.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(5), pcbnew.FromMM(10)))
        via.SetNumber("1")
        via.SetNet(board.FindNet("B"))
        tht.Add(via)
        board.Add(tht)
        tht.Flip(tht.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        pcbnew.SaveBoard(path, board)
        out = module.check(path, {"refs": ["C1"]})
        self.assertEqual([(t["refs"], t["short"]) for t in out["on_through_pads"]], [(["C1", "Q9"], True)])

    def test_placement_is_measured_in_reviews(self):
        """Reviews measure spacing and keep-outs and look close up, instead of judging a
        whole-board view."""
        patch = self.patch()
        self.assertIn('"check_part_spacing"', patch)
        self.assertIn('+      region: z', patch)
        skills = os.path.join(ROOT, "skills")
        for name in ("powerlab-design-review", "powerlab-visual-review", "powerlab-autoroute"):
            with open(os.path.join(skills, name, "SKILL.md"), encoding="utf-8") as f:
                self.assertIn("check_part_spacing", f.read(), name)
        with open(os.path.join(skills, "powerlab-visual-review", "SKILL.md"), encoding="utf-8") as f:
            self.assertIn("region", f.read())

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

        # no via allowed: no path, and the pocket check sees it without a search
        path, _ = module.search([grid(wall), grid()], bytes(nx * ny), nx, ny, 0.1, [(2, 20, 0, 0, 0.0)],
                                {(35, 20, 1): (0, 0.0)}, (0, 0, nx - 1, ny - 1), costs)
        self.assertIsNone(path)
        self.assertTrue(module.enclosed([grid(wall), grid()], bytes(nx * ny), nx, ny, [(2, 20, 0, 0, 0.0)],
                                        {(35, 20, 1): (0, 0.0)}))
        self.assertFalse(module.enclosed([grid(wall), grid()], vias_ok, nx, ny, [(2, 20, 0, 0, 0.0)],
                                         {(35, 20, 1): (0, 0.0)}))

        # dearer diagonals: horizontal and vertical runs, 45 degrees only as corners
        def diagonal_cells(path):
            return sum(1 for s in path if s[3] != module.FREE and s[3] % 2)
        cheap = module.Costs(turn=0.4, via=2.0, min_run=2, diagonal=1.0, min_run_diag=1)
        dear = module.Costs(turn=0.4, via=2.0, min_run=2, diagonal=1.6, min_run_diag=3)
        to = {(30, 20, 0): (2, 0.0)}  # arrive heading south
        p1, _ = module.search([grid()], grid(), nx, ny, 0.1, [(2, 2, 0, 0, 0.0)], to, (0, 0, nx - 1, ny - 1), cheap)
        p2, _ = module.search([grid()], grid(), nx, ny, 0.1, [(2, 2, 0, 0, 0.0)], to, (0, 0, nx - 1, ny - 1), dear)
        self.assertLess(diagonal_cells(p2), diagonal_cells(p1))
        runs, run = [], 0
        for a, b in zip(p2, p2[1:]):
            if b[3] == a[3]:
                run += 1
            else:
                if a[3] % 2:
                    runs.append(run + 1)
                run = 0
        self.assertTrue(all(r >= 3 for r in runs), runs)  # no 45 degree corner shorter than 3 cells

        # no via hop: two layers, a wall on layer 0 that a via down and straight back up
        # would get round with a sharp turn; vias only after a straight run
        wall = [(i, 20) for i in range(0, 25)]
        hop, _ = module.search([grid(wall), grid()], bytes([1]) * (nx * ny), nx, ny, 0.1, [(10, 15, 0, 2, 0.0)],
                               {(10, 25, 0): (2, 0.0)}, (0, 0, nx - 1, ny - 1), dear)
        self.assertIsNotNone(hop)
        changes = [k for k, (a, b) in enumerate(zip(hop, hop[1:])) if a[2] != b[2]]
        for first, second in zip(changes, changes[1:]):
            self.assertGreaterEqual(second - first, 3)  # at least a 3-cell run between two vias

        # a via pays for the pour it cuts on every layer: with both layers poured, a via
        # pair under a short wall is cheap as a via alone, but dearer than going round
        # once the holes count
        wall = [(20, j) for j in range(5, ny)]
        pour = [bytes([3]) * (nx * ny)] * 2
        args = ([grid(wall), grid()], bytes([1]) * (nx * ny), nx, ny, 0.1, [(2, 30, 0, 0, 0.0)],
                {(35, 30, 0): (0, 0.0)}, (0, 0, nx - 1, ny - 1), costs)
        under, _ = module.search(*args, penalty=pour, via_cost=({}, 2.0))
        self.assertEqual({s[2] for s in under}, {0, 1})
        round_, _ = module.search(*args, penalty=pour, via_cost=({}, 2.0, 30.0))
        self.assertEqual({s[2] for s in round_}, {0})

        # a penalty steers the path away from cells without blocking them
        band = bytearray(nx * ny)
        for i in range(12, 28):
            for j in range(15, 25):
                band[j * nx + i] = 50
        path, _ = module.search([grid()], grid(), nx, ny, 0.1, [(2, 20, 0, 0, 0.0)], {(37, 20, 0): (0, 0.0)},
                                (0, 0, nx - 1, ny - 1), costs, penalty=[bytes(band)])
        self.assertIsNotNone(path)
        self.assertFalse(any(15 <= j < 25 and 12 <= i < 28 for i, j, *_ in path))

    def test_autoroute_can_be_undone(self):
        """File > Revert loads the routed file, so autoroute keeps the board from before it."""
        patch = self.patch()
        self.assertIn('result["backupPath"] = autoroute_backup.keep(before_path, board_path)', patch)
        self.assertIn('+            "undo_autoroute": self._handle_undo_autoroute,', patch)
        self.assertIn('"check_freerouting", "clean_up_routing", "undo_autoroute",', patch)
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

    def test_powerlab_route_tool(self):
        """powerlab_route: the PowerLab router as a background MCP tool. Its result is put on
        the board once, only if the board is unchanged since the start, and the board from
        before is kept for undo_autoroute."""
        patch = self.patch()
        for line in ('+            "powerlab_route": self._handle_powerlab_route,',
                     '+            "powerlab_route_status": self._handle_powerlab_route_status,',
                     '+    "powerlab_route",', '+    "powerlab_route_status",',  # TS tools
                     '+  "powerlab_route", // PowerLab patch',  # long command timeout
                     '"powerlab_route",\n+      "powerlab_route_status"]',  # registry category
                     'if (command === "powerlab_route_status")',
                     'out["backupPath"] = autoroute_backup.keep(job["input"], board_path)',
                     'sync = push_to_kicad(kboard, source, "Undo autoroute")'):
            self.assertIn(line, patch)
        commands = types.ModuleType("commands")
        backup = types.ModuleType("commands.autoroute_backup")
        exec(self.new_file("python/commands/autoroute_backup.py"), backup.__dict__)
        commands.autoroute_backup = backup
        plr = types.ModuleType("powerlab_route")
        exec(self.new_file("python/commands/powerlab_route.py"), plr.__dict__)
        saved = {k: sys.modules.get(k) for k in ("commands", "commands.autoroute_backup")}
        sys.modules.update({"commands": commands, "commands.autoroute_backup": backup})
        try:
            folder = tempfile.mkdtemp()
            plr.ROOT = os.path.join(folder, "jobs")
            board = os.path.join(folder, "b.kicad_pcb")
            with open(board, "w") as f:
                f.write("unrouted")
            self.assertEqual(plr.status(board), {"state": "none"})
            # what start() and the router process leave behind
            jd = plr.job_dir(board)
            start = plr._copy_project(board, os.path.join(jd, "input"))
            plr._write(os.path.join(jd, "job.json"), {"input": start, "input_sha1": plr._sha1(start)})
            result = os.path.join(jd, "result.kicad_pcb")
            with open(result, "w") as f:
                f.write("routed")
            plr._write(os.path.join(jd, "status.json"), {"state": "done", "result": result, "updated": time.time()})

            with open(board, "w") as f:
                f.write("edited during the run")
            self.assertFalse(plr.apply(board)["success"])
            with open(board) as f:
                self.assertEqual(f.read(), "edited during the run")  # not overwritten
            with open(board, "w") as f:
                f.write("unrouted")

            applied = plr.apply(board)
            self.assertTrue(applied["success"], applied)
            self.assertFalse(applied["saved_in_kicad"])
            with open(board) as f:
                self.assertEqual(f.read(), "routed")
            self.assertEqual(plr.status(board)["state"], "applied")
            self.assertFalse(plr.apply(board)["success"])  # once only
            self.assertTrue(backup.restore(board)["success"])  # undo_autoroute
            with open(board) as f:
                self.assertEqual(f.read(), "unrouted")

            # a router process that stopped writing its status is gone
            plr._write(os.path.join(jd, "status.json"), {"state": "running", "updated": time.time() - 3600})
            self.assertEqual(plr.status(board)["state"], "failed")
        finally:
            for k, v in saved.items():
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v

    def test_powerlab_route_runs_the_router(self):
        """The router process: Default-class nets are routed from scratch, nets with locked
        copper and pour nets are left out, and the routed board and a report are written."""
        root = self.router_package()
        for name in ("powerlab_route", "route_cleanup", "autoroute_backup", "freerouting_live"):
            with open(os.path.join(root, "commands", name + ".py"), "w", encoding="utf-8") as f:
                f.write(self.new_file(f"python/commands/{name}.py") + "\n")
        import pcbnew
        mm, P = pcbnew.FromMM, lambda x, y: pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
        board = pcbnew.BOARD()
        for a, b in (((0, 0), (30, 0)), ((30, 0), (30, 20)), ((30, 20), (0, 20)), ((0, 20), (0, 0))):
            edge = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
            edge.SetStart(P(*a)); edge.SetEnd(P(*b)); edge.SetLayer(pcbnew.Edge_Cuts); edge.SetWidth(mm(0.1))
            board.Add(edge)
        nets = {}
        for name in ("SIG", "HAND", "GND"):
            nets[name] = pcbnew.NETINFO_ITEM(board, name)
            board.Add(nets[name])
        for ref, (x, y), net in (("R1", (5, 5), "SIG"), ("R2", (25, 5), "SIG"), ("R3", (5, 15), "HAND"),
                                 ("R4", (25, 15), "HAND"), ("C1", (15, 10), "GND"), ("C2", (20, 10), "GND")):
            fp = pcbnew.FOOTPRINT(board)
            fp.SetReference(ref)
            fp.SetPosition(P(x, y))
            pad = pcbnew.PAD(fp)
            pad.SetShape(pcbnew.PAD_SHAPE_RECTANGLE)
            pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
            pad.SetLayerSet(pcbnew.PAD.SMDMask())
            pad.SetSize(pcbnew.F_Cu, P(1, 1))
            pad.SetPosition(P(x, y))
            pad.SetNumber("1")
            pad.SetNet(nets[net])
            fp.Add(pad)
            board.Add(fp)
        old = pcbnew.PCB_TRACK(board)  # an old, unlocked SIG track: routed again
        old.SetStart(P(5, 5)); old.SetEnd(P(15, 2)); old.SetWidth(mm(0.2)); old.SetLayer(pcbnew.F_Cu)
        old.SetNet(nets["SIG"])
        board.Add(old)
        hand = pcbnew.PCB_TRACK(board)  # hand-routed and locked: left alone
        hand.SetStart(P(5, 15)); hand.SetEnd(P(25, 15)); hand.SetWidth(mm(0.5)); hand.SetLayer(pcbnew.F_Cu)
        hand.SetNet(nets["HAND"]); hand.SetLocked(True)
        board.Add(hand)
        folder = tempfile.mkdtemp()
        os.makedirs(os.path.join(folder, "input"))
        source = os.path.join(folder, "input", "b.kicad_pcb")
        board.Save(source)

        sys.path.insert(0, root)
        try:
            for m in [m for m in sys.modules if m == "commands" or m.startswith("commands.")]:
                del sys.modules[m]
            from commands import powerlab_route as plr
            job = {"input": source, "nets": None, "pour_nets": ["GND"], "kicad_cli": None, "pitch": 0.1,
                   "turn": 1.5, "via": 4.0, "diagonal": 1.3, "layers": [1.0, 1.2], "min_run": 2,
                   "min_run_diag": 3, "max_nodes": 2000000}
            plr._write(os.path.join(folder, "job.json"), job)
            plr.run(folder)
        finally:
            sys.path.pop(0)
        status = plr._read(os.path.join(folder, "status.json"))
        self.assertEqual(status["state"], "done", status.get("error"))
        report = plr._read(os.path.join(folder, "report.json"))
        self.assertEqual((report["nets"], report["routed"], report["connections"]), (1, 1, 1), report)
        self.assertEqual(sorted(report["nets_left_out"]), ["GND", "HAND"])
        self.assertEqual(report["old_tracks_removed"], 1)
        routed = pcbnew.LoadBoard(status["result"])
        ends = {(round(pcbnew.ToMM(p.x), 3), round(pcbnew.ToMM(p.y), 3))
                for t in routed.GetTracks() if t.GetNetname() == "SIG" for p in (t.GetStart(), t.GetEnd())}
        self.assertIn((5.0, 5.0), ends)
        self.assertIn((25.0, 5.0), ends)
        self.assertNotIn((15.0, 2.0), ends)  # the old track is gone
        self.assertEqual([t.IsLocked() for t in routed.GetTracks() if t.GetNetname() == "HAND"], [True])

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
        self.assertIn("powerlab-placement", c["PANEL_NOTE"])  # block plan agreed before placing
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
