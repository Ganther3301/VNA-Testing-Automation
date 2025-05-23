# main.py
import flet as ft
from core.runner import TestRunner
from core.log_panel import LogPanel
from views.test_modes import TestModesPanel
from extensions.loader import load_extensions

def main(page: ft.Page):
    page.title = "MACK IITM Testing System (Flet)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = "auto"

    log_panel = LogPanel()
    runner = TestRunner(log_panel)
    test_modes = TestModesPanel(runner, log_panel)

    extensions = load_extensions(page, runner, log_panel)

    page.add(
        ft.Column([
            ft.Text("MACK IITM Testing System", size=24, weight=ft.FontWeight.BOLD),
            test_modes,
            *extensions,
            log_panel
        ], expand=True, scroll=ft.ScrollMode.AUTO)
    )

ft.app(target=main)