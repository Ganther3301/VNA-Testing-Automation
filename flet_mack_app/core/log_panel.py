import flet as ft

class LogPanel(ft.Container):
    def __init__(self):
        self.text_box = ft.TextField(
            multiline=True,
            read_only=True,
            min_lines=10,
            max_lines=20,
            expand=True,
            text_align=ft.TextAlign.LEFT
        )
        super().__init__(
            content=self.text_box,
            padding=10,
            border_radius=6,
            bgcolor=ft.colors.SURFACE_VARIANT
        )

    def append(self, message, tag="info"):
        color = {
            "info": ft.colors.BLUE,
            "success": ft.colors.GREEN,
            "error": ft.colors.RED,
            "warning": ft.colors.ORANGE
        }.get(tag, ft.colors.BLACK)

        timestamped = f"[{ft.datetime.now().strftime('%H:%M:%S')}] {message}\n"
        self.text_box.value += timestamped
        self.text_box.color = color
        self.update()