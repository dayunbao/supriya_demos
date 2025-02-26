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

from supriya.clocks import Clock, ClockContext
from supriya.clocks.ephemera import TimeUnit

from .midi_handler import MIDIHandler

class BaseSequencer(ABC):
    def __init__(
            self, 
            bpm: int, 
            quantization: str,
    ):
        self._bpm: int = bpm
        self._clock = self._initialize_clock()
        self._clock_event_id: int | None = None
        self._quantization = quantization
        self._quantization_delta = self._convert_quantization_to_delta(quantization=quantization)
        self._SEQUENCER_STEPS: int = 16
        self._track_length_in_measures = self._compute_track_length_in_measures()

    @property
    @abstractmethod
    def midi_handler(self) -> MIDIHandler:
        pass

    @property
    def bpm(self) -> int:
        return self._bpm
    
    @bpm.setter
    def bpm(self, bpm: int) -> None:
        self._bpm = bpm
        self._clock.change(beats_per_minute=self._bpm)
    
    def _compute_track_length_in_measures(self) -> int:
        return self._SEQUENCER_STEPS // int(self.quantization.split('/')[1])

    def _convert_quantization_to_delta(self, quantization: str) -> float:
        # This helper function converts a string like '1/16' into a numeric value
        # used by the clock.
        return self._clock.quantization_to_beats(quantization=quantization)

    def exit(self) -> None:        
        self.midi_handler.exit()

    def _initialize_clock(self) -> Clock:
        """Initialize the Supriya's Clock."""
        clock = Clock()
        clock.change(beats_per_minute=self._bpm)

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
        """Start playing the track."""
        pass

    def stop_playback(self) -> None:
        """Stop playing track."""
        self._clock.stop()
        if self._clock_event_id is not None:
            self._clock.cancel(self._clock_event_id)