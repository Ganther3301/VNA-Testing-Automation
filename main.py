import tkinter as tk
import csv
from tkinter import ttk, filedialog
import os
import datetime
import time
import threading

from fpga import FPGA
from vna import VNA


class MackIITMGUI:
    def __init__(self, root):
        self.delay = 2  # Default delay in seconds

        self.root = root
        self.root.title("MACK IITM TESTING SYSTEM")
        self.root.geometry("900x600")
        self.root.minsize(700, 500)

        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.fpga = FPGA()
        self.vna = VNA()

        self.file_path = ''
        self.mode_var = tk.StringVar(value="")
        self.device_type_var = tk.StringVar(value="")
        self.test_running = False

        self.create_widgets()
        self.log("Welcome! Please select device type and initialize system.")

    def create_widgets(self):
        self.main_container = ttk.Frame(self.root)
        self.main_container.grid(row=1, column=0, sticky="nsew")
        self.main_container.rowconfigure(0, weight=1)  # Content expands
        self.main_container.rowconfigure(1, weight=0)  # Log stays fixed
        self.main_container.columnconfigure(0, weight=1)

        # Content Frame (top area)
        self.content_frame = ttk.Frame(self.main_container)
        self.content_frame.grid(
            row=0, column=0, sticky="nsew", padx=20, pady=10)

        # Title
        ttk.Label(self.content_frame, text="MACK IITM TESTING SYSTEM",
                  font=("Times New Roman", 16, "bold")).pack(pady=(10, 5))

        # Device Type Selection Frame (new)
        self.device_type_frame = ttk.Frame(self.content_frame)
        self.device_type_frame.pack(pady=10)
        ttk.Label(self.device_type_frame, text="Select Device Type:").pack(
            side="left", padx=(0, 10))

        # Radio buttons for device type
        device_types = {"Amplifier": "amplifier",
                        "Phase Shifter": "phase_shifter"}
        for text, value in device_types.items():
            ttk.Radiobutton(self.device_type_frame, text=text, variable=self.device_type_var,
                            value=value, command=self.on_device_type_change).pack(side="left", padx=5)

        # Frame 1 - Connect button (shown after device type selection)
        self.frame1 = ttk.Frame(self.content_frame)
        self.connect_button = ttk.Button(
            self.frame1, text="CONNECT", command=self.connect_devices)
        self.connect_button.pack(anchor="center")

        # Frame 2 (hidden until connect)
        self.frame2 = ttk.Frame(self.content_frame)
        self.setup_frame2()

        # Frame 3 (radio buttons + dynamic content - only for Phase Shifter)
        self.frame3 = ttk.Frame(self.content_frame)
        self.setup_frame3()

        # Frame 4 - Output log (bottom, always visible)
        self.frame4 = ttk.Frame(self.main_container, padding=10)
        self.frame4.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        output_frame = ttk.Frame(self.frame4)
        output_frame.pack(fill="both", expand=True)
        output_frame.rowconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)

        self.output_box = tk.Text(
            output_frame, wrap="word", state="disabled", height=8, font=("Consolas", 10))
        self.output_box.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            output_frame, orient="vertical", command=self.output_box.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.output_box.config(yscrollcommand=scrollbar.set)

        self.style_log_tags()

        # Set up the Amplifier mode specific UI elements
        self.setup_amplifier_frame()

    def on_device_type_change(self):
        """Handle device type selection"""
        device_type = self.device_type_var.get()
        self.device_type = device_type

        # Hide all frames first
        self.frame1.pack_forget()
        self.frame2.pack_forget()
        self.frame3.pack_forget()
        self.amplifier_test_frame.pack_forget()

        if device_type == "amplifier":
            self.log("Amplifier mode selected", "info")
            self.frame1.pack(pady=10)
        elif device_type == "phase_shifter":
            self.log("Phase Shifter mode selected", "info")
            self.frame1.pack(pady=10)
        else:
            self.log("Please select a device type", "warning")

        self.connect_button.state(["!disabled"])

    def setup_amplifier_frame(self):
        """Create special UI elements for Amplifier mode"""
        self.amplifier_test_frame = ttk.Frame(self.content_frame)

        # Add amplifier-specific controls
        test_frame = ttk.Frame(self.amplifier_test_frame)
        test_frame.pack(fill="x", expand=True)

        ttk.Button(test_frame, text="Save Traces",
                   command=self.run_amplifier_test).pack(pady=10)

    def run_amplifier_test(self):
        """Run the amplifier test in a separate thread"""
        if self.test_running:
            self.log("[ERROR] A test is already running", "error")
            return

        self.test_running = True
        threading.Thread(target=self._run_amplifier_test, daemon=True).start()

    def _run_amplifier_test(self):
        """Perform the actual amplifier test"""
        folder_name = datetime.datetime.now().strftime("measurement_%Y-%m-%d_%H-%M-%S")
        os.makedirs(folder_name, exist_ok=True)
        try:
            self.vna.save_traces_amp(
                folder_name, self.start_freq, self.stop_freq)  # TODO : UNCOMMENT

            self.log_threadsafe(
                "Amplifier data successfully saved", "success")
        except Exception as e:
            self.log_threadsafe(
                f"[ERROR] Amplifier test failed: {str(e)}", "error")
        finally:
            self.test_running = False

    def setup_frame2(self):
        frame_content = ttk.Frame(self.frame2)
        frame_content.pack(fill="x", expand=True)

        for i in range(6):
            frame_content.columnconfigure(i, weight=1)

        self.start_freq_entry = self.add_labeled_entry(
            frame_content, "Start Frequency", 0, 0)
        self.stop_freq_entry = self.add_labeled_entry(
            frame_content, "Stop Frequency", 0, 2)

        self.start_freq_entry.bind("<KeyRelease>", self.hide_frame3_on_change)
        self.stop_freq_entry.bind("<KeyRelease>", self.hide_frame3_on_change)
        self.config_button = ttk.Button(
            frame_content, text="CONFIGURE", command=self.configure_measurement)
        self.config_button.grid(row=0, column=6, padx=10)

    def setup_frame3(self):
        self.radio_panel = ttk.Frame(self.frame3)
        self.radio_panel.pack(fill="x", expand=True)

        radio_frame = ttk.Frame(self.radio_panel)
        radio_frame.pack(side="left", anchor="nw", padx=20)

        # Add delay configuration box
        delay_frame = ttk.Frame(self.radio_panel)
        delay_frame.pack(side="right", anchor="ne", padx=20)

        ttk.Label(delay_frame, text="Delay (seconds):").pack(
            side="left", padx=(0, 5))
        self.delay_entry = ttk.Entry(delay_frame, width=5)
        self.delay_entry.pack(side="left")
        self.delay_entry.insert(0, str(self.delay))  # Set default value
        self.delay_entry.bind("<KeyRelease>", self.update_delay)

        self.mode_container = ttk.Frame(self.frame3)
        self.mode_container.pack(fill="x", expand=True, pady=5)

        self.single_frame = ttk.Frame(self.mode_container, padding=10)
        self.all_state_frame = ttk.Frame(self.mode_container, padding=10)
        self.upload_frame = ttk.Frame(self.mode_container, padding=10)
        self.csv_label_var = tk.StringVar(value="No file selected")

        modes = {
            "Single State Transmission": "single",
            "All State Data": "all",
            "Upload CSV": "csv"
        }

        for text, value in modes.items():
            ttk.Radiobutton(radio_frame, text=text, variable=self.mode_var, value=value,
                            command=self.show_selected_mode).pack(anchor="w", pady=2)

        self.setup_single_frame()
        self.setup_all_state_frame()
        self.setup_upload_frame()

    def update_delay(self, event=None):
        """Update delay value when user changes the entry"""
        try:
            new_delay = float(self.delay_entry.get())
            if new_delay > 0:
                self.delay = new_delay
                self.log(f"Delay updated to {new_delay} seconds", "info")
            else:
                self.log("[WARNING] Delay must be positive", "warning")
                self.delay_entry.delete(0, tk.END)
                self.delay_entry.insert(0, str(self.delay))
        except ValueError:
            # Restore previous value if input is not a valid number
            self.log("[ERROR] Invalid delay value", "error")
            self.delay_entry.delete(0, tk.END)
            self.delay_entry.insert(0, str(self.delay))

    def setup_single_frame(self):
        container = ttk.Frame(self.single_frame)
        container.pack(expand=True)
        self.n_entry = self.add_labeled_entry(container, "Number of Bits:")
        self.state_entry = self.add_labeled_entry(
            container, "State for Transmission:")
        ttk.Button(container, text="Trigger", command=lambda: self.start_test_thread(
            'single_state')).pack(pady=10)

    def setup_all_state_frame(self):
        container = ttk.Frame(self.all_state_frame)
        container.pack(expand=True)
        self.bits_entry = self.add_labeled_entry(
            container, "Bits for Phase Shifter:")
        self.states_entry = self.add_labeled_entry(
            container, "Number of States:")
        ttk.Button(container, text="Trigger",
                   command=lambda: self.start_test_thread('all_states')).pack(pady=10)

    def setup_upload_frame(self):
        container = ttk.Frame(self.upload_frame)
        container.pack(expand=True)
        ttk.Button(container, text="Upload CSV",
                   command=self.upload_csv).pack(pady=5)
        ttk.Label(container, textvariable=self.csv_label_var,
                  font=("Arial", 9, "italic")).pack(pady=5)
        ttk.Button(container, text="Trigger", command=lambda: self.start_test_thread(
            'csv')).pack(pady=5)

    def add_labeled_entry(self, parent, label_text, row=None, column=None):
        if row is not None and column is not None:
            label = ttk.Label(parent, text=label_text)
            entry = ttk.Entry(parent, width=10)
            label.grid(row=row, column=column, sticky="w", padx=5)
            entry.grid(row=row, column=column + 1, sticky="w")
        else:
            container = ttk.Frame(parent)
            container.pack(fill="x", pady=5)
            label = ttk.Label(container, text=label_text, width=20)
            label.pack(side="left", padx=(0, 5))
            entry = ttk.Entry(container, width=10)
            entry.pack(side="left")
        return entry

    def style_log_tags(self):
        self.output_box.tag_configure("info", foreground="blue")
        self.output_box.tag_configure(
            "error", foreground="red", font=("Consolas", 10, "bold"))
        self.output_box.tag_configure("success", foreground="green")
        self.output_box.tag_configure("warning", foreground="orange")
        self.output_box.tag_configure(
            "timestamp", foreground="gray", font=("Consolas", 9, "italic"))

    def connect_devices(self):
        if self.device_type == 'phase_shifter':
            self.fpga.initialize_fpga()

            if self.fpga.connected:
                self.log("FPGA Successfully Connected", "success")
            else:
                self.log("[ERROR] FPGA Not Connected", "error")

        try:
            self.vna.initialize_vna()
        except:
            self.log(
                "[ERROR] Could not locate a VISA implementation", tag='error')

        if self.vna.connected:
            self.log("VNA Successfully Connected", "success")
        else:
            self.log("[ERROR] VNA Connection Failed", "error")

        if (self.fpga.connected and self.vna.connected and self.device_type == 'phase_shifter') or \
                (self.vna.connected and self.device_type == 'amplifier'):
            self.connect_button.state(["disabled"])
            self.frame2.pack(fill="x", pady=10)

    def configure_measurement(self):
        try:
            start_freq = float(self.start_freq_entry.get())
            stop_freq = float(self.stop_freq_entry.get())

            freq_range, _ = self.vna.get_trace_info()

            if freq_range[0] <= start_freq < stop_freq <= freq_range[-1] or freq_range[0] <= start_freq == stop_freq <= freq_range[-1]:
                self.start_freq = start_freq
                self.stop_freq = stop_freq

                # Different behavior depending on device type
                if self.device_type_var.get() == "phase_shifter":
                    self.frame3.pack()
                    self.log(
                        "Phase shifter measurement configuration successful. Choose a transmission mode.", "success")
                else:  # amplifier mode
                    self.amplifier_test_frame.pack(fill="x", pady=10)
                    self.log(
                        "Amplifier measurement configuration successful.", "success")

            else:
                self.log(
                    "[ERROR] Frequency range not within sweep range", "error")
        except ValueError:
            self.log(
                "[ERROR] Invalid input. Please enter valid numbers.", "error")

    def show_selected_mode(self):
        for frame in [self.single_frame, self.all_state_frame, self.upload_frame]:
            frame.pack_forget()

        selected = self.mode_var.get()
        if selected == "single":
            self.single_frame.pack(fill="x", pady=5)
        elif selected == "all":
            self.all_state_frame.pack(fill="x", pady=5)
        elif selected == "csv":
            self.upload_frame.pack(fill="x", pady=5)

    def hide_frame3_on_change(self, event=None):
        self.frame3.pack_forget()
        self.amplifier_test_frame.pack_forget()

        # Reset mode selection
        self.mode_var.set("")

        # Hide all mode-specific frames
        for frame in [self.single_frame, self.all_state_frame, self.upload_frame]:
            frame.pack_forget()

        # Clear entries in all modes
        for entry in [self.n_entry, self.state_entry, self.bits_entry, self.states_entry]:
            try:
                entry.delete(0, tk.END)
            except:
                pass  # Entry might not exist yet

        self.csv_label_var.set("No file selected")
        self.file_path = ''

    def upload_csv(self):
        self.file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")])
        if self.file_path:
            filename = os.path.basename(self.file_path)
            self.csv_label_var.set(f"Uploaded: {filename}")
            self.log(f"CSV Uploaded Successfully: {filename}", "success")
        else:
            self.csv_label_var.set("No file selected")
            self.log("CSV Upload cancelled.", "warning")

    # New method to start tests in a separate thread
    def start_test_thread(self, mode):
        if self.test_running:
            self.log("[ERROR] A test is already running", "error")
            return

        self.test_running = True
        threading.Thread(target=self.start_test,
                         args=(mode,), daemon=True).start()

    def log_threadsafe(self, message, tag="info"):
        """Thread-safe logging function"""
        self.root.after(0, lambda: self.log(message, tag))

    def start_test(self, mode):
        print(self.delay)
        try:
            folder_name = datetime.datetime.now().strftime("measurement_%Y-%m-%d_%H-%M-%S")

            if mode == 'csv':
                if self.file_path:
                    self.log_threadsafe("Reading CSV file...")
                    with open(self.file_path, 'r') as f:
                        csv_data = csv.reader(f)
                        states = []
                        for i in list(csv_data)[0]:
                            try:
                                states.append(int(i))
                            except:
                                pass

                    if not states:
                        self.log_threadsafe(
                            "[ERROR] No valid states found in CSV", "error")
                        self.test_running = False
                        return

                    os.makedirs(folder_name, exist_ok=True)

                    for idx, state in enumerate(states):
                        self.fpga.trigger_state(state)
                        self.log_threadsafe(
                            f"[TRIGGER] Triggered state {state}", "success")
                        time.sleep(self.delay)
                        self.vna.save_traces(
                            state, folder_name, self.start_freq, self.stop_freq)
                        self.log_threadsafe(
                            f"Saved measurement for state {state}", "success")

                    self.vna.start_index = None
                    self.vna.stop_index = None
                else:
                    self.log_threadsafe(
                        "[ERROR] Please upload a CSV file first", 'error')

            elif mode == 'single_state':
                try:
                    n = int(self.n_entry.get())
                    state = int(self.state_entry.get())
                    if state >= 2 ** n:
                        self.log_threadsafe(
                            f"[ERROR] Invalid: State exceeds 2^{n}", "error")
                    else:
                        os.makedirs(folder_name, exist_ok=True)
                        self.log_threadsafe(
                            f"Transmitting State {state} (n={n})", "info")
                        self.fpga.trigger_state(state)
                        self.log_threadsafe(
                            f"[TRIGGER] Triggered state {state}", "success")

                        time.sleep(self.delay)

                        self.vna.save_traces(
                            state, folder_name, self.start_freq, self.stop_freq)
                        self.log_threadsafe(
                            f"Saved measurement for state {state}", "success")

                        self.vna.start_index = None
                        self.vna.stop_index = None
                except ValueError:
                    self.log_threadsafe(
                        "[ERROR] Enter valid integers.", "error")

            elif mode == 'all_states':
                try:
                    bits = int(self.bits_entry.get())
                    states = int(self.states_entry.get())
                    if states > 2 ** bits:
                        self.log_threadsafe(
                            f"[ERROR] Invalid: Max states is {2**bits}", "error")
                    else:
                        self.log_threadsafe(
                            f"All states mode: {states} states for {bits}-bit", "info")
                        os.makedirs(folder_name, exist_ok=True)

                        for idx, state in enumerate(range(states)):
                            self.fpga.trigger_state(state)
                            self.log_threadsafe(
                                f"[TRIGGER] Triggered state {state}", "success")
                            time.sleep(self.delay)
                            self.vna.save_traces(
                                state, folder_name, self.start_freq, self.stop_freq)
                            self.log_threadsafe(
                                f"Saved measurement for state {state}", "success")

                        self.vna.start_index = None
                        self.vna.stop_index = None
                except ValueError:
                    self.log_threadsafe("[ERROR] Invalid value added", "error")

        finally:
            # Always execute this when test finishes (normally or with exception)
            self.test_running = False
            self.log_threadsafe("Test completed", "success")

    def log(self, message, tag="info"):
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S] ")
        self.output_box.configure(state="normal")
        self.output_box.insert("end", timestamp, "timestamp")
        self.output_box.insert("end", message + "\n", tag)
        self.output_box.see("end")
        self.output_box.configure(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = MackIITMGUI(root)
    root.mainloop()
