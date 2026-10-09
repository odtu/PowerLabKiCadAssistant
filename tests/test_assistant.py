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
        self.assertIn("Fan out the pour nets first", route)
        self.assertIn("Don't give every GND pad its own via", rules)


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
        names = ("say", "save_chat", "open_chat", "handle", "finished", "show_image")

        class Fake:
            pass

        for name in names:
            setattr(Fake, name, getattr(ClaudePanel, name))
        panel = Fake()
        panel.source = types.SimpleNamespace(editor="pcb")
        panel.session_id, panel.chat_cwd, panel.events = None, None, []
        panel.retry, panel.stale_session, panel.proc = None, False, None
        panel.got_result, panel.watched, panel.image_reads = False, {}, {}
        panel.last_text, panel.limits, panel.started, panel.effort = "", [], 0.0, "high"
        panel.emitted = []
        panel.emit = lambda kind, **data: panel.emitted.append(dict(data, kind=kind))
        panel.load_page = lambda: panel.emitted.clear()
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

    def test_echoed_kicad_state_is_not_shown(self):
        panel = self.fake_panel()
        state = "<kicad_state>\nOpen board: C:/p/b.kicad_pcb\nSelected footprints: U1\n</kicad_state>"
        panel.handle({"type": "assistant", "message": {"content": [
            {"type": "text", "text": "Which part do you mean?\n\n" + state},
            {"type": "text", "text": state}]}})
        self.assertEqual([e["text"] for e in panel.emitted], ["Which part do you mean?"])
        self.assertEqual(panel.last_text, "Which part do you mean?")

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
        self.source.selected, self.source.clip_seq = ["R1 (10k)"], 0
        self.source.poll_clipboard = lambda: None
        window = types.SimpleNamespace(
            foreground_title=lambda: self.foreground,
            find_editor=lambda kind="Schematic Editor": 1 if "schematic" in self.open else None,
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

    def test_gerbers_can_be_zipped(self):
        # Issue #24: PCBWay wants the Gerbers zipped, but only kicad-cli was allowed in the shell.
        c = self.constants()
        # Compress-Archive is blocked by Claude Code as a file write; Windows' tar is not.
        self.assertIn("PowerShell(tar -a -cf:*)", c["ALLOWED_TOOLS"])
        self.assertNotIn("PowerShell(tar:*)", c["ALLOWED_TOOLS"])  # never extraction
        self.assertIn(r"tar -a -cf fab\gerbers.zip -C fab\gerbers *", c["PANEL_NOTE"])

    def test_board_minimums_are_the_pcbway_floor(self):
        with open(os.path.join(ROOT, "skills", "powerlab-pcb-design-rules", "SKILL.md"), encoding="utf-8") as f:
            rules = f.read()
        self.assertIn("| Minimum track width | 0.15 mm |", rules)
        self.assertIn("| Default | 0.2 mm | 0.2 mm |", rules)  # lab default stays in the net class


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
