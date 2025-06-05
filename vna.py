import pyvisa as visa
import os
from abc import ABC, abstractmethod


class BaseVNA(ABC):
    """
    Abstract base class for Vector Network Analyzers.
    Defines the interface that all VNA implementations must follow.
    """

    def __init__(self):
        """
        Initializes the VNA object with common attributes.
        """
        self.connected = False
        self.instru = None
        self.start_index = None
        self.stop_index = None
        self.sep = ","
        self.rm = None

    def initialize_vna(self):
        """
        Attempts to initialize and connect to a VNA using PyVISA.
        Sets the connected attribute to True on success.
        """
        self.rm = visa.ResourceManager()
        for r in self.rm.list_resources():
            try:
                instru = self.rm.open_resource(r)
                res = instru.query("*IDN?").split(",")

                # Check if this is a VNA we can handle
                if self.is_compatible_vna(res):
                    self.instru = instru
                    self.connected = True
                    break
            except Exception:
                # print(f"Error connecting to {r}: {e}")
                continue

        if self.connected:
            print(f"Connected successfully to {self.get_vendor_name()} VNA")
            return True
        else:
            # print("Couldn't find compatible VNA device")
            return False

    @abstractmethod
    def is_compatible_vna(self, idn_response):
        """
        Check if the VNA is compatible with this implementation.

        Args:
            idn_response (list): Split response from *IDN? query

        Returns:
            bool: True if compatible, False otherwise
        """
        pass

    @abstractmethod
    def create_trace(self, name, parameter, unit):
        """
        Check if the VNA is compatible with this implementation.

        Args:
            idn_response (list): Split response from *IDN? query

        Returns:
            bool: True if compatible, False otherwise
        """
        pass

    @abstractmethod
    def get_vendor_name(self):
        """
        Returns the vendor name for this VNA implementation.

        Returns:
            str: Vendor name
        """
        pass

    @abstractmethod
    def get_trace_info(self, start_freq=None, stop_freq=None):
        """
        Retrieves frequency points and trace metadata from the VNA.

        Args:
            start_freq (float, optional): Custom start frequency (in GHz).
            stop_freq (float, optional): Custom stop frequency (in GHz).

        Returns:
            tuple: (List[float] frequency points in GHz, List[str] trace names)
        """
        pass

    @abstractmethod
    def get_trace_data(self):
        """
        Retrieves all trace data from the VNA.

        Returns:
            list: Trace values
        """
        pass

    def reset_indices(self):
        """
        Resets the values of start and stop indices
        """
        self.start_index = None
        self.stop_index = None

    def save_traces_amp(self, folder_name, start_freq, end_freq):
        """
        Saves trace data for amplifiers in a given frequency range to individual CSV files.

        Args:
            folder_name (str): The directory to store CSV files.
            start_freq (float): Start frequency in GHz.
            end_freq (float): End frequency in GHz.
        """
        in_gigs, trace_names = self.get_trace_info(start_freq, end_freq)
        steps = len(in_gigs)

        trace_values = self.get_trace_data()

        # Create folder if it doesn't exist
        os.makedirs(folder_name, exist_ok=True)

        for i, name in enumerate(trace_names):
            if name not in os.listdir(folder_name):
                with open(f"{folder_name}/{name}", mode="w") as f:
                    for j, v in enumerate(in_gigs):
                        print(v, start_freq)
                        if v < start_freq:
                            continue

                        h = (
                            str(v)
                            + self.sep
                            + str(trace_values[j + (i * steps)])
                            + f"{self.sep}\n"
                        )
                        f.write(h)

                        if v >= end_freq:
                            break

    def save_traces(self, state, folder_name, start_freq, end_freq):
        """
        Saves full trace data (all frequency points) for a given state into CSV files.
        Updates header row with frequency values and appends trace data per state.

        Args:
            state (str): Identifier for the measurement state (e.g., 'ON', 'OFF').
            folder_name (str): Directory to store trace CSV files.
            start_freq (float): Start frequency in GHz.
            end_freq (float): End frequency in GHz.
        """
        in_gigs, trace_names = self.get_trace_info(start_freq, end_freq)
        steps = len(in_gigs)

        trace_values = self.get_trace_data()

        # Create folder if it doesn't exist
        os.makedirs(folder_name, exist_ok=True)

        for i, name in enumerate(trace_names):
            if name not in os.listdir(folder_name):
                with open(f"{folder_name}/{name}", mode="w") as f:
                    for j, v in enumerate(in_gigs):
                        if v >= start_freq and self.start_index is None:
                            self.start_index = j
                        if v == end_freq and self.stop_index is None:
                            self.stop_index = j
                            break
                        elif v > end_freq and self.stop_index is None:
                            self.stop_index = j - 1
                            break

                    h = (
                        self.sep
                        + self.sep.join(
                            list(
                                map(
                                    lambda x: str(x),
                                    in_gigs[self.start_index : self.stop_index + 1],
                                )
                            )
                        )
                        + f"{self.sep}\n"
                    )
                    f.write(h)

            with open(f"{folder_name}/{name}", mode="a+") as f:
                vals = (
                    f"{state},"
                    + self.sep.join(
                        list(
                            map(
                                lambda x: str(x),
                                trace_values[
                                    self.start_index + (i * steps) : (i * steps)
                                    + self.stop_index
                                    + 1
                                ],
                            )
                        )
                    )
                    + f"{self.sep}\n"
                )
                f.write(vals)

    def write_command(self, command):
        try:
            self.instru.write(command)
            return True
        except Exception as e:
            print(f"[ERROR] {e}")
            return False

    def query_command(self, command):
        try:
            print(self.instru.query(command))
            return True
        except Exception as e:
            print(f"[ERROR] {e}")
            return False


class RohdeSchwartzVNA(BaseVNA):
    """
    Implementation for Rohde & Schwarz VNAs.
    """

    def is_compatible_vna(self, idn_response):
        """Check if the instrument is a compatible Rohde & Schwarz VNA"""
        if idn_response[0] == "Rohde-Schwarz":
            try:
                # Test a R&S specific command
                self.instru.query("TRAC:STIM? CH1DATA")
                return True
            except Exception:
                return False
        return False

    def get_vendor_name(self):
        """Return vendor name"""
        return "Rohde & Schwarz"

    def get_trace_info(self, start_freq=None, stop_freq=None):
        """
        Retrieves frequency points and trace metadata from R&S VNA.
        """
        freq_points = self.instru.query("TRAC:STIM? CH1DATA").split(",")
        in_gigs = [float(freq_point) / 1000000000 for freq_point in freq_points]

        trace_id_name = self.instru.query("CONF:TRAC:CAT?").split(",")
        trace_id_name = list(map(lambda x: str(x).strip(), trace_id_name))

        trace_names = []
        for i in range(1, len(trace_id_name), 2):
            if start_freq is None and stop_freq is None:
                trace_names.append(f"{in_gigs[0]}-{in_gigs[-1]}_{trace_id_name[i]}.csv")
            elif start_freq is not None and stop_freq is not None:
                trace_names.append(f"{start_freq}-{stop_freq}_{trace_id_name[i]}.csv")

        return in_gigs, trace_names

    def get_trace_data(self):
        """Get trace data from R&S VNA"""
        trace_values = self.instru.query("CALCulate1:DATA:ALL? FDAT").split(",")
        return list(map(float, trace_values))

    def create_trace(self, name, parameter, unit):
        pass


class KeysightVNA(BaseVNA):
    """
    Implementation for Keysight VNAs.
    """

    def is_compatible_vna(self, idn_response):
        """Check if the instrument is a compatible Keysight VNA"""
        if (
            idn_response[0] == "Keysight Technologies"
            or idn_response[0] == "Agilent Technologies"
        ):
            return True
        return False

    def get_vendor_name(self):
        """Return vendor name"""
        return "Keysight"

    def get_trace_info(self, start_freq=None, stop_freq=None):
        """
        Retrieves frequency points and trace metadata from Keysight VNA.
        """
        trace_info = self.instru.query("CALC:PAR:CAT?").split(",")
        print(trace_info)
        only_trace_names = []

        # for i in range(0, len(trace_info), 2):
        #     num = trace_info[i].split("_")[-1]
        #     only_trace_names.append(f"Trc{num}")

        # for i in range(0, len(trace_info), 2): # TODO :test this
        #     only_trace_names.append(trace_info[i])

        for i in range(0, int(len(trace_info) // 2)):
            only_trace_names.append(f"Trc{i + 1}")

        print(only_trace_names)

        freq_points = self.instru.query("CALC:MEAS:X:VAL?").split(",")
        in_gigs = [float(freq_point) / 1000000000 for freq_point in freq_points]

        trace_names = []
        for i in range(len(only_trace_names)):
            if start_freq is None and stop_freq is None:
                trace_names.append(
                    f"{in_gigs[0]}-{in_gigs[-1]}_{only_trace_names[i]}.csv"
                )
            elif start_freq is not None and stop_freq is not None:
                trace_names.append(
                    f"{start_freq}-{stop_freq}_{only_trace_names[i]}.csv"
                )

        return in_gigs, trace_names

    def get_trace_data(self):
        """Get trace data from Keysight VNA"""
        # Make sure we're getting data in the right format
        trace_info = self.instru.query("CALC:PAR:CAT?").split(",")
        # print(trace_info)
        all_data = []

        # for i in range(0, len(trace_info), 2):
        #     # for i in range(1, int(len(trace_info) / 3) + 1):
        #     num = trace_info[i].split("_")[-1].split(" ")[0]
        #     d = self.instru.query(f'CALC:DATA:MFD? "{num}"')
        #     # print(d)
        #     all_data.extend(list(map(float, d.strip().split(","))))

        for i in range(1, int(len(trace_info) // 2) + 1):
            print(i)
            d = self.instru.query(f'CALC:DATA:MFD? "{i}"')
            # print(d)
            all_data.extend(list(map(float, d.strip().split(","))))

        return all_data

    def create_trace(self, name, parameter, unit):
        command = f"CALC:PAR:DEF:EXT '{name}', '{parameter}'"  # create Trace
        try:
            self.instru.write(command)
        except Exception as e:
            print("[ERROR] Invalid parameter or Trace with name already exists")
            print(e)
            return

        count = self.instru.query("CALC:PAR:COUN?")  # get number of traces
        count = int(count)
        if unit == "deg":
            self.instru.write(f"CALC:MEAS{count}:FORM PHAS")

        command = f"DISP:WIND:TRAC{count}:FEED '{name}'"  # Display trace

        try:
            self.instru.write(command)
        except Exception as e:
            print(e)


class VNAFactory:
    """
    Factory class to create appropriate VNA instance based on available hardware.
    """

    @staticmethod
    def create_vna():
        """
        Try to connect to available VNAs and return the appropriate instance.

        Returns:
            BaseVNA: Instance of a VNA class that successfully connected
        """
        # Try Rohde & Schwarz first
        vna = RohdeSchwartzVNA()
        if vna.initialize_vna():
            return vna

        # Try Keysight next
        vna = KeysightVNA()
        if vna.initialize_vna():
            return vna

        # If no compatible VNA is found, return None
        print("No compatible VNA found")
        return None


# For backwards compatibility with existing code
class VNA(BaseVNA):
    """
    Legacy VNA class for backward compatibility.
    """

    def __init__(self):
        """
        Initialize VNA object and create internal reference to actual VNA implementation.
        """
        super().__init__()
        self._impl = None
        self.connected = False
        # self.connected = True  # TODO: comment this

    def initialize_vna(self):
        """
        Initialize VNA by delegating to factory.
        """
        self._impl = VNAFactory.create_vna()
        if self._impl:
            self.connected = True
            self.instru = self._impl.instru
            return True
        return False

    def is_compatible_vna(self, idn_response):
        """Delegate to implementation"""
        if self._impl:
            return self._impl.is_compatible_vna(idn_response)
        return False

    def get_vendor_name(self):
        """Delegate to implementation"""
        if self._impl:
            return self._impl.get_vendor_name()
        return "Unknown"

    def get_trace_info(self, start_freq=None, stop_freq=None):
        """Delegate to implementation"""
        if self._impl:
            return self._impl.get_trace_info(start_freq, stop_freq)
        return [15.5, 17.5], "hehe"  # Original debug values

    def get_trace_data(self):
        """Delegate to implementation"""
        if self._impl:
            return self._impl.get_trace_data()
        return []

    def save_traces_amp(self, folder_name, start_freq, end_freq):
        """Delegate to implementation"""
        if self._impl:
            self._impl.save_traces_amp(folder_name, start_freq, end_freq)

    def save_traces(self, state, folder_name, start_freq, end_freq):
        """Delegate to implementation"""
        if self._impl:
            self._impl.save_traces(state, folder_name, start_freq, end_freq)

    def create_trace(self, name, parameter, unit):
        self._impl.create_trace(name, parameter, unit)


if __name__ == "__main__":
    v = VNA()
    v.initialize_vna()
    # v.create_trace("trial2", "S21")
