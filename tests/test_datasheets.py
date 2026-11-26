"""Datasheet tools for the panel (patches/kicad-mcp.patch: python/commands/datasheets.py).

fetch_datasheet keeps a datasheet library and, when a site refuses downloads by programs,
opens the page in the user's browser and takes the PDF they save from Downloads.
read_datasheet maps, searches, reads and renders PDFs with PyMuPDF, which the MCP server
already installs into KiCad's Python (the PDF tests are skipped without it).
"""

import http.server
import os
import shutil
import sys
import tempfile
import threading
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from test_mcp_issues import load, patch_text  # noqa: E402

REPO = os.path.dirname(ROOT)
ds = load("python/commands/datasheets.py")


def make_pdf(pages):
    """A small PDF with one line of Helvetica text per entry of each page."""
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", None,
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    kids = []
    for lines in pages:
        body = "BT /F1 14 Tf 72 740 Td 18 TL " + " ".join(
            "(" + l.replace("(", "\\(").replace(")", "\\)") + ") '" for l in lines) + " ET"
        objs.append(f"<< /Length {len(body)} >>\nstream\n{body}\nendstream")
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                    f"/Resources << /Font << /F1 3 0 R >> >> /Contents {len(objs)} 0 R >>")
        kids.append(f"{len(objs)} 0 R")
    objs[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>"
    out = b"%PDF-1.4\n"
    offsets = []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


PDF = make_pdf([
    ["TPX100 100 V N-channel MOSFET", "Features"],
    ["7.1 Absolute Maximum Ratings", "Drain-source voltage VDS 100 V", "Gate-source voltage VGS 20 V"],
    ["7.3 Electrical Characteristics", "RDS(on) at VGS 10 V 2.1 mOhm", "Package Outline"],
])


def has_mupdf():
    try:
        ds._mupdf()
        return True
    except ImportError:
        return False


class TempDirs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.lib = os.path.join(self.tmp, "lib")
        self.downloads = os.path.join(self.tmp, "Downloads")
        os.makedirs(self.downloads)
        self.saved = {k: os.environ.get(k) for k in ("POWERLAB_DATASHEETS", "POWERLAB_DOWNLOADS")}
        os.environ["POWERLAB_DATASHEETS"] = self.lib
        os.environ["POWERLAB_DOWNLOADS"] = self.downloads

    def tearDown(self):
        for k, v in self.saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, path, data=PDF):
        with open(path, "wb") as f:
            f.write(data)
        return path


class WiringTests(unittest.TestCase):
    def test_tools_are_wired(self):
        patch = patch_text()
        for tool in ("fetch_datasheet", "read_datasheet"):
            self.assertIn(f'+    "{tool}",', patch)  # TypeScript tool
            self.assertIn(f'"{tool}": datasheets.', patch)  # Python dispatcher
        self.assertIn('"fetch_datasheet", "read_datasheet", "get_datasheet_url", "enrich_datasheets"],',
                      patch)  # registry, so search_tools finds them
        self.assertIn('+  "fetch_datasheet", // PowerLab patch', patch)  # 600 s: it waits for the browser
        self.assertIn("+from commands import datasheets, part_search, part_spacing,", patch)

    def test_mupdf_never_writes_to_stdout(self):
        """The Python worker answers on stdout; a damaged PDF makes MuPDF print."""
        text = patch_text()
        self.assertIn("+            pymupdf.set_messages(pylogging=True)", text)
        self.assertIn("+            pymupdf.TOOLS.mupdf_display_errors(False)", text)

    def test_panel_loads_the_skill(self):
        with open(os.path.join(REPO, "plugin", "powerlab_assistant", "panel.py"), encoding="utf-8") as f:
            self.assertIn("powerlab-datasheet-lookup", f.read())
        skill = os.path.join(REPO, "skills", "powerlab-datasheet-lookup", "SKILL.md")
        with open(skill, encoding="utf-8") as f:
            text = f.read()
        self.assertTrue(text.startswith("---\nname: powerlab-datasheet-lookup\n"))
        for word in ("fetch_datasheet", "read_datasheet", "browser: true", "never try to\n   get round it",
                     "and `lcsc`", "`printedDate`"):
            self.assertIn(word, text)


class PureTests(unittest.TestCase):
    def test_printed_date(self):
        cases = {
            "LMR51430 SLUSEF4A – JUNE 2022 – REVISED NOVEMBER 2022 www.ti.com": "November 2022",
            "PSMN1R0-30YLD N-channel 30 V 14 December 2015 Product data sheet": "14 December 2015",
            "DS12499 - Rev 3 - July 2020 For further information contact": "July 2020",
            "Data sheet, April 21, 2023, rev. B": "21 April 2023",
            "Released 2019-03-05, superseded 2021-11-30": "30 November 2021",
            "No date here, (C) 2022 and 60134": None,
        }
        for text, date in cases.items():
            self.assertEqual(ds.printed_date(text), date, text)

    def test_same_part(self):
        self.assertTrue(ds.same_part("PSMN1R0-30YLD", "PSMN1R0-30YLDX"))  # packing suffix
        self.assertTrue(ds.same_part("STUSB4500", "STUSB4500QTR"))
        self.assertFalse(ds.same_part("PSMN1R0-30YLD", "PSMN1R2-30YLD"))
        self.assertFalse(ds.same_part("LMR51430", "LMR51420"))
        self.assertFalse(ds.same_part("TPX100", ""))

    def test_lcsc_product_reads_the_parts_own_datasheet(self):
        product = ds.lcsc_product(LCSC_PAGE.format(base="https://datasheet.lcsc.com"))
        self.assertEqual(product, {"sku": "C100", "mpn": "TPX100X", "brand": "Lab",
                                   "datasheet": "https://datasheet.lcsc.com/ldx-datasheet.pdf?productCode=C100"})
        self.assertIsNone(ds.lcsc_product("<html>no data</html>"))


class DownloadWatchTests(TempDirs):
    """The browser path: the first new PDF that is finished and stops growing."""

    def run_watch(self, steps, wait=10):
        before = ds._pdfs_in(self.downloads)
        t = [0.0]
        script = list(steps)

        def sleep(_):
            t[0] += 1
            if script:
                script.pop(0)()

        return ds.wait_for_download(self.downloads, before, wait, clock=lambda: t[0], sleep=sleep)

    def test_takes_a_finished_new_pdf(self):
        old = self.write(os.path.join(self.downloads, "old.pdf"))
        new = os.path.join(self.downloads, "TPX100.pdf")
        steps = [
            lambda: self.write(new + ".crdownload", b"%PDF-1.4 partial"),  # Chrome/Edge still writing
            lambda: self.write(new, b"%PDF-1.4 half"),  # Firefox: final name + .part
            lambda: (os.remove(new + ".crdownload"), self.write(new)),
        ]
        found = self.run_watch(steps)
        self.assertEqual(found, new)
        self.assertNotEqual(found, old)

    def test_ignores_non_pdf_and_times_out(self):
        steps = [lambda: self.write(os.path.join(self.downloads, "page.pdf"), b"<html>bot check</html>")]
        self.assertIsNone(self.run_watch(steps, wait=4))

    def test_a_pdf_saved_over_an_old_one_counts(self):
        path = self.write(os.path.join(self.downloads, "TPX100.pdf"), b"%PDF-1.4 old")
        os.utime(path, (1, 1))
        self.assertEqual(self.run_watch([lambda: self.write(path)]), path)


LCSC_PDF = make_pdf([["TPX100 100 V N-channel MOSFET", "14 December 2015 Product data sheet"],
                     ["7.1 Absolute Maximum Ratings", "Gate-source voltage VGS 20 V"]])

LCSC_PAGE = """<html><head><script type="application/ld+json">{{"@context":"https://schema.org",
"@type":"Product","name":"Lab TPX100X","sku":"C100","mpn":"TPX100X","brand":{{"@type":"Brand","name":"Lab"}},
"subjectOf":{{"@type":"DigitalDocument","name":"Datasheet","url":"{base}/ldx-datasheet.pdf?productCode=C100"}}}}
</script><script type="application/ld+json">{{"@type":"BreadcrumbList"}}</script></head><body>
<script>window.__NUXT__={{"similar":[{{"pdfUrl":"{base}/other-part.pdf"}}]}}</script></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    agents = []
    paths = []

    def do_GET(self):
        Handler.agents.append(self.headers.get("User-Agent"))
        Handler.paths.append(self.path)
        if self.path == "/product-detail/C100.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(LCSC_PAGE.format(base="http://" + self.headers["Host"]).encode())
        elif self.path.startswith("/ldx-datasheet.pdf"):
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.end_headers()
            self.wfile.write(LCSC_PDF)
        elif self.path == "/ok.pdf":
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.end_headers()
            self.wfile.write(PDF)
        elif self.path == "/check":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body>Checking your browser...</body></html>")
        else:
            self.send_response(403)
            self.end_headers()

    def log_message(self, *args):
        pass


class FetchTests(TempDirs):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_downloads_a_pdf_and_says_who_it_is(self):
        out = ds.fetch({"part": "TPX100", "maker": "Lab Parts", "url": self.base + "/ok.pdf"})
        self.assertTrue(out["success"], out)
        self.assertEqual(out["pdf"], os.path.join(self.lib, "Lab_Parts", "TPX100.pdf"))
        self.assertTrue(os.path.isfile(out["pdf"][:-4] + ".json"))
        self.assertFalse(os.path.exists(out["pdf"] + ".download"))
        self.assertTrue(Handler.agents[-1].startswith("PowerLabKiCadAssistant"))  # no browser disguise
        again = ds.fetch({"part": "tpx100", "maker": "Lab Parts"})
        self.assertTrue(again["success"])
        self.assertIn("Already in the datasheet library", again["message"])

    def test_refusals_lead_to_the_browser_not_round_it(self):
        for path, why in (("/blocked", "HTTP 403"), ("/check", "an HTML page")):
            n = len(Handler.agents)
            out = ds.fetch({"part": "TPX100", "url": self.base + path})
            self.assertFalse(out["success"])
            self.assertTrue(out["refused"])
            self.assertIn(why, out["reason"])
            self.assertIn("lcsc", out["message"])  # LCSC's copy next, with nothing for the user to do
            self.assertIn("browser: true", out["message"])  # the user's browser only after that
            self.assertIn("Don't try to get round it", out["message"])
            self.assertEqual(len(Handler.agents), n + 1)  # one request, no retries

    def lcsc_on_local_server(self):
        """LCSC's checks accept this test server's pages in place of lcsc.com."""
        saved = ds.LCSC_PAGE, ds._lcsc_host_ok
        ds.LCSC_PAGE = self.base + "/product-detail/{}.html"
        ds._lcsc_host_ok = lambda url: url.startswith(self.base)
        self.addCleanup(lambda: (setattr(ds, "LCSC_PAGE", saved[0]), setattr(ds, "_lcsc_host_ok", saved[1])))

    def test_lcsc_copy_when_the_maker_refuses(self):
        self.lcsc_on_local_server()
        out = ds.fetch({"part": "TPX100", "maker": "Lab", "url": self.base + "/blocked", "lcsc": "c100"})
        self.assertTrue(out["success"], out)
        self.assertEqual(out["copy"], "lcsc")
        self.assertEqual((out["lcsc"], out["mpn"]), ("C100", "TPX100X"))
        self.assertIn("HTTP 403", out["makerRefused"])
        self.assertIn("ldx-datasheet.pdf", Handler.paths[-1])  # the page's own datasheet, not a related part's
        self.assertTrue(all(a.startswith("PowerLabKiCadAssistant") for a in Handler.agents[-3:]))
        again = ds.fetch({"part": "TPX100", "maker": "Lab"})
        self.assertEqual(again["copy"], "lcsc")
        if not has_mupdf():
            return  # the printed date is read from the PDF's text, which needs PyMuPDF
        self.assertEqual(out["printedDate"], "14 December 2015")
        self.assertIn("dated 14 December 2015", out["note"])
        self.assertIn("dated 14 December 2015", again["note"])  # the date goes with every later use

    def test_lcsc_alone_and_a_different_part_refused(self):
        self.lcsc_on_local_server()
        self.assertTrue(ds.fetch({"part": "TPX100", "lcsc": "C100"})["success"])
        out = ds.fetch({"part": "TPX200", "url": self.base + "/blocked", "lcsc": "C100"})
        self.assertFalse(out["success"])
        self.assertIn("is TPX100X, not TPX200", out["reason"])
        self.assertIn("browser: true", out["message"])
        self.assertFalse(ds.fetch({"part": "TPX100", "lcsc": "C999", "refresh": True})["success"])  # 403 page

    def test_lcsc_only_on_lcsc_com(self):
        self.assertEqual(ds.lcsc_page("c478145"), "https://www.lcsc.com/product-detail/C478145.html")
        page = "https://www.lcsc.com/product-detail/C478145.html"
        self.assertEqual(ds.lcsc_page(page), page)
        for bad in ("https://evil.example/product-detail/C1.html", "http://www.lcsc.com/x", "478145",
                    "https://lcsc.com.evil.example/x"):
            self.assertIsNone(ds.lcsc_page(bad), bad)
        out = ds.fetch({"part": "TPX100", "lcsc": "https://evil.example/x"})
        self.assertFalse(out["success"])

    def test_browser_replaces_lcsc_copy(self):
        self.lcsc_on_local_server()
        ds.fetch({"part": "TPX100", "maker": "Lab", "url": self.base + "/blocked", "lcsc": "C100"})
        out = ds.fetch({"part": "TPX100", "maker": "Lab", "url": self.base + "/blocked", "browser": True,
                        "wait": 10}, opener=lambda url: self.write(os.path.join(self.downloads, "new.pdf")))
        self.assertTrue(out["success"], out)
        self.assertEqual(out["copy"], "browser")
        self.assertEqual(ds.fetch({"part": "TPX100", "maker": "Lab"})["copy"], "browser")

    def test_browser_path_takes_the_users_download(self):
        opened = []

        def opener(url):  # the user's browser: they pass the check and save the PDF
            opened.append(url)
            self.write(os.path.join(self.downloads, "tpx100-datasheet.pdf"))

        out = ds.fetch({"part": "TPX100", "maker": "Lab", "url": self.base + "/blocked", "browser": True,
                        "wait": 10}, opener=opener)
        self.assertEqual(opened, [self.base + "/blocked"])
        self.assertTrue(out["success"], out)
        self.assertEqual(out["pdf"], os.path.join(self.lib, "Lab", "TPX100.pdf"))
        self.assertIn("browser download", out["source"])
        self.assertTrue(os.path.isfile(os.path.join(self.downloads, "tpx100-datasheet.pdf")))  # left in place

    def test_only_web_urls(self):
        out = ds.fetch({"part": "X", "url": "file:///C:/Windows/win.ini", "browser": True}, opener=self.fail)
        self.assertFalse(out["success"])
        self.assertFalse(ds.fetch({"part": "X", "url": "file:///etc/passwd"})["success"])

    def test_adds_a_file_and_rejects_non_pdfs(self):
        pdf = self.write(os.path.join(self.tmp, "attached.pdf"))
        out = ds.fetch({"part": "TPX100", "file": pdf})
        self.assertTrue(out["success"])
        self.assertTrue(os.path.isfile(pdf))
        html = self.write(os.path.join(self.tmp, "page.pdf"), b"<html></html>")
        self.assertFalse(ds.fetch({"part": "TPX100", "file": html, "refresh": True})["success"])

    def test_not_in_library_without_url(self):
        out = ds.fetch({"part": "NOPE1"})
        self.assertFalse(out["success"])
        self.assertTrue(out["notInLibrary"])


@unittest.skipUnless(has_mupdf(), "PyMuPDF isn't installed (the MCP server's requirements.txt has it)")
class ReadTests(TempDirs):
    def setUp(self):
        super().setUp()
        self.pdf = ds.fetch({"part": "TPX100", "maker": "Lab", "file": self.write(
            os.path.join(self.tmp, "x.pdf"))})["pdf"]

    def test_list_and_resolve(self):
        out = ds.read({"mode": "list", "part": "tpx"})
        self.assertEqual([d["part"] for d in out["datasheets"]], ["TPX100"])
        self.assertEqual(out["datasheets"][0]["pages"], 3)
        self.assertFalse(ds.read({"mode": "map", "part": "OTHER9"})["success"])

    def test_map_finds_sections(self):
        out = ds.read({"mode": "map", "part": "TPX100"})
        self.assertTrue(out["success"], out)
        self.assertEqual(out["pages"], 3)
        self.assertEqual(out["sections"]["absolute maximum ratings"], [2])
        self.assertEqual(out["sections"]["electrical characteristics"], [3])
        self.assertEqual(out["sections"]["package / mechanical"], [3])
        self.assertIn("TPX100", out["page1"])

    def test_find_and_text(self):
        hits = ds.read({"mode": "find", "part": "TPX100", "words": ["VGS", "RDS(on)"]})["hits"]
        self.assertEqual(hits[0]["page"], 3)
        text = ds.read({"mode": "text", "part": "TPX100", "page": 2})
        self.assertIn("Drain-source voltage VDS 100 V", text["text"])
        self.assertFalse(ds.read({"mode": "text", "part": "TPX100", "page": 9})["success"])

    def test_render_page_and_clip(self):
        page = ds.read({"mode": "render", "part": "TPX100", "page": 2, "dpi": 72})
        self.assertTrue(page["success"], page)
        self.assertEqual((page["width"], page["height"]), (612, 792))
        with open(page["png"], "rb") as f:
            self.assertTrue(f.read(8).startswith(b"\x89PNG"))
        clip = ds.read({"mode": "render", "part": "TPX100", "page": 2, "dpi": 144, "clip": [0, 0, 0.5, 0.25]})
        self.assertEqual((clip["width"], clip["height"]), (612, 396))
        self.assertNotEqual(clip["png"], page["png"])
        self.assertTrue(clip["png"].startswith(os.path.join(self.lib, "_renders")))
        bad = ds.read({"mode": "render", "part": "TPX100", "page": 2, "clip": [0.5, 0, 0.2, 1]})
        self.assertFalse(bad["success"])

    def test_wrong_datasheet_is_flagged(self):
        out = ds.fetch({"part": "ZZQ9000", "file": self.pdf})
        self.assertIn("warning", out)


if __name__ == "__main__":
    unittest.main()
