import flet as ft

def load(page, runner, log_panel):
    def click_handler(e):
        log_panel.append("[EXT] Button clicked from extension.", "info")

    return ft.Container(
        content=ft.Column([
            ft.Text("Sample Extension Panel", weight=ft.FontWeight.BOLD),
            ft.ElevatedButton("Click Me", on_click=click_handler)
        ]),
        padding=10,
        border_radius=6,
        bgcolor=ft.colors.AMBER_100
    )