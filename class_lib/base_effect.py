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
from typing import Optional

from supriya import Bus, Group, Server, Synth, SynthDef

from .base_instrument import BaseInstrument

class BaseEffect(ABC):
    def __init__(
        self,
        name: str,
        server: Server,
        synth_def: SynthDef, 
        group: Optional[Group | None]=None,
        out_bus: int | Bus=0,
    ):
        self.group = group
        self.name = name
        self.server = server
        self.synth_def = synth_def
        self.bus = self.server.add_bus(calculation_rate='audio')
        self.in_bus = self.bus
        #  Default to standard out
        self.out_bus = out_bus
        #  Where in the signal processing chain the effect should be.
        self.priority = 0
        self._load_synth_def()

    @abstractmethod
    def get_parameters(self) -> dict[str, any]:
        pass

    def _load_synth_def(self) -> None:
        self.server.add_synthdefs(self.synth_def)
        # Wait for the server to fully load the SynthDef before proceeding.
        self.server.sync()
        
    def route_signal(self, instrument: BaseInstrument) -> None:
        instrument.out_bus = self.bus
    
    def set_parameters(self, parameters: dict[str, any]) -> None:
        self.group.set(**parameters)