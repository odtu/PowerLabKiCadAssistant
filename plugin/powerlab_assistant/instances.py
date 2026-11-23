"""Which KiCad a panel belongs to, and where that KiCad's API listens.

KiCad 10 listens on %TEMP%\\kicad\\api.sock, and is meant to use api-<pid>.sock when that
name is taken. On Windows the socket is a named pipe, which leaves no file, so KiCad never
sees the name taken: a second KiCad tries api.sock too, fails, and has no API at all, and
every tool that asks for "the" KiCad reaches the first one. An ordinary file with that name
makes every KiCad started afterwards use its own api-<pid>.sock, so the panel leaves one.
"""

import os
import sys
import tempfile

# KiCad puts its socket in the temp folder, but in /tmp on macOS (a Unix socket's path may
# be at most 104 bytes there, and $TMPDIR is long).
SOCKET_DIR = "/tmp/kicad" if sys.platform == "darwin" else os.path.join(tempfile.gettempdir(), "kicad")
SHARED = os.path.join(SOCKET_DIR, "api.sock")
# Only Windows needs the placeholder: elsewhere api.sock is a real file while a KiCad listens
# on it, so a second KiCad already picks api-<pid>.sock, and the first keeps the default one
# that a plain Claude Code session's kicad tools look for.
NEEDS_PLACEHOLDER = os.name == "nt"


def ensure_placeholder():
    """Leave the file that makes KiCads started from now on use api-<pid>.sock."""
    if not NEEDS_PLACEHOLDER:
        return
    try:
        os.makedirs(SOCKET_DIR, exist_ok=True)
        if not os.path.exists(SHARED):
            open(SHARED, "a").close()
    except OSError:
        pass


def own_socket(pid):
    return os.path.join(SOCKET_DIR, f"api-{pid}.sock")


def find_socket(pid, pipes, server_of):
    """ipc:// address of the API of the KiCad with process id pid, or None if it has none.

    pipes: lower-case names of the open named pipes; server_of(name): process id serving one.
    A KiCad started while api.sock was free has that one; later ones have api-<pid>.sock."""
    for path in (own_socket(pid), SHARED):
        if path.lower() in pipes and (path != SHARED or server_of(path) == pid):
            return "ipc://" + path
    return None


def shared_holder(pid, pipes, server_of):
    """Process id of another KiCad holding api.sock, or 0."""
    holder = server_of(SHARED) if SHARED.lower() in pipes else 0
    return holder if holder != pid else 0
