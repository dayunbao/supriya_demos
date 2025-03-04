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
from pathlib import Path
from typing import Optional

from mido import Message

from supriya import Buffer, Group, Server, SynthDef

from class_lib import BaseInstrument

class Sampler(BaseInstrument):
    def __init__(
            self, 
            midi_channels: list[int],
            name: str,
            samples_path: Path,
            server: Server, 
            synth_definition: SynthDef,
            group: Optional[Group | None]=None,
        ):
        super().__init__(
            midi_channels,
            server, 
            synth_definition, 
            group=group,
        )
        self._samples_path = samples_path
        self._buffers = self._load_buffers()
        self._load_synthdefs()
        self._name = name

    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, name: str) -> str:
        self._name = name

    def _load_buffers(self) -> list[Buffer]:
        buffers = []
        for sample_path in sorted(self._samples_path.rglob(pattern='*.wav')):
            buffers.append(self._server.add_buffer(file_path=str(sample_path)))
        
        return buffers
