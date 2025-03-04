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

from class_lib import BaseInstrument
from .program import Program

class Sampler(BaseInstrument):
    def __init__(
            self, 
            name: str,
            samples_paths: list[Path],
            server: Server, 
            synth_definition: SynthDef,
            group: Optional[Group | None]=None,
        ):
        super().__init__(
            server=server, 
            synth_definition=synth_definition, 
            group=group,
        )
        self.programs = self._create_programs(samples_paths=samples_paths)
        self.num_programs = len(self.programs)
        self.selected_program = self.programs[0]
        self._load_synthdefs()
        self._name = name
        self.sample_select_cc_num = 0

    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, name: str) -> str:
        self._name = name
    
    def _create_programs(self, samples_paths: list[Path]) -> list[Program]:
        programs = []
        for number, path in enumerate(samples_paths):
            programs.append(
                Program(
                    name=path.name,
                    program_number=number,
                    samples_path=path,
                    server=self._server,
                )
            )

        return programs

    def handle_midi_message(self, message: Message) -> None:
        if message.type == 'control_change':
            self._on_control_change(message=message)
        
        if message.type == 'note_off':
            self._on_note_off(message=message)
        
        if message.type == 'note_on':
            self._on_note_on(message=message)
        
        if message.type == 'program_change':
            self._on_program_change(message=message)

    def _on_control_change(self, message: Message) -> None:
        """Handle a Control Change message.
        
        Args:
            message: a Control Change message
        """
        if message.is_cc(self.sample_select_cc_num):
            sample_number = self.scale(
                value=message.value,
                target_min=0,
                target_max=self.selected_program.number_samples - 1,
            )
            self.selected_program.selected_sample = self.selected_program.buffers[sample_number]

    def _on_note_off(self, message: Message) -> None:
        """Play a Note Off message.
        
        Args:
            message: a Note Off Message
        """
        pass

    def _on_note_on(self, message: Message) -> None:
        """Play a Note On message.
        
        Args:
            message: a Note On Message
        """
        buffer = self.selected_program.selected_sample
        self.group.add_synth(
            synthdef=self._synth_definition, 
            buffer=buffer,
            out_bus=self.out_bus,
        )
    
    def _on_program_change(self, message: Message) -> None:
        """Handle a Program Change message.
        
        Args:
            message: a Program Change message
        """
        program = self.scale(
            value=message.program, 
            target_min=0, 
            target_max=self.num_programs - 1,
        )
        self.selected_program = self.programs[program]

    def scale(self, value: int, target_min: int, target_max: int) -> int:
        """
        Linearly scale a value from one range to another.

        Args:
            source_value (int): The value to be scaled.

        Returns:
            int: The scaled value in the target range.
        """
        source_min = 0
        source_max = 127
        
        scaled_value = (value - source_min) * (target_max - target_min) / (source_max - source_min) + target_min
        return round(scaled_value)