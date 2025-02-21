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
from enum import Enum

from supriya.clocks import Clock, ClockContext
from supriya.clocks.ephemera import TimeUnit

from .midi_handler import MIDIHandler
from .synth_handler import SynthHandler

class BaseSequencer(ABC):
    def __init__(
            self, 
            bpm: int, 
            quantization: str,
            synth_handler: SynthHandler,
    ):
        self.bpm: int = bpm
        self.clock = self._initialize_clock()
        self.clock_event_id: int | None = None
        self.quantization_delta = self._convert_quantization_to_delta(quantization=quantization)
        
        self.SEQUENCER_STEPS: int = 16
        self.synth_handler = synth_handler

    @property
    @abstractmethod
    def midi_handler(self) -> MIDIHandler:
        pass

    @property
    @abstractmethod
    def recorded_notes(self):
        """Leave choice of data structure to child classes."""
        pass

    @property
    @abstractmethod
    def mode(self) -> None:
        pass

    def _convert_quantization_to_delta(self, quantization: str) -> float:
        # This helper function converts a string like '1/16' into a numeric value
        # used by the clock.
        return self.clock.quantization_to_beats(quantization=quantization)

    @abstractmethod
    def erase_recorded_notes(self) -> None:
        pass

    def exit(self) -> None:        
        self.midi_handler.exit()

    def _initialize_clock(self) -> Clock:
        """Initialize the Supriya's Clock."""
        clock = Clock()
        clock.change(beats_per_minute=self.bpm)
        clock.start()

        return clock

    @abstractmethod
    def sequencer_clock_callback(
            self, 
            context = ClockContext, 
            delta=0.0625, 
            time_unit=TimeUnit.BEATS,
    ) -> tuple[float, TimeUnit]:
        pass

    @abstractmethod
    def start_playback(self) -> None:
        """Start playing back the sequenced drum pattern."""
        pass

    def stop_playback(self) -> None:
        """Stop playing back the sequenced drum pattern."""
        self.clock.cancel(self.clock_event_id)
