import importlib
import os
import sys
import flet as ft

def load_extensions(page, runner, log_panel):
    extensions = []
    ext_dir = os.path.dirname(__file__)
    sys.path.insert(0, ext_dir)

    for file in os.listdir(ext_dir):
        if file.endswith(".py") and file != "loader.py" and file != "__init__.py":
            mod_name = file[:-3]
            try:
                mod = importlib.import_module(mod_name)
                if hasattr(mod, "load") and callable(mod.load):
                    panel = mod.load(page, runner, log_panel)
                    if isinstance(panel, ft.Control):
                        extensions.append(panel)
            except Exception as e:
                log_panel.append(f"[EXT ERROR] {mod_name}: {e}", "error")

    return extensions