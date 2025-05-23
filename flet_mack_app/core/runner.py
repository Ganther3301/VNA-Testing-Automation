import time
import threading

class TestRunner:
    def __init__(self, log_panel):
        self.log = log_panel
        self.test_thread = None
        self.pause_event = threading.Event()
        self.cancel_event = threading.Event()
        self.running = False
        self.delay = 1  # seconds between states

    def start(self, states):
        if self.running:
            self.log.append("[INFO] Test is already running.", "warning")
            return

        self.pause_event.clear()
        self.cancel_event.clear()
        self.running = True

        def run():
            self.log.append("[START] Running test...")
            for state in states:
                if self.cancel_event.is_set():
                    self.log.append("[CANCELLED] Test was cancelled.", "error")
                    break

                while self.pause_event.is_set():
                    time.sleep(0.1)

                self.log.append(f"Triggered state {state}", "info")
                time.sleep(self.delay)
                self.log.append(f"Saved measurement for state {state}", "success")

            self.running = False
            self.log.append("[DONE] Test completed.", "success")

        self.test_thread = threading.Thread(target=run)
        self.test_thread.start()

    def pause(self):
        if self.running:
            self.pause_event.set()
            self.log.append("[PAUSE] Test paused.", "warning")

    def resume(self):
        if self.running and self.pause_event.is_set():
            self.pause_event.clear()
            self.log.append("[RESUME] Test resumed.", "success")

    def cancel(self):
        if self.running:
            self.cancel_event.set()
            self.log.append("[CANCEL] Cancelling test...", "warning")