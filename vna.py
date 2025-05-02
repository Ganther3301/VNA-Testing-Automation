import pyvisa as visa
from pprint import pprint
import datetime
import os


class VNA:
    def __init__(self):
        self.connected = True
        self.instru = None
        self.start_index = None
        self.stop_index = None

    def initialize_vna(self):
        # return  # TODO
        self.rm = visa.ResourceManager()
        for r in self.rm.list_resources():
            try:
                instru = self.rm.open_resource(r)
                res = instru.query("*IDN?").split(',')
                instru.query("TRAC:STIM? CH1DATA")
                # print(res)
                if res[0] != 'Rohde-Schwarz':
                    continue
                self.instru = instru
                self.connected = True
                break
            except:
                pass

        if self.connected:
            print("Connected successfully")
        else:
            print("Couldn't find device")
            return

    def get_trace_info(self, start_freq=None, stop_freq=None):
        # return [15.5, 17.5], 'hehe'  # TODO
        freq_points = self.instru.query("TRAC:STIM? CH1DATA").split(',')
        print(freq_points)
        in_gigs = [int(freq_point)/1000000000 for freq_point in freq_points]

        trace_id_name = self.instru.query("CONF:TRAC:CAT?").split(',')
        trace_id_name = list(map(lambda x: str(x).strip(), trace_id_name))
        print(trace_id_name)

        trace_names = []
        for i in range(1, len(trace_id_name), 2):
            if start_freq == None and stop_freq == None:
                trace_names.append(
                    f"{in_gigs[0]}-{in_gigs[-1]}_{trace_id_name[i]}.csv")
            elif start_freq != None and stop_freq != None:
                trace_names.append(
                    f"{start_freq}-{stop_freq}_{trace_id_name[i]}.csv")

        print(trace_names)

        return in_gigs, trace_names

    def save_traces_amp(self, folder_name, start_freq, end_freq):
        sep = ','

        in_gigs, trace_names = self.get_trace_info(start_freq, end_freq)
        steps = len(in_gigs)

        trace_values = self.instru.query(
            "CALCulate1:DATA:ALL? FDAT").split(',')
        trace_values = list(map(lambda x: float(x), trace_values))

        for i, name in enumerate(trace_names):
            if name not in os.listdir(folder_name):
                with open(f'{folder_name}/{name}', mode='w') as f:
                    for j, v in enumerate(in_gigs):
                        if v >= start_freq and self.start_index == None:
                            continue

                        h = str(v) + sep + \
                            str(trace_values[j+(i*steps)]) + f"{sep}\n"
                        f.write(h)

                        if v >= end_freq and self.stop_index == None:
                            break

    # print(instru.write(f"MMEMory:STORe:TRACe:CHANnel ALL, '{save_count}.csv', FORM, LOGPhase"))

    def save_traces(self, state, folder_name, start_freq, end_freq):
        sep = ','

        in_gigs, trace_names = self.get_trace_info(start_freq, end_freq)
        steps = len(in_gigs)

        trace_values = self.instru.query(
            "CALCulate1:DATA:ALL? FDAT").split(',')
        trace_values = list(map(lambda x: float(x), trace_values))

        # for i, name in enumerate(trace_names):
        #     if name not in os.listdir(folder_name):
        #         with open(f'{folder_name}/{name}', mode='w') as f:
        #

        #     with open(f'{folder_name}/{name}', mode='a+') as f:
        #         vals = f'{state},' + sep.join(
        #             list(map(lambda x: str(x), trace_values[i*steps:steps*(i+1)]))) + f'{sep}\n'
        #         f.write(vals)

        # for i, name in enumerate(trace_names):
        #     if name not in os.listdir(folder_name):
        #         with open(f'{folder_name}/{name}', mode='w') as f:
        #             h = sep + \
        #                 sep.join(list(map(lambda x: str(x), in_gigs))
        #                          ) + f'{sep}\n'
        #             f.write(h)

        #     with open(f'{folder_name}/{name}', mode='a+') as f:
        #         vals = f'{state},' + sep.join(
        #             list(map(lambda x: str(x), trace_values[i*steps:steps*(i+1)]))) + f'{sep}\n'
        #         f.write(vals)

        for i, name in enumerate(trace_names):
            if name not in os.listdir(folder_name):
                with open(f'{folder_name}/{name}', mode='w') as f:
                    for j, v in enumerate(in_gigs):
                        if v >= start_freq and self.start_index == None:
                            self.start_index = j
                        if v == end_freq and self.stop_index == None:
                            self.stop_index = j
                            break
                        elif v > end_freq and self.stop_index == None:
                            self.stop_index = j-1
                            break

                    h = sep + \
                        sep.join(list(map(lambda x: str(x), in_gigs[self.start_index:self.stop_index+1]))
                                 ) + f'{sep}\n'
                    f.write(h)

            with open(f'{folder_name}/{name}', mode='a+') as f:
                vals = f'{state},' + sep.join(
                    list(map(lambda x: str(x), trace_values[self.start_index+(i*steps):(i*steps)+self.stop_index+1]))) + f'{sep}\n'
                f.write(vals)

    # print(instru.write(f"MMEMory:STORe:TRACe:CHANnel ALL, '{save_count}.csv', FORM, LOGPhase"))


if __name__ == '__main__':
    v = VNA()
    v.initialize_vna()
    print(v.get_trace_info())
