from collections import defaultdict

from mido import Message

from supriya.clocks import Clock, ClockContext
from supriya.clocks.ephemera import TimeUnit

from class_lib import BaseTrack, BaseInstrument

class Track(BaseTrack):
    def __init__(
            self, 
            clock: Clock,
            is_recording: bool,
            quantization: str, 
            sequencer_steps: int,
            instrument: BaseInstrument,
            track_number: int,
        ):
        super().__init__(
            clock, 
            instrument, 
            quantization, 
            sequencer_steps, 
            track_number,
        )
        self.is_recording = is_recording
        self._recorded_notes: dict[float, list[Message]] = defaultdict(list)

    @property
    def recorded_notes(self) -> dict[float, list[Message]]:
        return self._recorded_notes
    
    @recorded_notes.setter
    def recorded_notes(self, notes: dict[float, list[Message]]):
        self._recorded_notes = notes

    def erase_recorded_notes(self) -> None:
        self.recorded_notes = defaultdict(list)
    
    def handle_midi_message(self, message: Message) -> None:
        """Decide how to handle incoming MIDI notes based on the mode."""
        # The SynthHandler is responsible for playing notes
        # We play a note whether or note we're recording. 
        self.instrument.handle_midi_message(message=message)
        
        # The Sequencer is responsible for recording the notes
        if self.is_recording:
            # recorded_time is in a factor of quantization_delta, and is based
            # on the scaled value of the message's note.
            # This makes playback very simple because for each invocation of 
            # the clock's callback, we can simply check for messages at the delta.
            recorded_time = (message.note % self.sequencer_steps) * self.quantization_delta
            recorded_message = message.copy(time=recorded_time)
            self.recorded_notes[recorded_time].append(recorded_message)


    def track_clock_callback(
            self, 
            context = ClockContext, 
            delta=0.0625, 
            time_unit=TimeUnit.BEATS,
    ) -> tuple[float, TimeUnit]:
        """The function that runs on each invocation.

        The callback is executed once every `delta`.  What delta means depends on time_unit.  
        Options for time_unit are BEATS or SECONDS.  If you want this function to called
        once every 1/4, 1/8, or 1/16 note, then time_unit should be BEATS.  Otherwise
        you can specify SECONDS as the time_unit to have it called outside of a 
        musical rhythmic context.
        """
        recorded_notes_index = delta * (context.event.invocations % self.sequencer_steps )

        midi_messages = self.recorded_notes[recorded_notes_index]
        for message in midi_messages:
            self.instrument.handle_midi_message(message=message)
        
        delta = self.quantization_delta
        return delta, time_unit
    
    def start_playback(self) -> None:
        self.clock_event_id = self.clock.cue(procedure=self.track_clock_callback, quantization='1/4')