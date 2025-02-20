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
from sys import exit

from mido import Message

from supriya import Server, SynthDef


class SynthHandler(ABC):
    def __init__(self, server: Server, synth_definitions: dict[str, SynthDef]):
        self.server = server
        self.synth_definitions = synth_definitions
        self.synths = {}
    
    @property
    def synth_definitions(self) -> dict[str, SynthDef]:
        return self.synth_definitions
    
    def _load_synthdefs(self) -> None:
        _ = self.server.add_synthdefs([s for s in self.synth_definitions.values()])
        # Wait for the server to fully load the SynthDef before proceeding.
        self.server.sync()
    
    def handle_midi_message(self, message: Message) -> None:
        if message.type == 'note_on':
            self._on_note_on_message(message=message)
        
        if message.type == 'note_off':
            self._on_note_off_message(message=message)
        
        if message.type == 'control_change':
            self._on_control_change_message(message=message)
    
    @abstractmethod
    def _on_control_change_message(self, message: Message) -> None:
        """Handle a Control Change message.
        
        Args:
            message: a Control Change message
        """
        pass

    @abstractmethod
    def _on_note_off_message(self, message: Message) -> None:
        """Play a Note Off message.
        
        Args:
            message: a Note Off Message
        """
        pass
    
    @abstractmethod
    def _on_note_on_message(self, message: Message) -> None:
        """Play a Note On message.
        
        Args:
            message: a Note On Message
        """
        pass
