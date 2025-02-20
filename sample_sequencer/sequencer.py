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

from collections import defaultdict

from mido import Message

from supriya.clocks import ClockContext
from supriya.clocks.ephemera import TimeUnit

from midi_handler import MIDIHandler
from base_sequencer import BaseSequencer
from synth_handler import SynthHandler

class Sequencer(BaseSequencer):
    def __init__(
            self, 
            bpm: int, 
            quantization: str,
            synth_handler: SynthHandler,
    ):
        super().__init__(bpm, quantization, synth_handler)
        self._recorded_notes: dict[float, list[Message]] = defaultdict(list)
        self._midi_handler = self._initialize_midi_handler()
        self.SAMPLE_COUNT = 12

    @property
    def recorded_notes(self) -> dict[float, list[Message]]:
        return self._recorded_notes
    
    @recorded_notes.setter
    def recorded_notes(self, notes: dict[float, list[Message]]):
        self._recorded_notes = notes

    @property
    def midi_handler(self) -> MIDIHandler:
        return self._midi_handler
    
    @midi_handler.setter
    def midi_handler(self, midi_handler: MIDIHandler) -> None:
        self._midi_handler = midi_handler

    def _initialize_midi_handler(self) -> MIDIHandler:
        return MIDIHandler(message_handler_callback=self.handle_midi_message)

    def erase_recorded_notes(self) -> None:
        self.recorded_notes = defaultdict(list)

    def handle_midi_message(self, message: Message) -> None:
        """Decide how to handle incoming MIDI notes based on the mode."""
        # The SynthHandler is responsible for playing notes
        # We play a note whether or note we're recording. 
        self.synth_handler.handle_midi_message(message=message)
        
        # The Sequencer is responsible for recording the notes
        if self.mode == Sequencer.Mode.RECORD:
            # recorded_time is in a factor of quantization_delta, and is based
            # on the scaled value of the message's note.
            # This makes playback very simple because for each invocation of 
            # the clock's callback, we can simply check for messages at the delta.
            recorded_time = (message.note % self.SEQUENCER_STEPS) * self.quantization_delta
            recorded_message = message.copy(time=recorded_time)
            self.recorded_notes[recorded_time].append(recorded_message)


    def sequencer_clock_callback(
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
        recorded_notes_index = delta * (context.event.invocations % self.SEQUENCER_STEPS )

        midi_messages = self.recorded_notes[recorded_notes_index]
        for message in midi_messages:
            self.synth_handler.handle_midi_message(message=message)
        
        delta = self.quantization_delta
        return delta, time_unit

    def start_playback(self) -> None:
        """Start playing back the sequenced drum pattern."""
        self.clock_event_id = self.clock.cue(procedure=self.sequencer_clock_callback, quantization='1/4')
