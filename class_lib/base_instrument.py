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

from mido import Message

from supriya import Server, SynthDef


class BaseInstrument(ABC):
    def __init__(
        self, 
        server: Server, 
        synth_definition: SynthDef,
        midi_channels: list[int],
    ):
        self._server = server
        self._synth_definition = synth_definition
        self._midi_channels = midi_channels
        self._synths = {}
    
    @property
    @abstractmethod
    def name(self):
        pass
    
    @abstractmethod
    def handle_midi_message(self, message: Message) -> None:
        pass
    
    def _load_synthdefs(self) -> None:
        self._server.add_synthdefs(self._synth_definition)
        # Wait for the server to fully load the SynthDef before proceeding.
        self._server.sync()

    @abstractmethod
    def _on_control_change(self, message: Message) -> None:
        """Handle a Control Change message.
        
        Args:
            message: a Control Change message
        """
        pass

    @abstractmethod
    def _on_note_off(self, message: Message) -> None:
        """Play a Note Off message.
        
        Args:
            message: a Note Off Message
        """
        pass
    
    @abstractmethod
    def _on_note_on(self, message: Message) -> None:
        """Play a Note On message.
        
        Args:
            message: a Note On Message
        """
        pass
