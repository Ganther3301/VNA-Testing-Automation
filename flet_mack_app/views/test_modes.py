import flet as ft

class TestModesPanel(ft.Container):
    def __init__(self, runner, log_panel):
        self.runner = runner
        self.log = log_panel

        self.state_input = ft.TextField(label="States (comma separated)", expand=True)
        self.trigger_button = ft.ElevatedButton("Start Test", on_click=self.start_test)
        self.pause_button = ft.ElevatedButton("Pause", on_click=lambda _: self.runner.pause())
        self.resume_button = ft.ElevatedButton("Resume", on_click=lambda _: self.runner.resume())
        self.cancel_button = ft.ElevatedButton("Cancel", on_click=lambda _: self.runner.cancel())

        controls = [
            self.state_input,
            ft.Row([self.trigger_button, self.pause_button, self.resume_button, self.cancel_button])
        ]

        super().__init__(
            content=ft.Column(controls, spacing=10),
            padding=10,
            border_radius=6,
            bgcolor=ft.colors.SURFACE
        )

    def start_test(self, e):
        try:
            states = list(map(int, self.state_input.value.split(",")))
            self.runner.start(states)
        except ValueError:
            self.log.append("[ERROR] Invalid input. Use comma-separated integers.", "error")