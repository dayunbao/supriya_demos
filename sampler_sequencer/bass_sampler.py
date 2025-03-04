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

from .sampler import Sampler

class BassSampler(Sampler):
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
            midi_channels=midi_channels,
            name=name,
            samples_path=samples_path,
            server=server, 
            synth_definition=synth_definition, 
            group=group,
        )
    
    def handle_midi_message(self, message: Message) -> None:
        if message.type == 'control_change':
            self._on_control_change(message=message)
        
        if message.type == 'note_off':
            self._on_note_off(message=message)
        
        if message.type == 'note_on':
            self._on_note_on(message=message)

    def _on_control_change(self, message: Message) -> None:
        """Handle a Control Change message.
        
        Args:
            message: a Control Change message
        """
        pass

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
        if message.channel in self._midi_channels:
            synth_buff = self._buffers[message.channel]
            self.group.add_synth(
                synthdef=self._synth_definition, 
                buffer=synth_buff,
                out_bus=self.out_bus,
            )
        
        print(self._server.dump_tree())
