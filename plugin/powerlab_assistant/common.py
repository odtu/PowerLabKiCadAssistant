"""Pieces shared by the PCB editor plugin and the standalone schematic panel."""

import os
import shutil
import subprocess

from . import config

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
    """Environment for child processes: no KiCad-embedded Python variables, and KiCad's
    bin folder on PATH so Claude can call kicad-cli by name."""
    env = dict(os.environ)
    for var in ("PYTHONHOME", "PYTHONPATH"):
        env.pop(var, None)
    bin_dir = config.kicad_bin()
    if bin_dir:
        env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")
    return env


def open_console(args, cwd=None):
    """Run a command in a new console window the user can see and type into."""
    subprocess.Popen(args, cwd=cwd or os.path.expanduser("~"), env=clean_env(),
                     creationflags=subprocess.CREATE_NEW_CONSOLE)


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
                              creationflags=subprocess.CREATE_NO_WINDOW)
        # rstrip only: leading spaces can be meaningful (git status columns).
        return proc.returncode, (proc.stdout + proc.stderr).rstrip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return -1, str(exc)
