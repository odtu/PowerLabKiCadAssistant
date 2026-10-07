"""Plan limits and context use, read from Claude Code's stream-json events."""

import time

WINDOW_LABELS = {
    "five_hour": ("5h", "5-hour limit"),
    "seven_day": ("week", "Weekly limit"),
    "seven_day_opus": ("week Opus", "Weekly Opus limit"),
    "seven_day_sonnet": ("week Sonnet", "Weekly Sonnet limit"),
}


def _when(epoch, now=None):
    if not epoch:
        return ""
    now = now or time.time()
    t = time.localtime(epoch)
    if epoch - now < 20 * 3600:
        return time.strftime("%H:%M", t)
    return time.strftime("%a %H:%M", t)


def limits(event, now=None):
    """From a rate_limit_event: [{"short", "label", "pct", "resets"}], most used first."""
    info = (event or {}).get("rate_limit_info") or {}
    windows = info.get("unifiedWindows") or {}
    if not windows and info.get("rateLimitType"):
        windows = {info["rateLimitType"]: {"utilization": info.get("utilization"),
                                           "resetsAt": info.get("resetsAt")}}
    out = []
    for key, w in windows.items():
        pct = w.get("utilization")
        if pct is None:
            continue
        short, label = WINDOW_LABELS.get(key, (key.replace("_", " "), key.replace("_", " ").capitalize()))
        out.append({"short": short, "label": label, "pct": round(float(pct) * 100),
                    "resets": _when(w.get("resetsAt"), now)})
    out.sort(key=lambda x: -x["pct"])
    return out


def context(result):
    """From a result event: (tokens in the context window, window size) or (0, 0)."""
    usage = (result or {}).get("usage") or {}
    last = (usage.get("iterations") or [usage])[-1]
    tokens = sum(int(last.get(k) or 0) for k in
                 ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens", "output_tokens"))
    window = 0
    for model in ((result or {}).get("modelUsage") or {}).values():
        window = max(window, int(model.get("contextWindow") or 0))
    return tokens, window


def summary(limit_items, tokens, window):
    """Short text for the panel plus a longer tooltip."""
    parts, tips = [], []
    for item in limit_items[:1]:
        parts.append(f"{item['short']} {item['pct']}%")
    for item in limit_items:
        tips.append(f"{item['label']}: {item['pct']}% used" + (f", resets {item['resets']}" if item["resets"] else ""))
    if tokens and window:
        pct = round(100 * tokens / window)
        parts.append(f"context {pct}%")
        tips.append(f"This chat's context: {tokens / 1000:.0f}k of {window / 1000:.0f}k tokens. "
                    "Start a new chat (+) when it gets full.")
    return " · ".join(parts), "\n".join(tips)
