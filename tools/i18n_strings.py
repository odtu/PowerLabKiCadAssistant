"""The panel's text to translate, and what each language file still lacks.

    python tools/i18n_strings.py            writes plugin/powerlab_assistant/lang/en.json
    python tools/i18n_strings.py --check    lists the texts each lang/<code>.json lacks

Texts come from panel.html (t('...') calls and data-t elements) and from the notes, buttons
and menus panel.py and sources.py show. A note filled in at run time (an f-string) becomes a
key with {name} where its values go; the page matches filled notes against those keys.
en.json maps each text to itself: it is the list to translate, not a translation.
"""

import ast
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "plugin", "powerlab_assistant")
LANG = os.path.join(PLUGIN, "lang")
PLACEHOLDER = re.compile(r"\{\w+\}")


def _js_strings(src):
    """The string literals passed to t() in the page's script (both branches of a ?:)."""
    found = []
    literal = r"'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\""
    for m in re.finditer(r"\bt\(", src):
        depth, i, buf = 1, m.end(), []
        while i < len(src) and depth:  # the call's first argument
            c = src[i]
            if c in "'\"`":
                j = i + 1
                while j < len(src) and src[j] != c:
                    j += 2 if src[j] == "\\" else 1
                buf.append(src[i:j + 1])
                i = j + 1
                continue
            if c in "([{":
                depth += 1
            elif c in ")]}":
                depth -= 1
                if not depth:
                    break
            elif c == "," and depth == 1:
                break
            buf.append(c)
            i += 1
        arg = "".join(buf)
        lits = []
        for lit in re.finditer(literal, arg):
            before, after = arg[:lit.start()].rstrip(), arg[lit.end():].lstrip()
            if before.endswith(("===", "!==")) or after.startswith(":") and before.endswith(("{", ",")):
                continue  # compared with (b.side === 'bottom') or a key ({'??': ...}), not shown
            text = lit.group(1) if lit.group(1) is not None else lit.group(2)
            lits.append(re.sub(r"\\(.)", r"\1", text))
        if re.fullmatch(rf"\s*(?:{literal})(?:\s*\+\s*(?:{literal}))+\s*", arg):
            lits = ["".join(lits)]  # 'one text ' + 'split over lines'
        found += lits
    return found


def _page_strings():
    with open(os.path.join(PLUGIN, "panel.html"), encoding="utf-8") as f:
        html = f.read()
    script = html[html.index("<script>"):]
    texts = _js_strings(script)
    # The page's own elements: data-t (text), data-t-title, data-t-ph (placeholder).
    for m in re.finditer(r"<(\w+)([^>]*)>([^<]*)", html[:html.index("<script>")]):
        attrs, text = m.group(2), m.group(3).strip()
        if re.search(r"\bdata-t\b(?!-)", attrs) and text:
            texts.append(text)
        if "data-t-title" in attrs:
            texts.append(re.search(r'title="([^"]*)"', attrs).group(1))
        if "data-t-ph" in attrs:
            texts.append(re.search(r'placeholder="([^"]*)"', attrs).group(1))
    activity = re.search(r"const ACTIVITY = \{(.*?)\};", script, re.S).group(1)
    texts += [a or b for a, b in re.findall(r":\s*(?:'([^']*)'|\"([^\"]*)\")", activity)]
    return texts


def _template(node):
    """A Python string expression as a key: f"Couldn't attach {name}: {exc}." and the like."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        out = ""
        for part in node.values:
            if isinstance(part, ast.Constant):
                out += part.value
            else:
                value = part.value
                name = (value.id if isinstance(value, ast.Name) else value.attr
                        if isinstance(value, ast.Attribute) else "value")
                out += "{" + name + "}"
        return out
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _template(node.left), _template(node.right)
        text = (left if left is not None else "{value}") + (right if right is not None else "{value}")
        return re.sub(r"(\{value\})+", "{value}", text)
    return None


def _python_strings():
    texts = []
    with open(os.path.join(PLUGIN, "panel.py"), encoding="utf-8") as f:
        tree = ast.parse(f.read())
    consts = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(getattr(node.targets[0], "id", None), str):
            consts[node.targets[0].id] = node.value
    for name in ("BOARD_CHANGED", "SCHEMATIC_CHANGED"):
        texts.append(_template(consts[name]))
    for row in consts["MODELS"].elts:  # (id, label, short, hint)
        texts += [_template(e) for e in row.elts[1:]]
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = getattr(node.func, "attr", "")
        args = node.args
        if func in ("emit", "say") and args and getattr(args[0], "value", None) == "note":
            for kw in node.keywords:
                if kw.arg == "text":
                    texts.append(_template(kw.value))
        if func == "problem" and len(args) >= 2:
            texts.append(_template(args[1]))
        for kw in node.keywords:  # a note's button: action={"label": ...}
            if kw.arg == "action" and isinstance(kw.value, ast.Dict):
                for k, v in zip(kw.value.keys, kw.value.values):
                    if getattr(k, "value", None) == "label":
                        texts.append(_template(v))
    with open(os.path.join(PLUGIN, "sources.py"), encoding="utf-8") as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):  # the suggestion chips: (label, text)
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "suggestions":
            for row in node.value.elts:
                texts += [_template(e) for e in row.elts]
    return texts


def strings():
    """Every text the panel translates, in order, once each."""
    out = []
    for text in _page_strings() + _python_strings():
        if text and text.strip() and text not in out and not PLACEHOLDER.fullmatch(text.strip()):
            out.append(text)
    return out


def problems(code, texts=None):
    """(missing, bad): texts lang/<code>.json lacks, and translations whose {names} differ."""
    texts = strings() if texts is None else texts
    with open(os.path.join(LANG, f"{code}.json"), encoding="utf-8") as f:
        table = json.load(f)
    missing = [t for t in texts if t not in table]
    bad = [k for k, v in table.items()
           if sorted(PLACEHOLDER.findall(k)) != sorted(PLACEHOLDER.findall(v))]
    return missing, bad


def main():
    texts = strings()
    if "--check" not in sys.argv:
        os.makedirs(LANG, exist_ok=True)
        with open(os.path.join(LANG, "en.json"), "w", encoding="utf-8") as f:
            json.dump({t: t for t in texts}, f, ensure_ascii=False, indent=1)
        print(f"{len(texts)} texts -> {os.path.join(LANG, 'en.json')}")
        return
    status = 0
    for name in sorted(os.listdir(LANG)):
        code = name[:-5]
        if not name.endswith(".json") or code == "en":
            continue
        missing, bad = problems(code, texts)
        print(f"{code}: {len(missing)} missing, {len(bad)} with wrong {{names}}")
        for t in missing:
            print("  missing:", t[:100])
        for t in bad:
            print("  {names}:", t[:100])
        status |= bool(bad)
    sys.exit(status)


if __name__ == "__main__":
    main()
