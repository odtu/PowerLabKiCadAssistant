"""Hand-routed tracks drawn 45 degrees only (patches/kicad-mcp.patch: python/utils/track45.py,
python/commands/hand_route.py).

route_trace and route_pad_to_pad drew one straight line between their points: slanted runs
at any angle, square 90 degree corners, a kink just before a pad, and same-net neighbours
joined by a loop. Run with KiCad's Python, like the other tests:

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" -m unittest discover -s tests -v

The modules have no pcbnew or kipy imports at the top, so they are taken from the patch text.
"""

import math
import os
import sys
import types
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from test_mcp_issues import load, patch_text  # noqa: E402

track45 = load("python/utils/track45.py")


def load_hand_route():
    """hand_route imports `from utils import track45`: give it the patch's track45."""
    saved = {k: sys.modules.get(k) for k in ("utils", "utils.track45")}
    pkg = types.ModuleType("utils")
    pkg.track45 = track45
    sys.modules["utils"] = pkg
    sys.modules["utils.track45"] = track45
    try:
        return load("python/commands/hand_route.py")
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


def pieces(points):
    return [(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:])]


def angle(v):
    return math.degrees(math.atan2(v[1], v[0])) % 360.0


def pad(x=0.0, y=0.0, w=1.5, h=0.6, angle=0.0, shape="roundrect", fine=False, body=None):
    return {"x": x, "y": y, "w": w, "h": h, "angle": angle, "shape": shape, "fine": fine, "body": body}


class Track45Tests(unittest.TestCase):
    def assertOctilinear(self, points, allow_first=False, allow_last=False):
        ps = pieces(points)
        for i, (dx, dy) in enumerate(ps):
            if (i == 0 and allow_first) or (i == len(ps) - 1 and allow_last):
                continue
            self.assertTrue(track45.is_octilinear(dx, dy), f"piece {i} at {angle((dx, dy)):.2f} deg: {points}")
        # ends that don't line up with the grid may leave a piece up to TOL_DEG off it,
        # rather than a sliver of a jog
        self.assertLessEqual(track45.max_turn(points), 45.0 + track45.TOL_DEG, points)

    def assertClose(self, a, b, tol=1e-6):
        self.assertAlmostEqual(a[0], b[0], delta=tol)
        self.assertAlmostEqual(a[1], b[1], delta=tol)

    # --- free ends -----------------------------------------------------------------------
    def test_off_angle_run_becomes_straight_then_45(self):
        pts = track45.route([(0, 0), (10, 3)])
        self.assertEqual(pts, [(0.0, 0.0), (7.0, 0.0), (10.0, 3.0)])
        self.assertOctilinear(pts)

    def test_run_on_the_grid_stays_one_piece(self):
        for end in [(5, 0), (0, -4), (3, 3), (-2.5, 2.5)]:
            self.assertEqual(track45.route([(0, 0), end]), [(0.0, 0.0), (float(end[0]), float(end[1]))])

    def test_steep_off_angle_run(self):
        pts = track45.route([(1, 1), (2.2, 9.7)])
        self.assertClose(pts[0], (1, 1))
        self.assertClose(pts[-1], (2.2, 9.7))
        self.assertOctilinear(pts)

    def test_waypoints_are_passed_through(self):
        pts = track45.route([(0, 0), (5, 0.5), (5, 8), (12, 9)])
        self.assertOctilinear(pts)
        self.assertClose(pts[0], (0, 0))
        self.assertClose(pts[-1], (12, 9))

    def test_existing_track_direction_is_continued(self):
        # a track arriving travelling +x: the new one goes on along x first
        pts = track45.route([(0, 0), (10, 3)], start_dir=(1, 0))
        self.assertEqual(angle(pieces(pts)[0]), 0.0)

    # --- pads ----------------------------------------------------------------------------
    def test_track_leaves_a_pad_along_its_axis_and_clear_of_it(self):
        a = pad(w=1.5, h=0.6)  # long axis along x
        pts = track45.route([(0.2, 0.1), (10, 3)], 0.25, start_pad=a)
        self.assertClose(pts[0], (0, 0))  # snapped to the pad's centre
        first = pieces(pts)[0]
        self.assertEqual(angle(first), 0.0)
        self.assertGreaterEqual(math.hypot(*first), track45.escape_length(a, (1, 0), 0.25) - 1e-6)
        self.assertOctilinear(pts)

    def test_pads_at_both_ends_get_straight_45_straight(self):
        a = pad(0, 0)
        b = pad(10, 3)
        pts = track45.route([(0, 0), (10, 3)], 0.25, a, b)
        ps = pieces(pts)
        self.assertEqual(len(ps), 3)
        self.assertEqual(angle(ps[0]), 0.0)
        self.assertEqual(angle(ps[-1]), 0.0)
        self.assertAlmostEqual(angle(ps[1]), 45.0, places=6)
        for end, u in ((a, (1, 0)), (b, (-1, 0))):
            self.assertGreaterEqual(math.hypot(*(ps[0] if end is a else ps[-1])),
                                    track45.escape_length(end, u, 0.25) - 1e-6)

    def test_no_bend_just_before_a_pad(self):
        """The maintainer's screenshot: a run changing angle right at the pad."""
        b = pad(10, 3, w=0.6, h=1.5)  # long axis along y
        pts = track45.route([(0, 0), (10, 3)], 0.25, end_pad=b)
        last = pieces(pts)[-1]
        u = (-last[0] / math.hypot(*last), -last[1] / math.hypot(*last))
        if len(pts) > 2:
            self.assertGreaterEqual(math.hypot(*last), track45.escape_length(b, u, 0.25) - 1e-6)
        self.assertOctilinear(pts)

    def test_rotated_pad_axis_follows_kicad_orientation(self):
        # KiCad turns counter-clockwise on screen: a 90 degree pad has its x axis pointing up
        ex, ey = track45._pad_axes(pad(angle=90))
        self.assertClose(ex, (0, -1))
        self.assertClose(ey, (1, 0))

    def test_pad_off_the_45_grid_is_left_along_its_own_axis(self):
        a = pad(angle=30)
        pts = track45.route([(0, 0), (10, 3)], 0.25, start_pad=a)
        first = angle(pieces(pts)[0])
        axes = [(-30 + 90 * k) % 360 for k in range(4)]
        self.assertTrue(any(abs((first - ax + 180) % 360 - 180) < 1e-3 for ax in axes), first)
        self.assertOctilinear(pts, allow_first=True)

    def test_pads_on_one_rotated_axis_are_joined_straight(self):
        a = pad(0, 0, angle=-26.5)
        d = (math.cos(math.radians(26.5)) * 1.3, math.sin(math.radians(26.5)) * 1.3)
        b = pad(d[0], d[1], angle=-26.5)
        self.assertEqual(len(track45.route([(0, 0), d], 0.25, a, b)), 2)

    def test_same_net_neighbours_are_joined_directly(self):
        body = (1.9, 3.0)
        for pitch, fine in ((1.27, False), (0.5, True)):
            a = pad(0, 0, 0.25 if fine else 0.6, 0.8 if fine else 1.5, fine=fine, body=body)
            b = pad(pitch, 0, 0.25 if fine else 0.6, 0.8 if fine else 1.5, fine=fine, body=body)
            self.assertEqual(track45.route([(0, 0), (pitch, 0)], 0.25, a, b), [(0.0, 0.0), (pitch, 0.0)])

    def test_fine_pitch_pin_is_left_out_of_its_row(self):
        a = pad(0, 0, 0.25, 0.8, fine=True, body=(1.9, 3.0))  # row along x, body below
        for end in [(6, 0.3), (-5, -2)]:
            pts = track45.route([(0, 0), end], 0.25, start_pad=a)
            self.assertEqual(angle(pieces(pts)[0]), 270.0, pts)  # up, away from the body
            self.assertOctilinear(pts)

    def test_round_pad_takes_any_45_direction(self):
        a = pad(w=1.0, h=1.0, shape="circle")
        self.assertEqual(track45.route([(0, 0), (4, 4)], 0.25, start_pad=a), [(0.0, 0.0), (4.0, 4.0)])

    def test_pad_contains(self):
        a = pad(10, 10, w=2.0, h=1.0, angle=90)  # 1 mm wide in x, 2 mm tall in y
        self.assertTrue(track45.pad_contains(a, 10.4, 10.9))
        self.assertFalse(track45.pad_contains(a, 10.9, 10.4))
        self.assertTrue(track45.pad_contains(pad(w=1, h=1, shape="circle"), 0.3, 0.3))
        self.assertFalse(track45.pad_contains(pad(w=1, h=1, shape="circle"), 0.4, 0.4))

    # --- chamfers and cleanup ------------------------------------------------------------
    def test_90_degree_corner_gets_a_45_chamfer(self):
        pts = track45.chamfer([(0, 0), (10, 0), (10, 5)])
        self.assertEqual(pts, [(0, 0), (9.0, 0.0), (10.0, 1.0), (10, 5)])
        self.assertOctilinear(pts)

    def test_135_degree_turn_gets_two_45_pieces(self):
        pts = track45.chamfer([(0, 0), (5, 0), (1, 4)])
        self.assertEqual(len(pts), 5)
        self.assertOctilinear(pts)
        turns = [abs(track45._turn(u, v)) for u, v in zip(pieces(pts), pieces(pts)[1:])]
        self.assertTrue(all(abs(t - 45) < 1e-6 for t in turns), turns)

    def test_45_degree_corner_is_kept(self):
        self.assertEqual(track45.chamfer([(0, 0), (5, 0), (8, 3)]), [(0, 0), (5, 0), (8, 3)])

    def test_chamfer_shrinks_on_short_pieces(self):
        pts = track45.chamfer([(0, 0), (0.3, 0), (0.3, 0.6)])
        self.assertClose(pts[1], (0.2, 0.0))  # a third of the 0.3 mm piece
        self.assertClose(pts[2], (0.3, 0.1))
        pts = track45.chamfer([(0, 0), (5, 0), (5, 5)], max_chamfer=0.5)
        self.assertClose(pts[1], (4.5, 0.0))

    def test_chamfer_keeps_the_pad_escape(self):
        pts = track45.chamfer([(0, 0), (1.5, 0), (1.5, 5)], keep_first=1.2)
        self.assertGreaterEqual(pts[1][0], 1.2 - 1e-9)

    def test_cleanup_drops_repeats_and_collinear_points(self):
        self.assertEqual(track45.cleanup([(0, 0), (0, 0), (1, 0), (2, 0), (2, 0), (2, 3), (2, 5)]),
                         [(0.0, 0.0), (2.0, 0.0), (2.0, 5.0)])

    def test_every_route_is_45_only(self):
        cases = [((0, 0), (17.3, 4.1)), ((3, 3), (-4, 11)), ((0, 0), (0.4, 0.1)), ((0, 0), (-9, -2))]
        pads = [None, pad(), pad(w=0.6, h=1.5), pad(w=1, h=1, shape="circle")]
        for p, q in cases:
            for a in pads:
                for b in pads:
                    a2 = dict(a, x=p[0], y=p[1]) if a else None
                    b2 = dict(b, x=q[0], y=q[1]) if b else None
                    pts = track45.route([p, q], 0.25, a2, b2)
                    self.assertClose(pts[0], p)
                    self.assertClose(pts[-1], q)
                    self.assertOctilinear(pts)

    # --- a track already on the board ----------------------------------------------------
    def test_joint_chamfer_at_a_90_degree_joint(self):
        jc = track45.joint_chamfer((-5, 0), (0, 0), (0, 5))
        self.assertClose(jc["existing_end"], (-1, 0))
        self.assertEqual(len(jc["points"]), 2)
        self.assertClose(jc["points"][1], (0, 1))

    def test_joint_chamfer_not_needed(self):
        self.assertIsNone(track45.joint_chamfer((-5, 0), (0, 0), (5, 5)))  # 45 degrees
        self.assertIsNone(track45.joint_chamfer((-5, 0), (0, 0), (5, 0)))  # straight on
        self.assertIsNone(track45.joint_chamfer((-5, 0), (0, 0), (-3, 0)))  # back over it

    def test_segments_report_kicad_angles(self):
        segs = track45.segments([(0, 0), (2, 0), (3, -1)])
        self.assertEqual([s["angle"] for s in segs], [0.0, 45.0])  # 45 = up and right on screen


class HandRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hr = load_hand_route()

    def test_plan_chamfers_the_joint_with_the_existing_track(self):
        track = {"layer": "F.Cu", "net": "TCK", "start": (90.0, 70.0), "end": (90.0, 66.0), "locked": False}
        joint = self.hr._pick_joint([track], [], (90.0, 66.0), "F.Cu", "TCK")
        self.assertIsNotNone(joint)
        p = self.hr.plan([(90.0, 66.0), (93.0, 66.0)], 0.25, start_joint=joint)
        (moved, to), = p["moves"]
        self.assertIs(moved, joint)
        self.assertEqual(to, (90.0, 67.0))
        self.assertEqual(p["points"], [(90.0, 67.0), (91.0, 66.0), (93.0, 66.0)])

    def test_no_joint_at_a_via_or_a_branch(self):
        t1 = {"layer": "F.Cu", "net": "A", "start": (0.0, 0.0), "end": (5.0, 0.0)}
        t2 = {"layer": "F.Cu", "net": "A", "start": (5.0, 0.0), "end": (5.0, 5.0)}
        self.assertIsNone(self.hr._pick_joint([t1, t2], [], (5.0, 0.0), "F.Cu", "A"))
        self.assertIsNone(self.hr._pick_joint([t1], [(5.0, 0.0)], (5.0, 0.0), "F.Cu", "A"))
        self.assertIsNone(self.hr._pick_joint([t1], [], (5.0, 0.0), "B.Cu", "A"))

    def test_end_in_a_pad_snaps_to_its_centre_but_never_to_another_net(self):
        pads = [dict(pad(10, 10), layers=["F.Cu"], net="VCC"), dict(pad(10, 10), layers=["B.Cu"], net="GND")]
        self.assertEqual(self.hr._pick_pad(pads, (10.4, 10.1), "F.Cu", "VCC")["net"], "VCC")
        self.assertEqual(self.hr._pick_pad(pads, (10.4, 10.1), "F.Cu", None)["net"], "VCC")
        self.assertIsNone(self.hr._pick_pad(pads, (10.4, 10.1), "F.Cu", "GND"))
        self.assertIsNone(self.hr._pick_pad(pads, (12.0, 10.0), "F.Cu", "VCC"))

    def test_locked_track_keeps_its_corner(self):
        track = {"layer": "F.Cu", "net": "A", "start": (0.0, 4.0), "end": (0.0, 0.0), "locked": True}
        joint = self.hr._pick_joint([track], [], (0.0, 0.0), "F.Cu", "A")
        self.assertEqual(self.hr.plan([(0.0, 0.0), (3.0, 0.0)], 0.25, start_joint=joint)["moves"], [])

    def test_snap45_false_keeps_the_geometry(self):
        p = self.hr.plan([(60, 80), (70, 83)], 0.3, snap45=False)
        self.assertEqual(p["points"], [(60.0, 80.0), (70.0, 83.0)])

    def test_points_and_waypoints(self):
        self.assertEqual(self.hr.path_specs({"points": [[0, 0], [1, 2], [3, 3]]}), ([0, 0], [[1, 2]], [3, 3]))
        self.assertEqual(self.hr.path_specs({"start": {"x": 0, "y": 0}, "end": {"x": 1, "y": 1},
                                             "waypoints": [[0.5, 0]]}),
                         ({"x": 0, "y": 0}, [[0.5, 0]], {"x": 1, "y": 1}))
        self.assertEqual(self.hr.as_point({"x": 10, "y": 20, "unit": "mil"}), (0.254, 0.508))

    def test_via_goes_out_of_the_start_pad_along_its_axis(self):
        a = dict(pad(10, 10, w=1.5, h=0.6), layers=["F.Cu"], side="F.Cu")
        b = dict(pad(20, 14, w=0.6, h=0.8), layers=["B.Cu"], side="B.Cu")
        legs, via, la, lb = self.hr.pad_to_pad_plan(a, b, 0.25, [], None, 0.6)
        self.assertEqual((la, lb), ("F.Cu", "B.Cu"))
        # along +x (towards the other pad), the via's ring 0.25 mm clear of the pad's edge
        self.assertClose(via, (10 + 0.75 + 0.25 + 0.3, 10))
        self.assertEqual(legs[0], ("F.Cu", [(10.0, 10.0), via]))
        self.assertEqual(legs[1][0], "B.Cu")
        self.assertEqual(legs[1][1][0], via)
        self.assertEqual(legs[1][1][-1], (20.0, 14.0))
        self.assertLessEqual(track45.max_turn(legs[1][1]), 45.0 + 1e-6)

    def test_pads_sharing_a_layer_need_no_via(self):
        a = dict(pad(0, 0), layers=["F.Cu", "B.Cu"], side="B.Cu")  # through-hole
        b = dict(pad(8, 3), layers=["B.Cu"], side="B.Cu")
        legs, via, la, lb = self.hr.pad_to_pad_plan(a, b, 0.25, [], None, 0.6)
        self.assertIsNone(via)
        self.assertEqual((la, lb), ("B.Cu", None))

    def assertClose(self, a, b, tol=1e-6):
        self.assertAlmostEqual(a[0], b[0], delta=tol)
        self.assertAlmostEqual(a[1], b[1], delta=tol)


class WiringTests(unittest.TestCase):
    def test_both_tools_use_hand_route_offline_and_live(self):
        patch = patch_text()
        self.assertIn("+            return hand_route.swig_route_trace(self, params)", patch)
        self.assertIn("+            return hand_route.swig_route_pad_to_pad(self, params)", patch)
        self.assertIn('+        "route_pad_to_pad": "_ipc_route_pad_to_pad",', patch)
        self.assertIn("hand_route.ipc_route_trace(self.ipc_board_api._get_board(), params)", patch)
        self.assertIn("hand_route.ipc_route_pad_to_pad(self.ipc_board_api._get_board(), params)", patch)

    def test_schemas_offer_waypoints_and_snap45(self):
        patch = patch_text()
        for text in ("+      waypoints: z", "+      snap45: z", "+      viaSize: z", '+                "snap45": {'):
            self.assertIn(text, patch)


if __name__ == "__main__":
    unittest.main()
