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

from pypdevs.simulator import Simulator
from acc_models_instrumented import AdaptiveCruiseControlSystem
import os
from plot_acc_system_pypdevs import plot


def run_pypdevs_simulation(trace_file):
    # Instantiate the model
    cruise_control = AdaptiveCruiseControlSystem(name="adaptive_cruise_control",
                                                 lead_vehicle_interval=0.1,
                                                 ego_vehicle_interval=0.1,
                                                 controller_interval=0.1,
                                                 supervisor_interval=0.1,
                                                 supervisor_Kp=1.0,
                                                 supervisor_Kd=0.05,
                                                 controller_Kp=4.0,
                                                 controller_Kd=1.0)

    # Set up the simulator
    sim = Simulator(cruise_control)

    # Set up end time
    sim.setTerminationTime(80.0)

    # Set up logging
    sim.setXML(trace_file)
    sim.setVerbose(None)

    # Simulate
    sim.simulate()


def run_pypdevs_simulation_and_plot():
    os.makedirs('.\\traces', exist_ok=True)
    trace_file = '.\\traces\\acc_system_pypdevs.xml'

    # Run simulation
    run_pypdevs_simulation(trace_file)

    # Plot (and save) results
    plot(trace_file)


if __name__ == "__main__":
    run_pypdevs_simulation_and_plot()
