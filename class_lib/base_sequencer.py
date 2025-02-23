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

from supriya.clocks import Clock

from .midi_handler import MIDIHandler

class BaseSequencer(ABC):
    def __init__(
            self, 
            bpm: int, 
            quantization: str,
    ):
        self._bpm: int = bpm
        self._clock = self._initialize_clock()
        self._quantization = quantization
        self.SEQUENCER_STEPS: int = 16

    @property
    @abstractmethod
    def midi_handler(self) -> MIDIHandler:
        pass

    def exit(self) -> None:        
        self.midi_handler.exit()

    def _initialize_clock(self) -> Clock:
        """Initialize the Supriya's Clock."""
        clock = Clock()
        clock.change(beats_per_minute=self._bpm)
        clock.start()

        return clock
