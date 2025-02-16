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

# Import code for DEVS model representation:
from pypdevs.DEVS import AtomicDEVS, CoupledDEVS, DEVSException
from logging_atomic_devs import LoggingAtomicDEVS as AtomicDEVS
from pypdevs.infinity import INFINITY
import math


class VehicleState:
    """
    Encapsulates the vehicle's state
    """

    def __init__(self, state=None):
        """
        Constructor
        """
        # Initialize the state as a dictionary
        self.__state = {
            'state': 'idle',  # Overall (DEVS) state
            'x': 0.0,  # Position
            'v': 0.0,  # Velocity
            'a': 0.0,  # Acceleration
            'a_wanted': 0.0,  # Commanded acceleration
        }

        if state:
            self.__state.update(state)

    def set(self, data):
        """
        Updates the internal state with the provided data.

        :param data: Dictionary containing new state values.
        """
        self.__state.update(data)

    def get(self):
        """
        Retrieves the current state as a dictionary.

        :return: The current state dictionary.
        """
        return self.__state

    def __str__(self):
        """
        Provides a string representation of the current state.

        :return: A formatted string representation of the state.
        """
        return str(self.__state['state'])

    def toXML(self):
        return "<mode>%s</mode>" % self.__str__()


class Vehicle(AtomicDEVS):
    """
    Simple vehicle model
    """

    def __init__(self, name=None, x0=0.0, v0=0.0, a0=0.0):
        """
        Constructor (parameterizable).
        """
        # Always call parent class' constructor FIRST:
        AtomicDEVS.__init__(self, name)

        # STATE:
        #  Define 'state' attribute (initial sate):
        state = VehicleState().get()
        state['x'] = x0
        state['v'] = v0
        state['a'] = a0
        self.state = VehicleState(state)

        # PORTS:
        #  Declare as many input and output ports as desired
        #  (usually store returned references in local variables):
        self.UPDATE_STATE = self.addInPort(name="update_state")
        self.UPDATE_A_WANTED = self.addInPort(name="update_a_wanted")

        self.VEHICLE_STATE = self.addOutPort(name="vehicle_state")

    def extTransition(self, inputs):
        """
        External Transition Function.
        """
        # Compute the new state 'Snew' based (typically) on current
        # State, Elapsed time parameters and calls to 'self.peek(self.IN)'.
        update_state = inputs.get(self.UPDATE_STATE)
        update_a_wanted = inputs.get(self.UPDATE_A_WANTED)

        state = self.state.get()

        if state['state'] == 'idle':
            # state['state'] = 'update_as'
            if update_state:
                # Semi-implicit Euler
                state['a'] = state['a'] + self.elapsed * 2.0 * (state['a_wanted'] - state['a'])
                state['v'] = state['v'] + self.elapsed * state['a']
                state['x'] = state['x'] + self.elapsed * state['v']
                state['state'] = 'update_state'
            if update_a_wanted:
                state['a_wanted'] = update_a_wanted[0]
            new_state = VehicleState(state)
            self.logExtTransition(new_state)
            return new_state
        elif state['state'] == 'update_state':
            if update_a_wanted:
                state['a_wanted'] = update_a_wanted[0]
            new_state = VehicleState(state)
            self.logExtTransition(new_state)
            return new_state
        else:
            raise DEVSException(
                "Unsupported state <%s> in Vehicle external transition function" % state['state']
            )

    def intTransition(self):
        """
        Internal Transition Function.
        """

        state = self.state.get()

        if state['state'] == 'update_state':
            state['state'] = 'idle'
            new_state = VehicleState(state)
            self.logIntTransition(new_state)
            return new_state
        else:
            raise DEVSException(
                "Unsupported state <%s> in Vehicle internal transition function" % state['state']
            )

    def outputFnc(self):
        """
        Output Function.
        """
        state = self.state.get()

        if state['state'] == 'update_state':
            return {self.VEHICLE_STATE: [[state['x'], state['v'], state['a']]]}
        elif state['state'] == 'idle':
            return {}
        else:
            raise DEVSException(
                "Unsupported state <%s> in Vehicle external transition function" % state['state']
            )

    def timeAdvance(self):
        """
        Time-Advance Function.
        """
        # Compute 'ta', the time to the next scheduled internal transition,
        # based (typically) on current State.
        state = self.state.get()
        if state['state'] == 'idle':
            return INFINITY
        # elif state['state'] == 'update_as':
        #     return 0
        elif state['state'] == 'update_state':
            return 0
        else:
            raise DEVSException(
                "Unsupported state <%s> in Vehicle time advance transition function" % state['state']
            )


class GenericState:
    """
    Encapsulates a generic state
    """

    def __init__(self, value):
        """
        Constructor
        """
        # Initialize the state as a dictionary
        self.__state = value

    def set(self, data):
        """
        Updates the internal state with the provided data.

        :param data: Dictionary containing new state values.
        """
        self.__state = data

    def get(self):
        """
        Retrieves the current state as a dictionary.

        :return: The current state dictionary.
        """
        return self.__state

    def __str__(self):
        """
        Provides a string representation of the current state.

        :return: A formatted string representation of the state.
        """
        return str(self.__state)

    def toXML(self):
        return "<mode>%s</mode>" % self.__str__()


class Generator(AtomicDEVS):
    """
    The generator
    """

    def __init__(self, name=None, interval=INFINITY):
        """
        Constructor (parameterizable).
        """
        # Always call parent class' constructor FIRST:
        AtomicDEVS.__init__(self, name)
        self.interval = interval

        # STATE:
        #  Define 'state' attribute (initial sate):
        self.state = GenericState('idle')

        # PORTS:
        #  Declare as many input and output ports as desired
        #  (usually store returned references in local variables):
        self.UPDATE_STATE = self.addOutPort(name="update_state")

    def extTransition(self, inputs):
        """
        External Transition Function.
        """
        state = self.state.get()

        raise DEVSException(
            "Unsupported state <%s> in Generator external transition function" % state
        )

    def intTransition(self):
        """
        Internal Transition Function.
        """

        state = self.state.get()

        if state == 'idle':
            state = GenericState('idle')
            self.logExtTransition(state)
            return state
        else:
            raise DEVSException(
                "Unsupported state <%s> in Generator internal transition function" % state
            )

    def outputFnc(self):
        """
        Output Function.
        """
        state = self.state.get()

        if state == 'idle':
            return {self.UPDATE_STATE: [1.0]}
        else:
            raise DEVSException(
                "Unsupported state <%s> in Generator external transition function" % state
            )

    def timeAdvance(self):
        """
        Time-Advance Function.
        """
        # Compute 'ta', the time to the next scheduled internal transition,
        # based (typically) on current State.
        state = self.state.get()
        if state == 'idle':
            return self.interval
        else:
            raise DEVSException(
                "Unsupported state <%s> in Generator time advance transition function" % state
            )


class SignalState:
    """
    Encapsulates the state for the stimuli generator(s)
    """

    def __init__(self, state=None):
        """
        Constructor
        """
        # Initialize the state as a dictionary
        self.__state = {
            'state': 'idle',  # Overall (DEVS) state
            't': 0.0,  # Time
            'y': 0.0,  # Value
        }

        if state:
            self.__state.update(state)

    def set(self, data):
        """
        Updates the internal state with the provided data.

        :param data: Dictionary containing new state values.
        """
        self.__state.update(data)

    def get(self):
        """
        Retrieves the current state as a dictionary.

        :return: The current state dictionary.
        """
        return self.__state

    def __str__(self):
        """
        Provides a string representation of the current state.

        :return: A formatted string representation of the state.
        """
        return str(self.__state['state'])

    def toXML(self):
        return "<mode>%s</mode>" % self.__str__()


class Sine(AtomicDEVS):
    """
    Sine generator for input stimuli
    """

    def __init__(self, name=None, interval=INFINITY, amplitude=0.0, omega=0.0, offset=0.0):
        """
        Constructor (parameterizable).
        """
        # Always call parent class' constructor FIRST:
        AtomicDEVS.__init__(self, name)
        self.interval = interval
        self.amplitude = amplitude
        self.omega = omega
        self.offset = offset

        # STATE:
        #  Define 'state' attribute (initial sate):
        state = SignalState().get()
        state['t'] = 0.0
        state['v'] = self.amplitude * math.sin(self.omega * state['t']) + self.offset
        self.state = SignalState(state)

        # PORTS:
        #  Declare as many input and output ports as desired
        #  (usually store returned references in local variables):
        self.VALUE = self.addOutPort(name="value")

    def extTransition(self, inputs):
        """
        External Transition Function.
        """
        state = self.state.get()

        raise DEVSException(
            "Unsupported state <%s> in Sine external transition function" % state
        )

    def intTransition(self):
        """
        Internal Transition Function.
        """

        state = self.state.get()

        if state['state'] == 'idle':

            state['t'] = state['t'] + self.interval
            state['v'] = self.amplitude * math.sin(self.omega * state['t']) + self.offset

            state = SignalState(state)
            self.logIntTransition(state)
            return state
        else:
            raise DEVSException(
                "Unsupported state <%s> in Sine internal transition function" % state
            )

    def outputFnc(self):
        """
        Output Function.
        """
        state = self.state.get()

        if state['state'] == 'idle':
            return {self.VALUE: [state['v']]}
        else:
            raise DEVSException(
                "Unsupported state <%s> in Sine external transition function" % state
            )

    def timeAdvance(self):
        """
        Time-Advance Function.
        """
        # Compute 'ta', the time to the next scheduled internal transition,
        # based (typically) on current State.
        state = self.state.get()
        if state['state'] == 'idle':
            return self.interval
        else:
            raise DEVSException(
                "Unsupported state <%s> in Sine time advance transition function" % state
            )


class ControllerState:
    """
    Encapsulates the (Cruise) Controller's state
    """

    def __init__(self, state=None):
        """
        Constructor
        """
        # Initialize the state as a dictionary
        self.__state = {
            'state': 'idle',  # Overall (DEVS) state
            'integral': 0.0,  # Integral term
            'error_prev': 0.0,  # Previous error
            'setpoint': 0.0,  # Setpoint
            'actual': 0.0,  # Current actual value
            'output': 0.0,  # Controller output
        }

        if state:
            self.__state.update(state)

    def set(self, data):
        """
        Updates the internal state with the provided data.

        :param data: Dictionary containing new state values.
        """
        self.__state.update(data)

    def get(self):
        """
        Retrieves the current state as a dictionary.

        :return: The current state dictionary.
        """
        return self.__state

    def __str__(self):
        """
        Provides a string representation of the current state.

        :return: A formatted string representation of the state.
        """
        return str(self.__state['state'])

    def toXML(self):
        return "<mode>%s</mode>" % self.__str__()


class SpeedController(AtomicDEVS):
    """
    Cruise controller model
    """

    def __init__(self, name=None, Kp=4.0, Ki=0.0, Kd=1.0):
        """
        Constructor (parameterizable).
        """
        # Always call parent class' constructor FIRST:
        AtomicDEVS.__init__(self, name)
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd

        # STATE:
        #  Define 'state' attribute (initial sate):
        state = ControllerState().get()
        self.state = ControllerState(state)

        # PORTS:
        #  Declare as many input and output ports as desired
        #  (usually store returned references in local variables):
        self.UPDATE_STATE = self.addInPort(name="update_state")
        self.UPDATE_SETPOINT = self.addInPort(name="update_setpoint")
        self.VEHICLE_STATE = self.addInPort(name="vehicle_state")

        self.OUTPUT = self.addOutPort(name="output")

    def extTransition(self, inputs):
        """
        External Transition Function.
        """
        # Compute the new state 'Snew' based (typically) on current
        # State, Elapsed time parameters and calls to 'self.peek(self.IN)'.
        update_state = inputs.get(self.UPDATE_STATE)
        update_setpoint = inputs.get(self.UPDATE_SETPOINT)
        vehicle_state = inputs.get(self.VEHICLE_STATE)

        state = self.state.get()

        if state['state'] == 'idle':
            # state['state'] = 'update_as'
            if vehicle_state:
                state['actual'] = vehicle_state[0][1]
            if update_setpoint:
                state['setpoint'] = update_setpoint[0]
            if update_state:
                error = state['setpoint'] - state['actual']
                state['integral'] = state['integral'] + (error * self.elapsed)
                d_error = (error - state['error_prev']) / self.elapsed
                output = (self.Kp * error) + (self.Ki * state['integral']) + (self.Kd * d_error)
                state['output'] = max(min(output, 2.0), -3.0)
                state['error_prev'] = error
                state['state'] = 'update_state'
            state = ControllerState(state)
            self.logExtTransition(state)
            return state

        elif state['state'] == 'update_state':
            if vehicle_state:
                state['actual'] = vehicle_state[0][1]
            if update_setpoint:
                state['setpoint'] = update_setpoint[0]
            state = ControllerState(state)
            self.logExtTransition(state)
            return state

        else:
            raise DEVSException(
                "Unsupported state <%s> in Vehicle external transition function" % state['state']
            )

    def intTransition(self):
        """
        Internal Transition Function.
        """

        state = self.state.get()

        if state['state'] == 'update_state':
            state['state'] = 'idle'
            state = ControllerState(state)
            self.logIntTransition(state)
            return state
        else:
            raise DEVSException(
                "Unsupported state <%s> in Vehicle internal transition function" % state['state']
            )

    def outputFnc(self):
        """
        Output Function.
        """
        state = self.state.get()

        if state['state'] == 'update_state':
            return {self.OUTPUT: [state['output']]}
        elif state['state'] == 'idle':
            return {}
        else:
            raise DEVSException(
                "Unsupported state <%s> in Vehicle external transition function" % state['state']
            )

    def timeAdvance(self):
        """
        Time-Advance Function.
        """
        # Compute 'ta', the time to the next scheduled internal transition,
        # based (typically) on current State.
        state = self.state.get()
        if state['state'] == 'idle':
            return INFINITY
        elif state['state'] == 'update_state':
            return 0
        else:
            raise DEVSException(
                "Unsupported state <%s> in Vehicle time advance transition function" % state['state']
            )


class SupervisorPIDState:
    """
    Encapsulates the Supervisor's state
    """

    def __init__(self, state=None):
        """
        Constructor
        """
        # Initialize the state as a dictionary
        self.__state = {
            'state': 'idle',  # Overall (DEVS) state
            'ego_init': False,  # Whether we have received at least one state update from the ego car
            'lead_init': False,  # Whether we have received at least one state update from the lead car
            'v_ego': 0.0,  # Speed of the ego car
            'v_lead': 0.0,  # Speed of the lead car
            'x_ego': 0.0,  # Position of the ego car
            'x_lead': 0.0,  # Position of the lead car
            'v_wanted': 0.0,  # Wanted speed (for the speed controller)
            'integral': 0.0,  # Integral term
            'error_prev': 0.0,  # Previous error
            'setpoint': 0.0,  # Setpoint
            'actual': 0.0,  # Current actual value
        }

        if state:
            self.__state.update(state)

    def set(self, data):
        """
        Updates the internal state with the provided data.

        :param data: Dictionary containing new state values.
        """
        self.__state.update(data)

    def get(self):
        """
        Retrieves the current state as a dictionary.

        :return: The current state dictionary.
        """
        return self.__state

    def __str__(self):
        """
        Provides a string representation of the current state.

        :return: A formatted string representation of the state.
        """
        return str(self.__state['state'])

    def toXML(self):
        return "<mode>%s</mode>" % self.__str__()


class SupervisorPID(AtomicDEVS):
    """
    Supervisor model
    """

    def __init__(self, name=None, v_limit=30.0, d_default=10.0, t_gap=1.4, Kp=1.0, Ki=0.0, Kd=0.05):
        """
        Constructor (parameterizable).
        """
        # Always call parent class' constructor FIRST:
        AtomicDEVS.__init__(self, name)
        self.v_limit = v_limit
        self.d_default = d_default
        self.t_gap = t_gap
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd

        # STATE:
        #  Define 'state' attribute (initial sate):
        state = SupervisorPIDState().get()
        self.state = SupervisorPIDState(state)

        # PORTS:
        #  Declare as many input and output ports as desired
        #  (usually store returned references in local variables):
        self.UPDATE_STATE = self.addInPort(name="update_state")
        self.EGO_VEHICLE_STATE = self.addInPort(name="ego_vehicle_state")
        self.LEAD_VEHICLE_STATE = self.addInPort(name="lead_vehicle_state")

        self.OUTPUT = self.addOutPort(name="output")

    def extTransition(self, inputs):
        """
        External Transition Function.
        """
        # Compute the new state 'Snew' based (typically) on current
        # State, Elapsed time parameters and calls to 'self.peek(self.IN)'.
        update_state = inputs.get(self.UPDATE_STATE)
        ego_vehicle_state = inputs.get(self.EGO_VEHICLE_STATE)
        lead_vehicle_state = inputs.get(self.LEAD_VEHICLE_STATE)

        state = self.state.get()

        if state['state'] == 'idle':
            # state['state'] = 'update_as'
            if ego_vehicle_state:
                state['x_ego'] = ego_vehicle_state[0][0]
                state['v_ego'] = ego_vehicle_state[0][1]
                state['ego_init'] = True
            if lead_vehicle_state:
                state['x_lead'] = lead_vehicle_state[0][0]
                state['v_lead'] = lead_vehicle_state[0][1]
                state['lead_init'] = True
            if update_state:
                if state['ego_init'] and state['lead_init']:
                    d_rel = state['x_lead'] - state['x_ego']  # Relative distance to lead car (how far away are we)
                    v_rel = state['v_ego'] - state['v_lead']  # Relative speed to lead car (how fast are we closing the gap)
                    d_safe = self.d_default + self.t_gap * state['v_ego']  # Safe distance at current speed

                    error = d_rel - d_safe
                    state['integral'] = state['integral'] + (error * self.elapsed)
                    d_error = (error - state['error_prev']) / self.elapsed
                    output = (self.Kp * error) + (self.Ki * state['integral']) + (self.Kd * d_error)

                    state['error_prev'] = error
                    state['v_wanted'] = min(state['v_ego'] + output, self.v_limit)
                else:
                    state['v_wanted'] = self.v_limit
                state['state'] = 'update_state'
            state = SupervisorPIDState(state)
            self.logExtTransition(state)
            return state

        elif state['state'] == 'update_state':
            if ego_vehicle_state:
                state['x_ego'] = ego_vehicle_state[0][0]
                state['v_ego'] = ego_vehicle_state[0][1]
            if lead_vehicle_state:
                state['x_lead'] = ego_vehicle_state[0][0]
                state['v_lead'] = ego_vehicle_state[0][1]
            state = SupervisorPIDState(state)
            self.logExtTransition(state)
            return state

        else:
            raise DEVSException(
                "Unsupported state <%s> in Vehicle external transition function" % state['state']
            )

    def intTransition(self):
        """
        Internal Transition Function.
        """

        state = self.state.get()

        if state['state'] == 'update_state':
            state['state'] = 'idle'
            state = SupervisorPIDState(state)
            self.logIntTransition(state)
            return state
        else:
            raise DEVSException(
                "Unsupported state <%s> in Vehicle internal transition function" % state['state']
            )

    def outputFnc(self):
        """
        Output Function.
        """
        state = self.state.get()

        if state['state'] == 'update_state':
            return {self.OUTPUT: [state['v_wanted']]}
        elif state['state'] == 'idle':
            return {}
        else:
            raise DEVSException(
                "Unsupported state <%s> in Vehicle external transition function" % state['state']
            )

    def timeAdvance(self):
        """
        Time-Advance Function.
        """
        # Compute 'ta', the time to the next scheduled internal transition,
        # based (typically) on current State.
        state = self.state.get()
        if state['state'] == 'idle':
            return INFINITY
        elif state['state'] == 'update_state':
            return 0
        else:
            raise DEVSException(
                "Unsupported state <%s> in Vehicle time advance transition function" % state['state']
            )


class EgoVehicle(CoupledDEVS):
    def __init__(self, name=None, x0=10.0, v0=20.0, a0=0.0, interval=0.1):
        """
        A simple system consisting of a Supervisor and a Controller.
        """
        # Always call parent class' constructor FIRST:
        CoupledDEVS.__init__(self, name)

        # Declare the coupled model's output ports:
        self.UPDATE_A_WANTED = self.addInPort(name="update_a_wanted")
        self.VEHICLE_STATE = self.addOutPort(name="vehicle_state")

        # Declare the coupled model's sub-models:

        # The Vehicle
        self.vehicle = self.addSubModel(Vehicle(name="ego_vehicle_vehicle", x0=x0, v0=v0, a0=a0))

        # The Generator periodically triggering state updates
        self.generator = self.addSubModel(Generator(name="ego_vehicle_generator", interval=interval))

        # Connect ...
        self.connectPorts(self.generator.UPDATE_STATE, self.vehicle.UPDATE_STATE)

        self.connectPorts(self.UPDATE_A_WANTED, self.vehicle.UPDATE_A_WANTED)
        self.connectPorts(self.vehicle.VEHICLE_STATE, self.VEHICLE_STATE)


class LeadVehicle(CoupledDEVS):
    def __init__(self, name=None, x0=50.0, v0=25.0, a0=0.0, interval=0.1, amplitude=0.6, omega=0.2):
        """
        A simple system consisting of a Supervisor and a Controller.
        """
        # Always call parent class' constructor FIRST:
        CoupledDEVS.__init__(self, name)

        # Declare the coupled model's output ports:
        self.VEHICLE_STATE = self.addOutPort(name="vehicle_state")

        # Declare the coupled model's sub-models:

        # The Vehicle
        self.vehicle = self.addSubModel(Vehicle(name="lead_vehicle_vehicle", x0=x0, v0=v0, a0=a0))

        # The Generator periodically triggering state updates
        self.generator = self.addSubModel(Generator(name="lead_vehicle_generator", interval=interval))

        # The Sine generator generating input stimuli
        self.sine = self.addSubModel(Sine(name="lead_vehicle_sine", interval=interval, amplitude=amplitude, omega=omega, offset=0.0))

        # Connect ...
        self.connectPorts(self.generator.UPDATE_STATE, self.vehicle.UPDATE_STATE)
        self.connectPorts(self.sine.VALUE, self.vehicle.UPDATE_A_WANTED)

        self.connectPorts(self.vehicle.VEHICLE_STATE, self.VEHICLE_STATE)


class CruiseControlSystem(CoupledDEVS):
    def __init__(self, name=None, controller_Kp=5, controller_Ki=0.1, controller_Kd=0.0, controller_interval=0.1,
                 ego_vehicle_x0=0.0, ego_vehicle_v0=0.0, ego_vehicle_a0=0.0, ego_vehicle_interval=0.1):
        """
        A simple system consisting of a Vehicle and a Controller.
        """
        # Always call parent class' constructor FIRST:
        CoupledDEVS.__init__(self, name)

        # Declare the coupled model's sub-models:

        # The Vehicle
        self.ego_vehicle = self.addSubModel(EgoVehicle(name="ego_vehicle", x0=ego_vehicle_x0, v0=ego_vehicle_v0,
                                                       a0=ego_vehicle_a0, interval=ego_vehicle_interval))

        # The Generator periodically triggering state updates for the Controller
        self.controller_generator = self.addSubModel(
            Generator(name="generator_speed_controller", interval=controller_interval))

        # The Sine generator generating input stimuli
        self.sine = self.addSubModel(Sine(name="sine", interval=controller_interval, amplitude=5, omega=0.2, offset=25))

        # The Controller controlling the speed of the vehicle
        self.controller = self.addSubModel(SpeedController(name="speed_controller", Kp=controller_Kp, Ki=controller_Ki,
                                                           Kd=controller_Kd))

        # Connect ...
        self.connectPorts(self.controller_generator.UPDATE_STATE, self.controller.UPDATE_STATE)
        self.connectPorts(self.sine.VALUE, self.controller.UPDATE_SETPOINT)
        self.connectPorts(self.ego_vehicle.VEHICLE_STATE, self.controller.VEHICLE_STATE)
        self.connectPorts(self.controller.OUTPUT, self.ego_vehicle.UPDATE_A_WANTED)


class AdaptiveCruiseControlSystem(CoupledDEVS):
    def __init__(self, name=None, ego_vehicle_x0=10.0, ego_vehicle_v0=20.0, ego_vehicle_a0=0.0, ego_vehicle_interval=0.1,
                 lead_vehicle_x0=50.0, lead_vehicle_v0=25.0, lead_vehicle_a0=0.0, lead_vehicle_interval=0.1,
                 lead_vehicle_a_amplitude=0.6, lead_vehicle_a_omega=0.2,
                 controller_Kp=4.0, controller_Ki=0.0, controller_Kd=1.0, controller_interval=0.1,
                 supervisor_v_limit=30.0, supervisor_d_default=10.0, supervisor_t_gap=1.4,
                 supervisor_Kp=1.0, supervisor_Ki=0.0, supervisor_Kd=0.05, supervisor_interval=0.1,
                 ):
        """
        A simple system consisting of a Vehicle and a Controller.
        """
        # Always call parent class' constructor FIRST:
        CoupledDEVS.__init__(self, name)

        # Declare the coupled model's sub-models:

        # The Ego Vehicle
        self.ego_vehicle = self.addSubModel(EgoVehicle(name="ego_vehicle", x0=ego_vehicle_x0, v0=ego_vehicle_v0,
                                                       a0=ego_vehicle_a0, interval=ego_vehicle_interval))

        # The Lead Vehicle
        self.lead_vehicle = self.addSubModel(LeadVehicle(name="lead_vehicle", x0=lead_vehicle_x0, v0=lead_vehicle_v0,
                                                         a0=lead_vehicle_a0, interval=lead_vehicle_interval,
                                                         amplitude=lead_vehicle_a_amplitude,
                                                         omega=lead_vehicle_a_omega))

        # The Generator periodically triggering state updates for the Controller
        self.controller_generator = self.addSubModel(Generator(name="generator_speed_controller",
                                                               interval=controller_interval))

        # The Controller controlling the speed of the vehicle
        self.controller = self.addSubModel(SpeedController(name="speed_controller", Kp=controller_Kp, Ki=controller_Ki,
                                                           Kd=controller_Kd))

        # The Generator periodically triggering state updates for the Supervisor
        self.supervisor_generator = self.addSubModel(Generator(name="generator_supervisor",
                                                               interval=supervisor_interval))

        # The Supervisor controlling the speed or distance when necessary
        # self.supervisor = self.addSubModel(Supervisor(name="supervisor", v_limit=supervisor_v_limit,
        #                                               d_default=supervisor_d_default, t_gap=supervisor_t_gap,
        #                                               t_intercept=supervisor_t_intercept))
        self.supervisor = self.addSubModel(SupervisorPID(name="supervisor", v_limit=supervisor_v_limit,
                                                         d_default=supervisor_d_default, t_gap=supervisor_t_gap,
                                                         Kp=supervisor_Kp, Ki=supervisor_Ki, Kd=supervisor_Kd))

        # Connect ...

        # Controller I/O
        self.connectPorts(self.controller_generator.UPDATE_STATE, self.controller.UPDATE_STATE)
        self.connectPorts(self.ego_vehicle.VEHICLE_STATE, self.controller.VEHICLE_STATE)
        self.connectPorts(self.controller.OUTPUT, self.ego_vehicle.UPDATE_A_WANTED)

        # Supervisor I/O
        self.connectPorts(self.supervisor_generator.UPDATE_STATE, self.supervisor.UPDATE_STATE)
        self.connectPorts(self.ego_vehicle.VEHICLE_STATE, self.supervisor.EGO_VEHICLE_STATE)
        self.connectPorts(self.lead_vehicle.VEHICLE_STATE, self.supervisor.LEAD_VEHICLE_STATE)
        self.connectPorts(self.supervisor.OUTPUT, self.controller.UPDATE_SETPOINT)

