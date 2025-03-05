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

from supriya import Group, Server, SynthDef

from program import Program
from sampler_note import SamplerNote

class Sampler:
    def __init__(
            self, 
            name: str,
            samples_paths: list[Path],
            server: Server, 
            synth_definition: SynthDef,
            group: Optional[Group | None]=None,
        ):
        self.group = group
        self.in_bus = 2
        self.name = name
        self.out_bus = 0
        self.server = server
        self.sample_select_cc_num = 0
        self._synth_definition = synth_definition
        self._load_synth_definitions()

        self.programs = self._create_programs(samples_paths=samples_paths)
        self.num_programs = len(self.programs.keys())
        self.selected_program = list(self.programs.values())[0]
    
    def _create_programs(self, samples_paths: list[Path]) -> dict[str, Program]:
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

    def handle_midi_message(self, sampler_note: SamplerNote) -> None:
        if sampler_note.message.type == 'control_change':
            self._on_control_change(sampler_note=sampler_note)
        
        if sampler_note.message.type == 'note_on':
            self._on_note_on(sampler_note=sampler_note)
        
        if sampler_note.message.type == 'program_change':
            self._on_program_change(sampler_note=sampler_note)

    def _load_synth_definitions(self) -> None:
        self.server.add_synthdefs(self._synth_definition)
        # Wait for the server to fully load the SynthDef before proceeding.
        self.server.sync()

    def _on_control_change(self, sampler_note: SamplerNote) -> None:
        if sampler_note.message.is_cc(self.sample_select_cc_num):
            sample_number = self.scale(
                value=sampler_note.message.value,
                target_min=0,
                target_max=self.selected_program.number_samples - 1,
            )
            self.selected_program.selected_sample = self.selected_program.buffers[sample_number]

    def _on_note_on(self, sampler_note: SamplerNote) -> None:
        buffer = self.programs[sampler_note.program].selected_sample
        self.group.add_synth(
            synthdef=self._synth_definition, 
            buffer=buffer,
            out_bus=self.out_bus,
        )
    
    def _on_program_change(self, sampler_note: SamplerNote) -> None:
        program = self.scale(
            value=sampler_note.message.program, 
            target_min=0, 
            target_max=self.num_programs - 1,
        )
        self.selected_program = list(self.programs.values())[program]

    def scale(self, value: int, target_min: int, target_max: int) -> int:
        source_min = 0
        source_max = 127
        
        scaled_value = (value - source_min) * (target_max - target_min) / (source_max - source_min) + target_min
        return round(scaled_value)