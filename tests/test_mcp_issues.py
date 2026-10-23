"""Fixes to the KiCad MCP server for issues #79, #80 and #81 (patches/kicad-mcp.patch).

Run with KiCad's Python, like the other tests:

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" -m unittest discover -s tests -v

The new modules have no pcbnew or kipy imports at the top, so their pure parts are taken
from the patch text and run here.
"""

import os
import types
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def patch_text():
    with open(os.path.join(ROOT, "patches", "kicad-mcp.patch"), encoding="utf-8") as f:
        return f.read()


def new_file(name):
    """A file the patch adds, as its text."""
    text = patch_text().split(f"+++ b/{name}\n", 1)[1]
    body = text.split("\ndiff --git", 1)[0].split("\n")[1:]  # skip the @@ header
    return "\n".join(line[1:] for line in body if line.startswith("+"))


def load(name):
    module = types.ModuleType(os.path.basename(name)[:-3])
    exec(compile(new_file(name), name, "exec"), module.__dict__)
    return module


class ZoneToolsTests(unittest.TestCase):
    """#79: zones could be added and queried but not deleted or changed."""

    @classmethod
    def setUpClass(cls):
        cls.zone_edit = load("python/commands/zone_edit.py")

    def test_tools_are_wired_in_both_modes(self):
        patch = patch_text()
        for tool in ("delete_zone", "edit_zone"):
            self.assertIn(f'+    "{tool}",', patch)  # TypeScript tool
            self.assertIn(f'+      "{tool}",', patch)  # registry, so search_tools finds it
            self.assertIn(f'+        "name": "{tool}",', patch)  # JSON-RPC schema
            self.assertIn(f'+        "{tool}": "_ipc_{tool}",  # PowerLab patch (#79)', patch)
            self.assertIn(f'+            "{tool}": self._handle_{tool},  # PowerLab patch (#79)', patch)
        # live query_zones reads KiCad's board, so its uuids are the ones the tools find there
        self.assertIn('+        "query_zones": "_ipc_query_zones",', patch)
        self.assertIn("entry.update(swig_zone_settings(zone))", patch)

    def test_live_locks_come_from_the_saved_file(self):
        """KiCad 10.0.5's API reports every zone unlocked and unlocks zones it updates."""
        patch = patch_text()
        self.assertIn("zone_edit.locked_zone_uuids(fh.read())", patch)
        self.assertIn("if zone_edit.ipc_edit_needs_file(kboard, params, locked_uuids):", patch)
        text = (
            '\t(zone\n\t\t(net "GND")\n\t\t(locked yes)\n\t\t(layer "F.Cu")\n'
            '\t\t(uuid "4CCB5200-ed6d-4e07-bb13-9ebd8f47dfe8")\n\t\t(priority 2)\n\t)\n'
            '\t(zone\n\t\t(net "GND")\n\t\t(layer "B.Cu")\n'
            '\t\t(uuid "3ddd8879-2457-4339-8384-b407f2b8004d")\n\t)\n'
            '\t(zone (net 1) (net_name "VIN") (locked) (layer "F.Cu") '
            '(uuid "11111111-2222-3333-4444-555555555555"))\n'
        )
        self.assertEqual(
            self.zone_edit.locked_zone_uuids(text),
            {"4ccb5200-ed6d-4e07-bb13-9ebd8f47dfe8", "11111111-2222-3333-4444-555555555555"},
        )

    def zones(self):
        return [
            {"uuid": "aaaaaaaa-0000-0000-0000-000000000001", "net": "GND", "layers": ["F.Cu"], "name": ""},
            {"uuid": "aaaaaaaa-0000-0000-0000-000000000002", "net": "GND", "layers": ["B.Cu"], "name": ""},
            {"uuid": "aaaaaaaa-0000-0000-0000-000000000003", "net": "", "layers": ["F.Cu", "B.Cu"],
             "name": "keepout", "isRuleArea": True},
        ]

    def test_picking_a_zone(self):
        select = self.zone_edit.select_zones
        found, err = select(self.zones(), {"uuid": "AAAAAAAA-0000-0000-0000-000000000002"})
        self.assertIsNone(err)
        self.assertEqual(found[0]["layers"], ["B.Cu"])
        # kipy's KIID text works too, as for delete_trace
        found, err = select(self.zones(), {"uuid": 'value: "aaaaaaaa-0000-0000-0000-000000000001"'})
        self.assertEqual(found[0]["layers"], ["F.Cu"])
        found, err = select(self.zones(), {"net": "GND", "layer": "B.Cu"})
        self.assertEqual(found[0]["uuid"][-1], "2")
        found, err = select(self.zones(), {"name": "keepout"})
        self.assertTrue(found[0]["isRuleArea"])
        # two GND zones: name the one you mean, unless all of them (delete_zone's all)
        found, err = select(self.zones(), {"net": "GND"})
        self.assertEqual(found, [])
        self.assertIn("2 zones have net 'GND'", err["message"])
        self.assertEqual(len(err["zones"]), 2)
        found, err = select(self.zones(), {"net": "GND"}, many=True)
        self.assertEqual(len(found), 2)
        _, err = select(self.zones(), {"uuid": "nope"})
        self.assertIn("No zone with uuid", err["message"])
        _, err = select(self.zones(), {})
        self.assertIn("Say which zone", err["message"])

    def test_changes_are_checked(self):
        parse = self.zone_edit.parse_zone_changes
        changes, err = parse({
            "newNet": "+5V", "newLayers": ["B.Silkscreen", "B.Cu"], "priority": 2,
            "clearance": 20, "minWidth": 10, "padConnection": "solid", "newName": "5V",
            "outline": [{"x": 0, "y": 0}, {"x": 100, "y": 0}, [100, 100]], "unit": "mil",
            "locked": False,
        })
        self.assertIsNone(err)
        self.assertEqual(changes["layers"], ["B.SilkS", "B.Cu"])
        self.assertAlmostEqual(changes["clearance"], 0.508)
        self.assertAlmostEqual(changes["minThickness"], 0.254)
        self.assertEqual(changes["outline"][2], (2.54, 2.54))
        self.assertIs(changes["locked"], False)
        for bad, text in (
            ({}, "Nothing to change"),
            ({"padConnection": "none"}, "padConnection"),
            ({"priority": -1}, "negative"),
            ({"minThickness": 0}, "more than 0"),
            ({"outline": [{"x": 0, "y": 0}, {"x": 1, "y": 0}]}, "at least 3 points"),
            ({"newLayers": []}, "newLayers"),
            ({"priority": 1, "unit": "cm"}, "unknown unit"),
        ):
            self.assertEqual(parse(bad)[0], {})
            self.assertIn(text, parse(bad)[1])

    def test_locked_zones_and_rule_areas(self):
        check = self.zone_edit._locked_outline_error
        outline = {"outline": [(0, 0), (1, 0), (1, 1)]}
        self.assertIn("locked", check({"locked": True}, outline))
        self.assertIsNone(check({"locked": True}, dict(outline, locked=False)))
        self.assertIsNone(check({"locked": True}, {"priority": 1}))
        self.assertIn("rule area", check({"isRuleArea": True}, {"newNet": "GND"}))
        self.assertIsNone(check({"isRuleArea": True}, {"layers": ["F.Cu"]}))
        patch = patch_text()
        # delete_zone keeps locked zones, like delete_trace keeps locked copper
        self.assertIn("pass includeLocked: true", patch)


class BoardRegionTests(unittest.TestCase):
    """#80: get_elements_in_region needed schematicPath, so a call from PCB work failed."""

    def test_schematic_path_is_optional(self):
        patch = patch_text()
        self.assertIn(
            '+      schematicPath: z\n+        .string()\n+        .optional()', patch)
        self.assertIn('+            "required": ["x1", "y1", "x2", "y2"],', patch)
        self.assertIn("return self._board_elements_in_region(params)", patch)
        self.assertIn("board_region.ipc_items(self.ipc_board_api._get_board(), box, limit)", patch)

    def test_what_touches_the_rectangle(self):
        region = load("python/commands/board_region.py")
        box = (10.0, 10.0, 20.0, 20.0)
        self.assertTrue(region.segment_crosses(box, 0, 15, 30, 15))  # straight through
        self.assertTrue(region.segment_crosses(box, 12, 12, 13, 13))  # inside
        self.assertFalse(region.segment_crosses(box, 0, 0, 30, 5))  # passes below
        self.assertFalse(region.segment_crosses(box, 0, 9.8, 30, 9.8))
        self.assertTrue(region.segment_crosses(box, 0, 9.8, 30, 9.8, half_width=0.25))
        self.assertTrue(region.segment_crosses(box, 0, 0, 30, 30))  # diagonal

        track = lambda x0, y0, x1, y1: {"start": {"x": x0, "y": y0}, "end": {"x": x1, "y": y1}, "width": 0.2}
        out = region.collect(
            box,
            footprints=[{"reference": "R1", "_bbox": (19, 19, 22, 22)},
                        {"reference": "R2", "_bbox": (30, 30, 32, 32)}],
            pads=[{"reference": "R1", "pad": str(i), "x": 15, "y": 15} for i in range(5)],
            tracks=[track(0, 15, 30, 15), track(0, 0, 5, 5)],
            vias=[{"x": 15, "y": 15}, {"x": 25, "y": 15}],
            zones=[{"uuid": "z", "_bbox": (0, 0, 100, 100)}],
            limit=3,
        )
        self.assertEqual(out["counts"], {"footprints": 1, "pads": 5, "tracks": 1, "vias": 1, "zones": 1})
        self.assertEqual(out["footprints"], [{"reference": "R1"}])  # private keys dropped
        self.assertEqual(len(out["pads"]), 3)
        self.assertEqual(out["truncated"], ["pads"])
        self.assertEqual(out["mode"], "board")


class RegionShapeTests(unittest.TestCase):
    """#81: get_board_2d_view said "Bad region" with no reason; zod dropped other shapes."""

    @classmethod
    def setUpClass(cls):
        cls.rb = load("python/utils/region_box.py")

    def test_the_reason_reaches_claude(self):
        patch = patch_text()
        self.assertIn('+                            "message": f"Bad region: {err}",', patch)
        self.assertIn("+            .passthrough(),", patch)
        self.assertIn("+          z.array(z.number()).length(4),", patch)

    def test_shapes(self):
        box = self.rb.region_box
        want = (10.0, 20.0, 30.0, 50.0)
        for region in (
            {"x0": 10, "y0": 20, "x1": 30, "y1": 50},
            {"x0": 30, "y0": 50, "x1": 10, "y1": 20},  # corners either way round
            {"x1": 10, "y1": 20, "x2": 30, "y2": 50},
            {"x": 10, "y": 20, "width": 20, "height": 30},
            {"x": 10, "y": 20, "w": 20, "h": 30},
            {"cx": 20, "cy": 35, "width": 20, "height": 30},
            {"xmin": 10, "ymin": 20, "xmax": 30, "ymax": 50},
            {"minX": 10, "minY": 20, "maxX": 30, "maxY": 50},
            {"min_x": 10, "min_y": 20, "max_x": 30, "max_y": 50},
            {"left": 10, "top": 20, "right": 30, "bottom": 50},
            [10, 20, 30, 50],
            {"x0": "10", "y0": "20", "x1": "30", "y1": "50"},
        ):
            self.assertEqual(box(region), want, region)
        self.assertEqual(box({"x": 15, "y": 25, "size": 10}), (10.0, 20.0, 20.0, 30.0))
        x0, y0, x1, y1 = box({"x0": 0, "y0": 0, "x1": 100, "y1": 200, "unit": "mil"})
        self.assertAlmostEqual(x1, 2.54)
        self.assertAlmostEqual(y1, 5.08)

    def test_errors_say_what_is_wrong(self):
        box, checked = self.rb.region_box, self.rb.checked_region_box
        for region, text in (
            ({"x": 1, "y": 2}, "region has x, y; use one of"),
            ({}, "region has no keys"),
            ([1, 2, 3], "needs 4 numbers"),
            ("1,2,3,4", "must be an object or a list"),
            ({"x0": 1, "y0": "a", "x1": 2, "y1": 3}, "y0 must be a number"),
            ({"x0": 0, "y0": 0, "x1": 1, "y1": 1, "unit": "cm"}, "unknown unit"),
        ):
            with self.assertRaises(ValueError) as ctx:
                box(region)
            self.assertIn(text, str(ctx.exception))
        with self.assertRaises(ValueError) as ctx:
            checked({"x0": 0, "y0": 0, "x1": 0.2, "y1": 5})
        self.assertIn("at least 0.5 mm", str(ctx.exception))
        self.assertIn("{x, y, width, height}", self.rb.ACCEPTED)


if __name__ == "__main__":
    unittest.main()
