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

from pypdevs.DEVS import AtomicDEVS
import os

class LoggingAtomicDEVS(AtomicDEVS):
    """
    A 'mixin-like' subclass of AtomicDEVS that adds custom logging to a file.
    """

    def __init__(self, name=None):
        """
        :param name: Optional model name
        :param logfile_path: Path to the log file (defaults to 'my_log_file.log')
        """
        super().__init__(name)
        os.makedirs('./logs', exist_ok=True)
        self._logfile = open(f'./logs/%s.xml' % name.replace('.', '_'), "w", encoding="utf-8",
                             buffering=1)
        self._log('<?xml version=\'1.0\' encoding=\'utf-8\'?>\n')
        self._log('<trace>')


    def __del__(self):
        """
        Attempt to close the log file when this object is garbage-collected.
        Caveats apply!
        """
        try:
            if self._logfile and not self._logfile.closed:
                self._log('</trace>')
                self._logfile.close()
        except Exception:
            pass

    def _log(self, message):
        """
        Helper function to write a message to our open log file.
        """
        self._logfile.write(message)

    def logExtTransition(self, new_state):
        # Code to construct port_info taken from PythonPDEVS tracerXML.py
        port_info = ""
        for I in range(len(self.IPorts)):
            port_info += '<port name="' + self.IPorts[I].getPortName() + '" category="I">\n'
            for j in self.my_input.get(self.IPorts[I], []):
                port_info += "<message>" + str(j) + "</message>\n"
            port_info += "</port>\n"

        self._log('<event>\n')
        self._log(f'<model>{self.name}</model>\n')
        self._log(f'<time>{self.time_last[0] + (self.elapsed if self.elapsed is not None else 0)}</time>\n') # We need to add the elapsed time as our logging function gets called before the transition
        self._log(f'<kind>EX</kind>\n')
        self._log(port_info)
        self._log(f'<state>\n{self.state.toXML()}{self.state}\n</state>\n')
        self._log('</event>\n')

    def logIntTransition(self, new_state):
        # Code to construct port_info taken from PythonPDEVS tracerXML.py
        port_info = ""
        for I in range(len(self.OPorts)):
            if (self.OPorts[I] in self.my_output and
                    self.my_output[self.OPorts[I]] is not None):
                port_info += '<port name="' + self.OPorts[I].getPortName() + '" category="O">\n'
                for j in self.my_output.get(self.OPorts[I], []):
                    port_info += "<message>" + str(j) + "</message>\n"
                port_info += "</port>\n"

        self._log('<event>\n')
        self._log(f'<model>{self.name}</model>\n')
        self._log(f'<time>{self.time_last[0]}</time>\n')
        self._log(f'<kind>IN</kind>\n')
        self._log(port_info)
        self._log(f'<state>\n{self.state.toXML()}{self.state}\n</state>\n')
        self._log('</event>\n')
