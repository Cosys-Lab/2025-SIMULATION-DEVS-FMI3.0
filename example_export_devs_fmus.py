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

from acc_models_instrumented import *
from devs_fmu_exporter import export_fmu, export_coupled_model

# Example exporting a single (atomic or coupled) PythonPDEVS model as an FMU
# Instantiate the PythonPDEVS model
model = Sine(name="sine_generator", interval=0.1, amplitude=0.6, omega=0.2)
# Export as FMU using UniFMU
export_fmu(model, output_dir='.\\generated\\sine_generator')

# Example exporting a coupled PythonPDEVS model as co-simulation package, containing FMUs for each component of the
# coupled model + a coupling.json describing their connections
# Instantiate the coupled model
acc_system = AdaptiveCruiseControlSystem(name="acc_system")
# Export to co-simulation package
export_coupled_model(acc_system, output_dir='.\\generated\\acc_system')





