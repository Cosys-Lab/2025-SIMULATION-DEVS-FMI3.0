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
import json
from fmi_importer import (Importer)
from logger import CSVLogger
from plot_acc_system_fmi import plot


def load_coupling_model(coupled_model_dir):
    """
    Loads and returns the coupling data from coupling.json inside 'coupling_dir'.

    :param coupled_model_dir: Path to the directory containing coupling.json (and FMUs).
    :return: A dictionary with the JSON data.
             Expects keys like "root_model", "components", and "connections".
    """
    coupling_file = os.path.join(coupled_model_dir, "coupling.json")

    with open(coupling_file, "r") as f:
        data = json.load(f)

    return data


def run_fmi_simulation(model_dir):
    coupling = load_coupling_model(model_dir)

    # Instantiate the example (PDEVS) importer
    importer = Importer()

    model_fmus = {}
    log_variables = []

    # Now we can access any field in coupling_data
    print("Root model:", coupling["root_model"])

    print("\nComponents:")
    for comp in coupling["components"]:
        print("  - Name:", comp["name"])
        print("    FMU: ", comp["fmu"])
        print("    Source:", comp["source"])
        fmu = importer.add_fmu(os.path.join(model_dir, comp["source"]), instance_name=comp["name"])
        model_fmus[comp["name"]] = fmu
        log_variables.append(fmu.get_model_variable_by_name('state'))

    print("\nConnections:")
    for conn in coupling["connections"]:
        print(f"  - {conn['source_model']}:{conn['source_port']} --> "
              f"{conn['dest_model']}:{conn['dest_port']}")
        importer.add_external_relation_by_names(model_fmus[conn['source_model']], conn['source_port'],
                                                model_fmus[conn['dest_model']], conn['dest_port'])
        importer.add_external_relation_by_names(model_fmus[conn['source_model']], f"{conn['source_port']}_data",
                                                model_fmus[conn['dest_model']], f"{conn['dest_port']}_data")
        log_variables.append(model_fmus[conn['source_model']].get_model_variable_by_name(f"{conn['source_port']}_data"))

    os.makedirs('.\\traces', exist_ok=True)
    logger = CSVLogger(f'.\\traces\\{coupling["root_model"]}_fmi.csv', log_variables=log_variables)
    importer.add_logger(logger)

    # Simulate until we reach 80 seconds
    importer.run_until(80.0)

    # Terminate the simulation to free the FMU instances
    importer.terminate()


def run_fmi_simulation_and_plot():
    # Run the ACC system simulation
    run_fmi_simulation('.\\generated\\acc_system')

    # Plot (and save) the results
    plot('.\\traces\\acc_system_fmi.csv')


if __name__ == '__main__':
    run_fmi_simulation_and_plot()
