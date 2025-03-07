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

from supriya import Group, Server, SynthDef

from helpers import scale
from program import Program
from sampler_note import SamplerNote

class Sampler:
    def __init__(
            self, 
            name: str,
            samples_paths: list[Path],
            server: Server, 
            synthdef: SynthDef,
            group: Optional[Group | None]=None,
        ):
        self.group = group
        self.in_bus = 2
        self.name = name
        self.out_bus = 0
        self.server = server
        self.SAMPLE_SELECT_CC_NUM = 0
        self.synthdef = synthdef
        self._load_synth_definitions()

        self.programs = self._create_programs(samples_paths=samples_paths)
        self.num_programs = len(self.programs.keys())
        self.selected_program = list(self.programs.values())[0]
    
    def _create_programs(self, samples_paths: list[Path]) -> dict[str, Program]:
        """A program corresponds to a directory in the 'samples' directory."""
        programs = {}
        for number, path in enumerate(samples_paths):
            programs.update(
                {
                    path.name:
                    Program(
                        name=path.name,
                        program_number=number,
                        samples_path=path,
                        server=self.server,
                    )
                }
            )

        return programs

    def _load_synth_definitions(self) -> None:
        self.server.add_synthdefs(self.synthdef)
        # Wait for the server to fully load the SynthDef before proceeding.
        self.server.sync()

    def on_control_change(self, message: Message) -> None:
        if message.is_cc(self.SAMPLE_SELECT_CC_NUM):
            sample_number = scale(
                value=message.value,
                target_min=0,
                target_max=self.selected_program.number_samples - 1,
            )
            self.selected_program.selected_sample = self.selected_program.set_selected_sample(sample_number=sample_number)

    def on_note_on(self, sampler_note: SamplerNote) -> None:
        buffer = self.programs[sampler_note.program].buffers[sampler_note.sample_index]
        self.group.add_synth(
            synthdef=self.synthdef, 
            buffer=buffer,
            out_bus=self.out_bus,
        )
    
    def on_program_change(self, message: Message) -> None:
        program = scale(
            value=message.program, 
            target_min=0, 
            target_max=self.num_programs - 1,
        )
        self.selected_program = list(self.programs.values())[program]
