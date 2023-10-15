import numpy as np
import pandas as pd
import csv
from time import sleep

#import from computer
from PLQY.ldc502 import LDC502
from frghardware.keithleyjv import control3
plus_minus = u"\u00B1"

#Version 8

class pJV:
    ''' A class to take pseudo JV curves '''
    def __init__(self):
        self.ldc = LDC502("COM24")
        self.JVcode = control3.Control(address='GPIB1::22::INSTR')
        self.laser_wl = 532
        self.LASERSTABILIZETIME = 3.0
        self.laser_current = self.ldc.get_laser_current()
        self.laser_temp = self.ldc.get_laser_temp()

    # Function to take intensity dependent voltage measurments of a cell: 
    def take_pJV(self, sample_name = "sample", min_current = 300, max_current = 800, step = 20, n_wires = 2, num_measurements = 5):
        ''' Method to take a pseudo-JV curve that will save the data in a csv file
        Parameters
        ---------
        sample_name : str
            The name of your sample
        min_current : int
            Minimum current setting of laser
        max_curent : int
            Maximum current setting of laser
        step : int
            Steps between min and max current
        n_wires : int
            The number of probes you are using with the Keithly to measure Voc
        num_measurements : int
            The number of times each condition is measured and averaged
        '''
            sample name
        self.ldc.set_laserOn()
        self.ldc.set_tecOn()
        self.ldc.set_modulationOff()
        print("Laser and TEC turned on, modulation turned off.")
        print('\nSetting Laser Current and waiting to stabilize...')
        data = {}
        self.JVcode.keithley.wires = n_wires

        for current_setting in np.arange(min_current, max_current, step):
            voc_list = []
            if np.abs(self.ldc.get_laser_current() - current_setting) > 2:
                self.ldc.set_laserCurrent(current_setting)
                sleep(self.LASERSTABILIZETIME)
            else:
                self.ldc.set_laserCurrent(current_setting)

            print('\nLaser Current Set and Stable.')
            sleep(1)

            # Take 5 measurments
            for _ in range(num_measurements):
                voc = self.JVcode.voc()
                voc_list.append(voc)
                sleep(0.3)
            # Calculate average     
            avg_voc= np.mean(voc_list)
            std_voc = np.std(voc_list) 

            print(f"At current = {current_setting} mA, average Voc = {avg_voc} {plus_minus} {std_voc} V")
            data[current_setting] = (avg_voc, std_voc) # Store data in dictionary

        # Save data: 
        csv_filename = f"{sample_name}_data.csv"
        with open(csv_filename, mode = 'w', newline = '') as file:
            writer = csv.writer(file)
            writer.writerow(["Current", "Voc", "V_err"])  # Write header row
            for current_setting, (avg_voc, std_voc) in data.items():
                writer.writerow([current_setting, avg_voc, std_voc]) #Write data rows

        print(f"Data saved to {csv_filename}")

        
