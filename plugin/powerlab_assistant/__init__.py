import os

if not os.environ.get("POWERLAB_ASSISTANT_STANDALONE"):  # the schematic panel runs outside KiCad
    from .pcb import AssistantButton

    AssistantButton().register()