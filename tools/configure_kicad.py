"""Point KiCad 10 at a git clone of the METU Power Lab library, and (optionally)
turn on KiCad's API server for the schematic panel.

Run by install.ps1 with KiCad's Python while KiCad is closed (KiCad rewrites its
settings on exit). Every file it touches is backed up first.

    python configure_kicad.py --library D:\\path\\to\\PowerLabKiCadLibraries [--enable-api] [--dry-run]
"""

import argparse
import json
import os
import re
import shutil
import sys
import time

KICAD_CONFIG = os.path.join(os.environ["APPDATA"], "kicad", "10.0")
BACKUP_ROOT = os.path.join(os.environ["APPDATA"], "PowerLabKiCadAssistant", "backup")
LIB_PREFIX = "METUPowerLab_"
TABLES = (
    ("sym-lib-table", "symbols", ".kicad_sym", "METUPOWERLAB_SYMBOLS"),
    ("fp-lib-table", "footprints", ".pretty", "METUPOWERLAB_FOOTPRINTS"),
)
LIB_LINE = re.compile(r'\(lib\s*\(name\s+"(?P<name>[^"]+)"\)(?P<mid>.*?)\(uri\s+"(?P<uri>[^"]*)"\)')


def backup(paths, dry):
    folder = os.path.join(BACKUP_ROOT, time.strftime("%Y%m%d-%H%M%S"))
    if dry:
        return folder
    os.makedirs(folder, exist_ok=True)
    for path in paths:
        if os.path.isfile(path):
            shutil.copy2(path, folder)
    return folder


def set_path_variables(common, library, enable_api, kicad_bin):
    with open(common, encoding="utf-8") as f:
        data = json.load(f)
    changes = []
    if library:
        env = data.setdefault("environment", {})
        variables = env.get("vars") or {}
        variables["METUPOWERLAB_SYMBOLS"] = os.path.join(library, "symbols")
        variables["METUPOWERLAB_FOOTPRINTS"] = os.path.join(library, "footprints")
        variables["METUPOWERLAB_3D"] = os.path.join(library, "3dmodels", "powerlab.3dshapes")
        env["vars"] = variables
        changes.append("path variables METUPOWERLAB_SYMBOLS / _FOOTPRINTS / _3D -> library clone")
    if enable_api:
        api = data.setdefault("api", {})
        api["enable_server"] = True
        api["interpreter_path"] = os.path.join(kicad_bin, "pythonw.exe")
        changes.append("KiCad API server on; plugin Python = KiCad 10's pythonw.exe")
    return data, changes


def update_table(path, library, folder, suffix, var):
    """Repoint METUPowerLab_* entries at the clone and add libraries the table lacks."""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        text = '(sym_lib_table\n  (version 7)\n)\n' if "sym" in os.path.basename(path) else \
               '(fp_lib_table\n  (version 7)\n)\n'
    available = {item[: -len(suffix)] for item in os.listdir(os.path.join(library, folder))
                 if item.endswith(suffix)}
    seen, repointed = set(), 0

    def fix(match):
        nonlocal repointed
        name = match.group("name")
        seen.add(name)
        if not name.startswith(LIB_PREFIX) or name not in available:
            return match.group(0)
        uri = "${%s}/%s%s" % (var, name, suffix)
        if match.group("uri") == uri:
            return match.group(0)
        repointed += 1
        return f'(lib (name "{name}"){match.group("mid")}(uri "{uri}")'

    text = LIB_LINE.sub(fix, text)
    missing = sorted(available - seen)
    if missing:
        body = "".join(f'  (lib (name "{n}")(type "KiCad")(uri "${{{var}}}/{n}{suffix}")'
                       f'(options "")(descr "METU PowerLab"))\n' for n in missing)
        text = text.rstrip()
        text = text[:-1].rstrip() + "\n" + body + ")\n"
    return text, repointed, missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--library", default="")
    ap.add_argument("--enable-api", action="store_true")
    ap.add_argument("--kicad-bin", default=os.path.dirname(sys.executable))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    library = os.path.abspath(args.library) if args.library else ""
    for sub in ("symbols", "footprints", "3dmodels") if library else ():
        if not os.path.isdir(os.path.join(library, sub)):
            sys.exit(f"{library} doesn't look like the PowerLab library (no {sub} folder).")

    common = os.path.join(KICAD_CONFIG, "kicad_common.json")
    tables = [os.path.join(KICAD_CONFIG, t[0]) for t in TABLES] if library else []
    folder = backup([common, *tables], args.dry_run)
    print(f"Backup: {folder}")

    data, changes = set_path_variables(common, library, args.enable_api, args.kicad_bin)
    results = []
    for (table, sub, suffix, var), path in zip(TABLES, tables):
        text, repointed, missing = update_table(path, library, sub, suffix, var)
        results.append((path, text))
        changes.append(f"{table}: {repointed} entries now use the clone, {len(missing)} added")

    for line in changes:
        print(" -", line)
    if args.dry_run:
        print("Dry run: nothing written.")
        return
    with open(common, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    for path, text in results:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    print("KiCad configured.")


if __name__ == "__main__":
    main()
