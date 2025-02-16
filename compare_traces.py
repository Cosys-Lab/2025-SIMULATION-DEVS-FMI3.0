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

import h5py
import numpy as np
import matplotlib.pyplot as plt

# Note: this script contains code generated using ChatGPT (4o)

def load_simulation_data(filename):
    """
    Load simulation data from an HDF5 file.
    """
    data = {}
    with h5py.File(filename, 'r') as f:
        for key in f.keys():
            data[key] = np.array(f[key])
    return data

def compare_traces(file_python_pdevs, file_devs_fmi, plot_errors=False):
    # Load the two traces
    data_python_pdevs = load_simulation_data(file_python_pdevs)
    data_devs_fmi = load_simulation_data(file_devs_fmi)

    # Remove the extra sample at t=0.0 from data_DEVS_FMI
    if data_devs_fmi['ego_time'][0] == 0.0:
        fields_to_fix = [
            'ego_time', 'ego_position', 'ego_speed', 'ego_accel',
            'lead_time', 'lead_position', 'lead_speed', 'lead_accel',
            'time_speed', 'wanted_speed', 'time_acceleration', 'wanted_acceleration'
        ]
        for field in fields_to_fix:
            if field in data_devs_fmi:
                data_devs_fmi[field] = data_devs_fmi[field][1:]

    # Check if the time vectors are the same length and values (with a small tolerance)
    tol = 1e-12

    def check_time_vectors(vec1, vec2, name):
        if np.any(np.abs(vec1 - vec2) > tol):
            raise ValueError(f"{name} vectors do not match between DEVS_FMI and PythonPDEVS")

    check_time_vectors(data_devs_fmi['ego_time'], data_python_pdevs['ego_time'], 'ego_time')
    check_time_vectors(data_devs_fmi['lead_time'], data_python_pdevs['lead_time'], 'lead_time')
    check_time_vectors(data_devs_fmi['time_speed'], data_python_pdevs['time_speed'], 'time_speed')
    check_time_vectors(data_devs_fmi['time_acceleration'], data_python_pdevs['time_acceleration'], 'time_acceleration')

    # Calculate errors between traces
    errors = {}
    for key in data_devs_fmi.keys():
        if key in data_python_pdevs:
            errors[key] = data_devs_fmi[key] - data_python_pdevs[key]

    # Print stats
    def print_stats(name, error):
        print(f"{name},\tmax abs: {np.max(np.abs(error)):.2E},\tmean: {np.nanmean(error):.2E},\tstd: {np.nanstd(error):.2E}")

    print("\nEgo Vehicle:")
    for key in ['ego_time', 'ego_position', 'ego_speed', 'ego_accel']:
        print_stats(key, errors[key])

    print("\nLead Vehicle:")
    for key in ['lead_time', 'lead_position', 'lead_speed', 'lead_accel']:
        print_stats(key, errors[key])

    print("\nController:")
    for key in ['time_acceleration', 'wanted_acceleration']:
        print_stats(key, errors[key])

    print("\nSupervisor:")
    for key in ['time_speed', 'wanted_speed']:
        print_stats(key, errors[key])

    # Plot errors
    if plot_errors:
        def plot_error_subplot(errors, keys, title):
            fig, axes = plt.subplots(len(keys), 1, figsize=(8, len(keys) * 2))
            for i, key in enumerate(keys):
                axes[i].plot(errors[key], linewidth=1.5)
                axes[i].set_xlabel('Sample')
                axes[i].set_ylabel('Error')
                axes[i].set_title(key.replace('_', '\\_'))
                axes[i].grid(True)
            plt.suptitle(title)
            plt.show()

        plot_error_subplot(errors, ['ego_time', 'ego_position', 'ego_speed', 'ego_accel'], 'Ego Vehicle State')
        plot_error_subplot(errors, ['lead_time', 'lead_position', 'lead_speed', 'lead_accel'], 'Lead Vehicle State')
        plot_error_subplot(errors, ['time_acceleration', 'wanted_acceleration'], 'Controller Output')
        plot_error_subplot(errors, ['time_speed', 'wanted_speed'], 'Supervisor Output')


if __name__ == "__main__":
    # Example usage:
    file_python_pdevs = ".\\traces\\hdf5\\acc_system_pypdevs.h5"
    file_devs_fmi = ".\\traces\\hdf5\\acc_system_fmi.h5"

    compare_traces(file_python_pdevs, file_devs_fmi)
