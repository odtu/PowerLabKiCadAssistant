"""Drive a KiCad editor window through its native Windows menu.

KiCad 10's schematic editor exposes no save/revert over the IPC API and doesn't
watch its files, so the panel uses the editor's own File > Save and File > Revert
commands instead. wxWidgets uses native menus on Windows, so posting WM_COMMAND
with a menu item's id behaves exactly like the user clicking it.
"""

import ctypes
import ctypes.wintypes as wt
import os

user32 = ctypes.windll.user32
user32.GetWindowTextLengthW.argtypes = [wt.HWND]
user32.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
user32.GetMenu.argtypes = [wt.HWND]
user32.GetMenu.restype = wt.HMENU
user32.GetSubMenu.argtypes = [wt.HMENU, ctypes.c_int]
user32.GetSubMenu.restype = wt.HMENU
user32.GetMenuItemCount.argtypes = [wt.HMENU]
user32.GetMenuItemID.argtypes = [wt.HMENU, ctypes.c_int]
user32.GetMenuItemID.restype = wt.UINT
user32.GetMenuStringW.argtypes = [wt.HMENU, wt.UINT, wt.LPWSTR, ctypes.c_int, wt.UINT]
user32.PostMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
user32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
user32.GetForegroundWindow.restype = wt.HWND

WM_COMMAND = 0x0111
BM_CLICK = 0x00F5
MF_BYPOSITION = 0x0400
ENUM_PROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)


def window_text(hwnd):
    n = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def window_pid(hwnd):
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def top_windows():
    found = []
    user32.EnumWindows(ENUM_PROC(lambda h, _: found.append(h) or True), 0)
    return [h for h in found if user32.IsWindowVisible(h)]


def child_windows(hwnd):
    found = []
    user32.EnumChildWindows(hwnd, ENUM_PROC(lambda h, _: found.append(h) or True), 0)
    return found


def kicad_processes():
    """[(pid, has_visible_window)] for every running kicad.exe."""
    import csv
    import subprocess

    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq kicad.exe", "/FO", "CSV", "/NH"],
                             capture_output=True, text=True, timeout=10,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    pids = [int(row[1]) for row in csv.reader(out.splitlines()) if len(row) > 1 and row[1].isdigit()]
    with_window = {window_pid(h) for h in top_windows() if window_text(h)}
    return [(pid, pid in with_window) for pid in pids]


def find_editor(kind="Schematic Editor", pid=0):
    """The visible '<project> — Schematic Editor' window ('*' prefix when unsaved) of the
    KiCad with that process id (any KiCad if 0)."""
    for hwnd in top_windows():
        if window_text(hwnd).endswith(kind) and (not pid or window_pid(hwnd) == pid):
            return hwnd
    return None


def bring_to_front(hwnd):
    """Restore the window if minimized and put it in front. Windows allows this because
    the panel, the foreground window when the user clicks in it, asks."""
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    user32.SetForegroundWindow(hwnd)


def foreground_title(pid=0):
    """Title of the window the user is working in; "" if it isn't one of that KiCad's."""
    hwnd = user32.GetForegroundWindow()
    return window_text(hwnd) if not pid or window_pid(hwnd) == pid else ""


# ---- which KiCad a button was pressed in, and its API pipe ----

KICAD_EXES = {"kicad.exe", "eeschema.exe", "pcbnew.exe"}


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD), ("th32ProcessID", wt.DWORD),
                ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wt.DWORD),
                ("cntThreads", wt.DWORD), ("th32ParentProcessID", wt.DWORD),
                ("pcPriClassBase", ctypes.c_long), ("dwFlags", wt.DWORD),
                ("szExeFile", ctypes.c_wchar * 260)]


def processes():
    """{pid: (parent pid, exe name)} of every running process."""
    k32 = ctypes.windll.kernel32
    k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
    snap = k32.CreateToolhelp32Snapshot(0x2, 0)  # TH32CS_SNAPPROCESS
    found = {}
    if not snap or snap == wt.HANDLE(-1).value:
        return found
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(entry)
        ok = k32.Process32FirstW(wt.HANDLE(snap), ctypes.byref(entry))
        while ok:
            found[entry.th32ProcessID] = (entry.th32ParentProcessID, entry.szExeFile)
            ok = k32.Process32NextW(wt.HANDLE(snap), ctypes.byref(entry))
    finally:
        k32.CloseHandle(wt.HANDLE(snap))
    return found


def kicad_ancestor(pid):
    """The KiCad process that started pid (pid itself if it is one), or 0. The schematic
    button runs in a Python that KiCad started, sometimes through a venv launcher."""
    procs, seen = processes(), set()
    while pid and pid in procs and pid not in seen:
        seen.add(pid)
        parent, exe = procs[pid]
        if exe.lower() in KICAD_EXES:
            return pid
        pid = parent
    return 0


def process_running(pid):
    k32 = ctypes.windll.kernel32
    k32.OpenProcess.restype = wt.HANDLE
    handle = k32.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
    if not handle:
        return k32.GetLastError() == 5  # access denied: it exists
    try:
        return k32.WaitForSingleObject(wt.HANDLE(handle), 0) == 0x102  # WAIT_TIMEOUT
    finally:
        k32.CloseHandle(wt.HANDLE(handle))


def pipe_names():
    """Names of the named pipes; KiCad's API pipes are named after their socket path."""
    try:
        return {name.lower() for name in os.listdir("\\\\.\\pipe\\")}
    except OSError:
        return set()


def pipe_server(name):
    """Process id serving the named pipe, or 0."""
    k32 = ctypes.windll.kernel32
    k32.CreateFileW.restype = wt.HANDLE
    k32.CreateFileW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD, ctypes.c_void_p, wt.DWORD,
                                wt.DWORD, wt.HANDLE]
    path = "\\\\.\\pipe\\" + name
    for _ in range(3):
        handle = k32.CreateFileW(path, 0xC0000000, 0, None, 3, 0, None)  # read/write, existing
        if handle and handle != wt.HANDLE(-1).value:
            pid = wt.ULONG()
            try:
                ok = k32.GetNamedPipeServerProcessId(wt.HANDLE(handle), ctypes.byref(pid))
            finally:
                k32.CloseHandle(wt.HANDLE(handle))
            return pid.value if ok else 0
        if k32.GetLastError() != 231:  # ERROR_PIPE_BUSY: wait for a free instance
            return 0
        k32.WaitNamedPipeW(path, 300)
    return 0


def is_dirty(hwnd):
    return window_text(hwnd).startswith("*")


def _label(menu, pos):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetMenuStringW(menu, pos, buf, 256, MF_BYPOSITION)
    return buf.value.split("\t")[0].replace("&", "").strip()


def menu_command(hwnd, top, item):
    """Post the command of menu `top` > `item` (English labels). Returns True if found."""
    bar = user32.GetMenu(hwnd)
    if not bar:
        return False
    for i in range(user32.GetMenuItemCount(bar)):
        if _label(bar, i) != top:
            continue
        sub = user32.GetSubMenu(bar, i)
        for j in range(user32.GetMenuItemCount(sub)):
            if _label(sub, j) == item:
                user32.PostMessageW(hwnd, WM_COMMAND, user32.GetMenuItemID(sub, j), 0)
                return True
    return False


def current_sheet(hwnd):
    """'MCUCore [ESC3Phase/MCU Core] — Schematic Editor' -> 'ESC3Phase/MCU Core'."""
    title = window_text(hwnd).lstrip("*").rsplit(" — ", 1)[0]
    if "[" in title and title.endswith("]"):
        return title[title.index("[") + 1:-1]
    return title


# ---- clipboard snapshot/restore (so reading the selection doesn't clobber it) ----

kernel32 = ctypes.windll.kernel32
kernel32.GlobalAlloc.argtypes = [wt.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = wt.HGLOBAL
kernel32.GlobalLock.argtypes = [wt.HGLOBAL]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalUnlock.argtypes = [wt.HGLOBAL]
kernel32.GlobalSize.argtypes = [wt.HGLOBAL]
kernel32.GlobalSize.restype = ctypes.c_size_t
kernel32.GlobalFree.argtypes = [wt.HGLOBAL]
user32.OpenClipboard.argtypes = [wt.HWND]
user32.EnumClipboardFormats.argtypes = [wt.UINT]
user32.EnumClipboardFormats.restype = wt.UINT
user32.GetClipboardData.argtypes = [wt.UINT]
user32.GetClipboardData.restype = wt.HANDLE
user32.SetClipboardData.argtypes = [wt.UINT, wt.HANDLE]
user32.SetClipboardData.restype = wt.HANDLE

# Formats whose data is a GDI handle rather than global memory; Windows
# re-synthesizes them from CF_DIB / text when needed.
GDI_FORMATS = {2, 3, 9, 14, 0x80, 0x82, 0x83, 0x8E}


def _open_clipboard(owner):
    for _ in range(20):  # another app may hold it for a moment
        if user32.OpenClipboard(owner):
            return True
        ctypes.windll.kernel32.Sleep(10)
    return False


def save_clipboard():
    """Copy of every memory-based clipboard format, or None if it couldn't be read."""
    if not _open_clipboard(None):
        return None
    items, fmt = [], 0
    try:
        while True:
            fmt = user32.EnumClipboardFormats(fmt)
            if not fmt:
                break
            if fmt in GDI_FORMATS:
                continue
            handle = user32.GetClipboardData(fmt)
            size = kernel32.GlobalSize(handle) if handle else 0
            if not size or size > 64 * 1024 * 1024:
                continue
            ptr = kernel32.GlobalLock(handle)
            if ptr:
                try:
                    items.append((fmt, ctypes.string_at(ptr, size)))
                finally:
                    kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()
    return items


def restore_clipboard(items, owner):
    """Put back what save_clipboard() took. `owner` must be a window of this process."""
    if items is None or not _open_clipboard(owner):
        return
    try:
        user32.EmptyClipboard()
        for fmt, data in items:
            handle = kernel32.GlobalAlloc(0x0002, len(data))  # GMEM_MOVEABLE
            ptr = kernel32.GlobalLock(handle)
            ctypes.memmove(ptr, data, len(data))
            kernel32.GlobalUnlock(handle)
            if not user32.SetClipboardData(fmt, handle):
                kernel32.GlobalFree(handle)
    finally:
        user32.CloseClipboard()


def click_dialog_button(owner_pid, labels):
    """Click a button labelled one of `labels` in a dialog of the given process."""
    for hwnd in top_windows():
        if window_pid(hwnd) != owner_pid:
            continue
        for child in child_windows(hwnd):
            if window_text(child).replace("&", "") in labels:
                user32.PostMessageW(child, BM_CLICK, 0, 0)
                return True
    return False
