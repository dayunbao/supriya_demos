from abc import ABC, abstractmethod

from supriya.clocks import Clock, ClockContext
from supriya.clocks.ephemera import TimeUnit

from .base_instrument import BaseInstrument

class BaseTrack(ABC):
    def __init__(
        self, 
        clock: Clock,
        instrument: BaseInstrument,
        quantization: str,
        sequencer_steps: int,
        track_number: int,
    ):
        self._track_number = track_number
        self._clock = clock
        self._clock_event_id: int | None = None
        self._quantization = quantization
        self._quantization_delta = self._convert_quantization_to_delta(quantization=quantization)
        self._sequencer_steps =  sequencer_steps
        self._instrument = instrument
    
    def __str__(self) -> str:
        return f'Track: {self._track_number}, \
        Quantization: {self._quantization}, \
        Instrument: {self._instrument}'
    
    @property
    def track_number(self) -> int:
        return self._track_number
    
    @track_number.setter
    def track_number(self, track_number: int) -> None:
        self._track_number = track_number

    @property
    def quantization(self) -> str:
        return self._quantization
    
    @quantization.setter
    def quantization(self, quantization: str) -> None:
        self._quantization = quantization
        self.quantization_delta = self._convert_quantization_to_delta(quantization=quantization)

    @property
    @abstractmethod
    def recorded_notes(self):
        """Leave choice of data structure to child classes."""
        pass

    def _convert_quantization_to_delta(self, quantization: str) -> float:
        # This helper function converts a string like '1/16' into a numeric value
        # used by the clock.
        return self._clock.quantization_to_beats(quantization=quantization)

    @abstractmethod
    def erase_recorded_notes(self) -> None:
        pass

    @abstractmethod
    def track_clock_callback(
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
        if self._clock_event_id is not None:
            self._clock.cancel(self._clock_event_id)
