"""Past conversations from Claude Code's records, as transcripts (sessions.py), with no
request to Claude; and the Dock icon on macOS."""

import importlib.util
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location(
    "sessions", os.path.join(ROOT, "plugin", "powerlab_assistant", "sessions.py"))
sessions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sessions)


def user(text, ts="2026-11-23T10:00:00Z"):
    return {"type": "user", "timestamp": ts, "message": {"role": "user", "content": text}}


def result():
    return {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}


def said(*blocks, stop="end_turn"):
    return {"type": "assistant", "message": {"model": "claude-opus-5-5", "stop_reason": stop,
                                             "content": list(blocks)}}


def text(t):
    return {"type": "text", "text": t}


def tool(tool_name, **inp):
    return {"type": "tool_use", "name": tool_name, "input": inp}


class SessionsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = os.path.join(self.tmp, "claude")
        self.project = os.path.join(self.tmp, "My Board.v2")
        os.makedirs(self.project)
        self.folder = os.path.join(self.root, "projects", sessions.encoded(self.project))
        os.makedirs(self.folder)

    def write(self, sid, entries):
        path = os.path.join(self.folder, sid + ".jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")
        return path

    def test_folder_name_is_claude_codes(self):
        self.assertEqual(sessions.encoded("/Users/a/Documents/test.v2"), "-Users-a-Documents-test-v2")
        self.assertEqual(sessions.session_folder(self.project, self.root), self.folder)

    def test_a_run_cut_off_at_the_usage_limit(self):
        sid = "b8af874b-055c-40eb-a8b7-23c7c9e37b78"
        path = self.write(sid, [
            user("Draw the schematic\n\n<kicad_state>\nThe user is in the PCB editor.\n</kicad_state>"),
            {"type": "user", "isMeta": True, "message": {"content": [text("Base directory for this skill: x")]}},
            said(text("Starting with the power sheet."), tool("mcp__kicad__add_schematic_wire",
                 schematicPath=os.path.join(self.project, "Power.kicad_sch")), stop="tool_use"),
            result(),
            said(tool("mcp__kicad__create_netclass", name="GND"), stop="tool_use"),
            result(),
            {"type": "assistant", "isApiErrorMessage": True, "error": "rate_limit",
             "message": {"model": "<synthetic>", "content": [text("You've hit your 5-hour limit")]}},
        ])
        rows = sessions.list_sessions(self.project, self.root)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual((row["id"], row["first"], row["prompts"], row["steps"], row["ending"]),
                         (sid, "Draw the schematic", 1, 2, "limit"))  # state and skill aren't prompts
        md = sessions.markdown(path, "My Board", self.project)
        self.assertIn("## 1. User (2026-11-23 10:00 UTC)\n\nDraw the schematic\n", md)
        self.assertNotIn("kicad_state", md)
        self.assertIn("**Claude:** Starting with the power sheet.", md)
        self.assertIn("`add_schematic_wire` Power.kicad_sch", md)  # relative to the project
        tail = md[md.index("## Where it stopped"):]
        self.assertIn("usage limit", tail)
        self.assertIn("You've hit your 5-hour limit", tail)
        self.assertIn("- `create_netclass` GND", tail)

    def test_stopped_mid_step_and_finished(self):
        self.write("aaaaaaaa-0000-0000-0000-000000000001", [
            user("Route it"), said(tool("mcp__kicad__powerlab_route"), stop="tool_use")])
        self.write("aaaaaaaa-0000-0000-0000-000000000002", [user("hi"), said(text("Hello"))])
        self.write("aaaaaaaa-0000-0000-0000-000000000003", [result()])  # no prompt: not listed
        endings = {r["first"]: r["ending"] for r in sessions.list_sessions(self.project, self.root)}
        self.assertEqual(endings, {"Route it": "mid-step", "hi": "done"})

    def test_transcript_goes_into_the_project(self):
        sid = "aaaaaaaa-0000-0000-0000-000000000004"
        self.write(sid, [user("hi"), said(text("Hello"))])
        out = sessions.write_transcript(self.project, sid, self.root)
        self.assertEqual(os.path.dirname(out), os.path.join(self.project, "chat-history"))
        self.assertTrue(out.endswith(f"_{sid[:8]}.md"))
        with open(out, encoding="utf-8") as f:
            self.assertIn("**Claude:** Hello", f.read())
        with self.assertRaises(ValueError):
            sessions.write_transcript(self.project, "../../etc/passwd", self.root)
        with self.assertRaises(FileNotFoundError):
            sessions.write_transcript(self.project, "aaaaaaaa-0000-0000-0000-00000000dead", self.root)


if __name__ == "__main__":
    unittest.main()
