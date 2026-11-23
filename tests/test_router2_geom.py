"""PowerLab router 2's grid geometry (patches/kicad-mcp.patch: python/commands/powerlab_router2/geom.py).

New copper is stamped on the router's grid by cell centre, like fixed copper: Pillow's lines
and ellipses missed the shape by up to a cell either way, so lanes the board allows between two
new tracks could read as taken (TestPCB2: 130 -> 139 joins with this and the retry). And two straight tracks are checked
by their exact distance: the polygon check's 2 um allowance let a track 1.5 um short through.

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" -m unittest discover -s tests -v
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_mcp_issues import load  # noqa: E402

try:
    import numpy  # noqa: F401
    import PIL  # noqa: F401
    G = load("python/commands/powerlab_router2/geom.py")
except ImportError:  # GitHub's runner may lack Pillow
    G = None


@unittest.skipIf(G is None, "numpy and Pillow are needed")
class ExactStampTests(unittest.TestCase):
    def test_cells_by_centre(self):
        g = G.Grid(0.0, 0.0, 10.0, 10.0, 0.1)
        r = 0.35
        p = g.patch([([(2.03, 2.07), (6.21, 2.07)], r)], [((7.02, 7.05), 0.55)], exact=True)
        for j in range(p.a.shape[0]):
            for i in range(p.a.shape[1]):
                x, y = g.at(p.i0 + i, p.j0 + j)
                d_line = G.seg_dist((x, y), (x, y), (2.03, 2.07), (6.21, 2.07))
                d_disc = math.dist((x, y), (7.02, 7.05))
                inside = d_line < r - 1e-9 or d_disc < 0.55 - 1e-9
                self.assertEqual(bool(p.a[j, i]), inside, (x, y))

    def test_empty(self):
        g = G.Grid(0.0, 0.0, 10.0, 10.0, 0.1)
        self.assertIsNone(g.patch([], [], exact=True))


@unittest.skipIf(G is None, "numpy and Pillow are needed")
class SegDistTests(unittest.TestCase):
    def test_parallel(self):
        # sf-motion: GLA at y 107.44586 beside GHA at 107.8, 0.2032 mm tracks: 1.5 um short of 0.1524
        d = G.seg_dist((155.3, 107.44586), (158.2, 107.44586), (151.4, 107.8), (158.4, 107.8))
        self.assertAlmostEqual(d - 0.2032, 0.15094, places=5)
        self.assertLess(d - 0.2032, 0.1524)

    def test_crossing_and_apart(self):
        self.assertEqual(G.seg_dist((0, 0), (1, 0), (0.5, -1), (0.5, 1)), 0.0)
        self.assertAlmostEqual(G.seg_dist((0, 0), (1, 0), (2, 1), (3, 1)), math.sqrt(2))
        self.assertAlmostEqual(G.seg_dist((0, 0), (0, 0), (1, 1), (1, -1)), 1.0)


if __name__ == "__main__":
    unittest.main()
