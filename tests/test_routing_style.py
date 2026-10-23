"""check_routing (patches/kicad-mcp.patch): how tracks are drawn, which DRC doesn't judge.

The maintainer's screenshots of a hand-routed board: a run drawn as one slanted line, a short
kink before a pad, 90-degree corners on JTAG lines, two same-net pads side by side joined by a
loop, GND pads connected solid. Run with KiCad's Python, like the other tests:

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" -m unittest discover -s tests -v
"""

import math
import os
import unittest

from test_mcp_issues import load, patch_text

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def seg(net, a, b, layer="F.Cu", width=0.15):
    return {"net": net, "layer": layer, "a": a, "b": b, "width": width, "id": f"{a}{b}"}


def pad(pid, net, at, half=0.3, axis=None, big=False):
    ref, num = pid.split(".")
    return {"id": pid, "net": net, "ref": ref, "pad": num, "at": at, "half": half, "axis": axis, "big": big}


def pad_at_for(pads, size=None):
    """A pad holds a point within its half size (square pads); long pads take `size`."""
    def pad_at(net, layer, p):
        for d in pads:
            hx, hy = (size or {}).get(d["id"], (d["half"], d["half"]))
            if d["net"] == net and abs(p[0] - d["at"][0]) <= hx + 1e-9 and abs(p[1] - d["at"][1]) <= hy + 1e-9:
                return d["id"]
        return None
    return pad_at


class RoutingStyleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rc = load("python/commands/routing_check.py")

    def kinds(self, segments, pads=(), vias=(), zones=(), size=None):
        return [f["kind"] for f in self.rc.analyse(segments, vias, pads, zones, pad_at_for(pads, size))]

    def test_wired_in(self):
        patch = patch_text()
        self.assertIn('+    "check_routing",', patch)  # TypeScript tool
        self.assertIn('+      "check_routing",', patch)  # registry
        self.assertIn('+            "check_routing": self._handle_check_routing,  # PowerLab patch', patch)

    def test_only_0_45_90_degrees(self):
        self.assertEqual(self.kinds([seg("A", (0, 0), (10, 3))]), ["off_angle"])  # 16.7 degrees
        for b in ((10, 0), (0, 10), (7, 7), (-7, 7)):
            self.assertEqual(self.kinds([seg("A", (0, 0), b)]), [])
        self.assertEqual(self.rc.off_45(46.0), 1.0)

    def test_corners_sharper_than_45_degrees(self):
        square = [seg("TDI", (0, 0), (5, 0)), seg("TDI", (5, 0), (5, 5))]
        found = self.rc.analyse(square, [], [], [], None)
        self.assertEqual([f["kind"] for f in found], ["corner"])
        self.assertIn("90-degree corner", found[0]["detail"])
        self.assertEqual(found[0]["link"], "kicad:at=5,0")
        chamfered = [seg("TDI", (0, 0), (5, 0)), seg("TDI", (5, 0), (6, 1)), seg("TDI", (6, 1), (6, 6))]
        self.assertEqual(self.kinds(chamfered), [])
        # a corner at a via or a pad is where the track changes layer or ends: not judged
        self.assertEqual(self.kinds(square, vias=[{"net": "TDI", "at": (5, 0)}]), [])

    def test_a_jog_is_a_kink_a_chamfer_isnt(self):
        jog = [seg("SDI", (0, 0), (5, 0)), seg("SDI", (5, 0), (5.3, 0.3)), seg("SDI", (5.3, 0.3), (10, 0.3))]
        self.assertEqual(self.kinds(jog), ["kink"])
        chamfer = [seg("SDI", (0, 0), (5, 0)), seg("SDI", (5, 0), (5.4, 0.4)), seg("SDI", (5.4, 0.4), (5.4, 5))]
        self.assertEqual(self.kinds(chamfer), [])

    def test_same_net_neighbours_joined_the_long_way(self):
        pads = [pad("C1.1", "+3V3", (0, 0)), pad("U1.4", "+3V3", (2.5, 0))]
        loop = [seg("+3V3", (0, 0), (0, -4)), seg("+3V3", (0, -4), (2.5, -4)), seg("+3V3", (2.5, -4), (2.5, 0))]
        found = self.rc.analyse(loop, [], pads, [], pad_at_for(pads))
        self.assertEqual([f["kind"] for f in found].count("detour"), 1)
        detour = next(f for f in found if f["kind"] == "detour")
        self.assertEqual((detour["path"], detour["direct"]), (10.5, 2.5))
        self.assertIn("connect them directly", detour["detail"])
        self.assertEqual(self.kinds([seg("+3V3", (0, 0), (2.5, 0))], pads), [])
        # through a via and back on the other layer counts too
        via = [seg("+3V3", (0, 0), (0, -3)), seg("+3V3", (0, -3), (2.5, -3), layer="B.Cu"),
               seg("+3V3", (2.5, -3), (2.5, 0))]
        vias = [{"net": "+3V3", "at": (0, -3)}, {"net": "+3V3", "at": (2.5, -3)}]
        self.assertIn("detour", self.kinds(via, pads, vias))

    def test_a_rail_feeding_pads_in_turn_is_fine(self):
        # A bus along a row of caps: far pairs are joined through the T-junctions, which is
        # how a rail is drawn, not a detour.
        pads = [pad(f"C{i}.1", "+5V", (i * 3.0, 0)) for i in range(1, 6)] + [pad("U1.1", "+5V", (15.0, 20.0))]
        bus = [seg("+5V", (3, -1), (15, -1), width=0.5)]
        bus += [seg("+5V", (i * 3.0, -1), (i * 3.0, 0), width=0.5) for i in range(1, 6)]
        bus += [seg("+5V", (15, -1), (15, 20), width=0.5)]
        self.assertNotIn("detour", self.kinds(bus, pads))
        # ... but a cap on that rail fed round a loop next to its neighbour is
        pads.append(pad("C9.1", "+5V", (4.5, 0)))
        bus += [seg("+5V", (3, -1), (3, -5)), seg("+5V", (3, -5), (4.5, -5)), seg("+5V", (4.5, -5), (4.5, 0))]
        self.assertIn("detour", self.kinds(bus, pads))

    def test_a_single_link_round_the_houses(self):
        pads = [pad("U4.30", "ENC_B", (0, 0)), pad("R5.2", "ENC_B", (12, 0))]
        far = [seg("ENC_B", (0, 0), (0, 6)), seg("ENC_B", (0, 6), (12, 6)), seg("ENC_B", (12, 6), (12, 0))]
        self.assertIn("detour", self.kinds(far, pads))
        bent = [seg("ENC_B", (0, 0), (2, 2)), seg("ENC_B", (2, 2), (10, 2)), seg("ENC_B", (10, 2), (12, 0))]
        self.assertNotIn("detour", self.kinds(bent, pads))  # a 45-degree way round an obstacle

    def test_pad_entry_at_the_centre(self):
        pads = [pad("C5.1", "VBUS", (0, 0), half=0.4)]
        off = [seg("VBUS", (0.35, 0.35), (3, 0.35))]
        self.assertEqual(self.kinds(off, pads), ["pad_entry"])
        self.assertEqual(self.kinds([seg("VBUS", (0, 0), (3, 0))], pads), [])
        # along a long QFP pad towards its centre is fine
        qfp = [pad("U4.36", "TCK", (0, 0), half=0.15, axis=0.0)]
        size = {"U4.36": (0.75, 0.15)}
        self.assertEqual(self.kinds([seg("TCK", (-0.7, 0), (-3, 0))], qfp, size=size), [])
        self.assertEqual(self.kinds([seg("TCK", (-0.7, 0.1), (-0.7, 3))], qfp, size=size), ["pad_entry"])

    def test_gnd_pours_use_thermal_reliefs(self):
        zones = [{"net": "GND", "layer": "B.Cu", "solid": True, "rule_area": False, "at": (1, 2)},
                 {"net": "GND", "layer": "In1.Cu", "solid": False, "rule_area": False, "at": (0, 0)},
                 {"net": "+48V_DC", "layer": "F.Cu", "solid": True, "rule_area": False, "at": (0, 0)},
                 {"net": "", "layer": "F.Cu", "solid": True, "rule_area": True, "at": (0, 0)}]
        self.assertEqual(self.kinds([], zones=zones), ["solid_gnd"])

    def test_nets_filter_and_order(self):
        segments = [seg("A", (0, 0), (10, 3)), seg("B", (0, 0), (10, 3))]
        found = self.rc.analyse(segments, [], [], [], None, {"nets": ["B"]})
        self.assertEqual([f["net"] for f in found], ["B"])
        self.assertEqual(self.rc.KIND_ORDER[0], "detour")
        self.assertTrue(math.isclose(self.rc.turn((0, 0), (1, 0), (1, 1)), 90.0))


class RoutingRulesTextTests(unittest.TestCase):
    """The rules and the review skills carry what the screenshots showed."""

    def read(self, name):
        with open(os.path.join(ROOT, "skills", name, "SKILL.md"), encoding="utf-8") as f:
            return f.read()

    def test_lab_rules(self):
        rules = self.read("powerlab-pcb-design-rules")
        self.assertIn("**Only three directions: 0°, 45° and 90°.**", rules)
        self.assertIn("**Same-net pads next to each other connect directly**", rules)
        self.assertIn("**Parallel runs stay parallel.**", rules)
        self.assertIn("**GND pours and planes always use thermal reliefs, never solid**", rules)
        self.assertIn("| Default | 0.15 mm | 0.2 mm | 0.3 / 0.6 |", rules)  # signals at 0.15 mm
        self.assertIn('`preset: "powerlab"`', rules)  # Board Setup itself, not only .kicad_dru
        self.assertIn("Pad_D1.5mm_Drill0.8mm", rules)  # small test points
        self.assertIn("`check_routing`", rules)

    def test_reviews_measure_the_routing(self):
        self.assertIn("**Routing, measured.** `check_routing`", self.read("powerlab-design-review"))
        self.assertIn("**measure with `check_routing`**", self.read("powerlab-visual-review"))


if __name__ == "__main__":
    unittest.main()
