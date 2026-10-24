"""set_design_rules writes Board Setup's rules into the project, and the lab preset
(patches/kicad-mcp.patch, python/utils/design_rules_project.py).

Run with KiCad's Python, like the other tests:

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" -m unittest discover -s tests -v

The module has no pcbnew or kipy imports, so it is taken from the patch text and run here.
"""

import copy
import json
import os
import re
import tempfile
import types
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE = "python/utils/design_rules_project.py"


def patch_text():
    with open(os.path.join(ROOT, "patches", "kicad-mcp.patch"), encoding="utf-8") as f:
        return f.read()


def load(name):
    """A file the patch adds, run as a module."""
    text = patch_text().split(f"+++ b/{name}\n", 1)[1]
    body = text.split("\ndiff --git", 1)[0].split("\n")[1:]  # skip the @@ header
    source = "\n".join(line[1:] for line in body if line.startswith("+"))
    module = types.ModuleType(os.path.basename(name)[:-3])
    exec(compile(source, name, "exec"), module.__dict__)
    return module


def sample_project():
    """The parts of a KiCad 10 .kicad_pro that set_design_rules touches, as KiCad writes
    them for a new project, plus keys it must leave alone."""
    return {
        "board": {
            "design_settings": {
                "defaults": {
                    "silk_line_width": 0.1,
                    "silk_text_size_h": 1.0,
                    "silk_text_size_v": 1.0,
                    "silk_text_thickness": 0.1,
                    "copper_line_width": 0.2,
                },
                "drc_exclusions": ["kept"],
                "rule_severities": {"clearance": "error"},
                "rules": {
                    "max_error": 0.005,
                    "min_clearance": 0.0,
                    "min_connection": 0.0,
                    "min_copper_edge_clearance": 0.5,
                    "min_hole_clearance": 0.25,
                    "min_hole_to_hole": 0.25,
                    "min_microvia_diameter": 0.2,
                    "min_microvia_drill": 0.1,
                    "min_silk_clearance": 0.0,
                    "min_text_height": 0.8,
                    "min_text_thickness": 0.08,
                    "min_through_hole_diameter": 0.3,
                    "min_track_width": 0.2,
                    "min_via_annular_width": 0.1,
                    "min_via_diameter": 0.5,
                },
            },
            "layer_presets": [],
        },
        "net_settings": {
            "classes": [
                {
                    "bus_width": 12,
                    "clearance": 0.2,
                    "name": "Default",
                    "priority": 2147483647,
                    "schematic_color": "rgba(0, 0, 0, 0.000)",
                    "track_width": 0.2,
                    "via_diameter": 0.6,
                    "via_drill": 0.3,
                    "wire_width": 6,
                },
                {
                    "bus_width": 12,
                    "clearance": 0.4,
                    "name": "Power",
                    "priority": 0,
                    "schematic_color": "rgb(255, 0, 0)",
                    "track_width": 1.0,
                    "via_diameter": 0.6,
                    "via_drill": 0.3,
                    "wire_width": 12,
                },
            ],
            "meta": {"version": 5},
            "net_colors": None,
            "netclass_assignments": None,
            "netclass_patterns": [{"netclass": "Power", "pattern": "+*"}],
        },
        "text_variables": {"REV": "B"},
    }


class PresetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.drp = load(MODULE)

    def test_preset_matches_the_skill_table(self):
        """The 1 oz preset is the Constraints table of powerlab-pcb-design-rules §2.6."""
        skill = os.path.join(ROOT, "skills", "powerlab-pcb-design-rules", "SKILL.md")
        with open(skill, encoding="utf-8") as f:
            text = f.read()
        section = text.split("### 2.6", 1)[1].split("**Default net classes:**", 1)[0]
        table = dict(re.findall(r"^\| ([^|]+?) \| ([^|]+?) \|$", section, re.M))
        names = {
            "Minimum clearance": "minClearance",
            "Minimum track width": "minTrackWidth",
            "Minimum connection width": "minConnectionWidth",
            "Minimum annular width": "minAnnularWidth",
            "Minimum via diameter": "minViaDiameter",
            "Copper to hole clearance": "holeClearance",
            "Copper to edge clearance": "copperEdgeClearance",
            "Minimum through hole": "minThroughHole",
            "Hole to hole clearance": "holeToHoleMin",
            "Solder mask expansion": "solderMaskExpansion",
            "Solder mask min web width": "solderMaskMinWidth",
            "Minimum silk text height": "minSilkTextHeight",
            "Minimum silk thickness": "minSilkThickness",
        }
        preset = self.drp.LAB_PRESETS["1oz"]
        for row, param in names.items():
            self.assertIn(row, table, row)
            self.assertAlmostEqual(preset[param], float(table[row].split()[0]), msg=row)
        self.assertEqual(table["Minimum uvia / blind vias"], "not allowed")
        self.assertIs(preset["allowMicrovias"], False)
        self.assertIs(preset["allowBlindVias"], False)
        # Default class: signals may be 0.15 mm; clearance 0.2, via 0.6 / 0.3
        self.assertEqual(
            (preset["defaultTrackWidth"], preset["defaultClearance"]), (0.15, 0.2)
        )
        self.assertEqual((preset["defaultViaDiameter"], preset["defaultViaDrill"]), (0.6, 0.3))
        self.assertEqual(
            preset["powerClass"],
            {"track_width": 0.5, "clearance": 0.3, "via_diameter": 0.8, "via_drill": 0.4},
        )

    def test_resolve_preset_and_overrides(self):
        v = self.drp.resolve_design_rule_params({"preset": "powerlab", "minTrackWidth": 0.2})
        self.assertEqual(v["copper"], "1oz")
        self.assertEqual(v["rules"]["min_track_width"], 0.2)  # explicit wins
        self.assertEqual(v["rules"]["min_clearance"], 0.15)
        self.assertEqual(v["rules"]["min_via_annular_width"], 0.15)
        self.assertEqual(v["rules"]["min_hole_to_hole"], 0.4)
        self.assertEqual(v["defaultClass"]["track_width"], 0.15)
        self.assertEqual(v["boardFile"], {"solderMaskExpansion": 0.05, "solderMaskMinWidth": 0.1})
        self.assertEqual(v["vias"], {"allowMicrovias": False, "allowBlindVias": False})
        self.assertEqual(v["labClasses"]["via_diameter"], 0.8)

        two = self.drp.resolve_design_rule_params({"preset": "powerlab", "copper": "2oz"})
        self.assertEqual(two["rules"]["min_via_annular_width"], 0.2)
        self.assertEqual(two["boardFile"]["solderMaskMinWidth"], 0.13)
        self.assertEqual(two["labClasses"]["via_diameter"], 0.85)

        no_classes = self.drp.resolve_design_rule_params(
            {"preset": "powerlab", "labNetClasses": False}
        )
        self.assertIsNone(no_classes["labClasses"])

    def test_old_parameter_names_still_work(self):
        v = self.drp.resolve_design_rule_params(
            {
                "clearance": 0.18,
                "trackWidth": 0.25,
                "viaDiameter": 0.7,
                "viaDrill": 0.35,
                "minViaDrill": 0.3,
                "microViaDiameter": 0.25,
            }
        )
        self.assertEqual(v["rules"]["min_clearance"], 0.18)
        self.assertEqual(v["rules"]["min_through_hole_diameter"], 0.3)
        self.assertEqual(v["rules"]["min_microvia_diameter"], 0.25)
        self.assertEqual(
            v["defaultClass"], {"track_width": 0.25, "via_diameter": 0.7, "via_drill": 0.35}
        )
        self.assertIsNone(v["preset"])
        self.assertIsNone(v["labClasses"])
        # the new name wins over the old one
        v = self.drp.resolve_design_rule_params({"minClearance": 0.2, "clearance": 0.1})
        self.assertEqual(v["rules"]["min_clearance"], 0.2)

    def test_bad_input_is_refused(self):
        bad = [
            {},
            {"preset": "jlcpcb"},
            {"copper": "2oz"},
            {"preset": "powerlab", "copper": "3oz"},
            {"minClearance": "0.15"},
            {"minClearance": -1},
            {"minClearance": True},
            {"allowMicrovias": "no"},
            {"defaultViaDiameter": 0.3, "defaultViaDrill": 0.4},
        ]
        for params in bad:
            with self.assertRaises(ValueError, msg=params):
                self.drp.resolve_design_rule_params(params)

    def test_every_parameter_is_known(self):
        """unknown_parameters spells the names out (for the MCP's schema check); keep it in
        step with the tables."""
        names = {"preset", "copper", "labNetClasses", "projectPath"}
        for name, aliases, *_ in self.drp.RULE_PARAMS + self.drp.CLASS_PARAMS:
            names |= {name, *aliases}
        names |= {name for name, *_ in self.drp.BOARD_FILE_PARAMS}
        names |= set(self.drp.VIA_PERMISSIONS)
        self.assertEqual(self.drp.unknown_parameters({n: 1 for n in names}), [])
        self.assertEqual(self.drp.unknown_parameters({"courtyardClearance": 1}), ["courtyardClearance"])


class ProjectFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.drp = load(MODULE)

    def test_preset_changes_only_its_keys(self):
        before = sample_project()
        data = copy.deepcopy(before)
        values = self.drp.resolve_design_rule_params({"preset": "powerlab"})
        done = self.drp.apply_design_rules_to_project(data, values)

        rules = data["board"]["design_settings"]["rules"]
        self.assertEqual(rules["min_clearance"], 0.15)
        self.assertEqual(rules["min_connection"], 0.15)
        self.assertEqual(rules["min_via_diameter"], 0.6)
        self.assertEqual(rules["min_text_height"], 1.0)
        self.assertEqual(rules["min_text_thickness"], 0.15)
        self.assertEqual(rules["max_error"], 0.005)  # not a lab rule: kept
        # untouched parts of the file
        for path in (("text_variables",), ("board", "layer_presets")):
            a, b = before, data
            for key in path:
                a, b = a[key], b[key]
            self.assertEqual(a, b)
        ds = data["board"]["design_settings"]
        self.assertEqual(ds["drc_exclusions"], ["kept"])
        self.assertEqual(ds["rule_severities"], {"clearance": "error"})
        # silk defaults raised to the minimums, others kept
        self.assertEqual(ds["defaults"]["silk_line_width"], 0.15)
        self.assertEqual(ds["defaults"]["silk_text_thickness"], 0.15)
        self.assertEqual(ds["defaults"]["silk_text_size_h"], 1.0)
        self.assertEqual(ds["defaults"]["copper_line_width"], 0.2)

        classes = {c["name"]: c for c in data["net_settings"]["classes"]}
        self.assertEqual(classes["Default"]["track_width"], 0.15)
        self.assertEqual(classes["Default"]["priority"], 2147483647)
        self.assertEqual(classes["Default"]["bus_width"], 12)
        # Power existed: sized for current, so a wider track stays; small vias are raised
        self.assertEqual(classes["Power"]["track_width"], 1.0)
        self.assertEqual(classes["Power"]["clearance"], 0.4)
        self.assertEqual((classes["Power"]["via_diameter"], classes["Power"]["via_drill"]), (0.8, 0.4))
        self.assertEqual(classes["Power"]["schematic_color"], "rgb(255, 0, 0)")
        # GND is new: cloned from Default, lab values and colour
        gnd = classes["GND"]
        self.assertEqual((gnd["track_width"], gnd["clearance"]), (0.5, 0.3))
        self.assertEqual(gnd["schematic_color"], "rgba(0, 0, 255, 1.000)")
        self.assertEqual((gnd["wire_width"], gnd["priority"], gnd["bus_width"]), (12, 0, 12))
        patterns = [(p["netclass"], p["pattern"]) for p in data["net_settings"]["netclass_patterns"]]
        self.assertEqual(patterns.count(("Power", "+*")), 1)  # not doubled
        self.assertIn(("Power", "VBUS*"), patterns)
        self.assertIn(("GND", "*GND*"), patterns)
        self.assertTrue(any(line.startswith("GND net class (new)") for line in done))

        again = copy.deepcopy(data)
        self.drp.apply_design_rules_to_project(again, values)
        self.assertEqual(again, data)  # running it twice changes nothing

    def test_explicit_values_without_preset(self):
        data = sample_project()
        values = self.drp.resolve_design_rule_params({"minClearance": 0.2, "defaultClearance": 0.25})
        done = self.drp.apply_design_rules_to_project(data, values)
        self.assertEqual(data["board"]["design_settings"]["rules"]["min_clearance"], 0.2)
        self.assertEqual(data["board"]["design_settings"]["rules"]["min_track_width"], 0.2)
        self.assertEqual(data["net_settings"]["classes"][0]["clearance"], 0.25)
        self.assertEqual(len(data["net_settings"]["classes"]), 2)  # no lab classes
        self.assertEqual(data["board"]["design_settings"]["defaults"]["silk_line_width"], 0.1)
        self.assertEqual(len(done), 2)

    def test_file_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            pro = os.path.join(tmp, "board.kicad_pro")
            with open(pro, "w", encoding="utf-8") as f:
                json.dump(sample_project(), f, indent=2, sort_keys=True)
            values = self.drp.resolve_design_rule_params({"preset": "powerlab"})
            done, rules = self.drp.persist_design_rules_to_project(pro, values)
            self.assertEqual(rules["min_hole_to_hole"], 0.4)
            with open(pro, encoding="utf-8") as f:
                data = json.load(f)
            read = self.drp.read_design_rules_from_project(data)
            self.assertEqual(read["rules"]["minClearance"], 0.15)
            self.assertEqual(read["rules"]["minThroughHole"], 0.3)
            self.assertEqual(read["silkDefaults"]["silk_text_thickness"], 0.15)
            self.assertEqual(
                [c["name"] for c in read["netClasses"]], ["Default", "Power", "GND"]
            )
            self.assertIn({"pattern": "*GND*", "netClass": "GND"}, read["netClassPatterns"])
            self.assertEqual(os.listdir(tmp), ["board.kicad_pro"])  # no temp files left


class DruTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.drp = load(MODULE)

    def test_lab_minimums_rule(self):
        values = self.drp.resolve_design_rule_params({"preset": "powerlab"})
        data = sample_project()
        self.drp.apply_design_rules_to_project(data, values)
        rule = self.drp.lab_minimums_rule(data["board"]["design_settings"]["rules"])
        self.assertTrue(rule.startswith('(rule "Lab minimums"\n'))
        for line in (
            "(constraint track_width (min 0.15mm))",
            "(constraint connection_width (min 0.15mm))",
            "(constraint annular_width (min 0.15mm))",
            "(constraint via_diameter (min 0.6mm))",
            "(constraint hole_size (min 0.3mm))",
            "(constraint hole_clearance (min 0.25mm))",
            "(constraint hole_to_hole (min 0.4mm))",
            "(constraint edge_clearance (min 0.5mm))",
        ):
            self.assertIn(line, rule)
        # an unconditional clearance rule would override every net class clearance
        self.assertNotIn("constraint clearance", rule)
        self.assertEqual(rule.count("("), rule.count(")"))
        self.assertIsNone(self.drp.lab_minimums_rule({"min_track_width": 0.0}))

    def test_no_vias_rule_keywords(self):
        """kicad-cli 10 drops the whole .kicad_dru on one unknown keyword: only these."""
        rule = self.drp.no_vias_rule(False, False)
        self.assertIn("(constraint disallow micro_via blind_via buried_via))", rule)
        self.assertIn("(constraint disallow micro_via))", self.drp.no_vias_rule(False, True))
        self.assertIn(
            "(constraint disallow blind_via buried_via))", self.drp.no_vias_rule(True, False)
        )
        self.assertIsNone(self.drp.no_vias_rule(True, True))

    def test_set_rule_keeps_the_other_rules(self):
        text = (
            "(version 1)\n\n# lab floor\n"
            '(rule "Lab minimums"\n\t(constraint track_width (min 0.2mm)))\n\n'
            '(rule "HV"\n\t(constraint clearance (min 0.6mm))\n\t(condition "A.NetName == \'(x)\'"))\n'
        )
        new = '(rule "Lab minimums"\n\t(constraint track_width (min 0.15mm)))'
        out = self.drp.set_dru_rule(text, "Lab minimums", new)
        self.assertIn("(min 0.15mm)", out)
        self.assertNotIn("(min 0.2mm)", out)
        self.assertIn('(rule "HV"', out)
        self.assertIn("# lab floor", out)
        added = self.drp.set_dru_rule(out, "Other", '(rule "Other"\n\t(constraint hole_size (min 0.3mm)))')
        self.assertTrue(added.rstrip().endswith('(rule "Other"\n\t(constraint hole_size (min 0.3mm)))'))
        removed = self.drp.set_dru_rule(added, "HV", None)
        self.assertNotIn('"HV"', removed)
        self.assertIn('(rule "Other"', removed)
        self.assertEqual(self.drp.set_dru_rule("", "X", '(rule "X")'), '(version 1)\n\n(rule "X")\n')

    def test_persist_dru(self):
        rules = {"min_track_width": 0.15, "min_via_diameter": 0.6}
        with tempfile.TemporaryDirectory() as tmp:
            dru = os.path.join(tmp, "board.kicad_dru")
            hand = '(version 1)\n\n(rule "Lab minimums"\n\t(constraint track_width (min 0.1mm)))\n'
            with open(dru, "w", encoding="utf-8") as f:
                f.write(hand)
            # a call that sets none of the rule's minimums leaves a hand-written rule alone
            self.assertEqual(self.drp.persist_dru_rules(dru, rules, {}, minimums=False), [])
            with open(dru, encoding="utf-8") as f:
                self.assertEqual(f.read(), hand)
            written = self.drp.persist_dru_rules(
                dru, rules, {"allowMicrovias": False, "allowBlindVias": False}
            )
            self.assertEqual(written, ["Lab minimums", "Lab: no micro or blind vias"])
            with open(dru, "rb") as f:
                raw = f.read()
            self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))  # a BOM makes KiCad drop the file
            self.assertNotIn(b"\r\n", raw)
            self.assertIn(b"(min 0.15mm)", raw)
            self.assertEqual(raw.count(b'(rule "Lab minimums"'), 1)
            # vias allowed again: the disallow rule goes
            self.drp.persist_dru_rules(
                dru, rules, {"allowMicrovias": True, "allowBlindVias": True}, minimums=False
            )
            with open(dru, encoding="utf-8") as f:
                self.assertNotIn("disallow", f.read())


class WiringTests(unittest.TestCase):
    def test_tool_is_wired(self):
        patch = patch_text()
        # the dispatcher runs set_design_rules through the live-aware wrapper
        self.assertIn('+            "set_design_rules": self._handle_set_design_rules,  # PowerLab patch', patch)
        # the tool's own pcbnew re-reads the project (LoadBoard reuses a loaded one)
        self.assertIn("+                manager.UnloadProject(project, False)", patch)
        # the solder mask settings reach KiCad through save / edit / revert
        self.assertIn("+                    live[1].revert()", patch)
        # TypeScript and JSON-RPC schemas
        self.assertIn('+        .enum(["powerlab"])', patch)
        self.assertIn('+                "preset": {"type": "string", "enum": ["powerlab"]},', patch)
        # get_design_rules reads the project file
        self.assertIn("+                result.update(drp.read_design_rules_from_project(data))", patch)


if __name__ == "__main__":
    unittest.main()
