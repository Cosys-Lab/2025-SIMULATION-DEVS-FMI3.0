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
import fmpy


class FMUInstance:
    def __init__(self, fmu_path, instance_name=None):
        self.fmu_path = os.path.abspath(fmu_path)
        self.fmu = None
        self.fmu_name = None
        self.model_description = None
        self.instance_name = instance_name
        self.has_event_mode = None

        self.data = {}
        self.clocks = {}
        self.internal_relations = []

        self.load_and_instantiate_fmu()

    def load_and_instantiate_fmu(self):
        if os.path.isdir(self.fmu_path):
            unzip_dir = self.fmu_path
        else:
            unzip_dir = fmpy.extract(self.fmu_path)

        self.model_description = fmpy.read_model_description(unzip_dir)
        self.fmu_name = self.model_description.modelName
        if not self.instance_name:
            self.instance_name = self.fmu_name
        self.has_event_mode = self.model_description.coSimulation.hasEventMode

        for variable in self.model_description.modelVariables:
            if variable.type.lower() == 'clock':
                clock = Clock(self, variable.name, variable.valueReference, variable.causality.lower(),
                              variable.intervalVariability.lower(), variable.description)
                self.clocks[clock.value_reference] = clock
            else:
                data = Data(self, variable.name, variable.valueReference, variable.causality.lower(),
                            variable.variability.lower(), variable.description, data_type=variable.type,
                            initial_value=variable.start)

                # If it's a clocked variable, add associated clocks to data object by value references
                if variable.clocks:
                    data.clocks.extend(clock.valueReference for clock in variable.clocks)

                self.data[data.value_reference] = data

        # Add internal relations (dependencies)
        for output in self.model_description.outputs:
            for dependency in output.dependencies:
                internal_relation = InternalRelation(self,
                                                     self.get_model_variable_by_value_reference(
                                                         dependency.valueReference),
                                                     self.get_model_variable_by_value_reference(
                                                         output.variable.valueReference))
                self.internal_relations.append(internal_relation)

        # Actually instantiate the FMU
        fmu_args = {
            'guid': self.model_description.guid,
            'unzipDirectory': unzip_dir,
            'instanceName': self.instance_name,
            'modelIdentifier': self.model_description.coSimulation.modelIdentifier,
            'fmiCallLogger': None,
            'requireFunctions': True
        }

        # TODO: currently this only support FMI3 FMUs ('generic' fmpy.instantiate_fmu() does not support instanceName)
        self.fmu = fmpy.fmi3.FMU3Slave(**fmu_args)
        self.fmu.instantiate(visible=False, loggingOn=False, eventModeUsed=True, earlyReturnAllowed=False,
                             logMessage=None, intermediateUpdate=None)

    def get_model_variable_by_value_reference(self, value_reference):
        # Check in self.data
        data_variable = self.data.get(value_reference)

        if data_variable is not None:
            return data_variable

        # If not found in self.data, check in self.clocks
        clock_variable = self.clocks.get(value_reference)

        return clock_variable

    def get_model_variable_by_name(self, name):
        # Check in self.data
        data_variable = next((variable for variable in self.data.values() if variable.name == name), None)

        if data_variable:
            return data_variable

        # If not found in self.data, check in self.clocks
        clock_variable = next((clock for clock in self.clocks.values() if clock.name == name), None)

        return clock_variable


class ModelVariable:
    def __init__(self, fmu_instance, name, value_reference, causality, description=None):
        self.fmu_instance = fmu_instance
        self.name = name
        self.value_reference = value_reference
        self.causality = causality
        self.description = description

    def __str__(self):
        return '%s.%s' % (self.fmu_instance.instance_name, self.name)


class Data(ModelVariable):
    def __init__(self, fmu_instance, name, value_reference, causality, variability, description=None, data_type='real',
                 initial_value=None, clocks=None):
        super().__init__(fmu_instance, name, value_reference, causality, description)
        self.variability = variability
        self.data_type = data_type
        self.value = initial_value
        if clocks:
            self.clocks = clocks
        else:
            self.clocks = []

    def set_value(self, value):
        data_type = self.data_type.lower()

        # FMI2.0
        if data_type == 'real':
            self.fmu_instance.fmu.setReal([self.value_reference], [value])
        elif data_type == 'integer':
            self.fmu_instance.fmu.setInteger([self.value_reference], [int(value)])
        elif data_type == 'boolean':
            self.fmu_instance.fmu.setBoolean([self.value_reference], [bool(value)])
        elif data_type == 'string':
            self.fmu_instance.fmu.setString([self.value_reference], [str(value)])

        # FMI3.0
        elif data_type == 'float32':
            self.fmu_instance.fmu.setFloat32([self.value_reference], [value])
        elif data_type == 'float64':
            self.fmu_instance.fmu.setFloat64([self.value_reference], [value])
        elif data_type == 'int8':
            self.fmu_instance.fmu.setInt8([self.value_reference], [int(value)])
        elif data_type == 'uint8':
            self.fmu_instance.fmu.setUInt8([self.value_reference], [int(value)])
        elif data_type == 'int16':
            self.fmu_instance.fmu.setInt16([self.value_reference], [int(value)])
        elif data_type == 'uint16':
            self.fmu_instance.fmu.setUInt16([self.value_reference], [int(value)])
        elif data_type == 'int32':
            self.fmu_instance.fmu.setInt32([self.value_reference], [int(value)])
        elif data_type == 'uint32':
            self.fmu_instance.fmu.setUInt32([self.value_reference], [int(value)])
        elif data_type == 'int64':
            self.fmu_instance.fmu.setInt64([self.value_reference], [int(value)])
        elif data_type == 'uint64':
            self.fmu_instance.fmu.setUInt64([self.value_reference], [int(value)])
        elif data_type == 'boolean':
            self.fmu_instance.fmu.setBoolean([self.value_reference], [bool(value)])
        elif data_type == 'string':
            self.fmu_instance.fmu.setString([self.value_reference], [str(value)])

        else:
            raise ValueError(f"ERROR: set_value unsupported data type '{data_type}' for variable '{self.name}'")

    def get_value(self):
        data_type = self.data_type.lower()

        # FMI2.0
        if data_type == 'real':
            value = self.fmu_instance.fmu.getReal([self.value_reference])[0]
        elif data_type == 'integer':
            value = self.fmu_instance.fmu.getInteger([self.value_reference])[0]
        elif data_type == 'boolean':
            value = self.fmu_instance.fmu.getBoolean([self.value_reference])[0]
        elif data_type == 'string':
            value = self.fmu_instance.fmu.getString([self.value_reference])[0]

        # FMI3.0
        elif data_type == 'float32':
            value = self.fmu_instance.fmu.getFloat32([self.value_reference])[0]
        elif data_type == 'float64':
            value = self.fmu_instance.fmu.getFloat64([self.value_reference])[0]
        elif data_type == 'int8':
            value = self.fmu_instance.fmu.getInt8([self.value_reference])[0]
        elif data_type == 'uint8':
            value = self.fmu_instance.fmu.getUInt8([self.value_reference])[0]
        elif data_type == 'int16':
            value = self.fmu_instance.fmu.getInt16([self.value_reference])[0]
        elif data_type == 'uint16':
            value = self.fmu_instance.fmu.getUInt16([self.value_reference])[0]
        elif data_type == 'int32':
            value = self.fmu_instance.fmu.getInt32([self.value_reference])[0]
        elif data_type == 'uint32':
            value = self.fmu_instance.fmu.getUInt32([self.value_reference])[0]
        elif data_type == 'int64':
            value = self.fmu_instance.fmu.getInt64([self.value_reference])[0]
        elif data_type == 'uint64':
            value = self.fmu_instance.fmu.getUInt64([self.value_reference])[0]
        elif data_type == 'boolean':
            value = self.fmu_instance.fmu.getBoolean([self.value_reference])[0]
        elif data_type == 'string':
            value = self.fmu_instance.fmu.getString([self.value_reference])[0]

        else:
            raise ValueError(f"ERROR: get_value unsupported data type '{data_type}' for variable '{self.name}'")
            value = None

        return value

    def get_and_store_value(self):
        self.value = self.get_value()


class Clock(ModelVariable):
    def __init__(self, fmu_instance, name, value_reference, causality, interval_variability, description=None):
        super().__init__(fmu_instance, name, value_reference, causality, description)
        self.interval_variability = interval_variability
        self.value = False

    def activate_clock(self):
        self.fmu_instance.fmu.setClock([self.value_reference], [True])

    def deactivate_clock(self):
        self.fmu_instance.fmu.setClock([self.value_reference], [False])
        # Todo: should deactivating a clock also set its value attribute to False?

    def get_state(self):
        return self.fmu_instance.fmu.getClock([self.value_reference])[0]

    def get_and_store_activation_state(self):
        self.value = self.get_state()
        return self.value


class InternalRelation:
    def __init__(self, fmu, model_variable_from, model_variable_to):
        self.fmu = fmu
        self.model_variable_from = model_variable_from
        self.model_variable_to = model_variable_to
