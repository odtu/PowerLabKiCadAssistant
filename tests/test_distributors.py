"""Mouser and Farnell searches for component research (patches/kicad-mcp.patch:
python/commands/distributors.py).

The tests run against a local stand-in for both APIs, so they need no network or keys.
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
ds = load("python/commands/distributors.py")
MOUSER_KEY = "mouser-test-key-123"
FARNELL_KEY = "farnell-test-key-456"

MOUSER_PART = {
    "ManufacturerPartNumber": "BSC093N15NS5ATMA1", "Manufacturer": "Infineon",
    "MouserPartNumber": "726-BSC093N15NS5ATMA", "Description": "MOSFET N-Ch 150V 87A",
    "Category": "MOSFETs", "LifecycleStatus": None, "AvailabilityInStock": "12345",
    "Availability": "12345 In Stock", "LeadTime": "26 Weeks", "Min": "1", "Mult": "1",
    "PriceBreaks": [{"Quantity": 1, "Price": "$4.89", "Currency": "USD"},
                    {"Quantity": 10, "Price": "$3.23", "RawPrice": 3.228, "Currency": "USD"}],
    "DataSheetUrl": "https://www.mouser.com/datasheet/2/196/x.pdf",
    "ProductDetailUrl": "https://www.mouser.com/ProductDetail/726-BSC093N15NS5ATMA",
    "ROHSStatus": "RoHS Compliant",
    "ProductAttributes": [{"AttributeName": "Vds - Drain-Source Breakdown Voltage", "AttributeValue": "150 V"}],
}
OLD_PART = dict(MOUSER_PART, ManufacturerPartNumber="OLD1", LifecycleStatus="Obsolete", MouserPartNumber="N/A",
                AvailabilityInStock=None, Availability=None, PriceBreaks=[], Min="0", Mult="0")  # as Mouser lists it
FARNELL_PRODUCT = {
    "sku": "2480756", "displayName": "INFINEON - BSC093N15NS5ATMA1 - MOSFET",
    "translatedManufacturerPartNumber": "BSC093N15NS5ATMA1", "brandName": "INFINEON",
    "productStatus": "STOCKED", "rohsStatusCode": "YES", "packSize": 1, "unitOfMeasure": "EACH",
    "translatedMinimumOrderQuality": 1,
    "stock": {"level": 812, "leastLeadTime": 0, "status": 1},
    "prices": [{"from": 1, "to": 9, "cost": 5.12}, {"from": 10, "to": 99, "cost": 3.9}],
    "datasheets": [{"type": "T", "description": "Data Sheet", "url": "https://www.farnell.com/datasheets/x.pdf"}],
    "attributes": [{"attributeLabel": "Drain Source Voltage Vds", "attributeUnit": "V", "attributeValue": "150"}],
}


class Service(http.server.BaseHTTPRequestHandler):
    seen = []

    def _send(self, code, body):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        query = dict(urllib.parse.parse_qsl(url.query))
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        Service.seen.append(("POST", url.path, query, body, self.headers.get("User-Agent")))
        if query.get("apiKey") != MOUSER_KEY:  # Mouser answers a bad key in Errors
            return self._send(200, {"Errors": [{"Code": "Invalid", "Message": f"Invalid key {query.get('apiKey')}"}],
                                    "SearchResults": None})
        if url.path.endswith("/search/keyword"):
            return self._send(200, {"Errors": [], "SearchResults": {"NumberOfResult": 2, "Parts": [MOUSER_PART, OLD_PART]}})
        if url.path.endswith("/search/partnumber"):
            return self._send(200, {"Errors": [], "SearchResults": {"NumberOfResult": 1, "Parts": [MOUSER_PART]}})
        self._send(404, {})

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        query = dict(urllib.parse.parse_qsl(url.query))
        Service.seen.append(("GET", url.path, query, None, self.headers.get("User-Agent")))
        if query.get("callInfo.apiKey") != FARNELL_KEY:
            return self._send(403, {"Fault": f"Developer key {query.get('callInfo.apiKey')} inactive"})
        term = query.get("term", "")
        name = ("keywordSearchReturn" if term.startswith("any:") else
                "manufacturerPartNumberSearchReturn" if term.startswith("manuPartNum:") else
                "premierFarnellPartNumberReturn")
        products = FARNELL_PRODUCT if name == "premierFarnellPartNumberReturn" else [FARNELL_PRODUCT]  # one is an object
        self._send(200, {name: {"numberOfResults": 1, "products": products}})

    def log_message(self, *args):
        pass


class PureTests(unittest.TestCase):
    def test_money_and_count(self):
        self.assertEqual(ds.money("$4.89"), 4.89)
        self.assertEqual(ds.money("4,89 €"), 4.89)
        self.assertEqual(ds.money("0,123 €"), 0.123)
        self.assertEqual(ds.money("1.234,50 TL"), 1234.5)
        self.assertEqual(ds.money("1,234.50"), 1234.5)
        self.assertIsNone(ds.money("call"))
        self.assertEqual(ds.count("26,320 In Stock"), 26320)
        self.assertEqual(ds.count(812), 812)
        self.assertIsNone(ds.count("On Order"))

    def test_lifecycle(self):
        for gone in ("Obsolete", "End of Life", "Not Recommended for New Designs", "NO_LONGER_MANUFACTURED"):
            self.assertFalse(ds.is_active(gone), gone)
        for fine in (None, "", "New Product", "STOCKED", "DIRECT_SHIP"):
            self.assertTrue(ds.is_active(fine), fine)


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Service)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.saved = (ds.MOUSER_BASE, ds.FARNELL_BASE)
        ds.MOUSER_BASE, ds.FARNELL_BASE = base + "/api/v1", base + "/catalog/products"
        cls.env = {k: os.environ.get(k) for k in ("MOUSER_API_KEY", "FARNELL_API_KEY", "FARNELL_STORE")}

    @classmethod
    def tearDownClass(cls):
        ds.MOUSER_BASE, ds.FARNELL_BASE = cls.saved
        cls.server.shutdown()
        for k, v in cls.env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def setUp(self):
        Service.seen.clear()
        os.environ["MOUSER_API_KEY"] = MOUSER_KEY
        os.environ["FARNELL_API_KEY"] = FARNELL_KEY
        os.environ.pop("FARNELL_STORE", None)

    def test_mouser_keyword(self):
        out = ds.mouser_search({"keywords": "MOSFET 150V", "limit": 500, "inStock": True})
        self.assertTrue(out["success"], out)
        method, path, query, body, agent = Service.seen[-1]
        self.assertEqual((method, path), ("POST", "/api/v1/search/keyword"))
        req = body["SearchByKeywordRequest"]
        self.assertEqual((req["keyword"], req["records"], req["searchOptions"]), ("MOSFET 150V", 50, "InStock"))
        self.assertIn("PowerLabKiCadAssistant", agent)
        part, old = out["products"]
        self.assertEqual((part["mpn"], part["stock"], part["active"]), ("BSC093N15NS5ATMA1", 12345, True))
        self.assertEqual(part["pricing"][0], {"quantity": 1, "unitPrice": 4.89, "currency": "USD"})
        self.assertEqual(part["pricing"][1]["unitPrice"], 3.228)  # RawPrice wins
        self.assertEqual(part["datasheet"], MOUSER_PART["DataSheetUrl"])
        self.assertEqual(part["parameters"][0]["value"], "150 V")
        self.assertEqual((old["active"], old["stock"], old["unitPrice"]), (False, 0, None))
        self.assertEqual((part["orderable"], old["orderable"], old["mouserPartNumber"]), (True, False, None))

    def test_mouser_part_number(self):
        out = ds.mouser_search({"partNumber": "726-BSC093N15NS5ATMA"})
        self.assertTrue(out["success"], out)
        _, path, _, body, _ = Service.seen[-1]
        self.assertEqual(path, "/api/v1/search/partnumber")
        self.assertEqual(body["SearchByPartRequest"], {"mouserPartNumber": "726-BSC093N15NS5ATMA",
                                                       "partSearchOptions": "Exact"})

    def test_farnell_searches(self):
        out = ds.farnell_search({"keywords": "MOSFET 150V", "inStock": True})
        self.assertTrue(out["success"], out)
        query = Service.seen[-1][2]
        self.assertEqual(query["term"], "any:MOSFET 150V")
        self.assertEqual(query["storeInfo.id"], "tr.farnell.com")  # the default store
        self.assertEqual(query["resultsSettings.responseGroup"], "large")
        self.assertEqual(query["resultsSettings.refinements.filters"], "inStock")
        p = out["products"][0]
        self.assertEqual((p["mpn"], p["manufacturer"], p["stock"], p["active"]), ("BSC093N15NS5ATMA1", "INFINEON", 812, True))
        self.assertEqual(p["pricing"], [{"quantity": 1, "unitPrice": 5.12}, {"quantity": 10, "unitPrice": 3.9}])
        self.assertEqual(p["parameters"][0]["value"], "150 V")
        self.assertEqual(p["productUrl"], "https://tr.farnell.com/2480756")
        self.assertFalse(p["reeled"])

        out = ds.farnell_search({"partNumber": "BSC093N15NS5ATMA1", "store": "uk.farnell.com"})
        self.assertEqual(Service.seen[-1][2]["term"], "manuPartNum:BSC093N15NS5ATMA1")
        self.assertEqual((out["store"], out["products"][0]["farnellPartNumber"]), ("uk.farnell.com", "2480756"))

        os.environ["FARNELL_STORE"] = "de.farnell.com"
        out = ds.farnell_search({"farnellPartNumber": "2480756"})  # products as one object
        self.assertEqual(Service.seen[-1][2]["term"], "id:2480756")
        self.assertEqual((out["store"], len(out["products"])), ("de.farnell.com", 1))

    def test_missing_and_wrong_keys_never_leak(self):
        os.environ.pop("MOUSER_API_KEY")
        os.environ.pop("FARNELL_API_KEY")
        for out, env in ((ds.mouser_search({"keywords": "x"}), "MOUSER_API_KEY"),
                         (ds.farnell_search({"keywords": "x"}), "FARNELL_API_KEY")):
            self.assertFalse(out["success"])
            self.assertEqual(out["requiredEnvironmentVariables"], [env])
        self.assertEqual(Service.seen, [])  # nothing sent without a key

        os.environ["MOUSER_API_KEY"] = "wrong-mouser-key"
        os.environ["FARNELL_API_KEY"] = "wrong-farnell-key"
        for out in (ds.mouser_search({"keywords": "x"}), ds.farnell_search({"keywords": "x"})):
            self.assertFalse(out["success"])
            text = json.dumps(out)
            self.assertNotIn("wrong-mouser-key", text)
            self.assertNotIn("wrong-farnell-key", text)
            self.assertIn("<key>", text)  # the service echoed it; the tool scrubbed it

    def test_bad_input(self):
        self.assertFalse(ds.mouser_search({})["success"])
        self.assertFalse(ds.farnell_search({})["success"])
        self.assertFalse(ds.farnell_search({"keywords": "x", "store": "evil.com/?a="})["success"])
        self.assertEqual(Service.seen, [])


class WiringTests(unittest.TestCase):
    def test_tools_are_wired(self):
        patch = patch_text()
        for tool in ("mouser_search_parts", "farnell_search_parts"):
            self.assertIn(f'+    "{tool}",', patch)  # TypeScript tool
            self.assertIn(f'+  "{tool}", // PowerLab patch', patch)  # long-running
        self.assertIn('+            "mouser_search_parts": distributors.mouser_search,  # PowerLab patch', patch)
        self.assertIn('+            "farnell_search_parts": distributors.farnell_search,  # PowerLab patch', patch)
        self.assertIn('"enrich_datasheets", "mouser_search_parts", "farnell_search_parts"]', patch)  # registry

    def test_skill_and_privacy(self):
        with open(os.path.join(REPO, "skills", "powerlab-component-research", "SKILL.md"), encoding="utf-8") as f:
            skill = f.read()
        for word in ("digikey_search_parts", "mouser_search_parts", "farnell_search_parts"):
            self.assertIn(word, skill)
        with open(os.path.join(REPO, "README.md"), encoding="utf-8") as f:
            readme = f.read()
        for row in ("| Digi-Key searches |", "| Mouser searches |", "| Farnell searches |"):
            self.assertIn(row, readme)


if __name__ == "__main__":
    unittest.main()
