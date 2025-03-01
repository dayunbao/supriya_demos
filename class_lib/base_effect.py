"""
Copyright 2025, Andrew Clark

This program is free software: you can redistribute it and/or modify 
it under the terms of the GNU General Public License as published by 
the Free Software Foundation, either version 3 of the License, or 
(at your option) any later version.

This program is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
GNU General Public License for more details.

You should have received a copy of the GNU General Public License 
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
from abc import ABC, abstractmethod

from supriya import Bus, Group, Server, Synth, SynthDef

from .base_instrument import BaseInstrument

class BaseEffect(ABC):
    def __init__(
        self,
        server: Server,
        synth_def: SynthDef, 
        parameters: dict[str, any]
    ):
        self.group: Group | None = None
        self.server = server
        self.synth_def = synth_def
        self.parameters = parameters
        self.bus = self._create_bus()
        self.in_bus = self.bus
        #  Default to standard out
        self.out_bus = 0
        #  Where in the signal processing chain the effect should be.
        self.priority = 0
        self._load_synth_def()
    
    @property
    def group(self) -> Group:
        return self._group
    
    @group.setter
    def group(self, group: Group) -> None:
        self._group = group

    def _create_bus(self) -> Bus:
        return self.server.add_bus(calculation_rate='audio')

    def create_synth(self) -> Synth:
        self.group.add_synth(
            in_bus = self.in_bus,
            out_bus=self.out_bus,
            synthdef=self.synth_def
        )

    def _load_synth_def(self) -> None:
        self.server.add_synthdefs(self.synth_def)
        # Wait for the server to fully load the SynthDef before proceeding.
        self.server.sync()
        
    def route_signal(self, instrument: BaseInstrument) -> None:
        instrument.out_bus = self.bus
    
    def set_parameters(self, parameters: dict[str, any]) -> None:
        self.group.set(**parameters)