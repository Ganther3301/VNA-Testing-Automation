import json
import math
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import datetime
import time
import threading
import pandas as pd
import numpy as np

from fpga import FPGA
from vna import VNA


class MackIITMGUI:
    def __init__(self, root):
        self.delay = 2  # Default delay in seconds

        self.root = root
        self.root.title("MACK IITM TESTING SYSTEM")
        self.root.geometry("900x600")
        self.root.minsize(700, 500)

        self.root.rowconfigure(2, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.fpga = FPGA()
        self.vna = VNA()

        self.file_path = ""
        self.mode_var = tk.StringVar(value="")
        self.device_type_var = tk.StringVar(value="")
        self.test_running = False

        self.phase_file_path = ""
        self.amp_file_path = ""
        self.analysis_save_path = ""

        self.title_label = ttk.Label(
            self.root,
            text="MACK IITM TESTING SYSTEM",
            font=("Times New Roman", 16, "bold"),
        )
        self.title_label.grid(row=0, column=0, pady=(10, 0))

        self.create_widgets()
        self.create_console()
        self.log("Welcome! Please ensure VNA is connected to before proceeding.")

        self.pause_event = threading.Event()
        self.cancel_event = threading.Event()

        self.trigger_states = {
            ("Receiver", "Phase Shifter"): (0, 128),
            ("Receiver", "Attenuator"): (0, 128),
            ("Transmitter", "Phase Shifter"): (0, 128),
            ("Transmitter", "Attenuator"): (0, 128),
        }

    def create_widgets(self):
        self.tab_control = ttk.Notebook(self.root)
        self.tab_control.grid(row=1, column=0, sticky="nsew")

        self.testing_tab = ttk.Frame(self.tab_control)
        self.analysis_tab = ttk.Frame(self.tab_control)

        self.tab_control.add(self.testing_tab, text="Testing")
        self.tab_control.add(self.analysis_tab, text="Analysis")

        # Testing Tab Content
        self.main_container = self.testing_tab
        self.main_container.rowconfigure(0, weight=1)
        self.main_container.columnconfigure(0, weight=1)

        self.content_frame = ttk.Frame(self.main_container)
        self.content_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=10)

        self.vna_connect_frame = ttk.Frame(self.content_frame)
        self.vna_connect_button = ttk.Button(
            self.vna_connect_frame,
            text="Connect To VNA",
            command=self.connect_vna,
        )
        self.vna_connect_button.pack(anchor="center")
        self.vna_connect_frame.pack()

        self.device_select_frame = ttk.Frame(self.content_frame)
        self.setup_device_select_frame()

        self.frame2 = ttk.Frame(self.content_frame)
        self.setup_frame2()

        self.config_frame = ttk.Frame(self.content_frame)
        self.setup_config_frame()

        self.calib_frame = ttk.Frame(self.content_frame)
        self.setup_calib_frame()

        self.frame3 = ttk.Frame(self.content_frame)
        self.setup_frame3()

        self.amplifier_test_frame = ttk.Frame(self.content_frame)
        self.setup_amplifier_frame()

        # Analysis Tab Content
        analysis_container = ttk.Frame(self.analysis_tab)
        analysis_container.pack(fill="both", expand=True)

        # Inner frame for centering content
        inner_frame = ttk.Frame(analysis_container)
        inner_frame.pack(anchor="center", pady=20)

        # Row 0: Equibits label and entry
        ttk.Label(inner_frame, text="Equibits", font=("Arial", 10)).grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=5
        )
        self.equibits_entry = ttk.Entry(inner_frame, width=40)
        self.equibits_entry.grid(row=0, column=1, sticky="ew", pady=5)

        # Row 1: Upload Phase CSV Button
        ttk.Button(
            inner_frame, text="Upload Phase CSV", command=self.upload_phase_csv
        ).grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)

        # Row 2: Phase file label
        self.phase_csv_label = ttk.Label(
            inner_frame,
            text="No phase file selected",
            font=("Arial", 9, "italic"),
        )
        self.phase_csv_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=2)

        # Row 3: Upload Amplitude CSV Button
        ttk.Button(
            inner_frame, text="Upload Amplitude CSV", command=self.upload_amp_csv
        ).grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)

        # Row 4: Amplitude file label
        self.amp_csv_label = ttk.Label(
            inner_frame,
            text="No amplitude file selected",
            font=("Arial", 9, "italic"),
        )
        self.amp_csv_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=2)

        # Row 5: Select save location button
        ttk.Button(
            inner_frame, text="Select Save Location", command=self.select_save_location
        ).grid(row=5, column=0, columnspan=2, sticky="ew", pady=5)

        # Row 6: Save location label
        self.save_location_label = ttk.Label(
            inner_frame,
            text="No save location selected",
            font=("Arial", 9, "italic"),
        )
        self.save_location_label.grid(row=6, column=0, columnspan=2, sticky="w", pady=2)

        # Row 7: Run analysis button
        ttk.Button(inner_frame, text="Run Analysis", command=self.run_analysis).grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=15
        )

    def upload_amp_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.amp_file_path = file_path
            filename = os.path.basename(file_path)
            self.amp_csv_label.config(text=f"Amplitude file: {filename}")
            self.log(f"[Analysis] Amplitude CSV uploaded: {filename}", "info")
        else:
            self.amp_csv_label.config(text="No CSV file selected")
            self.log("[Analysis] Amplitude CSV upload cancelled.", "warning")

    def upload_phase_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.phase_file_path = file_path
            filename = os.path.basename(file_path)
            self.phase_csv_label.config(text=f"Phase file: {filename}")
            self.log(f"[Analysis] Phase CSV uploaded: {filename}", "info")
        else:
            self.phase_csv_label.config(text="No phase file selected")
            self.log("[Analysis] Phase CSV upload cancelled.", "warning")

    def select_save_location(self):
        """Select directory to save analysis results"""
        save_dir = filedialog.askdirectory(
            title="Select folder to save analysis results"
        )
        if save_dir:
            self.analysis_save_path = save_dir
            folder_name = (
                os.path.basename(save_dir) if os.path.basename(save_dir) else save_dir
            )
            self.save_location_label.config(text=f"Save location: {folder_name}")
            self.log(f"[Analysis] Save location selected: {save_dir}", "info")
        else:
            self.save_location_label.config(text="No save location selected")
            self.log("[Analysis] Save location selection cancelled.", "warning")

    def run_analysis(self):
        # Validate required fields
        try:
            equibits = self.equibits_entry.get().strip()
            amp_analysis = True
            if not equibits.isdigit():
                self.log("[ERROR] Equibits must be a positive integer.", "error")
                return

            if not self.phase_file_path:
                self.log("[ERROR] Please upload a phase CSV file.", "error")
                return

            if not self.amp_file_path:
                amp_analysis = False

            if not self.analysis_save_path:
                self.log("[ERROR] Please select a save location.", "error")
                return

            self.log("[INFO] Starting analysis...", "info")

            trace_data = pd.read_csv(
                # "/home/ganther/Hithesh/Projects/MACK/VNA_automation/results/measurements with report/15.5-17.5_Trc3.csv",
                # "/home/ganther/Hithesh/Projects/MACK/VNA_automation/results/measurement 201 points/15.5-17.5_Trc6.csv",
                self.phase_file_path,
                index_col=0,
            )

            if amp_analysis:
                amp_data = pd.read_csv(
                    # "/home/ganther/Hithesh/Projects/MACK/VNA_automation/results/measurements with report/15.5-17.5_Trc3.csv",
                    # "/home/ganther/Hithesh/Projects/MACK/VNA_automation/results/measurement 201 points/15.5-17.5_Trc6.csv",
                    self.amp_file_path,
                    index_col=0,
                )
                re_arr_amp = amp_data.copy()

            equi_bits = int(self.equibits_entry.get())

            # Adjust phase relative to first value
            base_data = trace_data - trace_data.iloc[0]
            base_data = base_data.where(base_data >= 0, base_data + 360)
            base_data.to_excel(
                f"{self.analysis_save_path}/Analysis_{equi_bits}.xlsx",
                sheet_name="positive_converted",
            )

            # Ideal reference values
            one_angle = 360 / 2**equi_bits
            ideal = [i * one_angle for i in range(2**equi_bits)]  # C in MATLAB

            def process_it(bd):
                C = np.array(ideal)
                Array4_column = np.array(bd)
                z = []
                O_column = []

                for k in range(len(C)):
                    z1 = C[k] - Array4_column
                    min_abs_diff = np.min(np.abs(z1))
                    z.append(min_abs_diff)
                    indices_with_min = np.where(np.abs(z1) == min_abs_diff)[0]
                    min_index = np.min(indices_with_min)
                    # MATLAB is 1-based indexing
                    O_column.append(int(min_index) + 1)

                re_arr = list()
                for i in O_column:
                    re_arr.append(bd.iloc[i - 1])

                print(f"Max z: {max(z)}, Min z: {min(z)}")
                print(O_column)
                return pd.DataFrame(re_arr), O_column

            # Method 1: Process all columns and store re_arranged in a dictionary
            re_arranged = {}
            rmse_values = {}
            max_min_errors = {}
            ideal_df = pd.DataFrame(ideal)

            for i, column in enumerate(base_data.columns):
                print(f"Processing column: {column}")

                # Process the column
                fixed, ocol = process_it(base_data[column])
                if amp_analysis:
                    for j, col in enumerate(ocol):
                        print(col)
                        re_arr_amp.iloc[j, i] = amp_data.iloc[col - 1, i]

                # Calculate RMSE
                diff = ideal_df - fixed
                diff_squared = diff**2
                avg = diff_squared.values.mean()
                rmse = math.sqrt(avg)

                # Store re_arranged
                re_arranged[column] = fixed.iloc[
                    :, 0
                ].values  # Extract the series from DataFrame
                rmse_values[column] = rmse
                max_min_errors[column] = {
                    "max_error": diff.max()[0],
                    "min_error": diff.min()[0],
                }

                print(f"RMSE for {column}: {rmse}")
                print("-" * 50)

            max_rms_min = {}

            for col in rmse_values.keys():
                max_rms_min[col] = [
                    max_min_errors[col]["max_error"],
                    rmse_values[col],
                    max_min_errors[col]["min_error"],
                ]

            max_rms_min_df = pd.DataFrame(max_rms_min)
            max_rms_min_df.to_excel(
                f"{self.analysis_save_path}/PS_MAX_RMS_MIN_{equi_bits}.xlsx"
            )
            re_arranged_df = pd.DataFrame(re_arranged)

            with pd.ExcelWriter(
                f"{self.analysis_save_path}/Analysis_{equi_bits}.xlsx",
                engine="openpyxl",
                mode="a",
                if_sheet_exists="replace",
            ) as writer:
                re_arranged_df.to_excel(writer, sheet_name="re_arranged")

            with pd.ExcelWriter(
                f"{self.analysis_save_path}/PS_MAX_RMS_MIN_{equi_bits}.xlsx",
                engine="openpyxl",
                mode="a",
                if_sheet_exists="replace",
            ) as writer:
                # pd.DataFrame(rmse_values).to_excel(writer, sheet_name="RMS")
                pd.Series(rmse_values).to_excel(writer, sheet_name="RMS")
                # re_arranged_df.to_excel(writer, sheet_name="re_arranged")

            if amp_analysis:
                re_arr_amp.to_excel(f"{self.analysis_save_path}/AMP_{equi_bits}.xlsx")

            self.log(f"Equibits: {equibits}", "info")
            self.log(f"Phase file: {os.path.basename(self.phase_file_path)}", "info")
            self.log(f"Save location: {self.analysis_save_path}", "info")

            # Here you would implement your analysis logic
            self.log("[INFO] Analysis completed successfully!", "success")
        except Exception as e:
            self.log(
                "[ERROR] System crashed while analyzing. Please ensure the correct files are added.",
                "error",
            )
            self.log(f"{e}", "error")

    def create_console(self):
        # Console shared by both tabs
        self.console_frame = ttk.Frame(self.root, padding=10)
        self.console_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))

        self.console_frame.configure(height=150)
        self.console_frame.grid_propagate(False)

        output_frame = ttk.Frame(self.console_frame)
        output_frame.pack(fill="both", expand=True)
        output_frame.rowconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)

        self.output_box = tk.Text(
            output_frame, wrap="word", state="disabled", height=8, font=("Consolas", 10)
        )
        self.output_box.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            output_frame, orient="vertical", command=self.output_box.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.output_box.config(yscrollcommand=scrollbar.set)

        self.style_log_tags()

    def log(self, message, tag="info"):
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S] ")
        self.output_box.configure(state="normal")
        self.output_box.insert("end", timestamp, "timestamp")
        self.output_box.insert("end", message + "\n", tag)
        self.output_box.see("end")
        self.output_box.configure(state="disabled")

    def style_log_tags(self):
        self.output_box.tag_configure("info", foreground="blue")
        self.output_box.tag_configure(
            "error", foreground="red", font=("Consolas", 10, "bold")
        )
        self.output_box.tag_configure("success", foreground="green")
        self.output_box.tag_configure("warning", foreground="orange")
        self.output_box.tag_configure(
            "timestamp", foreground="gray", font=("Consolas", 9, "italic")
        )

    def on_device_type_change(self):
        device_type = self.device_type_var.get()
        self.device_type = device_type

        self.frame3.pack_forget()
        self.amplifier_test_frame.pack_forget()
        self.ku_trm_options_frame.pack_forget()

        if device_type == "amplifier":
            self.log("Amplifier mode selected", "info")
            self.device_select_frame.pack(pady=10)
        elif device_type == "phase_shifter":
            self.log("Phase Shifter mode selected", "info")
            self.device_select_frame.pack(pady=10)
        elif device_type == "ku_trm":
            self.log("KU TRM Module selected", "info")
            self.device_select_frame.pack(pady=10)
            self.ku_trm_options_frame.pack(pady=5)
        else:
            self.log("Please select a device type", "warning")

        self.connect_button.state(["!disabled"])

    def setup_device_select_frame(self):
        self.device_type_frame = ttk.Frame(self.device_select_frame)
        self.device_type_frame.pack(pady=10)
        ttk.Label(self.device_type_frame, text="Select Device Type:").pack(
            side="left", padx=(0, 10)
        )

        device_types = {
            "Amplifier": "amplifier",
            "Phase Shifter": "phase_shifter",
            "KU TRM Module": "ku_trm",
        }
        for text, value in device_types.items():
            ttk.Radiobutton(
                self.device_type_frame,
                text=text,
                variable=self.device_type_var,
                value=value,
                command=self.on_device_type_change,
            ).pack(side="left", padx=5)

        self.connect_button = ttk.Button(
            self.device_select_frame, text="CONNECT", command=self.connect_devices
        )
        self.connect_button.pack(anchor="center")

        self.ku_trm_options_frame = ttk.Frame(self.device_select_frame)

        self.role_var = tk.StringVar(value="Transmitter")
        self.role_dropdown = ttk.Combobox(
            self.ku_trm_options_frame,
            textvariable=self.role_var,
            values=["Transmitter", "Receiver"],
            state="readonly",
        )

        self.module_type_var = tk.StringVar(value="Phase Shifter")
        self.module_type_dropdown = ttk.Combobox(
            self.ku_trm_options_frame,
            textvariable=self.module_type_var,
            values=["Phase Shifter", "Attenuator"],
            state="readonly",
        )

    def setup_amplifier_frame(self):
        """Create special UI elements for Amplifier mode"""

        # Add amplifier-specific controls
        test_frame = ttk.Frame(self.amplifier_test_frame)
        test_frame.pack(fill="x", expand=True)

        ttk.Button(
            test_frame, text="Save Traces", command=self.run_amplifier_test
        ).pack(pady=10)

    def setup_calib_frame(self):
        frame_content = ttk.Frame(self.calib_frame)
        frame_content.pack(fill="both", expand=True, padx=10, pady=10)

        # Configure grid weights for responsive layout
        frame_content.columnconfigure(1, weight=1)
        for i in range(4):
            frame_content.rowconfigure(i, weight=1)

        # Path selection section
        ttk.Label(
            frame_content,
            text="Save Path:",
            font=("TkDefaultFont", 10, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        ttk.Label(frame_content, text="Path:").grid(
            row=1, column=0, sticky="w", padx=(0, 5), pady=5
        )

        self.calib_path_var = tk.StringVar(value="")
        self.calib_path_entry = ttk.Entry(
            frame_content, textvariable=self.calib_path_var, width=50
        )
        self.calib_path_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        self.browse_button = ttk.Button(
            frame_content, text="Browse...", command=self.browse_calib_path
        )
        self.browse_button.grid(row=1, column=2, padx=(5, 0), pady=5)

        # Instructions section
        instruction_frame = ttk.LabelFrame(frame_content, text="Instructions")
        instruction_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=20)
        instruction_frame.columnconfigure(0, weight=1)

        instruction_text = "Click 'Next' after selecting folder to save in"
        ttk.Label(
            instruction_frame,
            text=instruction_text,
            font=("TkDefaultFont", 9),
            foreground="blue",
        ).pack(padx=10, pady=10)

        # Save button section
        button_frame = ttk.Frame(frame_content)
        button_frame.grid(row=3, column=0, columnspan=3, pady=20)

        self.save_ref_button = ttk.Button(
            button_frame,
            text="Save Reference Line",
            command=self.save_ref_line,
            style="Accent.TButton",
        )

        self.save_ref_button.pack()

        self.next_button = ttk.Button(
            button_frame,
            text="Next",
            command=self.go_next,
            style="Accent.TButton",
        )

        self.next_button.pack()

    def browse_calib_path(self):
        """Open file dialog to select calibration save path"""
        from tkinter import filedialog

        # Ask for directory to save calibration files
        directory = filedialog.askdirectory(
            title="Select Directory to Save Data",
            initialdir=self.calib_path_var.get() if self.calib_path_var.get() else ".",
        )

        if directory:
            self.calib_path_var.set(directory)

    def save_ref_line(self):
        save_path = self.calib_path_var.get().strip()

        if not save_path:
            from tkinter import messagebox

            messagebox.showerror("Error", "Please select a folder to save data.")
            return

        folder_path = f"{save_path}/ref_lines_{self.start_freq}-{self.stop_freq}"
        os.makedirs(folder_path, exist_ok=True, mode=0o777)
        self.vna.save_traces_amp(folder_path, self.start_freq, self.stop_freq)
        self.log("Reference values saved", "success")

    def go_next(self):
        """Save calibration data to the specified path"""
        save_path = self.calib_path_var.get().strip()

        if not save_path:
            from tkinter import messagebox

            messagebox.showerror("Error", "Please select a folder to save data.")
            return

        try:
            self.save_path = save_path
            print(self.save_path)
            self.calib_frame.pack_forget()
            self.device_select_frame.pack(fill="x", pady=10)

        except Exception as e:
            from tkinter import messagebox

            messagebox.showerror("Error", f"Failed to save calibration data:\n{str(e)}")

    def get_calib_path(self):
        """Returns the selected calibration save path"""
        return self.calib_path_var.get().strip()

    def run_amplifier_test(self):
        """Run the amplifier test in a separate thread"""
        if self.test_running:
            self.log("[ERROR] A test is already running", "error")
            return

        self.test_running = True
        threading.Thread(target=self._run_amplifier_test, daemon=True).start()

    def _run_amplifier_test(self):
        """Perform the actual amplifier test"""
        folder_name = f"{self.save_path}/{datetime.datetime.now().strftime('measurement_%Y-%m-%d_%H-%M-%S')}"
        os.makedirs(folder_name, exist_ok=True, mode=0o777)
        try:
            self.vna.save_traces_amp(
                folder_name, self.start_freq, self.stop_freq
            )  # TODO : UNCOMMENT

            self.log_threadsafe("Amplifier data successfully saved", "success")
        except Exception as e:
            self.log_threadsafe(f"[ERROR] Amplifier test failed: {str(e)}", "error")
        finally:
            self.test_running = False

    def setup_frame2(self):
        frame_content = ttk.Frame(self.frame2)
        frame_content.pack(fill="x", expand=True)

        for i in range(6):
            frame_content.columnconfigure(i, weight=1)

        self.start_freq_entry = self.add_labeled_entry(
            frame_content, "Start Frequency (GHz)", 1, 0
        )
        self.stop_freq_entry = self.add_labeled_entry(
            frame_content, "Stop Frequency (GHz)", 1, 2
        )

        self.start_freq_entry.bind("<KeyRelease>", self.hide_frame3_on_change)
        self.stop_freq_entry.bind("<KeyRelease>", self.hide_frame3_on_change)
        self.config_button = ttk.Button(
            frame_content, text="CONFIGURE", command=self.configure_measurement
        )
        self.config_button.grid(row=1, column=6, padx=10)

        back_button = ttk.Button(
            frame_content, text="Back", command=self.go_back_to_config
        )
        if self.vna.get_vendor_name() == "Keysight":
            back_button.grid(row=0, column=0, sticky="w", pady=(0, 10), padx=(0, 5))

    def setup_frame3(self):
        self.radio_panel = ttk.Frame(self.frame3)
        self.radio_panel.pack(fill="x", expand=True)

        radio_frame = ttk.Frame(self.radio_panel)
        radio_frame.pack(side="left", anchor="nw", padx=20)

        # Add delay configuration box
        delay_frame = ttk.Frame(self.radio_panel)
        delay_frame.pack(side="right", anchor="ne", padx=20)

        ttk.Label(delay_frame, text="Delay (seconds):").pack(side="left", padx=(0, 5))
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
            "Upload CSV": "csv",
        }

        for text, value in modes.items():
            ttk.Radiobutton(
                radio_frame,
                text=text,
                variable=self.mode_var,
                value=value,
                command=self.show_selected_mode,
            ).pack(anchor="w", pady=2)

        self.setup_single_frame()
        self.setup_all_state_frame()
        self.setup_upload_frame()

    def setup_config_frame(self):
        frame_content = ttk.Frame(self.config_frame)
        frame_content.pack(fill="x", expand=True, padx=10, pady=10)

        # Configure grid weights
        for i in range(6):
            frame_content.columnconfigure(i, weight=1)
        for i in range(8):  # Increased rows for additional content
            frame_content.rowconfigure(i, weight=1)

        # Frequency and measurement parameters
        self.config_start_freq_entry = self.add_labeled_entry(
            frame_content, "Sweep Start Frequency (GHz)", 0, 0
        )
        self.config_stop_freq_entry = self.add_labeled_entry(
            frame_content, "Sweep Stop Frequency (GHz)", 0, 2
        )
        self.config_average_entry = self.add_labeled_entry(
            frame_content, "Average", 0, 4
        )
        self.config_sweep_points_entry = self.add_labeled_entry(
            frame_content, "Sweep Points", 1, 0
        )

        # Port selection with number fields
        port_frame = ttk.LabelFrame(frame_content, text="Port Configuration")
        port_frame.grid(row=2, column=0, columnspan=6, sticky="ew", pady=10)

        ttk.Label(port_frame, text="Port 1:").grid(row=0, column=0, padx=5, pady=5)
        self.port1_var = tk.StringVar(value="1")
        self.port1_entry = ttk.Entry(port_frame, textvariable=self.port1_var, width=5)
        self.port1_entry.grid(row=0, column=1, padx=5, pady=5)
        self.port1_entry.bind("<KeyRelease>", self.update_sparams)

        ttk.Label(port_frame, text="Port 2:").grid(row=0, column=2, padx=5, pady=5)
        self.port2_var = tk.StringVar(value="2")
        self.port2_entry = ttk.Entry(port_frame, textvariable=self.port2_var, width=5)
        self.port2_entry.grid(row=0, column=3, padx=5, pady=5)
        self.port2_entry.bind("<KeyRelease>", self.update_sparams)

        # Initialize port list
        self.port_vars = [self.port1_var, self.port2_var]
        self.port_entries = [self.port1_entry, self.port2_entry]

        # S-parameter selection frame
        self.sparams_frame = ttk.LabelFrame(frame_content, text="S-Parameters")
        self.sparams_frame.grid(row=3, column=0, columnspan=6, sticky="ew", pady=10)

        # Initialize S-parameter variables dictionary
        self.sparam_vars = {}

        # Create initial S-parameter checkboxes
        self.update_sparams()

        # Buttons
        button_frame = ttk.Frame(frame_content)
        button_frame.grid(row=4, column=0, columnspan=6, pady=10)

        self.load_config_button = ttk.Button(
            button_frame, text="Load Config", command=self.load_config
        )
        self.setup_config_button = ttk.Button(
            button_frame, text="Configure", command=self.configure_vna
        )
        self.skip_button = ttk.Button(
            button_frame, text="Skip", command=self.skip_calib
        )
        self.load_config_button.pack(side="left", padx=10)
        self.setup_config_button.pack(side="left", padx=10)
        self.skip_button.pack(side="left", padx=10)

    def go_back_to_config(self):
        # Hide all frames in the testing tab
        for frame in [
            self.vna_connect_frame,
            self.device_select_frame,
            self.frame2,
            self.frame3,
            self.calib_frame,
            self.amplifier_test_frame,
        ]:
            frame.pack_forget()

        # Show only the config frame
        self.config_frame.pack(fill="x", pady=10)
        self.device_type_var.set("")
        self.connect_button.state(["!disabled"])

    def load_config(self):
        """Load configuration from a JSON file and populate the form fields"""
        try:
            # Open file dialog to select JSON file
            file_path = filedialog.askopenfilename(
                title="Select Configuration File",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            )

            if not file_path:
                return  # User cancelled the dialog

            # Read and parse the JSON file
            with open(file_path, "r") as file:
                config_data = json.load(file)

            # Populate the configuration fields
            if "start_frequency" in config_data and hasattr(
                self, "config_start_freq_entry"
            ):
                self.config_start_freq_entry.delete(0, tk.END)
                self.config_start_freq_entry.insert(
                    0, str(config_data["start_frequency"])
                )

            if "stop_frequency" in config_data and hasattr(
                self, "config_stop_freq_entry"
            ):
                self.config_stop_freq_entry.delete(0, tk.END)
                self.config_stop_freq_entry.insert(
                    0, str(config_data["stop_frequency"])
                )

            if "average" in config_data and hasattr(self, "config_average_entry"):
                self.config_average_entry.delete(0, tk.END)
                self.config_average_entry.insert(0, str(config_data["average"]))

            if "sweep_points" in config_data and hasattr(
                self, "config_sweep_points_entry"
            ):
                self.config_sweep_points_entry.delete(0, tk.END)
                self.config_sweep_points_entry.insert(
                    0, str(config_data["sweep_points"])
                )

            # Update port configurations if present
            if "port1" in config_data and hasattr(self, "port1_var"):
                self.port1_var.set(str(config_data["port1"]))

            if "port2" in config_data and hasattr(self, "port2_var"):
                self.port2_var.set(str(config_data["port2"]))

            # Update S-parameter selections if present
            if "sparameters" in config_data and hasattr(self, "sparam_vars"):
                # First, uncheck all current S-parameters
                for var in self.sparam_vars.values():
                    var.set(False)

                # Then check the ones specified in the config
                for sparam in config_data["sparameters"]:
                    if sparam in self.sparam_vars:
                        self.sparam_vars[sparam].set(True)

            # Update S-parameters display in case ports changed
            self.update_sparams()

            messagebox.showinfo("Success", f"Configuration loaded from {file_path}")

        except FileNotFoundError:
            messagebox.showerror("Error", "Configuration file not found.")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON file format.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")

    def save_config(self):
        """Save current configuration to a JSON file (optional companion function)"""
        try:
            # Collect current configuration
            config_data = {}

            if hasattr(self, "config_start_freq_entry"):
                config_data["start_frequency"] = self.config_start_freq_entry.get()

            if hasattr(self, "config_stop_freq_entry"):
                config_data["stop_frequency"] = self.config_stop_freq_entry.get()

            if hasattr(self, "config_average_entry"):
                config_data["average"] = self.config_average_entry.get()

            if hasattr(self, "config_sweep_points_entry"):
                config_data["sweep_points"] = self.config_sweep_points_entry.get()

            if hasattr(self, "port1_var"):
                config_data["port1"] = self.port1_var.get()

            if hasattr(self, "port2_var"):
                config_data["port2"] = self.port2_var.get()

            # Get selected S-parameters
            if hasattr(self, "sparam_vars"):
                selected_sparams = [
                    sparam for sparam, var in self.sparam_vars.items() if var.get()
                ]
                config_data["sparameters"] = selected_sparams

            # Open file dialog to save JSON file
            file_path = filedialog.asksaveasfilename(
                title="Save Configuration File",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            )

            if not file_path:
                return  # User cancelled the dialog

            # Write the JSON file
            with open(file_path, "w") as file:
                json.dump(config_data, file, indent=4)

            messagebox.showinfo("Success", f"Configuration saved to {file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")

    def skip_calib(self):
        self.config_frame.pack_forget()
        self.frame2.pack(fill="x", pady=10)
        # self.calib_frame.pack()

    def update_sparams(self, event=None):
        """Update S-parameter checkboxes based on current port values"""
        # Clear existing checkboxes
        for widget in self.sparams_frame.winfo_children():
            widget.destroy()

        self.sparam_vars.clear()

        # Get current port values
        ports = []
        for port_var in self.port_vars:
            try:
                port_val = port_var.get().strip()
                if port_val:
                    ports.append(port_val)
            except:
                continue

        if len(ports) < 2:
            return

        # Generate all possible S-parameter combinations
        sparams = []
        for i in ports:
            for j in ports:
                sparams.append(f"S{i}{j}")

        # Create table header
        ttk.Label(
            self.sparams_frame, text="Parameter", font=("TkDefaultFont", 9, "bold")
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ttk.Label(
            self.sparams_frame, text="dB", font=("TkDefaultFont", 9, "bold")
        ).grid(row=0, column=1, padx=10, pady=5)
        ttk.Label(
            self.sparams_frame, text="deg", font=("TkDefaultFont", 9, "bold")
        ).grid(row=0, column=2, padx=10, pady=5)

        # Create separator line
        separator = ttk.Separator(self.sparams_frame, orient="horizontal")
        separator.grid(row=1, column=0, columnspan=3, sticky="ew", pady=2)

        # Create checkboxes for each S-parameter in table format
        for idx, sparam in enumerate(sparams):
            sparam_lower = sparam.lower()
            row = idx + 2  # Start from row 2 (after header and separator)

            # S-parameter label
            ttk.Label(self.sparams_frame, text=sparam).grid(
                row=row, column=0, padx=10, pady=2, sticky="w"
            )

            # dB checkbox
            db_var_name = f"{sparam_lower}_db"
            self.sparam_vars[db_var_name] = tk.BooleanVar(value=False)
            db_checkbox = ttk.Checkbutton(
                self.sparams_frame, variable=self.sparam_vars[db_var_name]
            )
            db_checkbox.grid(row=row, column=1, padx=10, pady=2)

            # Degree checkbox
            deg_var_name = f"{sparam_lower}_deg"
            self.sparam_vars[deg_var_name] = tk.BooleanVar(value=False)
            deg_checkbox = ttk.Checkbutton(
                self.sparams_frame, variable=self.sparam_vars[deg_var_name]
            )
            deg_checkbox.grid(row=row, column=2, padx=10, pady=2)

    def get_selected_sparams(self):
        """Returns a dictionary of selected S-parameters and their format options"""
        selected = {}

        # Get unique S-parameter names
        sparams = set()
        for var_name in self.sparam_vars.keys():
            if var_name.endswith("_db") or var_name.endswith("_deg"):
                sparam_name = var_name.replace("_db", "").replace("_deg", "")
                sparams.add(sparam_name)

        # Check which formats are selected for each S-parameter
        print(self.sparam_vars)
        for i, sparam in enumerate(self.sparam_vars.keys()):
            # db_selected = self.sparam_vars.get(f"{sparam}_db", tk.BooleanVar()).get()
            # deg_selected = self.sparam_vars.get(f"{sparam}_deg", tk.BooleanVar()).get()
            status = self.sparam_vars.get(sparam, tk.BooleanVar()).get()

            # Only include if at least one format is selected
            if status:
                selected[f"{sparam}-Trc_{i + 1}"] = sparam.split("_")[1]

        print(selected)

        return selected

    def get_port_config(self):
        """Returns the list of configured ports"""
        ports = []
        for port_var in self.port_vars:
            try:
                port_val = port_var.get().strip()
                if port_val:
                    ports.append(int(port_val))
            except ValueError:
                continue
        return ports

    def configure_vna(self):
        try:
            start_freq = float(self.config_start_freq_entry.get())
            end_freq = float(self.config_stop_freq_entry.get())
            sweep_points = float(self.config_sweep_points_entry.get())
            avg = float(self.config_average_entry.get())

            params = self.get_selected_sparams()
            print(params)

            self.vna.write_command(
                f"SENS:FREQ:START {start_freq * 10**9}"
            )  # TODO: uncomment
            self.vna.write_command(f"SENS:FREQ:STOP {end_freq * 10**9}")
            self.vna.write_command(f"SENS:SWE:POIN {sweep_points}")
            self.vna.write_command(f"SENS:AVER:COUN {avg}")

            for para in params.keys():
                name = para.upper()
                parameter = para.split("-")[0].split("_")[0].upper()
                print(name, parameter)

                if params[para] == "db":
                    self.vna.create_trace(
                        name=f"{name} dB",
                        parameter=parameter,
                        unit="db",
                    )
                elif params[para] == "deg":
                    self.vna.create_trace(
                        name=f"{name} deg",
                        parameter=parameter,
                        unit="deg",
                    )

            self.config_frame.pack_forget()
            self.frame2.pack(fill="x", pady=10)
            # self.calib_frame.pack()

            self.log("VNA values set", "success")

        except ValueError:
            self.log("[ERROR] Enter Valid Inputs", "error")

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
        self.state_entry = self.add_labeled_entry(container, "State for Transmission:")
        ttk.Button(
            container,
            text="Trigger",
            command=lambda: self.start_test_thread("single_state"),
        ).pack(pady=10)

    def setup_all_state_frame(self):
        container = ttk.Frame(self.all_state_frame)
        container.pack(expand=True)
        self.bits_entry = self.add_labeled_entry(container, "Bits for Phase Shifter:")
        self.states_entry = self.add_labeled_entry(container, "Number of States:")
        ttk.Button(
            container,
            text="Trigger",
            command=lambda: self.start_test_thread("all_states"),
        ).pack(pady=10)
        ttk.Button(container, text="Pause", command=self.pause_test).pack(
            side="left", padx=5
        )
        ttk.Button(container, text="Cancel", command=self.cancel_test).pack(
            side="left", padx=5
        )

    def setup_upload_frame(self):
        container = ttk.Frame(self.upload_frame)
        container.pack(expand=True)
        self.n_bits_entry = self.add_labeled_entry(container, "Bits for Phase Shifter:")
        ttk.Button(container, text="Upload CSV", command=self.upload_csv).pack(pady=5)
        ttk.Label(
            container, textvariable=self.csv_label_var, font=("Arial", 9, "italic")
        ).pack(pady=5)
        ttk.Button(
            container, text="Trigger", command=lambda: self.start_test_thread("csv")
        ).pack(pady=5)
        ttk.Button(container, text="Pause", command=self.pause_test).pack(
            side="left", padx=5
        )
        ttk.Button(container, text="Cancel", command=self.cancel_test).pack(
            side="left", padx=5
        )

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

    def connect_vna(self):
        try:
            self.vna.initialize_vna()
        except Exception:
            # pass
            self.log_threadsafe(
                "[ERROR] Could not locate a VISA implementation", tag="error"
            )

        if self.vna.connected:
            self.log_threadsafe("VNA Successfully Connected", "success")
            self.log_threadsafe(
                f"Connected to a {self.vna.get_vendor_name()} VNA", "success"
            )

            self.vna_connect_button.state(["disabled"])

            if self.vna.get_vendor_name() == "Keysight":
                self.vna.write_command("INIT:CONT ON")
                self.config_frame.pack(fill="x", pady=10)
            else:
                # self.config_frame.pack(fill="x", pady=10)  # TODO: comment this
                self.frame2.pack(fill="x", pady=10)  # TODO: Uncomment this
        else:
            self.log_threadsafe("[ERROR] VNA Connection Failed", "error")

    def connect_devices(self):
        try:
            self.device_type
        except:
            self.log_threadsafe("[ERROR] Select one of the options", "error")
            return

        if self.device_type in ["phase_shifter", "ku_trm"]:
            self.fpga.initialize_fpga()

            if self.fpga.connected:
                self.log_threadsafe("FPGA Successfully Connected", "success")
            else:
                self.log_threadsafe("[ERROR] FPGA Not Connected", "error")

        if (
            self.fpga.connected
            and self.vna.connected
            and self.device_type in ["phase_shifter", "ku_trm"]
        ) or (self.vna.connected and self.device_type == "amplifier"):
            self.connect_button.state(["disabled"])

        if self.vna.get_vendor_name() == "Keysight":
            self.vna.write_command("INIT:CONT ON")

        if self.device_type in ["phase_shifter", "ku_trm"]:
            if self.device_type == "ku_trm":
                self.role_dropdown.pack(side="left", padx=5)
                self.module_type_dropdown.pack(side="left", padx=5)
            self.frame3.pack()
            self.log(
                f"{'Phase shifter' if self.device_type == 'phase_shifter' else 'KU TRM Module'} measurement configuration successful.",
                "success",
            )
        else:
            self.amplifier_test_frame.pack(fill="x", pady=10)
            self.log("Amplifier measurement configuration successful.", "success")

    def configure_measurement(self):
        try:
            start_freq = float(self.start_freq_entry.get())
            stop_freq = float(self.stop_freq_entry.get())

            freq_range, _ = self.vna.get_trace_info()
            print(freq_range[0], freq_range[-1], start_freq, stop_freq)

            if (
                freq_range[0] <= start_freq < stop_freq <= freq_range[-1]
                or freq_range[0] <= start_freq == stop_freq <= freq_range[-1]
            ):
                self.start_freq = start_freq
                self.stop_freq = stop_freq

                self.calib_frame.pack()

            else:
                self.log("[ERROR] Frequency range not within sweep range", "error")
        except ValueError:
            self.log("[ERROR] Invalid input. Please enter valid numbers.", "error")

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
        for frame in [
            self.single_frame,
            self.all_state_frame,
            self.upload_frame,
            self.device_select_frame,
            self.calib_frame,
        ]:
            frame.pack_forget()

        # Clear entries in all modes
        for entry in [
            self.n_entry,
            self.state_entry,
            self.bits_entry,
            self.states_entry,
            self.n_bits_entry,
        ]:
            try:
                entry.delete(0, tk.END)
            except Exception:
                pass  # Entry might not exist yet

        self.csv_label_var.set("No file selected")
        self.file_path = ""

    def upload_csv(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
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
        threading.Thread(target=self.start_test, args=(mode,), daemon=True).start()

    def log_threadsafe(self, message, tag="info"):
        """Thread-safe logging function"""
        self.root.after(0, lambda: self.log(message, tag))

    def start_test(self, mode):
        try:
            folder_name = f"{self.save_path}/{datetime.datetime.now().strftime('measurement_%Y-%m-%d_%H-%M-%S')}"
            os.makedirs(folder_name, exist_ok=True, mode=0o777)
            print(self.role_var.get())
            print(self.module_type_var.get())

            if mode == "csv":
                try:
                    if self.file_path:
                        self.log_threadsafe("Reading CSV file...")
                        with open(self.file_path, "r") as f:
                            csv_data = csv.reader(f)
                            states = []
                            for i in list(csv_data)[0]:
                                try:
                                    states.append(int(i))
                                except Exception:
                                    pass

                        if not states:
                            self.log_threadsafe(
                                "[ERROR] No valid states found in CSV", "error"
                            )
                            self.test_running = False
                            return
                        bits = int(self.n_bits_entry.get())

                        if self.device_type_var == "phase_shifter":
                            if max(states) > 2**bits:
                                self.log_threadsafe(
                                    "[ERROR] CSV has a state greater than the number of states",
                                    "error",
                                )
                                return

                        if self.device_type_var == "ku_trm":
                            # if max(states) > 2**bits:
                            if (
                                max(states)
                                > self.trigger_states[
                                    (self.role_var.get(), self.module_type_var.get())
                                ][1]
                            ) and (
                                min(states)
                                < self.trigger_states[
                                    (self.role_var.get(), self.module_type_var.get())
                                ][0]
                            ):
                                self.log_threadsafe(
                                    "[ERROR] CSV has a state greater than the number of states",
                                    "error",
                                )
                                return

                        for state in states:
                            if self.cancel_event.is_set():
                                self.log_threadsafe(
                                    "[CANCELLED] Test was cancelled.", "warning"
                                )
                                return

                            while self.pause_event.is_set():
                                time.sleep(0.1)
                            if self.cancel_event.is_set():
                                self.log_threadsafe(
                                    "[CANCELLED] Test was cancelled.", "warning"
                                )
                                return

                            if not self.fpga.trigger_state(state):
                                self.log_threadsafe(
                                    "[ERROR] FPGA communication failed. Please make sure FPGA is connected and all applications using the port are closed",
                                    "error",
                                )
                                return

                            self.log_threadsafe(
                                f"[TRIGGER] Triggered state {state}", "success"
                            )

                            while self.pause_event.is_set():
                                time.sleep(0.1)
                            if self.cancel_event.is_set():
                                self.log_threadsafe(
                                    "[CANCELLED] Test was cancelled.", "warning"
                                )
                                return

                            time.sleep(self.delay)
                            self.vna.save_traces(
                                state, folder_name, self.start_freq, self.stop_freq
                            )
                            self.log_threadsafe(
                                f"Saved measurement for state {state}", "success"
                            )

                        self.log_threadsafe("Test completed", "success")
                        self.vna.reset_indices()
                    else:
                        self.log_threadsafe(
                            "[ERROR] Please upload a CSV file first", "error"
                        )
                except ValueError:
                    self.log_threadsafe("[ERROR] Enter valid integer", "error")

            elif mode == "single_state":
                try:
                    n = int(self.n_entry.get())
                    state = int(self.state_entry.get())

                    if self.device_type_var == "phase_shifter":
                        if state >= 2**bits:
                            self.log_threadsafe(
                                f"[ERROR] Invalid: State exceeds 2^{n}", "error"
                            )
                            return

                    elif self.device_type_var == "ku_trm":
                        # if max(states) > 2**bits:
                        if (
                            state
                            > self.trigger_states[
                                (self.role_var.get(), self.module_type_var.get())
                            ][1]
                        ) and (
                            state
                            < self.trigger_states[
                                (self.role_var.get(), self.module_type_var.get())
                            ][0]
                        ):
                            self.log_threadsafe(
                                f"[ERROR] Invalid: State needs to be within {
                                    self.trigger_states[
                                        (
                                            self.role_var.get(),
                                            self.module_type_var.get(),
                                        )
                                    ][0]
                                } and {
                                    self.trigger_states[
                                        (
                                            self.role_var.get(),
                                            self.module_type_var.get(),
                                        )
                                    ][1]
                                }",
                                "error",
                            )
                            return

                    if self.cancel_event.is_set():
                        self.log_threadsafe(
                            "[CANCELLED] Test was cancelled.", "warning"
                        )
                        return

                    while self.pause_event.is_set():
                        time.sleep(0.1)
                    if self.cancel_event.is_set():
                        self.log_threadsafe(
                            "[CANCELLED] Test was cancelled.", "warning"
                        )
                        return

                    self.log_threadsafe(f"Transmitting State {state} (n={n})", "info")

                    if not self.fpga.trigger_state(state):
                        self.log_threadsafe(
                            "[ERROR] FPGA communication failed. Please make sure FPGA is connected and all applications using the port are closed",
                            "error",
                        )
                        return

                    self.log_threadsafe(f"[TRIGGER] Triggered state {state}", "success")

                    while self.pause_event.is_set():
                        time.sleep(0.1)
                    if self.cancel_event.is_set():
                        self.log_threadsafe(
                            "[CANCELLED] Test was cancelled.", "warning"
                        )
                        return

                    time.sleep(self.delay)
                    self.vna.save_traces(
                        state, folder_name, self.start_freq, self.stop_freq
                    )
                    self.log_threadsafe(
                        f"Saved measurement for state {state}", "success"
                    )
                    self.log_threadsafe("Test completed", "success")
                    self.vna.reset_indices()
                except ValueError:
                    self.log_threadsafe("[ERROR] Enter valid integers.", "error")

            elif mode == "all_states":
                try:
                    if self.device_type_var == "phase_shifter":
                        bits = int(self.bits_entry.get())
                        states = int(self.states_entry.get())
                        if states > 2**bits:
                            self.log_threadsafe(
                                f"[ERROR] Invalid: Max states is {2**bits}", "error"
                            )
                            return

                        self.log_threadsafe(
                            f"All states mode: {states} states for {bits}-bit", "info"
                        )

                        for state in range(states):
                            if self.cancel_event.is_set():
                                self.log_threadsafe(
                                    "[CANCELLED] Test was cancelled.", "warning"
                                )
                                return

                            while self.pause_event.is_set():
                                time.sleep(0.1)
                            if self.cancel_event.is_set():
                                self.log_threadsafe(
                                    "[CANCELLED] Test was cancelled.", "warning"
                                )
                                return

                            if not self.fpga.trigger_state(state):
                                self.log_threadsafe(
                                    "[ERROR] FPGA communication failed. Please make sure FPGA is connected and all applications using the port are closed",
                                    "error",
                                )
                                return

                            self.log_threadsafe(
                                f"[TRIGGER] Triggered state {state}", "success"
                            )

                            while self.pause_event.is_set():
                                time.sleep(0.1)
                            if self.cancel_event.is_set():
                                self.log_threadsafe(
                                    "[CANCELLED] Test was cancelled.", "warning"
                                )
                                return

                            time.sleep(self.delay)
                            self.vna.save_traces(
                                state, folder_name, self.start_freq, self.stop_freq
                            )
                            self.log_threadsafe(
                                f"Saved measurement for state {state}", "success"
                            )

                        self.log_threadsafe("Test completed", "success")
                        self.vna.reset_indices()

                    elif self.device_type_var == "ku_trm":
                        bits = int(self.bits_entry.get())
                        states = int(self.states_entry.get())

                        start = self.trigger_states[
                            (self.role_var.get(), self.module_type_var.get())
                        ][0]
                        end = self.trigger_states[
                            (self.role_var.get(), self.module_type_var.get())
                        ][1]

                        valid_states_range = end - start

                        if valid_states_range < states:
                            self.log_threadsafe(
                                "[ERROR] States entered higher than valid range.",
                                "error",
                            )
                            return

                        for state in range(start, start + states):
                            if self.cancel_event.is_set():
                                self.log_threadsafe(
                                    "[CANCELLED] Test was cancelled.", "warning"
                                )
                                return

                            while self.pause_event.is_set():
                                time.sleep(0.1)
                            if self.cancel_event.is_set():
                                self.log_threadsafe(
                                    "[CANCELLED] Test was cancelled.", "warning"
                                )
                                return

                            if not self.fpga.trigger_state(state):
                                self.log_threadsafe(
                                    "[ERROR] FPGA communication failed. Please make sure FPGA is connected and all applications using the port are closed",
                                    "error",
                                )
                                return

                            self.log_threadsafe(
                                f"[TRIGGER] Triggered state {state}", "success"
                            )

                            while self.pause_event.is_set():
                                time.sleep(0.1)
                            if self.cancel_event.is_set():
                                self.log_threadsafe(
                                    "[CANCELLED] Test was cancelled.", "warning"
                                )
                                return

                            time.sleep(self.delay)
                            self.vna.save_traces(
                                state, folder_name, self.start_freq, self.stop_freq
                            )
                            self.log_threadsafe(
                                f"Saved measurement for state {state}", "success"
                            )

                        self.log_threadsafe("Test completed", "success")
                        self.vna.reset_indices()
                except ValueError:
                    self.log_threadsafe("[ERROR] Invalid value added", "error")

        finally:
            self.pause_event.clear()
            self.cancel_event.clear()
            self.test_running = False
            self.vna.reset_indices()

    def pause_test(self):
        if self.test_running:
            if not self.pause_event.is_set():
                self.pause_event.set()
                self.log("[INFO] Test paused. Click again to resume.", "warning")
            else:
                self.pause_event.clear()
                self.log("[INFO] Test resumed.", "success")

    def cancel_test(self):
        if self.test_running:
            self.cancel_event.set()
            self.pause_event.clear()  # in case it was paused
            self.test_running = False
            self.log("[INFO] Cancelling test...", "warning")


if __name__ == "__main__":
    root = tk.Tk()
    app = MackIITMGUI(root)
    root.mainloop()
