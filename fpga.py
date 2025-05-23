import serial  # type: ignore
import serial.tools.list_ports  # type: ignore


class FPGA:
    """
    A class to interact with an FPGA over serial (UART) connection

    Attributes:
        connected (bool) : Flag indicating whether FPGA is connected or not.
        port (str or None) : The port that FPGA is connected to.
        baudrate (int) : UART communication speed
        timeout (int) : timeout for operations
    """

    def __init__(self, baudrate=9600, timeout=1):
        """
        Initialization Function

        Args:
            baudrate (int, optional): UART communication speed. Defaults to 9600.
            timeout (int, optional): Timeout for operations. Defaults to 1.
        """
        # self.connected = True  # TODO : comment it
        self.connected = False
        self.port = None
        self.baudrate = baudrate
        self.timeout = timeout

    def initialize_fpga(self):
        """
        Scans connected serial ports and checks if FPGA is connected or not

        Returns:
            bool: Returns True if FPGA is found. Otherwise return False
        """
        # return  # TODO : comment it
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
        """
        Sends a single byte to the FPGA to trigger a single state

        Args:
            state (int): State that needs to be triggered

        Returns:
            bool: Returns True if state was successfully triggered. Otherwise False
        """
        if not self.connected:
            print("[ERROR] No device connected. Call initialize_fpga() first.")
            return False

        try:
            with serial.Serial(self.port, self.baudrate, timeout=self.timeout) as ser:
                ser.reset_input_buffer()

                ser.write(bytes([state]))
                ser.flush()
                print(f"[UART] Triggered Din[{state}]")

                response = ser.read_all().strip()

                if response:
                    print(f"[FPGA Response] {response}")
                else:
                    print("[WARN] No response received from FPGA")

                return True
        except serial.SerialException as e:
            print(f"[ERROR] Serial communication error: {e}")
            return False
