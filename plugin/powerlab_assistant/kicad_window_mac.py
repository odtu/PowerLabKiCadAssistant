"""Drive a KiCad editor window on macOS: the same functions as kicad_window_win.

KiCad 10's schematic editor has no save, revert or selection over its API, so the panel
clicks the editor's own File > Save, File > Revert and Edit > Copy. On macOS that goes
through System Events (AppleScript): the app that starts the panel needs the Accessibility
permission (System Settings > Privacy & Security > Accessibility; macOS asks the first
time). Without it, the window functions find no editor and the panel works on the files.

A "window" here is a (pid, title) pair: AppleScript has no stable window handles, and an
editor's title is what tells it apart ("<project> — Schematic Editor", "*" when unsaved).
KiCad shows menus and titles in its own language; its translation catalogues turn the
panel's English names into what is on screen (see localize).
The clipboard is NSPasteboard's, through the Objective-C runtime (ctypes, no PyObjC).
KiCad's API listens on a real Unix socket, /tmp/kicad/api[-<pid>].sock.
"""

import ctypes
import ctypes.util
import os
import re
import stat
import subprocess
import threading
import time
from collections import namedtuple

# title: in English (see english_title); shown: as on screen, to find the window by
Window = namedtuple("Window", "pid title shown")
Window.__new__.__defaults__ = (None,)

KICAD_EXES = {"kicad", "eeschema", "pcbnew"}  # KiCad.app, or the editors' own apps
OSASCRIPT_TIMEOUT = 5
access_error = ""  # why System Events refused, for the panel's hints ("" when it works)


# ---- processes --------------------------------------------------------------------------

def parse_ps(text):
    """{pid: (parent pid, exe name)} from `ps -axo pid=,ppid=,comm=`. comm is the
    executable's path, which may contain spaces."""
    found = {}
    for line in text.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            found[int(parts[0])] = (int(parts[1]), os.path.basename(parts[2].rstrip("/")))
    return found


def processes():
    """{pid: (parent pid, exe name)} of every running process."""
    try:
        out = subprocess.run(["ps", "-axo", "pid=,ppid=,comm="], capture_output=True,
                             text=True, timeout=10).stdout
    except (OSError, subprocess.TimeoutExpired):
        return {}
    return parse_ps(out)


def ancestor_in(procs, pid, names=KICAD_EXES):
    """The process among pid and its ancestors whose exe is one of names, or 0."""
    seen = set()
    while pid and pid in procs and pid not in seen:
        seen.add(pid)
        parent, exe = procs[pid]
        if exe.lower() in names:
            return pid
        pid = parent
    return 0


def kicad_ancestor(pid):
    """The KiCad process that started pid (pid itself if it is one), or 0. The schematic
    button runs in a Python that KiCad started, in a venv of KiCad's."""
    return ancestor_in(processes(), pid)


def process_running(pid):
    try:
        os.kill(pid, 0)
    except PermissionError:
        return True  # it exists, it's just someone else's
    except OSError:
        return False
    return True


def kicad_processes():
    """[(pid, has_visible_window)] for every running KiCad."""
    pids = [pid for pid, (_, exe) in processes().items() if exe.lower() == "kicad"]
    result = []
    for pid in pids:
        titles = window_titles(pid)
        # Without the Accessibility permission nothing can be seen: don't call it stuck.
        result.append((pid, bool(titles) or titles is None))
    return result


# ---- API sockets ------------------------------------------------------------------------

def socket_paths(folder):
    """Lower-cased paths of the Unix sockets in folder (KiCad's API sockets)."""
    try:
        names = os.listdir(folder)
    except OSError:
        return set()
    found = set()
    for name in names:
        path = os.path.join(folder, name)
        try:
            if stat.S_ISSOCK(os.stat(path).st_mode):
                found.add(path.lower())
        except OSError:
            pass
    return found


def pipe_names():
    """The API sockets KiCads listen on (instances.find_socket compares lower-case paths)."""
    from . import instances

    return socket_paths(instances.SOCKET_DIR)


def pipe_server(path):
    """Process id of the KiCad listening on the socket at path, or 0."""
    try:
        out = subprocess.run(["lsof", "-t", "--", path], capture_output=True, text=True,
                             timeout=10).stdout
    except (OSError, subprocess.TimeoutExpired):
        return 0
    procs = None
    for line in out.split():
        if line.isdigit():
            procs = procs if procs is not None else processes()
            pid = int(line)
            if procs.get(pid, (0, ""))[1].lower() in KICAD_EXES:
                return pid
    return 0


# ---- System Events ----------------------------------------------------------------------

def quote(text):
    """An AppleScript string literal."""
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def osascript(script):
    """Run AppleScript; returns its output, or None if it failed (no permission, no window)."""
    global access_error
    try:
        proc = subprocess.run(["osascript", "-e", script], capture_output=True, text=True,
                              timeout=OSASCRIPT_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        err = proc.stderr.strip()
        # -1743/-1719/-25211: not allowed; -1712: macOS is still asking the user
        if any(code in err for code in ("-1743", "-1719", "-25211", "-1712")) or "assistive" in err.lower():
            access_error = ("The panel isn't allowed to control KiCad's windows. Turn on KiCad in "
                            "System Settings > Privacy & Security > Accessibility, then restart KiCad.")
        return None
    access_error = ""
    return proc.stdout.rstrip("\n")


CLICK_TIMEOUT = 120  # a click behind a dialog the user never answers


def osascript_in_background(script):
    """Start AppleScript without waiting for it; True if it started."""
    try:
        proc = subprocess.Popen(["osascript", "-e", script], stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return False

    def reap():
        try:
            proc.wait(CLICK_TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

    threading.Thread(target=reap, daemon=True).start()
    return True


def _process(pid):
    return f'(first process whose unix id is {int(pid)})'


SEPARATOR = "\x1f"  # between list items in AppleScript's output


def _names(script_tail, pid):
    """A list AppleScript gives back (names of windows, menus, ...), or None."""
    out = osascript(
        'set AppleScript\'s text item delimiters to ASCII character 31\n'
        f'tell application "System Events" to tell {_process(pid)} to set t to {script_tail}\n'
        'return t as text')
    return None if out is None else [t for t in out.split(SEPARATOR) if t]


def window_titles(pid):
    """Titles of the KiCad's windows as KiCad shows them, front first; None if System
    Events can't tell."""
    return _names("name of every window", pid)


def menu_bar(pid):
    return _names("name of every menu bar item of menu bar 1", pid)


# ---- KiCad's own language ---------------------------------------------------------------
# KiCad shows its menus, window titles and buttons in its own language (on macOS the
# system's, by default): "Dosya > Kaydet", "proje — Şematik Düzenleyici". The panel names
# them in English, and KiCad's translation catalogues (KiCad.app/Contents/SharedSupport/
# internat/<lang>/kicad.mo) turn those into what is on screen. Which language KiCad uses
# is read off its menu bar: the catalogue whose "&File" is there.

EDITOR_KINDS = ("Schematic Editor", "PCB Editor")
_catalogs = {}  # language folder -> {msgid: translation}
_languages = {}  # KiCad pid -> its catalogue ({} for English)


def internat_dir():
    from . import config

    folder = config.kicad_bin()
    return os.path.join(os.path.dirname(folder), "SharedSupport", "internat") if folder else ""


def catalog(lang):
    """KiCad's translations into lang ({} if there are none)."""
    if lang not in _catalogs:
        import gettext

        try:
            with open(os.path.join(internat_dir(), lang, "kicad.mo"), "rb") as f:
                _catalogs[lang] = gettext.GNUTranslations(f)._catalog
        except (OSError, ValueError):
            _catalogs[lang] = {}
    return _catalogs[lang]


def translate(table, text):
    """text as KiCad shows it in the language of table, or None if it has no translation.
    KiCad's msgids carry the accelerator ("&File") or an ellipsis ("Revert...")."""
    for msgid in (text, "&" + text, text + "...", "&" + text + "...", text + "…"):
        found = table.get(msgid)
        if isinstance(found, str) and found:
            return menu_label(found.replace("&", ""))
    return None


def preferred_languages():
    """KiCad's catalogue folders for macOS's preferred languages, best first."""
    try:
        out = subprocess.run(["defaults", "read", "-g", "AppleLanguages"], capture_output=True,
                             text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    found = []
    for code in re.findall(r'"?([A-Za-z]{2,3}(?:-[A-Za-z0-9]+)*)"?\s*[,)]', out):
        parts = code.split("-")
        lang = parts[0].lower()
        if lang == "zh":
            found.append("zh_TW" if "Hant" in parts or "TW" in parts or "HK" in parts else "zh_CN")
        region = next((p for p in parts[1:] if len(p) == 2), "")
        if region:
            found.append(f"{lang}_{region.upper()}")
        found.append(lang)
    return found


def _shows(table, bar, shown_titles):
    """Whether KiCad's menu bar or an editor's title is in the language of table."""
    name = (lambda text: translate(table, text)) if table else (lambda text: text)
    if name("File") in bar:
        return True
    kinds = [name(kind) for kind in EDITOR_KINDS]
    return any(k and t.endswith(" — " + k) for t in shown_titles for k in kinds)


def language_of(bar, shown_titles, candidates):
    """The catalogue (by folder name) KiCad shows its File menu or editor titles in; "" for
    English, None if nothing tells (KiCad's menu bar is just Apple/KiCad/Window while one of
    its dialogs, or no editor, has the focus)."""
    if _shows({}, bar, shown_titles):
        return ""
    for lang in candidates:
        table = catalog(lang)
        if table and _shows(table, bar, shown_titles):
            return lang
    return None


UNSURE_FOR = 5.0  # seconds before asking KiCad's menu bar again when it told nothing
_unsure = {}  # pid -> when


def ui_catalog(pid, shown_titles=None):
    """The catalogue KiCad pid shows its menus in ({} for English, or while unknown)."""
    if pid in _languages:
        return _languages[pid]
    if time.time() - _unsure.get(pid, 0) < UNSURE_FOR:
        return {}
    bar = menu_bar(pid)
    if shown_titles is None:
        shown_titles = window_titles(pid) or []
    folder = internat_dir()
    everything = sorted(os.listdir(folder)) if folder and os.path.isdir(folder) else []
    lang = language_of(bar or [], shown_titles, preferred_languages() + everything)
    if lang is None:
        _unsure[pid] = time.time()  # no permission yet, or nothing to tell by: later
        return {}
    _languages[pid] = catalog(lang) if lang else {}
    return _languages[pid]


def localize(pid, text, shown_titles=None):
    """An English menu, button or editor name as KiCad pid shows it."""
    table = ui_catalog(pid, shown_titles)
    return (translate(table, text) or text) if table else text


def english_title(pid, title, shown_titles=None):
    """'esp — Şematik Düzenleyici' -> 'esp — Schematic Editor', so the panel's checks on
    titles work in every language."""
    for kind in EDITOR_KINDS:
        shown = localize(pid, kind, shown_titles if shown_titles is not None else [title])
        if shown != kind and title.endswith(" — " + shown):
            return title[:-len(shown)] + kind
    return title


# ---- windows ----------------------------------------------------------------------------

def titles(pid):
    """[(English title, title on screen)] of the KiCad's windows."""
    shown = window_titles(pid) or []
    return [(english_title(pid, t, shown), t) for t in shown]


def top_windows():
    """Every window of every running KiCad."""
    found = []
    for pid, (_, exe) in processes().items():
        if exe.lower() in KICAD_EXES:
            found += [Window(pid, english, shown) for english, shown in titles(pid)]
    return found


def window_text(window):
    return window.title if window else ""


def window_pid(window):
    return window.pid if window else 0


def _now(window):
    """(English title, title on screen) of the window now: it changes when the editor's
    sheet or saved state does."""
    now = titles(window.pid)
    for english, shown in now:
        if english == window.title:
            return english, shown
    stem = _stem(window.title)
    for english, shown in now:
        if _stem(english) == stem:
            return english, shown
    return window.title, window.shown or window.title


def current_title(window):
    return _now(window)[0]


def _stem(title):
    """The part of an editor title that stays: the project and the editor's name."""
    title = title.lstrip("*")
    project = title.split(" [", 1)[0].rsplit(" — ", 1)[0]
    return project + " — " + title.rsplit(" — ", 1)[-1]


def find_editor(kind="Schematic Editor", pid=0):
    """The '<project> — Schematic Editor' window of the KiCad with that process id (any
    KiCad if 0), or None."""
    for window in top_windows():
        if window.title.endswith(kind) and (not pid or window.pid == pid):
            return window
    return None


def _raise(window):
    return f'perform action "AXRaise" of (first window whose name is {quote(_now(window)[1])})'


def bring_to_front(window):
    osascript(f'tell application "System Events" to tell {_process(window.pid)}\n'
              f'  set frontmost to true\n'
              f'  {_raise(window)}\n'
              'end tell')


def foreground_title(pid=0):
    """Title of the window the user is working in; "" if it isn't one of that KiCad's."""
    out = osascript(
        'tell application "System Events"\n'
        '  set p to first process whose frontmost is true\n'
        '  set n to ""\n'
        '  try\n'
        '    set n to name of front window of p\n'
        '  end try\n'
        '  return (unix id of p as text) & (ASCII character 31) & n\n'
        'end tell')
    if not out or SEPARATOR not in out:
        return ""
    front_pid, title = out.split(SEPARATOR, 1)
    if pid and front_pid != str(pid):
        return ""
    return english_title(int(front_pid), title) if front_pid.isdigit() else title


def is_dirty(window):
    return current_title(window).startswith("*")


def current_sheet(window):
    """'MCUCore [ESC3Phase/MCU Core] — Schematic Editor' -> 'ESC3Phase/MCU Core'."""
    title = current_title(window).lstrip("*").rsplit(" — ", 1)[0]
    if "[" in title and title.endswith("]"):
        return title[title.index("[") + 1:-1]
    return title


def menu_label(name):
    """A menu item's name without its ellipsis, as the Windows labels are compared."""
    name = (name or "").strip()
    for tail in ("…", "..."):
        if name.endswith(tail):
            name = name[:-len(tail)].rstrip()
    return name


def find_label(names, wanted):
    """1-based position of `wanted` among menu item names, or 0."""
    for i, name in enumerate(names, 1):
        if menu_label(name) == wanted:
            return i
    return 0


# The schematic selection isn't read with Edit > Copy here (see menu_command): what the user
# copies with Cmd+C in the schematic editor is picked up from the clipboard instead.
DRIVES_COPY = False


def menu_command(window, top, item):
    """Click the editor window's menu `top` > `item` (English labels, shown in KiCad's
    language). Returns True if the item was found and clicked.

    KiCad's menu bar is the one of its key window, and a window becomes that only while
    KiCad is the active app. So KiCad is brought to the front with the window raised, and
    nothing is clicked unless that window is really in front (File > Save in the PCB editor
    would save the board). The app that was in front before gets the focus back."""
    proc = _process(window.pid)
    shown = _now(window)[1]
    menu = f'menu 1 of menu bar item {quote(localize(window.pid, top))} of menu bar 1'
    out = osascript(
        'set AppleScript\'s text item delimiters to ASCII character 31\n'
        'tell application "System Events"\n'
        '  set previous to unix id of first process whose frontmost is true\n'
        f'  tell {proc}\n'
        '    set frontmost to true\n'
        f'    perform action "AXRaise" of (first window whose name is {quote(shown)})\n'
        '  end tell\n'
        '  delay 0.3\n'
        f'  tell {proc} to set t to {{previous as text, name of window 1}} & (name of every menu item of {menu})\n'
        'end tell\n'
        'return t as text')
    if not out:
        return False
    before, front, *names = out.split(SEPARATOR)
    give_back = f'tell application "System Events" to set frontmost of {_process(before)} to true' \
        if before.isdigit() and int(before) != window.pid else ""
    index = find_label(names, localize(window.pid, item)) if front == shown else 0
    if not index:
        if give_back:
            osascript(give_back)
        return False
    # Not waiting for the click: a menu command that opens a modal dialog (Revert's
    # confirmation) holds it until the dialog closes. ("ignoring application responses"
    # doesn't do: osascript then exits before System Events has clicked.)
    return osascript_in_background(
        f'tell application "System Events" to tell {proc} to click menu item {index} of {menu}'
        + ("\n" + give_back if give_back else ""))


# On macOS, KiCad asks "Revert '<file>' to last version saved?" with Yes and No (a native
# alert) where Windows has a Revert button. Yes is clicked only on a dialog whose text is
# that question.
CONFIRMS = {"Revert": ("Revert '%s' (and all sub-sheets) to last version saved?",
                       "Revert '%s' to last version saved?")}
WINDOW_SEP, ITEM_SEP = "\x1d", "\x1e"


def asks(text, table, question):
    """Whether a dialog's text is KiCad's question (msgid with %s), in table's language."""
    shown = (table.get(question) if table else None) or question
    pieces = [p for p in shown.split("%s") if p.strip()]
    at = 0
    for piece in pieces:
        at = text.find(piece, at)
        if at < 0:
            return False
        at += len(piece)
    return bool(pieces)


def dialog_choice(dialogs, labels, table):
    """(window index, button) to click among [(texts, buttons)] of KiCad's windows: a button
    labelled one of labels, else Yes on a dialog asking one of CONFIRMS[label]."""
    shown = {translate(table, label) or label for label in labels} | set(labels) if table else set(labels)
    for i, (_, buttons) in enumerate(dialogs, 1):
        for button in buttons:
            if button.replace("&", "") in shown:
                return i, button
    yes = {"Yes", translate(table, "Yes") or "Yes"} if table else {"Yes"}
    for i, (text, buttons) in enumerate(dialogs, 1):
        for label in labels:
            if any(asks(text, table, q) for q in CONFIRMS.get(label, ())):
                for button in buttons:
                    if button in yes:
                        return i, button
    return None


def click_dialog_button(owner_pid, labels):
    """Click a button labelled one of `labels` (English, shown in KiCad's language) in a
    dialog of that process, or Yes on its confirmation question (CONFIRMS)."""
    out = osascript(
        'set out to ""\n'
        f'tell application "System Events" to tell {_process(owner_pid)}\n'
        '  repeat with w in windows\n'
        '    set AppleScript\'s text item delimiters to ASCII character 30\n'
        '    set texts to (value of every static text of w) as text\n'
        '    set names to (name of every button of w) as text\n'
        '    set out to out & texts & (ASCII character 31) & names & (ASCII character 29)\n'
        '  end repeat\n'
        'end tell\n'
        'return out')
    if not out:
        return False
    dialogs = []
    for chunk in out.split(WINDOW_SEP)[:-1]:
        text, _, buttons = chunk.partition(SEPARATOR)
        dialogs.append((text, [b for b in buttons.split(ITEM_SEP) if b and b != "missing value"]))
    choice = dialog_choice(dialogs, labels, ui_catalog(owner_pid))
    if not choice:
        return False
    index, button = choice
    return osascript(f'tell application "System Events" to tell {_process(owner_pid)} to '
                     f'click button {quote(button)} of window {index}') is not None


# ---- clipboard (NSPasteboard through the Objective-C runtime) ---------------------------

class _ObjC:
    """The few NSPasteboard calls the panel needs, without PyObjC (not in KiCad's Python)."""

    def __init__(self):
        self.lib = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
        ctypes.cdll.LoadLibrary("/System/Library/Frameworks/AppKit.framework/AppKit")
        self.lib.objc_getClass.restype = ctypes.c_void_p
        self.lib.objc_getClass.argtypes = [ctypes.c_char_p]
        self.lib.sel_registerName.restype = ctypes.c_void_p
        self.lib.sel_registerName.argtypes = [ctypes.c_char_p]
        self.send_addr = ctypes.cast(self.lib.objc_msgSend, ctypes.c_void_p).value

    def send(self, obj, selector, *args, restype=ctypes.c_void_p, argtypes=()):
        fn = ctypes.CFUNCTYPE(restype, ctypes.c_void_p, ctypes.c_void_p, *argtypes)(self.send_addr)
        return fn(obj, self.lib.sel_registerName(selector.encode()), *args)

    def cls(self, name):
        return self.lib.objc_getClass(name.encode())

    def string(self, text):
        return self.send(self.cls("NSString"), "stringWithUTF8String:", text.encode("utf-8"),
                         argtypes=(ctypes.c_char_p,))

    def text(self, nsstring):
        raw = self.send(nsstring, "UTF8String", restype=ctypes.c_char_p) if nsstring else None
        return raw.decode("utf-8", "replace") if raw else ""

    def items(self, nsarray):
        if not nsarray:
            return []
        n = self.send(nsarray, "count", restype=ctypes.c_ulong)
        return [self.send(nsarray, "objectAtIndex:", i, argtypes=(ctypes.c_ulong,)) for i in range(n)]

    def pasteboard(self):
        return self.send(self.cls("NSPasteboard"), "generalPasteboard")


_objc = None


def _runtime():
    global _objc
    if _objc is None:
        _objc = _ObjC()
    return _objc


def clipboard_sequence():
    """NSPasteboard's changeCount: it changes whenever anything is copied."""
    try:
        objc = _runtime()
        return objc.send(objc.pasteboard(), "changeCount", restype=ctypes.c_long)
    except (OSError, AttributeError, TypeError):
        return 0


MAX_CLIPBOARD = 64 * 1024 * 1024


def save_clipboard():
    """[[(type, bytes)] per pasteboard item], or None if it couldn't be read."""
    try:
        objc = _runtime()
        saved = []
        for item in objc.items(objc.send(objc.pasteboard(), "pasteboardItems")):
            kept = []
            for kind in objc.items(objc.send(item, "types")):
                data = objc.send(item, "dataForType:", kind, argtypes=(ctypes.c_void_p,))
                size = objc.send(data, "length", restype=ctypes.c_ulong) if data else 0
                if not size or size > MAX_CLIPBOARD:
                    continue
                ptr = objc.send(data, "bytes")
                kept.append((objc.text(kind), ctypes.string_at(ptr, size)))
            saved.append(kept)
        return saved
    except (OSError, AttributeError, TypeError):
        return None


def restore_clipboard(items, owner=None):
    """Put back what save_clipboard() took. `owner` is for Windows; unused here."""
    if items is None:
        return
    try:
        objc = _runtime()
        board = objc.pasteboard()
        objc.send(board, "clearContents", restype=ctypes.c_long)
        objects = []
        for kept in items:
            item = objc.send(objc.send(objc.cls("NSPasteboardItem"), "alloc"), "init")
            for kind, data in kept:
                nsdata = objc.send(objc.cls("NSData"), "dataWithBytes:length:", data, len(data),
                                   argtypes=(ctypes.c_char_p, ctypes.c_ulong))
                objc.send(item, "setData:forType:", nsdata, objc.string(kind), restype=ctypes.c_bool,
                          argtypes=(ctypes.c_void_p, ctypes.c_void_p))
            objects.append(item)
        if not objects:
            return
        array = (ctypes.c_void_p * len(objects))(*objects)
        nsarray = objc.send(objc.cls("NSArray"), "arrayWithObjects:count:", array, len(objects),
                            argtypes=(ctypes.c_void_p, ctypes.c_ulong))
        objc.send(board, "writeObjects:", nsarray, restype=ctypes.c_bool, argtypes=(ctypes.c_void_p,))
        for item in objects:
            objc.send(item, "release", restype=None)
    except (OSError, AttributeError, TypeError):
        pass
