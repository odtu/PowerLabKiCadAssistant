"""The panel's language: the language Claude writes in, and the panel's own text.

Claude writes in any of LANGUAGES (reply_note). The panel's buttons, notes and dialogs are
translated only where lang/<code>.json exists (English text -> translation, {name} for the
parts filled in); any other text, or another language, stays English.
"""

import json
import locale
import os

# (code, English name, own name). The first one is the default.
LANGUAGES = [
    ("en", "English", "English"),
    ("tr", "Turkish", "Türkçe"),
    ("zh", "Chinese (Simplified)", "简体中文"),
    ("zh-TW", "Chinese (Traditional)", "繁體中文"),
    ("de", "German", "Deutsch"),
    ("fr", "French", "Français"),
    ("es", "Spanish", "Español"),
    ("pt", "Portuguese (Brazil)", "Português (Brasil)"),
    ("it", "Italian", "Italiano"),
    ("pl", "Polish", "Polski"),
    ("ru", "Russian", "Русский"),
    ("uk", "Ukrainian", "Українська"),
    ("ar", "Arabic", "العربية"),
    ("fa", "Persian", "فارسی"),
    ("hi", "Hindi", "हिन्दी"),
    ("ja", "Japanese", "日本語"),
    ("ko", "Korean", "한국어"),
    ("vi", "Vietnamese", "Tiếng Việt"),
    ("id", "Indonesian", "Bahasa Indonesia"),
]
CODES = [code for code, _, _ in LANGUAGES]
RTL = ("ar", "fa")  # written right to left: the panel turns its layout round
FOLDER = os.path.join(os.path.dirname(__file__), "lang")
_tables = {}


def detect():
    """Windows' display language, if it is one of LANGUAGES; else English."""
    name = ""
    try:
        import ctypes
        name = locale.windows_locale.get(ctypes.windll.kernel32.GetUserDefaultUILanguage(), "")
    except (AttributeError, OSError):
        pass
    lang, _, region = (name or locale.getlocale()[0] or "").partition("_")
    if lang.lower() == "zh":  # Taiwan, Hong Kong and Macau write traditional characters
        return "zh-TW" if region.upper() in ("TW", "HK", "MO") else "zh"
    return lang.lower() if lang.lower() in CODES else "en"


def current(settings):
    code = settings.get("language")
    return code if code in CODES else detect()


def strings(code):
    """The panel's text in this language: {English: translation}, empty if not translated."""
    if code not in _tables:
        try:
            with open(os.path.join(FOLDER, f"{code}.json"), encoding="utf-8") as f:
                _tables[code] = json.load(f)
        except (OSError, ValueError):
            _tables[code] = {}
    return _tables[code]


def tr(code, text, **values):
    """text in this language, with {name} filled in from values."""
    text = strings(code).get(text, text) if code != "en" else text
    return text.format(**values) if values else text


def page_event(code):
    """The page's 'lang' event: the menu, the chosen language and its text."""
    return {"kind": "lang", "current": code, "dir": "rtl" if code in RTL else "ltr",
            "strings": strings(code) if code != "en" else {},
            "items": [{"code": c, "english": e, "name": n} for c, e, n in LANGUAGES]}


def reply_note(code):
    """For the system prompt: the language Claude writes in."""
    if code == "en":
        return ""
    _, english, own = next(l for l in LANGUAGES if l[0] == code)
    return (f"\nThe user chose {english} ({own}) for the panel. Write your replies, questions, "
            f"<choices> options, block-plan names and notes, and the design review in {english}, "
            "unless the user writes to you in another language. Keep part references, net names, "
            "file names, KiCad menu and tool names, rule numbers and code as they are, and keep "
            "these markers in English, since the panel reads them: ' (Recommended)' after an "
            "option, '**Verdict:**' in the review.\n")
