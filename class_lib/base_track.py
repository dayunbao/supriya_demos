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

from supriya.clocks import Clock, ClockContext, TimeUnit

from .base_instrument import BaseInstrument

class BaseTrack(ABC):
    def __init__(
        self, 
        clock: Clock,
        instrument: BaseInstrument,
        quantization_delta: str,
        sequencer_steps: int,
        track_number: int,
    ):
        self._clock = clock
        self._clock_event_id: int | None = None
        self._instrument = instrument
        self._quantization_delta = quantization_delta
        self._sequencer_steps =  sequencer_steps
        self._track_number = track_number

    @property
    def quantization_delta(self) -> str:
        return self._quantization_delta
    
    @quantization_delta.setter
    def quantization_delta(self, quantization_delta: float) -> None:
        self._quantization_delta = quantization_delta

    @property
    @abstractmethod
    def recorded_notes(self):
        """Leave choice of data structure to child classes."""
        pass

    @property
    def track_number(self) -> int:
        return self._track_number
    
    @track_number.setter
    def track_number(self, track_number: int) -> None:
        self._track_number = track_number

    @abstractmethod
    def erase_recorded_notes(self) -> None:
        pass

    @abstractmethod
    def track_clock_callback(
            self, 
            context:ClockContext, 
            delta: float,
    ) -> tuple[float, TimeUnit]:
        pass

    @abstractmethod
    def start_playback(self) -> None:
        """Start playing the track."""
        pass

    def stop_playback(self) -> None:
        """Stop playing track."""
        if self._clock_event_id is not None:
            self._clock.cancel(self._clock_event_id)
