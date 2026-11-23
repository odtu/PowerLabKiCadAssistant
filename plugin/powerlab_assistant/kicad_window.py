"""Drive the KiCad editor windows, the clipboard and KiCad's processes, for this platform.

KiCad 10's schematic editor exposes no save/revert/selection over the IPC API and doesn't
watch its files, so the panel uses the editor's own File > Save, File > Revert and Edit > Copy
menu commands instead: through the native Windows menu (kicad_window_win), or through macOS
accessibility (kicad_window_mac). Both modules have the same functions.
"""

import sys

if sys.platform == "win32":
    from .kicad_window_win import *  # noqa: F401,F403
    from .kicad_window_win import KICAD_EXES  # noqa: F401
elif sys.platform == "darwin":
    from .kicad_window_mac import *  # noqa: F401,F403
    from .kicad_window_mac import KICAD_EXES  # noqa: F401
else:
    raise ImportError("the PowerLab Assistant panel runs on Windows and macOS")
