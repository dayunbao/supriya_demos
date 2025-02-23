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
        self.track_number = track_number
        self.clock = clock
        self.clock_event_id: int | None = None
        self.quantization = quantization
        self.quantization_delta = self._convert_quantization_to_delta(quantization=quantization)
        self.sequencer_steps =  sequencer_steps
        self.instrument = instrument
    
    def __str__(self) -> str:
        return f'Track: {self.track_number}, \
        Quantization: {self.quantization}, \
        Instrument: {self.instrument}'
    
    @property
    @abstractmethod
    def recorded_notes(self):
        """Leave choice of data structure to child classes."""
        pass

    def _convert_quantization_to_delta(self, quantization: str) -> float:
        # This helper function converts a string like '1/16' into a numeric value
        # used by the clock.
        print(f'quantization={quantization}')
        return self.clock.quantization_to_beats(quantization=quantization)

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
        if self.clock_event_id is not None:
            self.clock.cancel(self.clock_event_id)
