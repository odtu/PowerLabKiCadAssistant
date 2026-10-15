"""The final design review, shown in the panel and saved as a PDF.

The powerlab-design-review skill has Claude write design-review/design-review.md in the
project folder. When that run ends, the panel turns the file into HTML (its images
embedded) for the chat, and prints the same HTML to design-review.pdf next to it with
Microsoft Edge, which every Windows 10 and 11 has, run headless. Nothing leaves the computer.
"""

import base64
import html
import os
import pathlib
import re
import shutil
import subprocess
import tempfile

from .common import CREATE_NO_WINDOW

FILE_NAME = "design-review.md"
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
               ".gif": "image/gif", ".webp": "image/webp"}
MAX_IMAGE_BYTES = 8 * 1024 * 1024
PDF_TIMEOUT = 120  # seconds; a report with a dozen board views prints in a few
EDGE_CANDIDATES = [
    os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
    os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
]
SEVERITIES = ("critical", "high", "medium", "low", "cosmetic")

IMAGE_LINE = re.compile(r"^\s*!\[([^\]]*)\]\(([^)]+)\)\s*$")
TABLE_RULE = re.compile(r"^\|[\s:|-]+\|\s*$")
BLOCK_START = re.compile(r"^(\s*```|#{1,6}\s|\s*([-*]|\d+\.)\s|\|)")
LIST_ITEM = re.compile(r"^\s*([-*]|\d+\.)\s")

CSS = """
@page { size: A4; margin: 16mm 14mm; }
body { font: 10.5pt/1.45 "Segoe UI", Arial, sans-serif; color: #1d232a; margin: 0; }
h1 { font-size: 19pt; margin: 0 0 4pt; }
h1 + p { color: #5b6672; margin-top: 0; }
h2 { font-size: 13.5pt; margin: 18pt 0 6pt; padding-bottom: 3pt; border-bottom: 1.5pt solid #d6dce2; }
h3 { font-size: 11pt; margin: 12pt 0 5pt; }
h3.sev { display: inline-block; padding: 1pt 8pt; border-radius: 8pt; color: #fff; }
h3.sev-critical { background: #b42318; } h3.sev-high { background: #c4570c; }
h3.sev-medium { background: #a37b00; } h3.sev-low { background: #3e6a9c; }
h3.sev-cosmetic { background: #6b7480; }
p, ul, ol { margin: 0 0 7pt; } ul, ol { padding-left: 18pt; } li { margin: 2pt 0; }
ul { list-style-type: "\\2022  "; }
table { border-collapse: collapse; width: 100%; margin: 0 0 9pt; font-size: 9.5pt; }
th, td { border: 0.75pt solid #c9d0d7; padding: 3pt 5pt; text-align: left; vertical-align: top; }
th { background: #eef1f4; }
td:nth-child(-n+2) { white-space: nowrap; }  /* # and rule ID */
tr { break-inside: avoid; }
code { font-family: Consolas, monospace; font-size: 9pt; background: #eef1f4; padding: 0 3pt; border-radius: 3pt; }
pre { background: #eef1f4; padding: 6pt 8pt; border-radius: 4pt; white-space: pre-wrap; }
pre code { background: none; padding: 0; }
a { color: #1f5fa8; }
a.loc { color: inherit; text-decoration: none; }  /* clickable in the panel only */
figure { margin: 8pt 0 12pt; break-inside: avoid; }
figure img { display: block; box-sizing: border-box; max-width: 100%; max-height: 235mm; margin: 0 auto; border: 0.75pt solid #c9d0d7; }
figcaption { font-size: 9pt; color: #5b6672; text-align: center; margin-top: 3pt; }
.missing { color: #b42318; font-style: italic; }
.foot { margin-top: 18pt; font-size: 8.5pt; color: #5b6672; }
"""


def is_review(path):
    return os.path.basename(path or "").lower() == FILE_NAME


def find_edge():
    for candidate in EDGE_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate
    return shutil.which("msedge")


def _inline(text):
    out = html.escape(text, quote=True)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(^|[^*])\*([^*\s][^*]*)\*", r"\1<em>\2</em>", out)
    # A place on the board (see parse_location): the panel shows it in KiCad when clicked.
    out = re.sub(r"\[([^\]]+)\]\(kicad:([^)\s]+)\)",
                 r'<a class="loc" data-loc="\2" title="Show in KiCad">\1</a>', out)
    return re.sub(r"\[([^\]]+)\]\((https?:[^)\s]+)\)", r'<a href="\2">\1</a>', out)


NEAR_MM = 2.5  # at=x,y: what lies within this distance of the point
SMALL_MM = 10.0  # a selection smaller than this gets zoomed out once, to show its surroundings


def parse_location(target):
    """A `kicad:` link target -> {"refs": [...], "nets": [...], "areas": [(x1, y1, x2, y2)]}.

    `refs=U6,Q2` parts; `net=GLC` a net (repeatable); `area=x1,y1,x2,y2` and `at=x,y` places,
    in mm in board coordinates as KiCad shows them. Joined with `&`; values percent-encoded.
    A bare `U6,Q2` means refs."""
    from urllib.parse import unquote

    found = {"refs": [], "nets": [], "areas": []}
    for part in (target or "").strip().split("&"):
        key, sep, value = part.partition("=")
        if not sep:
            key, value = "refs", part
        key = key.strip().lower()
        if key == "net":
            if unquote(value).strip():
                found["nets"].append(unquote(value).strip())
            continue
        values = [unquote(v).strip() for v in value.split(",") if unquote(v).strip()]
        if key in ("refs", "ref"):
            found["refs"] += values
            continue
        try:
            numbers = [float(v) for v in values]
        except ValueError:
            continue
        if key == "area" and len(numbers) == 4:
            x1, y1, x2, y2 = numbers
            found["areas"].append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
        elif key == "at" and len(numbers) == 2:
            x, y = numbers
            found["areas"].append((x - NEAR_MM, y - NEAR_MM, x + NEAR_MM, y + NEAR_MM))
    return found


def _mm(point):
    return point.x / 1e6, point.y / 1e6


def pick_items(where, footprints, tracks, vias, pads):
    """The board items a parse_location() result points at.

    Returns (items, missing, small): missing lists the refs, nets and places with nothing
    on the board; small is True when everything picked fits in SMALL_MM."""
    items, missing, points = [], [], []

    def take(item, *spots):
        if all(item is not other for other in items):
            items.append(item)
        points.extend(spots)

    by_ref = {fp.reference_field.text.value.upper(): fp for fp in footprints}
    for ref in where["refs"]:
        fp = by_ref.get(ref.upper())
        if fp is None:
            missing.append(ref)
        else:
            take(fp, _mm(fp.position))
    for net in where["nets"]:
        hits = 0
        for t in tracks:
            if t.net.name == net:
                take(t, _mm(t.start), _mm(t.end))
                hits += 1
        for item in list(vias) + list(pads):
            if item.net.name == net:
                take(item, _mm(item.position))
                hits += 1
        if not hits:
            missing.append(f"net {net}")
    for x1, y1, x2, y2 in where["areas"]:
        def inside(p):
            return x1 <= p[0] <= x2 and y1 <= p[1] <= y2
        hits = 0
        for fp in footprints:
            if inside(_mm(fp.position)):
                take(fp, _mm(fp.position))
                hits += 1
        for t in tracks:
            ends = [p for p in (_mm(t.start), _mm(t.end)) if inside(p)]
            if ends:
                take(t, *ends)
                hits += 1
        for v in vias:
            if inside(_mm(v.position)):
                take(v, _mm(v.position))
                hits += 1
        if not hits:
            missing.append(f"anything at ({x1:g}, {y1:g})–({x2:g}, {y2:g}) mm")
    small = bool(points) and max(max(p[0] for p in points) - min(p[0] for p in points),
                                 max(p[1] for p in points) - min(p[1] for p in points)) < SMALL_MM
    return items, missing, small


def _image(alt, src, base_dir, for_panel):
    """A figure with the image embedded, so the HTML works on its own (and in the panel)."""
    path = src.strip().strip("<>")
    if not os.path.isabs(path):
        path = os.path.join(base_dir, path)
    path = os.path.normpath(path)
    mime = IMAGE_TYPES.get(os.path.splitext(path)[1].lower())
    caption = f"<figcaption>{html.escape(alt)}</figcaption>" if alt else ""
    try:
        if not mime or os.path.getsize(path) > MAX_IMAGE_BYTES:
            raise OSError
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("ascii")
    except OSError:
        return f'<p class="missing">Image not found: {html.escape(src)}</p>'
    extra = f' data-path="{html.escape(path, quote=True)}"' if for_panel else ""
    return (f'<figure><img src="data:{mime};base64,{data}" alt="{html.escape(alt, quote=True)}"'
            f"{extra}>{caption}</figure>")


def body_html(md, base_dir, for_panel=False):
    """The review's Markdown as HTML: the subset the skill's format uses (headings,
    lists, tables, code, bold, links, images on a line of their own). Everything is
    escaped, so nothing in the file can run in the panel."""
    lines = md.replace("\r", "").split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^\s*```", line):
            buf = []
            i += 1
            while i < len(lines) and not re.match(r"^\s*```", lines[i]):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append(f"<pre><code>{html.escape(chr(10).join(buf))}</code></pre>")
        elif re.match(r"^#{1,6}\s", line):
            level = min(len(line) - len(line.lstrip("#")), 3)
            text = line.lstrip("#").strip()
            cls = ""
            if level == 3 and text.lower() in SEVERITIES:
                cls = f' class="sev sev-{text.lower()}"'
            out.append(f"<h{level}{cls}>{_inline(text)}</h{level}>")
            i += 1
        elif IMAGE_LINE.match(line):
            alt, src = IMAGE_LINE.match(line).groups()
            out.append(_image(alt, src, base_dir, for_panel))
            i += 1
        elif LIST_ITEM.match(line):
            tag = "ol" if re.match(r"^\s*\d+\.", line) else "ul"
            items = []
            while i < len(lines) and LIST_ITEM.match(lines[i]):
                items.append(f"<li>{_inline(LIST_ITEM.sub('', lines[i], count=1))}</li>")
                i += 1
            out.append(f"<{tag}>{''.join(items)}</{tag}>")
        elif re.match(r"^\|.*\|\s*$", line) and i + 1 < len(lines) and TABLE_RULE.match(lines[i + 1]):
            def cells(row):
                return [_inline(c.strip()) for c in row.strip().strip("|").split("|")]
            rows = ["<tr>" + "".join(f"<th>{c}</th>" for c in cells(line)) + "</tr>"]
            i += 2
            while i < len(lines) and re.match(r"^\|.*\|\s*$", lines[i]):
                rows.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells(lines[i])) + "</tr>")
                i += 1
            out.append(f"<table>{''.join(rows)}</table>")
        elif not line.strip() or re.match(r"^\s*(-{3,}|\*{3,})\s*$", line):
            i += 1
        else:
            buf = []
            while i < len(lines) and lines[i].strip() and not BLOCK_START.match(lines[i]) \
                    and not IMAGE_LINE.match(lines[i]):
                buf.append(_inline(lines[i]))
                i += 1
            if not buf:
                buf.append(_inline(lines[i]))
                i += 1
            out.append(f"<p>{'<br>'.join(buf)}</p>")
    return "\n".join(out)


def title_and_verdict(md):
    title = next((l.lstrip("#").strip() for l in md.splitlines() if re.match(r"^#\s", l)), "Design review")
    verdict = re.search(r"\*\*Verdict:?\*\*:?\s*(.+)", md)
    return title, verdict.group(1).strip() if verdict else ""


def document(md, base_dir):
    title, _ = title_and_verdict(md)
    return (f'<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title>'
            f"<style>{CSS}</style></head><body>{body_html(md, base_dir)}"
            '<p class="foot">Written by Claude in the PowerLab KiCad Assistant. Claude can make '
            "mistakes: check the findings against the board and the datasheets before you order."
            "</p></body></html>")


def make_pdf(html_path, pdf_path, edge):
    """Print html_path to pdf_path with headless Edge. Returns an error message, or ""."""
    if not edge:
        return "Microsoft Edge wasn't found, so the PDF couldn't be made."
    try:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    except OSError:
        return f"{os.path.basename(pdf_path)} is open in another program. Close it and ask for the review again."
    # A profile of its own, so it never hands the job to an Edge window the user has open.
    profile = tempfile.mkdtemp(prefix="powerlab-pdf-")
    try:
        subprocess.run(
            [edge, "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
             "--disable-extensions", f"--user-data-dir={profile}", "--no-pdf-header-footer",
             f"--print-to-pdf={pdf_path}", pathlib.Path(html_path).as_uri()],
            capture_output=True, timeout=PDF_TIMEOUT, creationflags=CREATE_NO_WINDOW)
    except (OSError, subprocess.SubprocessError) as exc:
        return f"Edge couldn't make the PDF ({type(exc).__name__})."
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    return "" if os.path.isfile(pdf_path) else "Edge didn't write the PDF."


def card(md_path):
    """What the panel shows for a review: title, verdict and the whole review."""
    try:
        with open(md_path, encoding="utf-8-sig") as f:
            md = f.read()
    except OSError:
        return {"path": md_path, "title": "Design review", "verdict": "",
                "body": '<p class="missing">The review file is no longer there.</p>'}
    title, verdict = title_and_verdict(md)
    return {"path": md_path, "title": title, "verdict": verdict,
            "body": body_html(md, os.path.dirname(md_path), for_panel=True)}


def build(md_path, edge=None):
    """The panel card for md_path, plus design-review.pdf next to it.

    If the PDF can't be made, the HTML is saved next to the review instead, so it can
    still be opened and printed from a browser."""
    data = card(md_path)
    if not os.path.isfile(md_path):
        return data
    with open(md_path, encoding="utf-8-sig") as f:
        page = document(f.read(), os.path.dirname(md_path))
    stem = os.path.splitext(md_path)[0]
    pdf = stem + ".pdf"
    tmp = tempfile.mkdtemp(prefix="powerlab-review-")
    try:
        html_path = os.path.join(tmp, "design-review.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(page)
        error = make_pdf(html_path, pdf, edge if edge is not None else find_edge())
        if error:
            try:
                shutil.copyfile(html_path, stem + ".html")
                data["html"] = stem + ".html"
            except OSError:
                pass
            data["error"] = error
        else:
            data["pdf"] = pdf
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return data
