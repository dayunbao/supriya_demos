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
from typing import Optional

from supriya import Bus, Group, Server, SynthDef

from class_lib import BaseEffect

class Reverb(BaseEffect):
    def __init__(self, 
        name: str, 
        server: Server, 
        synth_def: SynthDef, 
        group: Optional[Group | None]=None,
        out_bus: int | Bus=0,
    ) -> None:
        super().__init__(
            name=name, 
            server=server, 
            synth_def=synth_def, 
            group=group,
            out_bus=out_bus,
        )
        self.damping = 0.5
        self.mix = 0.33
        self.room_size = 0.5

    def get_parameters(self) -> dict[str, any]:
        return {
            'damping': self.damping,
            'in_bus': self.in_bus,
            'mix': self.mix,
            'out_bus': self.out_bus,
            'room_size': self.room_size,
            'synthdef': self.synth_def,
        }