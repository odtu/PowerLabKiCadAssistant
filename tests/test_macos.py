"""macOS support: paths, KiCad.app's Python, the window/clipboard/process helpers, the
panel's notes and install.sh. The pure parts run on every platform (CI is Windows and
Linux); the ones that need macOS itself (a Unix socket, osascript, NSPasteboard) say so.

    <KiCad.app>/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 -m unittest discover -s tests -v
"""

import importlib
import importlib.util
import os
import re
import shlex
import socket
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    import wx  # noqa: F401
except ImportError:  # outside KiCad: the stand-ins test_assistant also uses
    wx = types.ModuleType("wx")
    wx.FindWindowByName = lambda *args: None
    wx.Frame = object
    wx.html2 = types.ModuleType("wx.html2")
    sys.modules["wx"] = wx
    sys.modules["wx.html2"] = wx.html2
try:
    import pcbnew  # noqa: F401
except ImportError:
    pcbnew = types.ModuleType("pcbnew")
    pcbnew.ActionPlugin = type("ActionPlugin", (), {"register": lambda self: None})
    sys.modules["pcbnew"] = pcbnew
os.environ["POWERLAB_ASSISTANT_STANDALONE"] = "1"
sys.path.insert(0, os.path.join(ROOT, "plugin"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from powerlab_assistant import common, config, i18n, instances, kicad_window_mac as mac, updates  # noqa: E402
import configure_kicad  # noqa: E402

ON_MAC = sys.platform == "darwin"


def make_app(root, name="KiCad.app"):
    """A KiCad.app skeleton: kicad-cli and the framework's python3."""
    app = os.path.join(root, name)
    for rel in ("Contents/MacOS/kicad-cli", config.MAC_PYTHON):
        path = os.path.join(app, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w").close()
    return app


class MacPathTests(unittest.TestCase):
    """Where KiCad, its Python and the settings are on macOS."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        for name, value in (("IS_MAC", True), ("IS_WINDOWS", False), ("EXE", ""),
                            ("config", lambda: {})):
            patcher = mock.patch.object(config, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_app_of_a_path_inside_the_bundle(self):
        app = os.path.join(os.sep, "Volumes", "Disk", "Apps", "KiCad", "KiCad.app")
        python = os.path.join(app, *config.MAC_PYTHON.split("/"))
        self.assertEqual(config._app_of(python), app)
        self.assertEqual(config._app_of(os.path.join(os.sep, "usr", "bin", "python3")), "")

    def test_finds_kicad_wherever_the_app_is(self):
        """Not only /Applications: KiCad's own Python says which app it belongs to."""
        app = make_app(os.path.join(self.tmp.name, "Apps"))
        python = os.path.join(app, *config.MAC_PYTHON.split("/"))
        with mock.patch.object(sys, "executable", python), mock.patch.object(config, "MAC_APP", "/nowhere"):
            self.assertEqual(config.kicad_bin(), os.path.join(app, "Contents", "MacOS"))
            self.assertEqual(config.kicad_python(gui=True), python)

    def test_from_the_venv_kicad_makes_for_a_plugin(self):
        """The schematic button runs in a venv: sys.base_prefix is still inside KiCad.app."""
        app = make_app(self.tmp.name)
        base = os.path.join(app, "Contents", "Frameworks", "Python.framework", "Versions", "3.9")
        with mock.patch.object(sys, "executable", os.path.join(self.tmp.name, "venv", "bin", "python")), \
                mock.patch.object(sys, "base_prefix", base), mock.patch.object(config, "MAC_APP", "/nowhere"):
            self.assertEqual(config.kicad_bin(), os.path.join(app, "Contents", "MacOS"))
            self.assertTrue(config.kicad_python().startswith(app))

    def test_installer_settings_win(self):
        app = make_app(self.tmp.name, "Chosen.app")
        other = make_app(self.tmp.name)
        python = os.path.join(app, *config.MAC_PYTHON.split("/"))
        with mock.patch.object(config, "config", lambda: {"kicad_bin": os.path.join(app, "Contents", "MacOS"),
                                                          "kicad_python": python}), \
                mock.patch.object(config, "MAC_APP", other):
            self.assertEqual(config.kicad_bin(), os.path.join(app, "Contents", "MacOS"))
            self.assertEqual(config.kicad_python(), python)

    def test_nothing_found(self):
        with mock.patch.object(config, "MAC_APP", os.path.join(self.tmp.name, "none.app")), \
                mock.patch.object(sys, "executable", "/usr/bin/python3"), \
                mock.patch.object(sys, "base_prefix", "/usr"):
            self.assertEqual(config.kicad_bin(), "")
            self.assertEqual(config.kicad_python(), "")

    @unittest.skipUnless(ON_MAC, "macOS folders")
    def test_settings_folders(self):
        home = os.path.expanduser("~")
        self.assertEqual(config.CONFIG_DIR, os.path.join(home, "Library", "Application Support",
                                                         "PowerLabKiCadAssistant"))
        self.assertEqual(config.KICAD_CONFIG, os.path.join(home, "Library", "Preferences", "kicad", "10.0"))
        self.assertEqual(configure_kicad.KICAD_CONFIG, config.KICAD_CONFIG)


class MacProcessTests(unittest.TestCase):
    PS = ("    1     0 /sbin/launchd\n"
          "  501     1 /Applications/KiCad/KiCad.app/Contents/MacOS/kicad\n"
          "  777   501 /Users/me/Library/Caches/kicad/10.0/python-environments/x/bin/python3\n"
          "  778   777 /Volumes/My Disk/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python\n"
          "  900     1 /Applications/KiCad/KiCad.app/Contents/Applications/eeschema.app/Contents/MacOS/eeschema\n"
          "garbage line\n")

    def test_parse_ps(self):
        procs = mac.parse_ps(self.PS)
        self.assertEqual(procs[501], (1, "kicad"))
        self.assertEqual(procs[778], (777, "Python"))  # a path with a space
        self.assertEqual(procs[900], (1, "eeschema"))
        self.assertEqual(len(procs), 5)

    def test_the_kicad_a_button_was_pressed_in(self):
        procs = mac.parse_ps(self.PS)
        self.assertEqual(mac.ancestor_in(procs, 778), 501)
        self.assertEqual(mac.ancestor_in(procs, 501), 501)
        self.assertEqual(mac.ancestor_in(procs, 900), 900)  # eeschema started on its own
        self.assertEqual(mac.ancestor_in(procs, 1), 0)
        self.assertEqual(mac.ancestor_in({5: (6, "a"), 6: (5, "b")}, 5), 0)  # a loop ends

    @unittest.skipIf(os.name == "nt", "os.kill(pid, 0) terminates the process on Windows")
    def test_process_running(self):
        self.assertTrue(mac.process_running(os.getpid()))
        child = subprocess.Popen([sys.executable, "-c", "pass"])
        child.wait()
        self.assertFalse(mac.process_running(child.pid))

    def test_no_window_list_is_not_a_stuck_kicad(self):
        """Without the Accessibility permission no window can be seen: not 'stuck'."""
        with mock.patch.object(mac, "processes", lambda: {501: (1, "kicad"), 502: (1, "kicad")}), \
                mock.patch.object(mac, "window_titles", lambda pid: None if pid == 501 else []):
            self.assertEqual(sorted(mac.kicad_processes()), [(501, True), (502, False)])

    @unittest.skipUnless(ON_MAC, "ps on macOS")
    def test_live_process_table(self):
        procs = mac.processes()
        self.assertEqual(procs[os.getpid()][0], os.getppid())
        self.assertEqual(mac.kicad_ancestor(os.getpid()), 0)  # not started by KiCad


# A bit of KiCad's Turkish catalogue (internat/tr/kicad.mo), as gettext reads it.
TR = {"&File": "&Dosya", "&Edit": "&Düzenle", "&Save": "&Kaydet", "Revert": "Geri al", "Copy": "Kopyala",
      "Schematic Editor": "Şematik Düzenleyici", "PCB Editor": "Baskı Devre Düzenleyici",
      "Yes": "Evet", "No": "Hayır",
      "Revert '%s' (and all sub-sheets) to last version saved?":
          "'%s' (ve tüm alt sayfaları) en son kaydedilen sürüme geri döndürüyor musunuz?",
      ("%d item", 0): "%d öğe"}


class MacWindowTests(unittest.TestCase):
    """System Events is replaced by a fake KiCad: its windows, menus and front window."""

    def setUp(self):
        self.titles = {501: ["*esp [esp/Power] — Schematic Editor", "esp — PCB Editor", "KiCad 10.0"]}
        self.bar = ["Apple", "KiCad", "File", "Edit"]
        self.front = None  # KiCad's window 1 after it was raised; None: the one raised
        self.scripts, self.background = [], []
        self.real_osascript = mac.osascript
        patches = [mock.patch.object(mac, "window_titles", lambda pid: self.titles.get(pid)),
                   mock.patch.object(mac, "menu_bar", lambda pid: self.bar),
                   mock.patch.object(mac, "processes", lambda: {501: (1, "kicad"), 7: (1, "Finder")}),
                   mock.patch.object(mac, "osascript", self.fake_osascript),
                   mock.patch.object(mac, "frontmost_pid", lambda: 0),  # not the real Mac's
                   mock.patch.object(mac, "osascript_in_background", lambda s: self.background.append(s) or True),
                   mock.patch.object(mac, "preferred_languages", lambda: ["tr_TR", "tr"]),
                   mock.patch.object(mac, "catalog", lambda lang: TR if lang == "tr" else {}),
                   mock.patch.object(mac, "_languages", {}), mock.patch.object(mac, "_unsure", {})]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def fake_osascript(self, script):
        self.scripts.append(script)
        if "name of every menu item" in script:
            raised = re.search(r'first window whose name is "([^"]*)"', script).group(1)
            items = ["Yeni", "Aç…", "Kaydet", "Farklı Kaydet...", "Geri al"] if "Dosya" in script else \
                ["New", "Open…", "Save", "Save As...", "Revert"]
            return mac.SEPARATOR.join(["7", self.front or raised] + items)
        return ""

    def turkish(self):
        self.titles[501] = ["*esp [esp/Power] — Şematik Düzenleyici", "esp — Baskı Devre Düzenleyici",
                            "KiCad 10.0"]
        self.bar = ["Apple", "KiCad", "Dosya", "Düzenle", "Window"]

    def test_finds_the_editor_and_reads_its_title(self):
        sch = mac.find_editor(pid=501)
        self.assertEqual(sch, mac.Window(501, "*esp [esp/Power] — Schematic Editor",
                                         "*esp [esp/Power] — Schematic Editor"))
        self.assertEqual(mac.find_editor("PCB Editor").title, "esp — PCB Editor")
        self.assertIsNone(mac.find_editor(pid=999))
        self.assertTrue(mac.is_dirty(sch))
        self.assertEqual(mac.current_sheet(sch), "esp/Power")
        self.assertEqual(mac.window_pid(sch), 501)

    def test_title_followed_after_save_and_sheet_change(self):
        sch = mac.find_editor(pid=501)
        self.titles[501][0] = "esp [esp/MCU] — Schematic Editor"  # saved, another sheet
        self.assertFalse(mac.is_dirty(sch))
        self.assertEqual(mac.current_sheet(sch), "esp/MCU")

    def test_menu_labels(self):
        self.assertEqual(mac.menu_label("Revert…"), "Revert")
        self.assertEqual(mac.menu_label("Save As..."), "Save As")
        self.assertEqual(mac.find_label(["New", "Open…", "Save", "Revert"], "Revert"), 4)
        self.assertEqual(mac.find_label(["New"], "Save"), 0)

    def test_menu_command_brings_the_window_to_the_front_and_gives_the_focus_back(self):
        sch = mac.find_editor(pid=501)
        self.assertTrue(mac.menu_command(sch, "File", "Revert"))
        script = self.scripts[-1]
        self.assertIn("set frontmost to true", script)
        self.assertIn('perform action "AXRaise" of (first window whose name is '
                      '"*esp [esp/Power] — Schematic Editor")', script)
        self.assertIn("first process whose unix id is 501", script)
        click, = self.background  # not waited for: Revert's dialog would hold it
        self.assertIn('click menu item 5 of menu 1 of menu bar item "File"', click)
        self.assertIn("set frontmost of (first process whose unix id is 7) to true", click)
        self.assertFalse(mac.menu_command(sch, "File", "Plot"))

    def test_menu_command_refuses_another_window_in_front(self):
        """File > Save with the PCB editor in front would save the board."""
        self.front = "esp — PCB Editor"
        self.assertFalse(mac.menu_command(mac.find_editor(pid=501), "File", "Save"))
        self.assertEqual(self.background, [])
        self.assertIn("set frontmost of (first process whose unix id is 7) to true", self.scripts[-1])

    def test_kicad_in_turkish(self):
        """KiCad shows its own language: Dosya > Kaydet, '— Şematik Düzenleyici'."""
        self.turkish()
        sch = mac.find_editor(pid=501)
        self.assertEqual(sch.title, "*esp [esp/Power] — Schematic Editor")  # what the panel checks
        self.assertEqual(sch.shown, "*esp [esp/Power] — Şematik Düzenleyici")  # what is on screen
        self.assertEqual(mac.current_sheet(sch), "esp/Power")
        self.assertEqual(mac.find_editor("PCB Editor").shown, "esp — Baskı Devre Düzenleyici")
        self.assertTrue(mac.menu_command(sch, "File", "Save"))
        self.assertIn('menu bar item "Dosya"', self.scripts[-1])
        self.assertIn('(first window whose name is "*esp [esp/Power] — Şematik Düzenleyici")', self.scripts[-1])
        self.assertIn('click menu item 3 of menu 1 of menu bar item "Dosya"', self.background[-1])

    def test_language_from_titles_when_the_menu_bar_tells_nothing(self):
        """While a dialog has KiCad's focus, its menu bar is just Apple, KiCad, Window."""
        self.turkish()
        self.bar = ["Apple", "KiCad", "Window"]
        self.assertEqual(mac.localize(501, "File"), "Dosya")
        self.assertEqual(mac.foreground_title(), "")  # nothing in front in the fake

    def test_unknown_language_is_asked_again_later(self):
        self.titles[501] = ["KiCad 10.0"]
        self.bar = ["Apple", "KiCad", "Window"]
        self.assertEqual(mac.localize(501, "File"), "File")
        self.assertNotIn(501, mac._languages)  # not taken for English
        self.turkish()
        with mock.patch.object(mac, "_unsure", {}):
            self.assertEqual(mac.localize(501, "File"), "Dosya")

    def test_translate(self):
        self.assertEqual(mac.translate(TR, "File"), "Dosya")  # msgid "&File"
        self.assertEqual(mac.translate(TR, "Revert"), "Geri al")
        self.assertIsNone(mac.translate(TR, "Plot"))
        self.assertIsNone(mac.translate(TR, "%d item"))  # plural entries are keyed by tuples
        self.assertEqual(mac.language_of(["File"], [], ["tr"]), "")
        self.assertEqual(mac.language_of(["Dosya"], [], ["de", "tr"]), "tr")
        self.assertIsNone(mac.language_of(["Window"], ["KiCad 10.0"], ["tr"]))

    def test_applescript_strings(self):
        self.assertEqual(mac.quote('a "b" \\c'), '"a \\"b\\" \\\\c"')

    def test_revert_confirmation(self):
        """KiCad for macOS asks Yes/No; Yes only on the revert question."""
        question = ("Onay", "'/Users/me/b.kicad_sch' (ve tüm alt sayfaları) en son kaydedilen sürüme "
                            "geri döndürüyor musunuz?")
        other = ("Onay", "Kaydedilmemiş değişiklikler silinsin mi?")
        self.assertEqual(mac.dialog_choice([("", []), (" ".join(other), ["Evet", "Hayır"]),
                                            (" ".join(question), ["Hayır", "Evet"])], {"Revert"}, TR), (3, "Evet"))
        self.assertIsNone(mac.dialog_choice([(" ".join(other), ["Evet", "Hayır"])], {"Revert"}, TR))
        english = "Revert '/x/b.kicad_sch' (and all sub-sheets) to last version saved?"
        self.assertEqual(mac.dialog_choice([(english, ["No", "Yes"])], {"Revert"}, {}), (1, "Yes"))
        self.assertEqual(mac.dialog_choice([("Revert changes?", ["Cancel", "Revert"])], {"Revert"}, {}),
                         (1, "Revert"))  # a Revert button, as on Windows
        self.assertEqual(mac.dialog_choice([("x", ["Geri al"])], {"Revert"}, TR), (1, "Geri al"))
        self.assertFalse(mac.asks("Revert", {}, "Revert '%s' to last version saved?"))

    def test_dialog_click(self):
        reply = ("" + mac.SEPARATOR + mac.WINDOW_SEP
                 + "Revert '/x/b.kicad_sch' (and all sub-sheets) to last version saved?"
                 + mac.SEPARATOR + "No" + mac.ITEM_SEP + "Yes" + mac.WINDOW_SEP)
        with mock.patch.object(mac, "osascript", lambda script: self.scripts.append(script) or
                               (reply if "repeat with w in windows" in script else "")):
            self.assertTrue(mac.click_dialog_button(501, {"Revert"}))
        self.assertIn('click button "Yes" of window 2', self.scripts[-1])

    def test_access_error_is_recognised(self):
        failed = types.SimpleNamespace(returncode=1, stdout="",
                                       stderr="execution error: Not authorized to send Apple events (-1743)")
        with mock.patch.object(mac.subprocess, "run", lambda *a, **k: failed):
            self.assertIsNone(self.real_osascript("x"))
        self.assertIn("Accessibility", mac.access_error)
        ok = types.SimpleNamespace(returncode=0, stdout="fine\n", stderr="")
        with mock.patch.object(mac.subprocess, "run", lambda *a, **k: ok):
            self.assertEqual(self.real_osascript("x"), "fine")
        self.assertEqual(mac.access_error, "")

    def test_background_click_is_reaped(self):
        started = []

        class Proc:
            def __init__(self, args, **kw):
                started.append(args)

            def wait(self, timeout=None):
                return 0

        with mock.patch.object(mac.subprocess, "Popen", Proc):
            self.assertTrue(type(self).real_background("tell x"))
        self.assertEqual(started, [["osascript", "-e", "tell x"]])

    real_background = staticmethod(mac.osascript_in_background)

    def test_schematic_selection_from_the_users_copy(self):
        """No Edit > Copy driven on macOS (it would pull KiCad to the front on every send)."""
        from powerlab_assistant import sources
        source = sources.KiCadSource.__new__(sources.KiCadSource)
        polled = []
        source.poll_clipboard = lambda: polled.append(1)
        source.editor_window = lambda: self.fail("no window driven")
        done = []
        with mock.patch.object(sources, "kicad_window", mac):
            source.capture_selection(None, lambda: done.append(1))
        self.assertEqual((polled, done), ([1], [1]))


class MacFastWindowTests(unittest.TestCase):
    """KiCad's windows are read through the Accessibility API (under 1 ms), AppleScript
    (130-170 ms a call) only when it can't tell: the panel asks every second."""

    def test_titles_from_the_accessibility_api(self):
        with mock.patch.object(mac, "ax_window_titles", lambda pid: ["esp — Şematik Düzenleyici"]), \
                mock.patch.object(mac, "osascript", side_effect=AssertionError("no AppleScript")):
            self.assertEqual(mac.window_titles(501), ["esp — Şematik Düzenleyici"])

    def test_titles_fall_back_to_applescript(self):
        with mock.patch.object(mac, "ax_window_titles", lambda pid: None), \
                mock.patch.object(mac, "osascript", lambda script: "a" + mac.SEPARATOR + "b"):
            self.assertEqual(mac.window_titles(501), ["a", "b"])

    def test_foreground_title_without_applescript(self):
        no_script = mock.patch.object(mac, "osascript", side_effect=AssertionError("no AppleScript"))
        with no_script, mock.patch.object(mac, "frontmost_pid", lambda: 42):
            self.assertEqual(mac.foreground_title(501), "")  # the panel, or any other app
        with no_script, mock.patch.object(mac, "frontmost_pid", lambda: 501), \
                mock.patch.object(mac, "ax_focused_title", lambda pid: "esp — Schematic Editor"), \
                mock.patch.object(mac, "_languages", {501: {}}):
            self.assertEqual(mac.foreground_title(501), "esp — Schematic Editor")

    def test_find_editor_of_a_known_kicad_lists_no_processes(self):
        with mock.patch.object(mac, "processes", side_effect=AssertionError("no ps")), \
                mock.patch.object(mac, "window_titles", lambda pid: ["esp — Schematic Editor"]), \
                mock.patch.object(mac, "_languages", {501: {}}):
            self.assertEqual(mac.find_editor(pid=501).title, "esp — Schematic Editor")


class MacPermissionTests(unittest.TestCase):
    def test_settings_links(self):
        self.assertTrue(mac.settings_url("accessibility").endswith("?Privacy_Accessibility"))
        self.assertTrue(mac.settings_url("automation").endswith("?Privacy_Automation"))
        self.assertTrue(mac.settings_url("files").endswith("?Privacy_FilesAndFolders"))

    def test_folder_access(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(mac.folder_access(folder), "granted")
            with mock.patch.object(mac.os, "listdir", side_effect=PermissionError):
                self.assertEqual(mac.folder_access(folder), "denied")
            self.assertIsNone(mac.folder_access(os.path.join(folder, "missing")))

    def test_sheet_items(self):
        with tempfile.TemporaryDirectory() as folder, \
                mock.patch.object(mac, "accessibility_trusted", lambda ask=False: False), \
                mock.patch.object(mac, "automation_permission", lambda ask=False: "not_asked"):
            items = mac.permissions([("project", folder), ("library", os.path.join(folder, "x"))])
        self.assertEqual(items, [{"id": "accessibility", "state": "denied"},
                                 {"id": "automation", "state": "not_asked"},
                                 {"id": "project", "state": "granted", "path": folder}])

    @unittest.skipUnless(sys.platform == "darwin", "macOS only")
    def test_live_checks_answer(self):
        self.assertIn(mac.automation_permission(), ("granted", "denied", "not_asked", "unknown"))
        self.assertIsInstance(mac.accessibility_trusted(), bool)
        self.assertIsInstance(mac.frontmost_pid(), int)
        self.assertIn(mac.ax_window_titles(os.getpid()), (None, []))  # no windows here


class DockIconTests(unittest.TestCase):
    """The panel runs on KiCad's Python, so the Dock showed Python's rocket for it."""

    def test_panel_sets_its_dock_icon_on_macos(self):
        with open(os.path.join(ROOT, "plugin", "powerlab_assistant", "standalone.py"), encoding="utf-8") as f:
            source = f.read()
        self.assertIn('set_dock_icon(os.path.join(os.path.dirname(__file__), "app_icon.png"))', source)
        self.assertIn('if sys.platform == "darwin":', source)
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "plugin", "powerlab_assistant", "app_icon.png")))

    @unittest.skipUnless(sys.platform == "darwin", "macOS")
    def test_a_missing_image_is_not_set(self):
        from powerlab_assistant import kicad_window_mac
        self.assertFalse(kicad_window_mac.set_dock_icon(os.path.join(ROOT, "no-such-icon.png")))


class MacSocketTests(unittest.TestCase):
    @unittest.skipUnless(hasattr(socket, "AF_UNIX") and os.name != "nt", "Unix sockets")
    def test_lists_only_sockets(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.addCleanup(server.close)
            path = os.path.join(tmp, "api-42.sock")
            server.bind(path)
            open(os.path.join(tmp, "api.sock"), "w").close()  # a plain file isn't one
            self.assertEqual(mac.socket_paths(tmp), {path.lower()})
            self.assertEqual(mac.socket_paths(os.path.join(tmp, "missing")), set())

    @unittest.skipUnless(ON_MAC, "KiCad's socket folder on macOS")
    def test_socket_folder_is_tmp(self):
        self.assertEqual(instances.SOCKET_DIR, "/tmp/kicad")

    def test_placeholder_only_where_sockets_are_pipes(self):
        with tempfile.TemporaryDirectory() as tmp:
            shared = os.path.join(tmp, "kicad", "api.sock")
            with mock.patch.object(instances, "SOCKET_DIR", os.path.dirname(shared)), \
                    mock.patch.object(instances, "SHARED", shared), \
                    mock.patch.object(instances, "NEEDS_PLACEHOLDER", False):
                instances.ensure_placeholder()
                self.assertFalse(os.path.exists(shared))
        self.assertEqual(instances.NEEDS_PLACEHOLDER, os.name == "nt")


@unittest.skipUnless(ON_MAC, "NSPasteboard")
class MacClipboardTests(unittest.TestCase):
    def test_save_and_restore(self):
        saved = mac.save_clipboard()
        self.assertIsNotNone(saved)
        self.addCleanup(mac.restore_clipboard, saved)
        before = mac.clipboard_sequence()
        subprocess.run(["pbcopy"], input="(lib_id \"Device:R\") ünïcode".encode(), check=True)
        self.assertNotEqual(mac.clipboard_sequence(), before)
        copied = mac.save_clipboard()
        mac.restore_clipboard([[("public.utf8-plain-text", "restored ✓".encode())]])
        self.assertEqual(subprocess.run(["pbpaste"], capture_output=True).stdout.decode(), "restored ✓")
        mac.restore_clipboard(copied)
        self.assertEqual(subprocess.run(["pbpaste"], capture_output=True).stdout.decode(),
                         "(lib_id \"Device:R\") ünïcode")


class MacConsoleTests(unittest.TestCase):
    def test_terminal_script(self):
        script = common.terminal_script(["/opt/claude", "--append-system-prompt", "it's \"KiCad\"; rm -rf ~"],
                                        "/Users/me/My Board", {"PATH": "/a b:/c", "KICAD_API_SOCKET": "ipc:///tmp/kicad/api.sock",
                                                               "SECRET": "x"})
        lines = script.splitlines()
        self.assertEqual(lines[0], "#!/bin/bash")
        self.assertIn("export PATH='/a b:/c'", lines)
        self.assertIn("export KICAD_API_SOCKET=ipc:///tmp/kicad/api.sock", lines)
        self.assertNotIn("SECRET", script)  # only what the session needs
        self.assertIn("cd '/Users/me/My Board'", lines)
        self.assertEqual(shlex.split(lines[-1]), ["/opt/claude", "--append-system-prompt",
                                                  "it's \"KiCad\"; rm -rf ~"])

    @unittest.skipUnless(ON_MAC, "bash on macOS")
    def test_terminal_script_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "out")
            script = common.terminal_script(["/bin/sh", "-c", 'printf "%s|%s" "$PWD" "$KICAD_API_TOKEN" > "$0"', out],
                                            tmp, {"KICAD_API_TOKEN": "t 1"})
            path = os.path.join(tmp, "run.command")
            with open(path, "w") as f:
                f.write(script)
            subprocess.run(["/bin/bash", path], check=True)
            with open(out) as f:
                where, token = f.read().split("|")
            self.assertEqual(os.path.realpath(where), os.path.realpath(tmp))
            self.assertEqual(token, "t 1")
            self.assertFalse(os.path.exists(path))  # it removes itself

    def test_clean_env_has_homebrew_and_kicad(self):
        with mock.patch.object(common, "EXTRA_PATH", ["/opt/homebrew/bin"]), \
                mock.patch.object(config, "IS_WINDOWS", False), \
                mock.patch.object(config, "kicad_bin", lambda: "/K/KiCad.app/Contents/MacOS"), \
                mock.patch.dict(os.environ, {"PATH": "/usr/bin:/bin", "PYTHONHOME": "/x",
                                             "__PYVENV_LAUNCHER__": "/y"}):
            env = common.clean_env()
        self.assertEqual(env["PATH"].split(os.pathsep)[:2], ["/K/KiCad.app/Contents/MacOS", "/opt/homebrew/bin"])
        self.assertNotIn("PYTHONHOME", env)
        self.assertNotIn("__PYVENV_LAUNCHER__", env)

    @unittest.skipIf(os.name == "nt", "a file without .exe isn't a program on Windows")
    def test_finds_claude_outside_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            claude = os.path.join(tmp, "claude")
            with open(claude, "w") as f:
                f.write("#!/bin/sh\n")
            os.chmod(claude, 0o755)
            with mock.patch.object(common, "EXTRA_PATH", [tmp]), mock.patch.dict(os.environ, {"PATH": "/nowhere"}):
                self.assertEqual(common.find_claude(), claude)


class MacPanelTests(unittest.TestCase):
    def setUp(self):
        from powerlab_assistant import panel
        self.panel = panel

    def test_note_for_bash_and_forward_slashes(self):
        note = self.panel.platform_note(self.panel.PANEL_NOTE if config.IS_WINDOWS else
                                        self.windows_note(), windows=False)
        self.assertNotIn("PowerShell", note)
        self.assertNotIn("\\", note)
        self.assertIn("Bash tool: `zip -j fab/gerbers.zip fab/gerbers/*`", note)
        self.assertIn("documents/<name>.md", note)
        self.assertIn("design-review/design-review.md", note)
        self.assertIn("git, ls, cat and every other command are blocked", note)

    def windows_note(self):
        """PANEL_NOTE as Windows builds it, from panel.py's source."""
        with mock.patch.object(config, "IS_WINDOWS", True):
            src = importlib.util.find_spec("powerlab_assistant.panel")
            module = importlib.util.module_from_spec(src)
            src.loader.exec_module(module)
        self.assertIn("PowerShell tool: `tar -a -cf fab\\gerbers.zip", module.PANEL_NOTE)
        return module.PANEL_NOTE

    def test_every_windows_bit_is_replaced(self):
        """Each POSIX_NOTE replacement still matches the note (a reworded note would
        otherwise keep its PowerShell advice on macOS)."""
        note = self.windows_note() if not config.IS_WINDOWS else self.panel.PANEL_NOTE
        for old, _ in self.panel.POSIX_NOTE:
            self.assertIn(old, note)
        self.assertEqual(self.panel.platform_note(note, windows=True), note)

    def test_allowed_shell_commands(self):
        if config.IS_WINDOWS:
            self.assertIn("PowerShell(tar -a -cf:*)", self.panel.ALLOWED_TOOLS)
        else:
            self.assertIn("Bash(zip -j:*)", self.panel.ALLOWED_TOOLS)
            self.assertFalse([t for t in self.panel.ALLOWED_TOOLS if t.startswith("PowerShell")])
        self.assertIn("Bash(kicad-cli:*)", self.panel.ALLOWED_TOOLS)

    def test_posix_tool_list(self):
        """Read from panel.py's source, so it's checked on Windows too."""
        import ast
        with open(os.path.join(ROOT, "plugin", "powerlab_assistant", "panel.py"), encoding="utf-8") as f:
            tree = ast.parse(f.read())
        lists = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body
                 if isinstance(n, ast.Assign)
                 and getattr(n.targets[0], "id", "") in ("ALLOWED_TOOLS", "POSIX_ALLOWED_TOOLS")}
        posix, windows = lists["POSIX_ALLOWED_TOOLS"], lists["ALLOWED_TOOLS"]
        self.assertEqual([t for t in posix if "(" not in t], [t for t in windows if "(" not in t])
        self.assertEqual([t for t in posix if "(" in t], ["Bash(kicad-cli:*)", "Bash(zip -j:*)"])

    def test_install_deny_for_a_mac_path(self):
        with mock.patch.object(config, "mcp_path",
                               lambda: "/Users/me/Library/Application Support/PowerLabKiCadAssistant/KiCAD-MCP-Server"):
            self.assertEqual(self.panel.install_denies(),
                             ["Edit(//Users/me/Library/Application Support/PowerLabKiCadAssistant/KiCAD-MCP-Server/**)"])

    def test_panel_window_is_not_a_tool_window_on_macos(self):
        """A macOS tool window (NSPanel) hides while its app isn't active: the panel, started
        in the background by KiCad's button, never showed."""
        with open(os.path.join(ROOT, "plugin", "powerlab_assistant", "panel.py"), encoding="utf-8") as f:
            source = f.read()
        self.assertIn("(wx.FRAME_TOOL_WINDOW if config.IS_WINDOWS else 0)", source)
        self.assertNotIn("wx.FRAME_TOOL_WINDOW | wx.STAY_ON_TOP", source)
        present = source.split("    def present(self):", 1)[1].split("\n    def ", 1)[0]
        self.assertIn("bring_app_forward()", present)

    def test_web_backend(self):
        html2 = types.SimpleNamespace(WebViewBackendEdge="edge", WebViewBackendDefault="default")
        with mock.patch.object(self.panel.wx, "html2", html2, create=True):
            with mock.patch.object(config, "IS_WINDOWS", False):
                self.assertEqual(self.panel.web_backend(), "default")
            with mock.patch.object(config, "IS_WINDOWS", True):
                self.assertEqual(self.panel.web_backend(), "edge")


class MacLanguageTests(unittest.TestCase):
    def test_preferred_language(self):
        self.assertEqual(i18n.mac_language('(\n    "tr-TR",\n    "en-TR"\n)'), "tr_TR")
        self.assertEqual(i18n.mac_language('(\n    "de"\n)'), "de")
        self.assertEqual(i18n.mac_language('(\n    "zh-Hant-TW"\n)'), "zh_TW")
        self.assertEqual(i18n.mac_language('(\n    "zh-Hant"\n)'), "zh_TW")
        self.assertEqual(i18n.mac_language('(\n    "zh-Hans-CN"\n)'), "zh_CN")
        self.assertEqual(i18n.mac_language('(\n    "pt-BR"\n)'), "pt_BR")
        self.assertEqual(i18n.mac_language(""), "")

    def test_detect_uses_it(self):
        for name, code in (("tr_TR", "tr"), ("zh_TW", "zh-TW"), ("zh_CN", "zh"), ("xx_YY", "en")):
            with mock.patch.object(i18n, "system_language", lambda name=name: name):
                self.assertEqual(i18n.detect(), code)


class MacUpdateTests(unittest.TestCase):
    def test_update_script(self):
        script = updates.update_script("/Users/me/My Clones/PowerLab's")
        self.assertTrue(script.startswith("cd '/Users/me/My Clones/PowerLab'\"'\"'s' || exit 1;"))
        self.assertIn("git pull --ff-only", script)
        self.assertIn("/bin/bash ./install.sh --update", script)

    def test_self_update_needs_this_platforms_installer(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".git"))
            with mock.patch.object(config, "source_path", lambda: tmp):
                open(os.path.join(tmp, "install.ps1" if updates.INSTALLER == "install.sh" else "install.sh"),
                     "w").close()
                self.assertFalse(updates.can_self_update())
                open(os.path.join(tmp, updates.INSTALLER), "w").close()
                self.assertTrue(updates.can_self_update())


class ConfigureKiCadTests(unittest.TestCase):
    def test_plugin_python(self):
        self.assertEqual(configure_kicad.plugin_python("C:/KiCad/bin"), os.path.join("C:/KiCad/bin", "pythonw.exe"))
        mac_python = "/Applications/KiCad/KiCad.app/" + config.MAC_PYTHON
        self.assertEqual(configure_kicad.plugin_python("/Applications/KiCad/KiCad.app/Contents/MacOS", mac_python),
                         mac_python)
        with tempfile.TemporaryDirectory() as tmp:
            common_json = os.path.join(tmp, "kicad_common.json")
            with open(common_json, "w") as f:
                f.write('{"api": {"enable_server": false}}')
            data, changes = configure_kicad.set_path_variables(common_json, "", True, "/x", mac_python)
            self.assertEqual(data["api"], {"enable_server": True, "interpreter_path": mac_python})
            self.assertIn("python3", changes[0])


class InstallShTests(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "install.sh"), encoding="utf-8") as f:
            self.text = f.read()

    @unittest.skipIf(os.name == "nt", "bash")
    def test_syntax(self):
        subprocess.run(["bash", "-n", os.path.join(ROOT, "install.sh")], check=True)

    def test_plain_ascii_and_old_bash(self):
        """macOS's /bin/bash is 3.2: no associative arrays, case changes or mapfile."""
        self.assertTrue(all(ord(c) < 128 for c in self.text))
        for newer in ("declare -A", "${", "mapfile", "readarray"):
            if newer == "${":
                self.assertFalse(re.search(r"\$\{\w+(,,|\^\^)\}", self.text))
            else:
                self.assertNotIn(newer, self.text)

    @unittest.skipIf(os.name == "nt", "sed")
    def test_reads_the_pin_from_install_ps1(self):
        """One pin for both installers: install.sh's sed lines find install.ps1's values."""
        import mcp_patch
        repo, commit = mcp_patch.pin()
        script = "\n".join(line for line in self.text.splitlines()
                           if line.startswith(("ROOT=", "MCP_REPO=", "MCP_COMMIT=")))
        script = script.replace('ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"', f"ROOT={shlex.quote(ROOT)}")
        out = subprocess.run(["bash", "-c", script + '\necho "$MCP_REPO $MCP_COMMIT"'],
                             capture_output=True, text=True, check=True).stdout.split()
        self.assertEqual(out, [repo, commit])

    def test_pinned_wheels(self):
        block = self.text.split('PINNED_WHEELS="', 1)[1].split('"', 1)[0]
        rows = [line.split() for line in block.strip().splitlines()]
        self.assertEqual(len(rows), 6)
        for name, version, arch, sha in rows:
            self.assertIn(name, ("numpy", "numba", "llvmlite"))
            self.assertIn(arch, ("arm64", "x86_64"))
            self.assertRegex(version, r"^\d+\.\d+\.\d+$")
            self.assertRegex(sha, r"^[0-9a-f]{64}$")
        self.assertEqual(len({(r[0], r[2]) for r in rows}), 6)  # each wheel once per arch

    def test_same_steps_as_install_ps1(self):
        """What the panel relies on: the same folders, config keys and MCP registration."""
        for needle in ('scripting/plugins/powerlab_assistant', 'plugins/powerlab-assistant',
                       '"kicad_bin"', '"kicad_python"', 'mcp_path', 'library_path', 'pylib_path',
                       'source_path', 'mcp add kicad -s user', 'KICAD_PYTHON=', 'dist/.powerlab-patch',
                       'apply --check -R', 'powerlab-*', 'configure_kicad.py', '--enable-api', '--update'):
            self.assertIn(needle, self.text)

    @unittest.skipIf(os.name == "nt", "bash")
    def test_wheel_lookup(self):
        """The awk lookups pick the wheel for KiCad's Python's architecture."""
        functions = self.text.split("wheel() {", 1)[1].split("install_numpy() {", 1)[0]
        block = self.text.split('PINNED_WHEELS="', 1)[1].split('"', 1)[0]
        script = f'PINNED_WHEELS="{block}"\nwheel() {{{functions}\nPY_ARCH=x86_64\nrequirement numba\nwheel nothing'
        out = subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=True).stdout
        self.assertEqual(out.strip(), "numba==0.60.0 --hash=sha256:"
                                      "01ef4cd7d83abe087d644eaa3d95831b777aa21d441a23703d649e06b8e06b74")


    @unittest.skipIf(os.name == "nt", "bash")
    def test_patch_update_replaces_an_older_patchs_new_files(self):
        """#105 for install.sh: a file the patch adds, left behind by the older patch, doesn't
        stop git apply; and an applied patch isn't applied twice."""
        tmp = tempfile.mkdtemp()
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        repo = os.path.join(tmp, "mcp")
        os.makedirs(os.path.join(repo, "src"))

        def git(*args):
            return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True).stdout

        def write(rel, text):
            with open(os.path.join(repo, rel), "w", newline="\n") as f:
                f.write(text)

        git("init", "-q")
        write("src/a.ts", "one\n")
        git("add", ".")
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "pin")
        pin = git("rev-parse", "HEAD").decode().strip()
        os.makedirs(os.path.join(repo, "tests"))
        write("tests/new.py", "x = 2\n")
        write("src/a.ts", "two\n")
        git("add", "-N", "tests/new.py")
        os.makedirs(os.path.join(tmp, "patches"))
        patch = os.path.join(tmp, "patches", "kicad-mcp.patch")
        with open(patch, "wb") as f:
            f.write(git("diff", pin))
        git("reset", "-q")
        git("checkout", "-q", "--", "src")
        write("tests/new.py", "x = 1\n")  # the older patch's copy

        functions = self.text.split("remove_patch_new_files() {", 1)[1].split("build_mcp() {", 1)[0]
        script = (f"set -euo pipefail\nMCP_DIR={shlex.quote(repo)}\nMCP_COMMIT={pin}\n"
                  f"PATCH={shlex.quote(patch)}\nremove_patch_new_files() {{{functions}\n"
                  "if update_mcp_patch; then echo changed; fi\n"
                  "if update_mcp_patch; then echo changed; else echo unchanged; fi\n")
        run = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(run.stdout.split(), ["changed", "unchanged"])
        with open(os.path.join(repo, "tests", "new.py")) as f:
            self.assertEqual(f.read(), "x = 2\n")
        with open(os.path.join(repo, "src", "a.ts")) as f:
            self.assertEqual(f.read(), "two\n")


class McpMacPatchTests(unittest.TestCase):
    """The KiCad MCP server finds kicad-cli and numba on macOS too."""

    def patch(self):
        with open(os.path.join(ROOT, "patches", "kicad-mcp.patch"), encoding="utf-8") as f:
            return f.read()

    def test_kicad_cli_next_to_kicads_python(self):
        patch = self.patch()
        self.assertIn('+        marker = ".app" + os.sep + "Contents" + os.sep', patch)
        self.assertIn("+        from utils.kicad_cli import resolve_kicad_cli", patch)

    def test_numba_folder(self):
        self.assertIn('+        out.append(os.path.join(os.path.expanduser("~"), "Library", "Application Support",',
                      self.patch())


if __name__ == "__main__":
    unittest.main()
