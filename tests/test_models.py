"""The model picker: family aliases that run the newest model, and an effort per model."""

import os
import sys
import types
import unittest

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

from powerlab_assistant import models, panel, usage  # noqa: E402


def effort(model, settings):
    return panel.ClaudePanel.effort.fget(types.SimpleNamespace(model=model, settings=settings))


class AliasTests(unittest.TestCase):
    def test_picker_passes_family_aliases(self):
        self.assertEqual(panel.DEFAULT_MODEL, "opus")
        self.assertEqual([m[0] for m in panel.MODELS if m[0]], list(models.ALIASES))

    def test_label_shows_the_version_last_reported(self):
        resolved = {"opus": "claude-opus-5-5", "fable": "claude-fable-5-2"}
        self.assertEqual(models.label("opus", resolved), "Opus 5.5")
        self.assertEqual(models.label("fable", resolved), "Fable 5.2")
        self.assertEqual(models.label("sonnet", resolved), "Sonnet")  # no run with it yet
        self.assertEqual(models.pretty("claude-haiku-4-5-20251001"), "Haiku 4.5")
        self.assertEqual(models.pretty("claude-opus-5-5[1m]"), "Opus 5.5")
        self.assertEqual(models.pretty("something-else"), "something-else")

    def test_settings_from_before_aliases_count_as_their_family(self):
        self.assertEqual(models.alias_of("claude-fable-5-1"), "fable")
        self.assertEqual(models.alias_of("claude-haiku-4-5-20251001"), "haiku")
        self.assertEqual(models.alias_of("opus"), "opus")
        self.assertEqual(models.alias_of(""), "")

    def test_usage_finds_the_main_model_of_an_alias(self):
        result = {"modelUsage": {"claude-haiku-5-5": {"outputTokens": 900},
                                 "claude-opus-5-5": {"outputTokens": 100}}}
        self.assertEqual(usage.models(result, "opus"), ("claude-opus-5-5", ["claude-haiku-5-5"]))


class EffortTests(unittest.TestCase):
    def test_each_model_keeps_its_own(self):
        settings = {"efforts": {"opus": "xhigh", "sonnet": "low"}}
        self.assertEqual(effort("opus", settings), "xhigh")
        self.assertEqual(effort("sonnet", settings), "low")

    def test_untouched_model_starts_from_the_old_setting_or_high(self):
        self.assertEqual(effort("fable", {"effort": "medium"}), "medium")
        self.assertEqual(effort("fable", {}), "high")
        self.assertEqual(effort("opus", {"efforts": {"opus": "bogus"}}), "high")

    def test_haiku_4_5_takes_no_effort(self):
        self.assertEqual(panel.model_efforts("claude-haiku-4-5-20251001"), ())
        self.assertEqual(panel.model_efforts("claude-opus-5-5"), panel.EFFORTS)
        old = {"resolved": {"haiku": "claude-haiku-4-5-20251001"}, "effort": "max"}
        self.assertEqual(effort("haiku", old), "")
        items = {i["id"]: i for i in panel.model_items(old["resolved"])}
        self.assertEqual(items["haiku"]["efforts"], [])
        self.assertEqual(items["opus"]["efforts"], list(panel.EFFORTS))

    def test_effort_is_passed_only_when_the_model_takes_one(self):
        with open(os.path.join(ROOT, "plugin", "powerlab_assistant", "panel.py"), encoding="utf-8") as f:
            source = f.read()
        self.assertIn('        if self.effort:  # read at every message', source)


class PinTests(unittest.TestCase):
    def test_floating_follows_the_pin(self):
        with open(os.path.join(ROOT, "plugin", "powerlab_assistant", "panel.py"), encoding="utf-8") as f:
            source = f.read()
        # Windows keeps floating by default; macOS doesn't, until the pin is turned on.
        self.assertIn('on_top = config.settings().get("on_top", config.IS_WINDOWS)', source)
        self.assertIn("(wx.STAY_ON_TOP if on_top else 0)", source)
        self.assertNotIn("wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP |", source)
        self.assertTrue(callable(getattr(panel.ClaudePanel, "msg_on_top", None)))

    def test_header_has_the_pin(self):
        with open(os.path.join(ROOT, "plugin", "powerlab_assistant", "panel.html"), encoding="utf-8") as f:
            html = f.read()
        self.assertIn('id="pin-btn"', html)
        self.assertIn("post({type:'on_top'", html)


if __name__ == "__main__":
    unittest.main()
