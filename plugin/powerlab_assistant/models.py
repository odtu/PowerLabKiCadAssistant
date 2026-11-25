"""Which Claude model a picker entry runs, and what it's called.

The panel passes Claude Code's family aliases (opus, sonnet, haiku, fable), which it resolves
to the newest model of that family, so a new release is used without a panel update. The
version shown ("Opus 5.5") is the model id Claude Code reported in the init message of the
last run with that alias; until the first run the picker shows the family name ("Opus")."""

import re

ALIASES = ("opus", "sonnet", "haiku", "fable")
FAMILY_NAMES = {"opus": "Opus", "sonnet": "Sonnet", "haiku": "Haiku", "fable": "Fable"}
_ID = re.compile(r"^claude-([a-z]+)-(\d+)-(\d+)(?:-\d{8})?(?:\[.*\])?$")


def alias_of(model):
    """'claude-opus-5-5' -> 'opus' (settings from before aliases); an alias or '' as is."""
    m = _ID.match(model or "")
    return m.group(1) if m and m.group(1) in ALIASES else (model or "")


def pretty(model_id):
    """'claude-haiku-4-5-20251001' -> 'Haiku 4.5'; anything else unchanged."""
    m = _ID.match(model_id or "")
    if not m:
        return FAMILY_NAMES.get(model_id, model_id)
    return f"{m.group(1).capitalize()} {m.group(2)}.{m.group(3)}"


def resolve(model, resolved):
    """The model id an alias runs, as last reported (None if not known yet); an id as is."""
    if model in ALIASES:
        return (resolved or {}).get(model)
    return model or None


def label(model, resolved):
    """'Opus 5.5' for 'opus' once its id is known, else 'Opus'."""
    model_id = resolve(model, resolved)
    return pretty(model_id) if model_id else FAMILY_NAMES.get(model, model)
