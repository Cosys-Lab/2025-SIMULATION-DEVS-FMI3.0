"""
2025-SIMULATION-DEVS-FMI3.0
Copyright (C) 2025 Cosys-lab, University of Antwerp

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import csv

class Logger:
    def __init__(self, file_path, log_variables=None):
        self.file_path = os.path.abspath(file_path)
        if log_variables:
            self.log_variables = log_variables
        else:
            self.log_variables = []

class CSVLogger(Logger):
    def __init__(self, file_path, log_variables=None):
        super().__init__(file_path, log_variables)
        self.filehandle = None
        self.csv_writer = None

    def add_log_variable(self, variable):
        self.log_variables.append(variable)

    def start(self):
        # Open the file and initialize the CSV writer
        self.filehandle = open(self.file_path, 'w', newline='', encoding='utf-8')
        self.csv_writer = csv.writer(self.filehandle, quoting=csv.QUOTE_MINIMAL)

        # Write the header row
        header = ['time']
        header.extend([log_variable.__str__() for log_variable in self.log_variables])
        self.csv_writer.writerow(header)

    def add_sample(self, time):
        # Write a row of data
        row = [time]
        row.extend([log_variable.get_value() for log_variable in self.log_variables])
        self.csv_writer.writerow(row)

    def terminate(self):
        # Close the filehandle
        if self.filehandle:
            self.filehandle.close()