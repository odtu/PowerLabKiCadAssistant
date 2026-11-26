"""powerlab-pcb-design-rules is the lab's PCB_DESIGN_RULES.md, edited and split (#119)."""

import importlib.util
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")


def load():
    spec = importlib.util.spec_from_file_location(
        "split_design_rules", os.path.join(ROOT, "tools", "split_design_rules.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SplitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = load()
        cls.edited = cls.s.edit(cls.s.read(cls.s.SOURCE))
        cls.files = cls.s.skill_files()

    def test_parts_joined_equal_the_edited_source(self):
        self.assertEqual(self.s.join(self.files), self.edited)

    def test_the_skill_is_what_the_script_writes(self):
        # A rule changed in a part file by hand is lost at the next re-sync: change the lab's
        # file (or EDITS), then run python tools/split_design_rules.py.
        for name, text in self.s.split(self.edited).items():
            with self.subTest(name):
                self.assertEqual(self.files[name].replace("\r\n", "\n"), text)

    def test_each_part_holds_its_sections(self):
        for number, name in self.s.PARTS:
            text = self.files[name]
            self.assertTrue(text.startswith(f"## {number}. "), name)
            subs = re.findall(r"^### (\d+)\.\d+ ", text, re.M)
            self.assertTrue(subs and set(subs) == {number}, name)
        skill = self.files["SKILL.md"]
        self.assertEqual(re.findall(r"^### ", skill, re.M), [])
        self.assertIn("## How to apply these rules", skill)
        self.assertIn("## 4. Layout review handbook", skill)

    def test_index_says_which_file_for_which_task(self):
        skill = self.files["SKILL.md"]
        index = skill.split(self.s.INDEX_HEADING, 1)[1].split("## 4.", 1)[0]
        for _, name in self.s.PARTS:
            self.assertIn(f"`{name}`", index)
        layout = next(l for l in index.splitlines() if l.startswith("| Layout"))
        self.assertIn("`fab-and-drc.md` too", layout)  # board setup during layout work
        review = next(l for l in index.splitlines() if l.startswith("| Design review"))
        self.assertIn("all three", review)
        for section in ("3.3 Copper pours", "3.4 Routing", "3.5 Vias", "2.6 KiCad setup"):
            self.assertIn(section, index)

    def test_the_panel_edits_stay(self):
        rules = self.s.join(self.files)
        self.assertNotIn(".kicad_wks", rules)
        self.assertNotIn("PowerLab drawing sheet", rules)
        self.assertNotIn("PowerLabQrCode", rules)
        self.assertNotIn("power.eee.odtu.edu.tr", rules)
        self.assertIn("Designed with PowerLab KiCad Assistant and Claude", self.files["layout.md"])
        self.assertIn("name: powerlab-pcb-design-rules", self.files["SKILL.md"])
        self.assertIn("Source: https://github.com/odtu/Powerlab/", self.files["SKILL.md"])

    def test_an_edit_that_no_longer_applies_fails_loudly(self):
        lab = self.s.read(self.s.SOURCE).replace("organization logos (METU PowerLab)", "logos")
        with self.assertRaises(ValueError):
            self.s.edit(lab)

    def test_other_skills_cite_sections_that_exist(self):
        rules = self.s.join(self.files)
        have = set(re.findall(r"^#{2,3} (\d+(?:\.\d+)?)\.? ", rules, re.M))
        for name in os.listdir(SKILLS):
            if not name.startswith("powerlab-") or name == "powerlab-pcb-design-rules":
                continue
            with open(os.path.join(SKILLS, name, "SKILL.md"), encoding="utf-8") as f:
                text = f.read()
            if "powerlab-pcb-design-rules" not in text:
                continue
            for cited in re.findall(r"§(\d+(?:\.\d+)?)", text):
                with self.subTest(skill=name, section=cited):
                    self.assertIn(cited, have)


if __name__ == "__main__":
    unittest.main()
