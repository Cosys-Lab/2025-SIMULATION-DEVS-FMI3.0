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

from fmu_instance import *
from fmpy.fmi3 import fmi3ValueReference, fmi3Float64, fmi3IntervalQualifier, fmi3IntervalNotYetKnown


class Importer:
    def __init__(self, verbose=False):
        self.fmus = []
        self.time_based_clocks = []
        self.external_relations = []
        self.loggers = []
        self.verbose = verbose

    # Instantiate and add an FMU by providing a path to the .fmu file or extracted folder and an optional instance name
    def add_fmu(self, fmu_path, instance_name=None):
        fmu = FMUInstance(fmu_path, instance_name=instance_name)
        self.fmus.append(fmu)
        for clock in fmu.clocks.values():
            # For this simple example, we only consider countdown clocks.
            if clock.causality.lower() == 'input' and clock.interval_variability.lower() == 'countdown':
                self.time_based_clocks.append(TimeBasedClock(fmu, clock))
        return fmu

    # Add an external relationship by providing the relationship object directly
    def add_external_relation(self, external_relation):
        self.external_relations.append(external_relation)

    # Add an external relationship based on the connected FMUs and the names of the connected variables
    def add_external_relation_by_names(self, fmu_from, model_variable_from_name, fmu_to, model_variable_to_name):
        model_variable_from = fmu_from.get_model_variable_by_name(model_variable_from_name)
        model_variable_to = fmu_to.get_model_variable_by_name(model_variable_to_name)
        external_relation = ExternalRelation(fmu_from, model_variable_from, fmu_to, model_variable_to)
        self.external_relations.append(external_relation)

    # Get the earliest time at which one of the time-based clocks will tick, returns inf by default
    def get_earliest_tick_time(self):
        return min((clock.next_tick_time for clock in self.time_based_clocks if clock.next_time_known),
                   default=float('inf'))

    # Get the output which is connected to a certain input (variable)
    def get_connected_output(self, variable):
        output = [external_relation.model_variable_from for external_relation in self.external_relations if
                  external_relation.model_variable_to == variable]

        return output[0] if output else None

    # Add (register) a logger
    def add_logger(self, logger):
        self.loggers.append(logger)

    # Run the simulation until a certain stop time is reached
    def run_until(self, stop_time):
        time = 0

        # Initialize the FMUs, and get the first time to tick for the relevant time-based clocks
        for fmu in self.fmus:
            # Enter initialization mode for the FMU
            fmu.fmu.enterInitializationMode()

            # Update any time-based clocks for the FMU
            for clock in (clock for clock in self.time_based_clocks if clock.fmu_instance == fmu):
                clock.update_next_tick_time(time)

            # Exit initialization mode for the FMU
            fmu.fmu.exitInitializationMode()

        # Get the time when the first clock(s) should tick
        t_next = self.get_earliest_tick_time()

        # Start loggers and add first sample
        for logger in self.loggers:
            logger.start()
            logger.add_sample(time)

        # Main simulation loop
        # While simulation end time is not reached
        # Note: This is a simplified stop condition for this use case
        while t_next <= stop_time:
            if self.verbose:
                print(f'Next time: %f' % t_next)
            # --- Continuous Time --- #
            # Note: this part is extremely simplified for the current use case
            if t_next > time:
                # Calculate step size
                step_size = t_next - time
                if self.verbose:
                    print(f'Progress in time by %f...' % step_size)

                # Enter step mode and step each FMU
                for fmu in self.fmus:
                    # Enter step mode
                    fmu.fmu.enterStepMode()
                    # Do a doStep to advance the time
                    (*_, last_successful_time) = fmu.fmu.doStep(time, step_size, True)
                    # Check if the FMU has actually advanced to the expected time
                    assert last_successful_time == t_next

                # We are now at time + step_size (= time_next)
                time = t_next
                if self.verbose:
                    print(f'Time now: %f' % time)

            # --- Discrete Event --- #
            # Note: this part is somewhat simplified for the current use case
            # Enter event mode
            for fmu in self.fmus:
                fmu.fmu.enterEventMode()

            # Iterate to solve the occurrence of events (super-dense time)
            it = 0
            event_handling_needed = True
            while event_handling_needed:
                # Find which (time-based) clocks need activation initially, for the first iteration
                clocks_needing_activation = [clock.model_variable for clock in self.time_based_clocks if
                                             clock.next_time_known and clock.next_tick_time == time]

                if not clocks_needing_activation:
                    event_handling_needed = False
                    break

                if self.verbose:
                    print(f'Event handling needed...')
                while clocks_needing_activation:
                    # Event mode means super-dense time, i.e., tuple: (time instant (rational), iteration (natural))
                    if self.verbose:
                        print(f'Superdense time instant: (%f %d)' % (time, it))

                    # Keep track of currently active input and output clocks
                    active_input_clocks = []
                    active_output_clocks = []

                    # Tick input clocks needing activation
                    for clock in clocks_needing_activation:
                        clock.activate_clock()
                        if self.verbose:
                            print(f'Activate clock %s.%s' % (clock.fmu_instance.instance_name, clock.name))
                        # Input clock is now active, store it
                        active_input_clocks.append(clock)

                    # All clocks needing activation should have now been activated, so clear this variable. We will use
                    # this to store clocks needing activation in the next iteration, e.g., due to the occurrence of new
                    # events, connections between clocks, etc.
                    clocks_needing_activation = []

                    # For each active input clock, set any clocked (data) inputs and check potentially active output
                    # clocks
                    for clock in active_input_clocks:
                        # Set clocked (data) input based on connected (data) output
                        for data in clock.fmu_instance.data.values():
                            # If the active clock is one of the dependencies of this clocked input
                            if clock.value_reference in data.clocks:
                                if self.verbose:
                                    print('Set data %s.%s' % (data.fmu_instance.instance_name, data.name))
                                # Get the value of the connected output
                                connected_output = self.get_connected_output(data)
                                # Set the value of the clocked input
                                data.set_value(connected_output.value)

                        # Iterate over internal relationships to update potentially active (output) clocks
                        for internal_relation in clock.fmu_instance.internal_relations:
                            # If there is an internal relation between the active input clock and an output clock
                            if (internal_relation.model_variable_from == clock
                                    and isinstance(internal_relation.model_variable_to, Clock)):
                                # Update the activation state of the related clock (which may have become active)
                                if internal_relation.model_variable_to.get_and_store_activation_state():
                                    # Store if active
                                    if self.verbose:
                                        print('Clock %s.%s is active' %
                                              (internal_relation.model_variable_to.fmu_instance.instance_name,
                                               internal_relation.model_variable_to.name))
                                    active_output_clocks.append(internal_relation.model_variable_to)

                    # For each active output clock, update any clocked (data) outputs and flag any connected input
                    # clocks for activation
                    for clock in active_output_clocks:
                        # Update value of related clocked outputs
                        for data in clock.fmu_instance.data.values():
                            # If the active clock is one of the dependencies of this clocked output
                            if clock.value_reference in data.clocks:
                                if self.verbose:
                                    print('Get data %s.%s' % (data.fmu_instance.instance_name, data.name))
                                # Get the value of the output and store it in the object
                                data.get_and_store_value()

                        # Add linked input clocks to clocks needing activation based on active output clocks
                        for external_relation in self.external_relations:
                            # If there is an internal relation between the active output clock and an input clock
                            if (external_relation.model_variable_from == clock and
                                    isinstance(external_relation.model_variable_to, Clock)):
                                # Flag the connected input clock for needing activation in the next iteration
                                clocks_needing_activation.append(external_relation.model_variable_to)

                    # Increment iteration count
                    it += 1

                # If there are no more clocks needing activation, update discrete states
                for fmu in self.fmus:
                    # Update discrete states of FMUs, this needs to be called at least once per event mode
                    fmu.fmu.updateDiscreteStates()

                # Update time until next tick for time-based clocks
                for clock in self.time_based_clocks:
                    clock.update_next_tick_time(time)

            # Get the new earliest time when the next clock(s) should tick
            t_next = self.get_earliest_tick_time()

            # Log a sample
            for logger in self.loggers:
                logger.add_sample(time)

            # LOGGING FOR DEBUGGING PURPOSES
            print('\n>>>>>>>>>>>>>>>>>>>>>>>')
            print('time %f' % time)
            for fmu in self.fmus:
                if fmu.get_model_variable_by_name('state'):
                    print('%s state %s' % (fmu.instance_name, fmu.get_model_variable_by_name('state').get_value()))
            print('t_next %f' % t_next)
            print('<<<<<<<<<<<<<<<<<<<<<<<\n')

        # We have reached the stop condition
        # Stop loggers
        for logger in self.loggers:
            logger.terminate()

    # Terminate the simulation, free all FMU instances
    def terminate(self):
        for fmu in self.fmus:
            fmu.fmu.freeInstance()


# Class to store info about time-based clocks
class TimeBasedClock:
    def __init__(self, fmu_instance, model_variable, next_tick_time=float('inf'), next_time_known=False):
        self.fmu_instance = fmu_instance
        self.model_variable = model_variable
        self.next_tick_time = next_tick_time
        self.next_time_known = next_time_known

    # Calculate and store the time at which a clock should tick next by getting its interval from the FMU
    def update_next_tick_time(self, current_time):
        # Get the value reference of the clock
        value_reference = self.model_variable.value_reference
        # Get the interval from the FMU
        intervals, qualifiers = fmi3_get_interval_decimal(self.fmu_instance.fmu, [value_reference])
        # If the interval is known
        if qualifiers[0] is not fmi3IntervalNotYetKnown:
            # Calculate and store the next time based on the interval and the provided current time
            self.set_next_tick_time(current_time + intervals[0])

    # Store the next tick time
    def set_next_tick_time(self, next_tick_time):
        self.next_tick_time = next_tick_time
        self.next_time_known = True

    # Activate (tick) the clock
    def tick_clock(self):
        self.model_variable.activate_clock()


# Class to store external relationships (connections between inputs/outputs of FMUs)
class ExternalRelation:
    def __init__(self, fmu_from, model_variable_from, fmu_to, model_variable_to):
        self.fmu_from = fmu_from
        self.model_variable_from = model_variable_from
        self.fmu_to = fmu_to
        self.model_variable_to = model_variable_to


# Utility function to make it easier to get the clock interval from an FMU
def fmi3_get_interval_decimal(fmu, value_references):
    num_vrs = len(value_references)
    vrs = (fmi3ValueReference * num_vrs)(*value_references)
    intervals = (fmi3Float64 * num_vrs)()
    qualifiers = (fmi3IntervalQualifier * num_vrs)()

    fmu.getIntervalDecimal(vrs, intervals, qualifiers)

    return list(intervals), list(qualifiers)
