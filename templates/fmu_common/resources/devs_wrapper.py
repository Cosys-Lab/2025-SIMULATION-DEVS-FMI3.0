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

# This class provides a generic DEVS wrapper that provides a generic interface for both atomic and coupled devs models
from pypdevs.DEVS import AtomicDEVS, CoupledDEVS, directConnect
import math

class DEVSWrapper:
    def __init__(self, model):

        self.model = model

        if isinstance(model, AtomicDEVS):
            self.type = "atomic"
            self._models = [model]
        elif isinstance(model, CoupledDEVS):
            self.type = "coupled"
            # If it is a coupled DEVS model, we need to flatten it using the direct connection approach
            model.component_set = directConnect(model.component_set, {})
            self._models = model.component_set
        else:
            raise ValueError("Unsupported model type")

        self._outputs = None

    def increment_elapsed(self, time_step):
        # TODO: Check if elapsed would be >= time advance and signal early return?
        for model in self._models:
            model.elapsed = (0.0 if model.elapsed is None else model.elapsed) + time_step

    def get_state(self):
        state = {}
        for model in self._models:
            state[model.name] = str(model.state)
        return state

    def timeAdvance(self):
        return min(model.timeAdvance() for model in self._models)

    def outputFnc(self):
        # Get models about to transition
        imm = [m for m in self._models if m.elapsed is not None and math.isclose(m.elapsed, m.timeAdvance())]

        # Get outputs of models about to transition
        for model in imm:
            model.my_output = model.outputFnc()
        self._outputs = [model.my_output for model in imm]

        # Get "external" outputs
        # For atomic models, outputs wil be OPorts
        if self.type == "atomic":
            return self._outputs[0] if self._outputs else []

        # For coupled models, we need to follow the connections from component output ports to "external" OPorts
        elif self.type == "coupled":
            external_outputs = {}
            for output in self._outputs:
                for port, message in output.items():
                    outline = getattr(port, 'outline', [])
                    for dst_port in outline:
                        if dst_port in self.model.OPorts:
                            # external_outputs[dst_port] = message
                            external_outputs.setdefault(dst_port, []).append(message[0])

            return external_outputs

    def transition(self, external_inputs, time):
        if self.type == "atomic":
            return self.atomic_transition(external_inputs, time)
        elif self.type == "coupled":
            return self.coupled_transition(external_inputs, time)

    def atomic_transition(self, external_inputs, time):
        imm = self.model.elapsed is not None and math.isclose(self.model.elapsed, self.model.timeAdvance())
        inf = bool(external_inputs)
        self.model.my_input = external_inputs
        if inf:
            if imm:
                # Confluent transition
                self.model.elapsed = 0.0
                self.model.state = self.model.confTransition(self.model.my_input)
                self.model.time_last = (time, 1)
                self.model.my_output = {}
            else:
                # External transition
                self.model.state = self.model.extTransition(self.model.my_input)
                self.model.elapsed = 0.0
                self.model.time_last = (time, 1)
                self.model.my_output = {}
        elif imm:
            # Internal transition
            self.model.elapsed = None
            self.model.state = self.model.intTransition()
            self.model.time_last = (time, 1)
            self.model.my_output = {}

        return inf or imm

    def coupled_transition(self, external_inputs, time):
        imm = [m for m in self._models if m.elapsed is not None and math.isclose(m.elapsed, m.timeAdvance())]
        inf = []
        inputs = {}

        # Exchange events between components (if coupled)
        for output in self._outputs:
            for port, message in output.items():
                # Internal connections (for coupled models)
                if hasattr(port, 'routing_outline'):
                    for outline, z in port.routing_outline:
                        dst = outline.host_DEVS
                        dst_port = outline

                        if dst not in inputs:
                            inputs[dst] = {}

                        # TODO: add support for z functions
                        inputs[dst][dst_port] = message

                        inf.append(dst)

        # "Inject" inputs from "external" input port(s):
        for port, message in external_inputs.items():
            # Internal connections (for coupled models)
            if hasattr(port, 'outline'):
                for outline in port.outline:
                    dst = outline.host_DEVS
                    dst_port = outline

                    if dst not in inputs:
                        inputs[dst] = {}

                    # TODO: add support for z functions
                    inputs[dst][dst_port] = message

                    inf.append(dst)

        # Update states
        for model in self._models:
            model.my_input = inputs.get(model, {})
            if model in inf:
                if model in imm:
                    # Confluent transition
                    model.elapsed = 0
                    model.state = model.confTransition(model.my_input)
                    model.time_last = (time, 1)
                    model.my_output = {}
                else:
                    # External transition
                    model.state = model.extTransition(model.my_input)
                    model.elapsed = 0
                    model.time_last = (time, 1)
                    model.my_output = {}
            elif model in imm:
                # Internal transition
                model.elapsed = None
                model.state = model.intTransition()
                model.time_last = (time, 1)
                model.my_output = {}

        return bool(imm or inf)
