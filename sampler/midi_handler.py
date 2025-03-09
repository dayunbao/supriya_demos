"""A class responsible for MIDI.

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

import threading

from mido import get_input_names, Message, open_input
from mido.ports import MultiPort


class MIDIHandler:
    def __init__(self, message_handler_callback: callable):
        self.message_handler_callback = message_handler_callback
        self.multi_inport = self._open_multi_inport()
        self.stop_listening_for_input: threading.Event = threading.Event()
        self.start_listening_for_midi()

    def start_listening_for_midi(self) -> None:
        listening_thread = threading.Thread(target=self.listen_for_midi_messages, daemon=True)
        listening_thread.start()

    def exit(self) -> None:
        self.stop_listening_for_input.set()
        self.multi_inport.close()

    def _open_multi_inport(self) -> MultiPort:
        """Create a MultiPort that accepts all incoming MIDI messages.

        This is the easiest way to handle the fact that people using
        this script could have an input port named anything.
        """
        inports = [open_input(p) for p in get_input_names()]
        
        return MultiPort(inports)

    def listen_for_midi_messages(self) -> Message:
        """Listen for incoming MIDI messages in a non-blocking way."""
        while not self.stop_listening_for_input.is_set():
            for message in self.multi_inport.iter_pending():
                self.message_handler_callback(message)
