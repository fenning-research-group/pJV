import numpy as np
import pandas as pd
import csv
from time import sleep

# Import locally from computer
try:
    from PLQY.ldc502 import LDC502
except ImportError:
    raise ImportError("Failed to import LDC502 from PLQY.ldc502. Ensure the module is installed and accessible.")

try:
    from frghardware.keithleyjv import control3
except ImportError:
    raise ImportError("Failed to import control3 from frghardware.keithleyjv. Ensure the module is installed and accessible.")
    
plus_minus = u"\u00B1"

# Version 10- fwdrev capability

class pJV:
    ''' A class to take pseudo JV curves '''

    class CustomError(Exception):
        pass

    def __init__(self):
        # Initialize the hardware
        # Connect to the laser
        try: 
            self.ldc = LDC502("COM24")
            self.laser_current = self.ldc.get_laser_current()
            self.laser_temp = self.ldc.get_laser_temp()
            self.laser_wl = 532
        except Exception as e:  
            print("Error while trying to connect to the Laser: ", e)
            print("Please ensure the Laser is connected to COM24 and try again.")
            raise self.CustomError("Laser Connection Error")
        
        # Connect to the Keithley
        try:
            self.JVcode = control3.Control(address='GPIB1::22::INSTR')
        except Exception as e:
            print("Error while trying to connect to the Keithley: ", e)
            print("Please ensure the Keithley is connected to 'GPIB1::22::INSTR' and try again.")
            raise self.CustomError("Keithley Connection Error")

    # Method to configure the hardware
    def _configure(self, n_wires = 2):
        self.ldc.set_laserOn()
        self.ldc.set_tecOn()
        self.ldc.set_modulationOff()
        self.JVcode.keithley.wires = n_wires
        print("Laser and TEC turned on, modulation turned off.")
        print('\nSetting Laser Current and waiting to stabilize...')

    # Method to take a measurement of a sample
    def _take_measurement(self, start_current, end_current, step, stabilize_time, num_measurements, n_wires = 2):
        # First configure the hardware
        self._configure(n_wires)
        # Initialize the data dictionary
        data = {}
        # Stabilize the laser and take measurements
        for current_setting in np.arange(start_current, end_current+step, step):
            voc_list = []
            if np.abs(self.ldc.get_laser_current() - current_setting) > 2:
                self.ldc.set_laserCurrent(current_setting)
                sleep(stabilize_time)
            else:
                self.ldc.set_laserCurrent(current_setting)

            print('\nLaser Current Set and Stable.')
            sleep(0.5)

            # Take several measurements, calculate average and standard deviation
            for _ in range(num_measurements):
                voc = self.JVcode.voc()
                voc_list.append(voc)
                sleep(0.3)    
            avg_voc = np.mean(voc_list)
            std_voc = np.std(voc_list) 

            print(f"At current = {current_setting} mA, average Voc = {avg_voc} {plus_minus} {std_voc} V")
            data[current_setting] = (avg_voc, std_voc)

        return data

    # Method to save the data as a csv
    def _save_data(self, data, filename):
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Current", "Voc", "V_err"])
            for current_setting, (avg_voc, std_voc) in data.items():
                writer.writerow([current_setting, avg_voc, std_voc])

    # User facing method to take full pseudo JV data
    def take_pJV(self, sample_name = "sample", min_current = 300, max_current = 780, step = 20, n_wires = 2, num_measurements = 5, stabilize_time = 3, direction = "fwd"):
        ''' Method to take a pseudo-JV curve that will save the data in a csv file
        Parameters
        ----------
        sample_name : str
            The name of your sample, default is "sample"
        min_current : int
            Minimum current setting of laser, default is 300 mA
        max_current : int
            Maximum current setting of laser, default is 780 mA
        step : int
            Steps between min and max current, default is 20 mA
        n_wires : int
            The number of probes used with Keithly to measure Voc; options are 2 or 4; default is 2
        num_measurements : int
            The number of times each condition is measured and averaged, default is 5
        stabilize_time : float
            The time between laser current settings to allow laser power to stabilize, default is 3 seconds
        direction : str
            The direction of the scan: "fwd", "rev", or "fwdrev", default is "fwd"

        Returns
        -------
        Saves the data to csv file containing laser current settings, average Voc, and standard deviation 
        '''
        if direction == 'fwd':
            data = self._take_measurement(min_current, max_current, step, stabilize_time, num_measurements)
            self._save_data(data, f"{sample_name}_{direction}_data.csv")
        elif direction == 'rev':
            rev_data = self._take_measurement(max_current, min_current, -step, stabilize_time, num_measurements)
            ordered_rev_data = {key: rev_data[key] for key in sorted(rev_data)}
            self._save_data(ordered_rev_data, f"{sample_name}_{direction}_data.csv")
        elif direction == 'fwdrev':
            # Forward Scan
            fwd_data = self._take_measurement(min_current, max_current, step, stabilize_time, num_measurements)
            self._save_data(fwd_data, f"{sample_name}_fwd_data.csv")
            # Reverse Scan
            rev_data = self._take_measurement(max_current, min_current, -step, stabilize_time, num_measurements)
            ordered_rev_data = {key: rev_data[key] for key in sorted(rev_data)}
            self._save_data(ordered_rev_data, f"{sample_name}_rev_data.csv")
        else:
            print("Invalid direction. Please enter 'fwd', 'rev', or 'fwdrev'")

