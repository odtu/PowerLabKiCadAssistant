"""Pieces shared by the PCB editor plugin and the standalone schematic panel."""

import os
import shutil
import subprocess

from . import config

# Windows-only process flags (0 elsewhere, so tests also run on Linux CI).
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
CREATE_NEW_CONSOLE = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)

CLAUDE_CANDIDATES = [
    os.path.expandvars(r"%USERPROFILE%\.local\bin\claude.exe"),  # native installer
    os.path.expandvars(r"%APPDATA%\npm\claude.cmd"),  # npm install -g
]

INSTALL_HELP = (
    "Claude Code was not found.\n\n"
    "Install it from PowerShell:\n"
    "    irm https://claude.ai/install.ps1 | iex\n\n"
    "then sign in once by running `claude`, and restart KiCad."
)


def find_claude():
    path = shutil.which("claude")
    if path:
        return path
    for candidate in CLAUDE_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate
    return None


def find_gh():
    path = shutil.which("gh")
    if path:
        return path
    candidate = os.path.expandvars(r"%ProgramFiles%\GitHub CLI\gh.exe")
    return candidate if os.path.isfile(candidate) else None


def clean_env():
    """Environment for child processes: no KiCad-embedded Python variables, KiCad's
    bin folder on PATH so Claude can call kicad-cli by name, and the assistant's own
    Java 25 + Freerouting for the kicad MCP server's autoroute tool, and Windows' own
    tar (it writes zips) ahead of Git's GNU tar."""
    env = dict(os.environ)
    for var in ("PYTHONHOME", "PYTHONPATH"):
        env.pop(var, None)
    first = []
    java = config.java_home()
    if java:
        # The MCP server takes the first `java` on PATH; a system Java 8 would come first
        # otherwise and Freerouting 2.4.1 needs Java 25.
        first.append(os.path.join(java, "bin"))
        env["JAVA_HOME"] = java
    bin_dir = config.kicad_bin()
    if bin_dir:
        first.append(bin_dir)
    system32 = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")
    if os.path.isfile(os.path.join(system32, "tar.exe")):
        first.append(system32)
    if first:
        env["PATH"] = os.pathsep.join(first + [env.get("PATH", "")])
    jar = config.freerouting_jar()
    if jar:
        env["FREEROUTING_JAR"] = jar
    return env


def open_console(args, cwd=None):
    """Run a command in a new console window the user can see and type into."""
    subprocess.Popen(args, cwd=cwd or os.path.expanduser("~"), env=clean_env(),
                     creationflags=CREATE_NEW_CONSOLE)


def open_terminal(claude, cwd, context, session_id=None):
    """Open a full interactive Claude Code session in a new console window."""
    args = [claude, "--append-system-prompt", context]
    if session_id:
        args += ["--resume", session_id]
    open_console(args, cwd)


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
