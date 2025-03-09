"""A class the encapsulates functionality related to a set of samples.

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

from supriya import Buffer, Server

class Program:
    def __init__(
        self,
        name: str,
        program_number: int,
        samples_path: Path,
        server: Server,
    ):
        self.name = name
        self.program_number = program_number
        self.samples_path = samples_path
        self.server = server
        self.buffers = self._load_buffers()
        self.number_samples = len(self.buffers)
        self.selected_sample_index = 0
        self.selected_sample = self.buffers[self.selected_sample_index]
    
    def _load_buffers(self) -> list[Buffer]:
        buffers = []
        for sample_path in sorted(self.samples_path.rglob(pattern='*.wav')):
            buffers.append(self.server.add_buffer(file_path=str(sample_path)))
        
        return buffers
    
    def set_selected_sample(self, sample_number: int) -> Buffer:
        self.selected_sample_index = sample_number
        self.selected_sample = self.buffers[self.selected_sample_index]