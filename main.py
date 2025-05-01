import tkinter as tk
import csv
from tkinter import ttk, filedialog
import os
import datetime
import time

from fpga import FPGA
from vna import VNA


class MackIITMGUI:
    def __init__(self, root):
        self.delay = 2

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

        self.create_widgets()
        self.log("Welcome! Please initialize system.")

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

        # Frame 1 - Connect button
        self.frame1 = ttk.Frame(self.content_frame)
        self.frame1.pack(pady=10)
        self.connect_button = ttk.Button(
            self.frame1, text="CONNECT", command=self.connect_devices)
        self.connect_button.pack(anchor="center")

        # Frame 2 (hidden until connect)
        self.frame2 = ttk.Frame(self.content_frame)
        self.setup_frame2()

        # Frame 3 (radio buttons + dynamic content)
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

    def setup_frame2(self):
        frame_content = ttk.Frame(self.frame2)
        frame_content.pack(fill="x", expand=True)

        for i in range(6):
            frame_content.columnconfigure(i, weight=1)

        self.start_freq_entry = self.add_labeled_entry(
            frame_content, "Start Frequency", 0, 0)
        self.stop_freq_entry = self.add_labeled_entry(
            frame_content, "Stop Frequency", 0, 2)
        self.points_entry = self.add_labeled_entry(
            frame_content, "Measuring Points", 0, 4)

        config_button = ttk.Button(
            frame_content, text="CONFIGURE", command=self.configure_measurement)
        config_button.grid(row=0, column=6, padx=10)

    def setup_frame3(self):
        self.radio_panel = ttk.Frame(self.frame3)
        self.radio_panel.pack(fill="x", expand=True)

        radio_frame = ttk.Frame(self.radio_panel)
        radio_frame.pack(side="left", anchor="nw", padx=20)

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

    def setup_single_frame(self):
        container = ttk.Frame(self.single_frame)
        container.pack(expand=True)
        self.n_entry = self.add_labeled_entry(container, "Number of Bits:")
        self.state_entry = self.add_labeled_entry(
            container, "State for Transmission:")
        ttk.Button(container, text="Trigger", command=lambda: self.start_test(
            'single_state')).pack(pady=10)

    def setup_all_state_frame(self):
        container = ttk.Frame(self.all_state_frame)
        container.pack(expand=True)
        self.bits_entry = self.add_labeled_entry(
            container, "Bits for Phase Shifter:")
        self.states_entry = self.add_labeled_entry(
            container, "Number of States:")
        ttk.Button(container, text="Trigger",
                   command=lambda: self.start_test('all_states')).pack(pady=10)

    def setup_upload_frame(self):
        container = ttk.Frame(self.upload_frame)
        container.pack(expand=True)
        ttk.Button(container, text="Upload CSV",
                   command=self.upload_csv).pack(pady=5)
        ttk.Label(container, textvariable=self.csv_label_var,
                  font=("Arial", 9, "italic")).pack(pady=5)
        ttk.Button(container, text="Trigger", command=lambda: self.start_test(
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
        self.fpga.initialize_fpga()
        self.vna.initialize_vna()

        if self.fpga.connected:
            self.log("FPGA Successfully Connected", "success")
        else:
            self.log("[ERROR] FPGA Not Connected", "error")

        if self.vna.connected:
            self.log("VNA Successfully Connected", "success")
        else:
            self.log("[ERROR] VNA Not Connected", "error")

        if self.fpga.connected and self.vna.connected:
            self.connect_button.state(["disabled"])
            self.frame2.pack(fill="x", pady=10)

    def configure_measurement(self):
        try:
            start_freq = float(self.start_freq_entry.get())
            stop_freq = float(self.stop_freq_entry.get())
            int(self.points_entry.get())

            freq_range, _ = self.vna.get_trace_info()

            if freq_range[0] <= start_freq < stop_freq <= freq_range[-1]:
                self.frame3.pack()
                self.start_freq = start_freq
                self.stop_freq = stop_freq
                self.log(
                    "Measurement configuration successful. Choose a transmission mode.", "success")
            else:
                self.log(
                    "[ERROR] Frequency range not within sweep range", "error")
            # self.frame3.pack()
            # self.frame3.pack(fill="x", pady=5)
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

    def start_test(self, mode):
        folder_name = datetime.datetime.now().strftime("measurement_%Y-%m-%d_%H-%M-%S")
        if mode == 'csv':
            if self.file_path:
                self.log(self.file_path)
                with open(self.file_path, 'r') as f:
                    csv_data = csv.reader(f)
                    states = []
                    for i in list(csv_data)[0]:
                        try:
                            states.append(int(i))
                        except:
                            pass
                    print(states)
                    os.makedirs(folder_name, exist_ok=True)

                    for state in states:
                        self.fpga.trigger_state(state)
                        self.log(
                            f"[TRIGGER] Triggered state {state}", "success")
                        time.sleep(self.delay)
                        self.vna.save_traces(
                            state, folder_name, self.start_freq, self.stop_freq)
                        self.log(
                            f"Saved measurement for state {state}", "success")

                    self.vna.start_index = None
                    self.vna.stop_index = None
            else:
                self.log("[ERROR] Please upload a CSV file first", 'error')

        elif mode == 'single_state':
            try:
                n = int(self.n_entry.get())
                state = int(self.state_entry.get())
                if state >= 2 ** n:
                    self.log(f"[ERROR] Invalid: State exceeds 2^{n}", "error")
                else:
                    os.makedirs(folder_name, exist_ok=True)
                    self.log(f"Transmitting State {state} (n={n})", "info")
                    self.fpga.trigger_state(state)
                    self.log(
                        f"[TRIGGER] Triggered state {state}", "success")

                    time.sleep(self.delay)

                    self.vna.save_traces(
                        state, folder_name, self.start_freq, self.stop_freq)
                    self.log(
                        f"Saved measurement for state {state}", "success")

                    self.vna.start_index = None
                    self.vna.stop_index = None
            except ValueError:
                self.log("[ERROR] Enter valid integers.", "error")

        elif mode == 'all_states':
            try:
                bits = int(self.bits_entry.get())
                states = int(self.states_entry.get())
                if states > 2 ** bits:
                    self.log(
                        f"[ERROR] Invalid: Max states is {2**bits}", "error")
                else:
                    self.log(
                        f"All states mode: {states} states for {bits}-bit", "info")
                    os.makedirs(folder_name, exist_ok=True)
                    for state in range(states):
                        self.fpga.trigger_state(state)
                        self.log(
                            f"[TRIGGER] Triggered state {state}", "success")
                        time.sleep(self.delay)
                        self.vna.save_traces(
                            state, folder_name, self.start_freq, self.stop_freq)
                        self.log(
                            f"Saved measurement for state {state}", "success")

                    self.vna.start_index = None
                    self.vna.stop_index = None
            except ValueError:
                self.log("[ERROR] Invalid value added", "error")

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
