"""Catalogue search for component research (patches/kicad-mcp.patch: python/commands/part_search.py).

search_lcsc_catalog asks jlcsearch for candidates. These tests run against a local stand-in
for the service, so they need no network.
"""

import http.server
import json
import os
import sys
import threading
import unittest
import urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from test_mcp_issues import load, patch_text  # noqa: E402

REPO = os.path.dirname(ROOT)
ps = load("python/commands/part_search.py")

MOSFETS = [
    {"lcsc": 2995350, "mfr": "AP1310K", "package": "TO-252", "stock": 8284, "price1": 0.2233,
     "drain_source_voltage": 100, "continuous_drain_current": 50, "is_basic": False, "is_preferred": False,
     "attributes": json.dumps({"RDS(on)": "9.5mΩ@10V"}), "description": "100V 50A N-channel TO-252"},
    {"lcsc": 8545, "mfr": "2N7002", "package": "SOT-23", "stock": 6000028, "price1": 0.0155,
     "drain_source_voltage": 60, "continuous_drain_current": 0.115, "is_basic": True},
    {"lcsc": 1, "mfr": "GONE1", "package": "TO-252", "stock": 0, "price1": 0.1,
     "drain_source_voltage": 150, "continuous_drain_current": 80},
    {"lcsc": 2, "mfr": "NOVDS", "package": "TO-252", "stock": 10, "price1": 0.05,
     "drain_source_voltage": None, "continuous_drain_current": 60},
]
COMPONENTS = [{"lcsc": 478145, "mfr": "PSMN1R0-30YLDX", "package": "LFPAK-56", "stock": 550,
               "price": "1-9:1.2625,10-29:1.051,1500-:0.7045", "category": "Transistors/Thyristors",
               "subcategory": "MOSFETs", "is_basic": False, "is_preferred": False,
               "description": "N-channel 30V 300A  LFPAK-56   MOSFETs"}]


class Service(http.server.BaseHTTPRequestHandler):
    seen = []

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        query = dict(urllib.parse.parse_qsl(url.query))
        Service.seen.append((url.path, query, self.headers.get("User-Agent")))
        if url.path == "/":
            body, ctype = b'<a href="/mosfets/list">M</a><a href="/diodes/list">D</a><a href="/categories/list">C</a>', "text/html"
        elif url.path == "/components/list.json":  # like jlcsearch: long queries match nothing
            rows = COMPONENTS if len(query.get("search", "").split()) <= 2 else []
            body, ctype = json.dumps({"components": rows}).encode(), "application/json"
        elif url.path == "/mosfets/list.json":
            rows = MOSFETS  # like jlcsearch: honours the numeric minimum, not the rest
            if "drain_source_voltage_min" in query:
                rows = [r for r in rows if (r["drain_source_voltage"] or 0) >= float(query["drain_source_voltage_min"])]
            body, ctype = json.dumps({"mosfets": rows[: int(query.get("limit", 100))]}).encode(), "application/json"
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class PureTests(unittest.TestCase):
    def test_price_tiers(self):
        self.assertEqual(ps.price_tiers("1-9:1.2625,10-29:1.051,1500-:0.7045"),
                         [{"from": 1, "usd": 1.2625}, {"from": 10, "usd": 1.051}, {"from": 1500, "usd": 0.7045}])
        self.assertEqual(ps.price_tiers(None), [])

    def test_tidy_keeps_what_research_needs(self):
        row = ps.tidy(MOSFETS[0])
        self.assertEqual(row["lcsc"], "C2995350")  # fetch_datasheet's lcsc
        self.assertEqual((row["mpn"], row["package"], row["stock"], row["priceUsd"]), ("AP1310K", "TO-252", 8284, 0.2233))
        self.assertEqual(row["params"], {"drain_source_voltage": 100, "continuous_drain_current": 50})
        self.assertEqual(row["attributes"], {"RDS(on)": "9.5mΩ@10V"})
        self.assertNotIn("jlcpcbLibrary", row)
        self.assertEqual(ps.tidy(MOSFETS[1])["jlcpcbLibrary"], "basic")
        comp = ps.tidy(COMPONENTS[0])
        self.assertEqual(comp["priceUsd"], 1.2625)
        self.assertEqual(comp["description"], "N-channel 30V 300A LFPAK-56 MOSFETs")

    def test_filters_the_service_ignored_are_checked(self):
        rows = [ps.tidy(r) for r in MOSFETS]
        kept, ignored = ps.check_filters(rows, {"drain_source_voltage_min": 100, "package": "TO-252"})
        self.assertEqual([r["mpn"] for r in kept], ["AP1310K", "GONE1"])  # NOVDS: Vds unknown, not shown to meet it
        self.assertEqual(ignored, ["drain_source_voltage_min", "package"])
        kept, ignored = ps.check_filters(rows, {"continuous_drain_current_max": 1})
        self.assertEqual([r["mpn"] for r in kept], ["2N7002"])
        diodes = [{"mpn": "M7", "package": "SMA", "params": {"is_schottky": False, "reverse_voltage": 1000}},
                  {"mpn": "SS110", "package": "SMA", "params": {"is_schottky": True, "reverse_voltage": 100}}]
        kept, ignored = ps.check_filters(diodes, {"is_schottky": True})
        self.assertEqual([r["mpn"] for r in kept], ["SS110"])
        self.assertEqual(ignored, ["is_schottky"])


class ServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Service)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.saved = ps.BASE
        ps.BASE = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        ps.BASE = cls.saved
        cls.server.shutdown()

    def setUp(self):
        ps._TABLES.clear()

    def test_text_search(self):
        out = ps.search({"query": "PSMN1R0-30YLD", "package": "LFPAK-56"})
        self.assertTrue(out["success"], out)
        self.assertEqual(out["parts"][0]["lcsc"], "C478145")
        path, query, agent = Service.seen[-1]
        self.assertEqual((path, query["search"], query["package"]), ("/components/list.json", "PSMN1R0-30YLD", "LFPAK-56"))
        self.assertTrue(agent.startswith("PowerLabKiCadAssistant"))  # honest client
        self.assertIn("datasheet", out["note"])
        self.assertNotIn("searchedFor", out)
        self.assertFalse(ps.search({"query": " "})["success"])

    def test_long_text_search_drops_words(self):
        n = len(Service.seen)
        out = ps.search({"query": "half-bridge gate driver 100V"})
        self.assertEqual(out["searchedFor"], "half-bridge gate")
        self.assertIn("every word in one listing", out["searchNote"])
        self.assertEqual([q["search"] for _, q, _ in Service.seen[n:]],
                         ["half-bridge gate driver 100V", "half-bridge gate driver", "half-bridge gate"])
        self.assertEqual(out["parts"][0]["lcsc"], "C478145")

    def test_table_with_filters_stock_and_sort(self):
        out = ps.search({"table": "mosfets", "filters": {"drain_source_voltage_min": 100}})
        self.assertEqual([p["mpn"] for p in out["parts"]], ["AP1310K"])  # GONE1 has no stock
        self.assertNotIn("ignoredByService", out)  # the service applied it
        self.assertEqual(Service.seen[-1][1]["limit"], "100")  # filtering fetches a full page
        out = ps.search({"table": "mosfets", "filters": {"package": "TO-252"}, "sortBy": "priceUsd"})
        self.assertTrue(out["success"], out)
        self.assertEqual([p["mpn"] for p in out["parts"]], ["NOVDS", "AP1310K"])  # 2N7002 is SOT-23
        self.assertEqual(out["ignoredByService"], ["package"])  # the stand-in, like jlcsearch, skips some
        self.assertIn("doesn't filter on package", out["filterNote"])
        both = ps.search({"table": "mosfets", "inStock": False, "sortBy": "continuous_drain_current", "descending": True})
        self.assertEqual([p["mpn"] for p in both["parts"]][:2], ["GONE1", "NOVDS"])

    def test_tables_and_bad_input(self):
        out = ps.search({"mode": "tables"})
        self.assertEqual(out["tables"], ["diodes", "mosfets"])  # categories isn't a parts table
        self.assertIn("drain_source_voltage", ps.search({"mode": "tables", "table": "mosfets"})["fields"])
        missing = ps.search({"table": "gate_drivers"})
        self.assertFalse(missing["success"])
        self.assertEqual(missing["tables"], ["diodes", "mosfets"])
        for bad in ({"table": "../x"}, {"table": "mosfets", "filters": {"a;b": 1}},
                    {"table": "mosfets", "filters": {"x_min": [1]}}, {"mode": "other"}):
            self.assertFalse(ps.search(bad)["success"], bad)


class WiringTests(unittest.TestCase):
    def test_tool_is_wired(self):
        patch = patch_text()
        self.assertIn('+    "search_lcsc_catalog",', patch)  # TypeScript tool
        self.assertIn('+            "search_lcsc_catalog": part_search.search,  # PowerLab patch', patch)
        self.assertIn('"search_lcsc_catalog", "fetch_datasheet", "read_datasheet"', patch)  # registry
        self.assertIn('+  "search_lcsc_catalog", // PowerLab patch', patch)  # long-running
        self.assertIn("+from commands import datasheets, part_search,", patch)

    def test_skill_panel_and_privacy(self):
        with open(os.path.join(REPO, "skills", "powerlab-component-research", "SKILL.md"), encoding="utf-8") as f:
            skill = f.read()
        self.assertTrue(skill.startswith("---\nname: powerlab-component-research\n"))
        for word in ('library: "METUPowerLab"', "search_lcsc_catalog", "ignoredByService", "`lcsc`",
                     "design-requirements.md", "DesignRules.md"):
            self.assertIn(word, skill)
        with open(os.path.join(REPO, "plugin", "powerlab_assistant", "panel.py"), encoding="utf-8") as f:
            self.assertIn("powerlab-component-research", f.read())
        with open(os.path.join(REPO, "README.md"), encoding="utf-8") as f:
            readme = f.read()
        self.assertIn("| Catalogue searches | [jlcsearch]", readme)  # what leaves the computer
        self.assertIn("| Datasheet downloads |", readme)
        with open(os.path.join(REPO, "THIRD_PARTY_NOTICES.md"), encoding="utf-8") as f:
            self.assertIn("jlcsearch", f.read())


if __name__ == "__main__":
    unittest.main()
