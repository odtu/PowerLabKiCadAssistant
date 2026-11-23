"""Pieces shared by the PCB editor plugin and the standalone schematic panel."""

import os
import shlex
import shutil
import subprocess
import tempfile

from . import config

# Windows-only process flags (0 elsewhere, so tests also run on Linux CI).
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
CREATE_NEW_CONSOLE = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)

HOME = os.path.expanduser("~")
if config.IS_WINDOWS:
    CLAUDE_CANDIDATES = [
        os.path.expandvars(r"%USERPROFILE%\.local\bin\claude.exe"),  # native installer
        os.path.expandvars(r"%APPDATA%\npm\claude.cmd"),  # npm install -g
    ]
    GH_CANDIDATES = [os.path.expandvars(r"%ProgramFiles%\GitHub CLI\gh.exe")]
    # A program KiCad starts on macOS gets launchd's PATH (/usr/bin:/bin:...), not the
    # shell's, so Homebrew's and the native installer's folders are added by hand.
    EXTRA_PATH = []
else:
    CLAUDE_CANDIDATES = [os.path.join(HOME, ".local", "bin", "claude"),
                         "/opt/homebrew/bin/claude", "/usr/local/bin/claude"]
    GH_CANDIDATES = ["/opt/homebrew/bin/gh", "/usr/local/bin/gh"]
    EXTRA_PATH = [os.path.join(HOME, ".local", "bin"), "/opt/homebrew/bin", "/usr/local/bin"]

if config.IS_WINDOWS:
    INSTALL_HELP = (
        "Claude Code was not found.\n\n"
        "Install it from PowerShell:\n"
        "    irm https://claude.ai/install.ps1 | iex\n\n"
        "then sign in once by running `claude`, and restart KiCad."
    )
else:
    INSTALL_HELP = (
        "Claude Code was not found.\n\n"
        "Install it from Terminal:\n"
        "    curl -fsSL https://claude.ai/install.sh | bash\n\n"
        "then sign in once by running `claude`, and restart KiCad."
    )


def _which(name, candidates):
    path = shutil.which(name, path=os.pathsep.join([os.environ.get("PATH", "")] + EXTRA_PATH))
    if path:
        return path
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def find_claude():
    return _which("claude", CLAUDE_CANDIDATES)


def find_gh():
    return _which("gh", GH_CANDIDATES)


def clean_env():
    """Environment for child processes: no KiCad-embedded Python variables, KiCad's
    bin folder on PATH so Claude can call kicad-cli by name, and Windows' own tar (it
    writes zips) ahead of Git's GNU tar. On macOS also Homebrew's folders (git, node, gh),
    which a program started from the Dock doesn't have."""
    env = dict(os.environ)
    for var in ("PYTHONHOME", "PYTHONPATH", "PYTHONEXECUTABLE", "__PYVENV_LAUNCHER__"):
        env.pop(var, None)
    first = []
    bin_dir = config.kicad_bin()
    if bin_dir:
        first.append(bin_dir)
    system32 = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")
    if config.IS_WINDOWS and os.path.isfile(os.path.join(system32, "tar.exe")):
        first.append(system32)
    path = env.get("PATH", "")
    first += [d for d in EXTRA_PATH if d not in path.split(os.pathsep)]
    if first:
        env["PATH"] = os.pathsep.join(first + [path])
    return env


def terminal_script(args, cwd, env):
    """macOS: the shell script a Terminal window runs for open_console. Terminal starts
    a login shell of its own, so the environment the panel wants is set in the script."""
    keep = ("PATH", "KICAD_API_SOCKET", "KICAD_API_TOKEN", "ENABLE_CLAUDEAI_MCP_SERVERS",
            "CLAUDE_CODE_EXTRA_BODY")
    lines = ["#!/bin/bash", "rm -f -- \"$0\""]  # a one-off script: gone once it runs
    lines += [f"export {k}={shlex.quote(env[k])}" for k in keep if k in env]
    lines += [f"cd {shlex.quote(cwd)}", " ".join(shlex.quote(a) for a in args)]
    return "\n".join(lines) + "\n"


def open_console(args, cwd=None, extra_env=None):
    """Run a command in a new console window the user can see and type into."""
    env = clean_env()
    env.update(extra_env or {})
    cwd = cwd or HOME
    if config.IS_MAC:
        fd, path = tempfile.mkstemp(prefix="powerlab-", suffix=".command")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(terminal_script(args, cwd, env))
        os.chmod(path, 0o700)
        subprocess.Popen(["open", "-a", "Terminal", path], env=env)
        return
    subprocess.Popen(args, cwd=cwd, env=env, creationflags=CREATE_NEW_CONSOLE)


def open_path(path):
    """Open a file with the program the system uses for it (a PDF viewer, a browser)."""
    if config.IS_WINDOWS:
        os.startfile(path)
    else:
        subprocess.Popen(["open" if config.IS_MAC else "xdg-open", path])


def open_terminal(claude, cwd, context, session_id=None, extra_env=None):
    """Open a full interactive Claude Code session in a new console window."""
    args = [claude, "--append-system-prompt", context]
    if session_id:
        args += ["--resume", session_id]
    open_console(args, cwd, extra_env)


def run_quiet(args, cwd=None, timeout=60, extra_env=None):
    """Run a command without a console window; returns (exit code, combined output)."""
    env = clean_env()
    env.update(extra_env or {})
    try:
        proc = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout,
                              creationflags=CREATE_NO_WINDOW)
        # rstrip only: leading spaces can be meaningful (git status columns).
        return proc.returncode, (proc.stdout + proc.stderr).rstrip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return -1, str(exc)
