import pyvisa as visa
import os


class VNA:
    """
    A class to interact with a Vector Network Analyzer (VNA), specifically models from Rohde & Schwarz.
    Provides functionality to connect to the device, retrieve trace information, and save amplitude or full trace data.

    Attributes:
        connected (bool): Flag indicating whether the VNA is connected.
        instru (visa.Resource): VISA instrument resource object representing the connected VNA.
        start_index (int): Starting index of frequency range to extract.
        stop_index (int): Ending index of frequency range to extract.
    """

    def __init__(self):
        """
        Initializes the VNA object with connection status, instrument handle, and index placeholders.
        """
        self.connected = False  # TODO : change it to False
        self.instru = None
        self.start_index = None
        self.stop_index = None
        self.sep = ","

    def initialize_vna(self):
        """
        Attempts to initialize and connect to a Rohde & Schwarz VNA using PyVISA.
        Sets the connected attribute to True on success.
        """
        # return  # TODO : comment this
        self.rm = visa.ResourceManager()
        for r in self.rm.list_resources():
            try:
                instru = self.rm.open_resource(r)
                res = instru.query("*IDN?").split(",")
                instru.query("TRAC:STIM? CH1DATA")
                if res[0] != "Rohde-Schwarz":
                    continue
                self.instru = instru
                self.connected = True
                break
            except:
                pass

        if self.connected:
            print("Connected successfully")
            return True
        else:
            print("Couldn't find device")
            return False

    def get_trace_info(self, start_freq=None, stop_freq=None):
        """
        Retrieves frequency points and trace metadata from the VNA.

        Args:
            start_freq (float, optional): Custom start frequency (in GHz). Used for filename formatting.
            stop_freq (float, optional): Custom stop frequency (in GHz). Used for filename formatting.

        Returns:
            tuple: A tuple containing:
                - List[float]: Frequency points in GHz.
                - List[str]: Corresponding trace names (formatted filenames).
        """
        # return [15.5, 17.5], 'hehe'  # TODO
        freq_points = self.instru.query("TRAC:STIM? CH1DATA").split(",")
        print(freq_points)
        in_gigs = [int(freq_point) / 1000000000 for freq_point in freq_points]

        trace_id_name = self.instru.query("CONF:TRAC:CAT?").split(",")
        trace_id_name = list(map(lambda x: str(x).strip(), trace_id_name))
        print(trace_id_name)

        trace_names = []
        for i in range(1, len(trace_id_name), 2):
            if start_freq == None and stop_freq == None:
                trace_names.append(f"{in_gigs[0]}-{in_gigs[-1]}_{trace_id_name[i]}.csv")
            elif start_freq != None and stop_freq != None:
                trace_names.append(f"{start_freq}-{stop_freq}_{trace_id_name[i]}.csv")

        print(trace_names)

        return in_gigs, trace_names

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

        trace_values = self.instru.query("CALCulate1:DATA:ALL? FDAT").split(",")
        trace_values = list(map(lambda x: float(x), trace_values))

        for i, name in enumerate(trace_names):
            if name not in os.listdir(folder_name):
                with open(f"{folder_name}/{name}", mode="w") as f:
                    for j, v in enumerate(in_gigs):
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

        trace_values = self.instru.query("CALCulate1:DATA:ALL? FDAT").split(",")
        trace_values = list(map(lambda x: float(x), trace_values))

        for i, name in enumerate(trace_names):
            if name not in os.listdir(folder_name):
                with open(f"{folder_name}/{name}", mode="w") as f:
                    for j, v in enumerate(in_gigs):
                        if v >= start_freq and self.start_index == None:
                            self.start_index = j
                        if v == end_freq and self.stop_index == None:
                            self.stop_index = j
                            break
                        elif v > end_freq and self.stop_index == None:
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

    def reset_indices(self):
        """
        Resets the valus of start and stop indices
        """
        self.start_index = None
        self.stop_index = None


if __name__ == "__main__":
    v = VNA()
    v.initialize_vna()
    print(v.get_trace_info())
