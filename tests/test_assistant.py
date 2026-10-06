"""Run with KiCad's Python (it has wx and pcbnew):

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" -m unittest discover -s tests -v
"""

import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

    def test_newer_release_is_offered_once_a_day(self):
        settings = {}
        result = updates.check(settings, fetch=self.release("v99.0.0"))
        self.assertTrue(result["available"])
        self.assertEqual(result["version"], "99.0.0")
        self.assertEqual(result["summary"], "Fixes library Share")
        # Within a day the cached answer is reused: GitHub isn't asked again.
        again = updates.check(settings, fetch=lambda: self.fail("asked GitHub twice in a day"))
        self.assertTrue(again["available"])

    def test_same_or_older_release_is_not_offered(self):
        for tag in (f"v{config.VERSION}", "v0.0.1", "not-a-version"):
            self.assertFalse(updates.check({}, fetch=self.release(tag))["available"], tag)

    def test_version_order_is_numeric(self):
        self.assertGreater(updates.parse_version("v0.10.0"), updates.parse_version("v0.9.9"))


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
