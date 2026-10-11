"""Which KiCad a panel belongs to, and where that KiCad's API listens.

KiCad 10 listens on %TEMP%\\kicad\\api.sock, and is meant to use api-<pid>.sock when that
name is taken. On Windows the socket is a named pipe, which leaves no file, so KiCad never
sees the name taken: a second KiCad tries api.sock too, fails, and has no API at all, and
every tool that asks for "the" KiCad reaches the first one. An ordinary file with that name
makes every KiCad started afterwards use its own api-<pid>.sock, so the panel leaves one.
"""

import os
import tempfile

SOCKET_DIR = os.path.join(tempfile.gettempdir(), "kicad")
SHARED = os.path.join(SOCKET_DIR, "api.sock")


def ensure_placeholder():
    """Leave the file that makes KiCads started from now on use api-<pid>.sock."""
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
