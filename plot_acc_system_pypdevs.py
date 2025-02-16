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
import xmltodict
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import ast
import numpy as np
import h5py

def plot(filename):

    with open(filename) as fd:
        trace = xmltodict.parse(fd.read())

    ego_vehicle_state = []
    lead_vehicle_state = []
    setpoint = []
    output = []

    for event in trace["trace"]["event"]:
        if "port" in event:
            time = float(event['time'])
            ports = event["port"]
            ports = [ports] if isinstance(ports, dict) else ports
            for port in ports:
                if "message" in port:
                    if event["model"] == "adaptive_cruise_control.ego_vehicle.ego_vehicle_vehicle" and port["@name"] == 'vehicle_state':
                        ego_vehicle_state.append([time] + (ast.literal_eval(port["message"])))
                    elif event["model"] == "adaptive_cruise_control.lead_vehicle.lead_vehicle_vehicle" and port["@name"] == 'vehicle_state':
                        lead_vehicle_state.append([time] + (ast.literal_eval(port["message"])))
                    elif event["model"] == "adaptive_cruise_control.supervisor" and port["@name"] == 'output':
                        setpoint.append([time, ((float(port["message"])))])
                    elif event["model"] == "adaptive_cruise_control.speed_controller" and port["@name"] == 'output':
                        output.append([time, ((float(port["message"])))])

    # Convert to separate lists for plotting
    ego_time = [row[0] for row in ego_vehicle_state]  # Extract time
    ego_position = [row[1] for row in ego_vehicle_state]  # Extract position (x)
    ego_speed = [row[2] for row in ego_vehicle_state]  # Extract speed (v)
    ego_accel = [row[3] for row in ego_vehicle_state]  # Extract acceleration (a)

    lead_time = [row[0] for row in lead_vehicle_state]  # Extract time
    lead_position = [row[1] for row in lead_vehicle_state]  # Extract position (x)
    lead_speed = [row[2] for row in lead_vehicle_state]  # Extract speed (v)
    lead_accel = [row[3] for row in lead_vehicle_state]  # Extract acceleration (a)

    time_speed = [row[0] for row in setpoint]  # Extract time
    wanted_speed = [row[1] for row in setpoint]  # Extract wanted speed (v)

    time_acceleration = [row[0] for row in output]  # Extract time
    wanted_acceleration = [row[1] for row in output]  # Extract wanted speed (v)

    # Create the plot
    plt.figure(figsize=(16, 16))

    # Plot position over time
    lead_position_interpolated = np.interp(ego_time, lead_time, lead_position)
    distance = lead_position_interpolated - ego_position
    safe_distance = 10.0 + 1.4 * np.array(ego_speed, dtype=float)

    plt.rcParams.update({'font.size': 28})
    plt.rcParams.update({'legend.loc': 'best'})
    line_width = 4.0

    plt.subplot(3, 1, 1)
    plt.plot(ego_time, distance, label='Actual', linestyle='-', drawstyle='steps-post', linewidth=line_width)
    plt.plot(ego_time, safe_distance, label='Safe', linestyle='--', drawstyle='steps-post', linewidth=line_width)
    plt.ylabel('\nDistance (m)')
    plt.xlabel('Time (s)')
    plt.title('Distance Between Vehicles')
    plt.legend(ncol=2)
    plt.grid(True)

    # Plot speed over time
    plt.subplot(3, 1, 2)
    plt.plot(lead_time, lead_speed, label='Lead', linestyle='-', drawstyle='steps-post', linewidth=line_width)
    plt.plot(ego_time, ego_speed, label='Ego Actual', linestyle='--', drawstyle='steps-post', linewidth=line_width)
    plt.plot(time_speed, wanted_speed, label='Ego Wanted', linestyle='-.', drawstyle='steps-post', linewidth=line_width)
    plt.ylabel('\nSpeed (m/s)')
    plt.xlabel('Time (s)')
    plt.title('Vehicle Speeds')
    plt.legend(ncol=3)
    plt.grid(True)

    # Plot acceleration over time
    plt.subplot(3, 1, 3)
    plt.plot(lead_time, lead_accel, label='Lead', linestyle='-', drawstyle='steps-post', linewidth=line_width)
    plt.plot(ego_time, ego_accel, label='Ego Actual', linestyle='--', drawstyle='steps-post', linewidth=line_width)
    plt.plot(time_acceleration, wanted_acceleration, label='Ego Wanted', linestyle='-.', drawstyle='steps-post', linewidth=line_width)
    plt.ylabel('Acceleration\n(m/(s^2))')
    plt.xlabel('Time (s)')
    plt.title('Vehicle Accelerations')
    plt.legend(ncol=3)
    plt.grid(True)

    # Adjust layout and show the plots
    #plt.suptitle("PythonPDEVS")
    plt.tight_layout()
    os.makedirs('.\\traces\\plots\\', exist_ok=True)
    plt.savefig(".\\traces\\plots\\acc_system_pypdevs.pdf", format="pdf", bbox_inches="tight")
    plt.savefig(".\\traces\\plots\\acc_system_pypdevs.png", format="png", bbox_inches="tight")
    plt.show(block=False)
    plt.pause(0.001)

    # Save data to hdf5 file
    os.makedirs('.\\traces\\hdf5\\', exist_ok=True)
    with h5py.File('.\\traces\\hdf5\\acc_system_pypdevs.h5', 'w') as hf:
        hf.create_dataset('ego_time', data=ego_time)
        hf.create_dataset('ego_position', data=ego_position)
        hf.create_dataset('ego_speed', data=ego_speed)
        hf.create_dataset('ego_accel', data=ego_accel)

        hf.create_dataset('lead_time', data=lead_time)
        hf.create_dataset('lead_position', data=lead_position)
        hf.create_dataset('lead_speed', data=lead_speed)
        hf.create_dataset('lead_accel', data=lead_accel)

        hf.create_dataset('time_speed', data=time_speed)
        hf.create_dataset('wanted_speed', data=wanted_speed)

        hf.create_dataset('time_acceleration', data=time_acceleration)
        hf.create_dataset('wanted_acceleration', data=wanted_acceleration)


if __name__ == "__main__":
    plot('.\\traces\\acc_system_pypdevs.xml')
