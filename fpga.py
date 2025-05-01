import serial  # type: ignore
import serial.tools.list_ports  # type: ignore
import time


class FPGA:
    def __init__(self, baudrate=9600, timeout=1):
        self.connected = False
        self.port = None
        self.baudrate = baudrate
        self.timeout = timeout

    def initialize_fpga(self):
        # return
        keyword = "USB Serial"
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if keyword.lower() in port.description.lower():
                print(f"[INFO] Found FPGA on {port.device}")
                self.port = port.device
                self.connected = True
                return True

        print("[ERROR] FPGA not found")
        return False

    def trigger_state(self, state):
        if not self.connected:
            print("[ERROR] No device connected. Call initialize_fpga() first.")
            return False

        try:
            with serial.Serial(self.port, self.baudrate, timeout=self.timeout) as ser:
                # Clear any existing data in the buffer
                ser.reset_input_buffer()

                # Send the state command
                ser.write(bytes([state]))
                ser.flush()
                print(f"[UART] Triggered Din[{state}]")

                # Wait a moment for the FPGA to process
                # time.sleep(0.5)

                # Read response with timeout
                response = ser.read_all().strip()

                if response:
                    print(f"[FPGA Response] {response}")
                    return True
                else:
                    print("[WARN] No response received from FPGA")
                    return False
        except serial.SerialException as e:
            print(f"[ERROR] Serial communication error: {e}")
            return False
