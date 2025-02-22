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
from mido import Message

from class_lib import MIDIHandler
from class_lib import BaseSequencer
from class_lib import SynthHandler
from .track import Track

class Sequencer(BaseSequencer):    
    def __init__(
            self, 
            bpm: int, 
            instruments: list[SynthHandler],
            quantization: str,
    ):
        super().__init__(bpm, quantization)
        self.instruments = instruments
        self._midi_handler = self._initialize_midi_handler()
        self.is_recording = False
        self._tracks: list[Track] = self._initialize_tracks()

    @property
    def midi_handler(self) -> MIDIHandler:
        return self._midi_handler
    
    @midi_handler.setter
    def midi_handler(self, midi_handler: MIDIHandler) -> None:
        self._midi_handler = midi_handler

    @property
    def tracks(self) -> list[Track]:
        return self._tracks
    
    @tracks.setter
    def tracks(self, tracks: list[Track]) -> None:
        self._tracks = tracks

    def add_track(self) -> None:
        track = Track(
            clock=self.clock,
            quantization=self.quantization,
            sequencer_mode=self.mode,
            synth_handler=self.synth_handler,
            track_number=self.tracks[-1].track_number + 1,
        )

        self.tracks.append(track)

    def get_tracks_strings(self) -> list[str]:
        return [str(t) for t in self.tracks]

    def delete_track(self, track_num) -> None:
        removed = self.tracks.pop(track_num)
        for t in range(removed.track_number):
            self.tracks[t].track_number = t

    def _initialize_midi_handler(self) -> MIDIHandler:
        return MIDIHandler(message_handler_callback=self.handle_midi_message)

    def _initialize_tracks(self) -> list[Track]:
        track = Track(
            clock=self.clock,
            quantization=self.quantization,
            sequencer_mode=self.mode,
            synth_handler=self.synth_handler,
            track_number=0,
        )
        
        return [track]

    def handle_midi_message(self, message: Message) -> None:
        # The SynthHandler is responsible for playing notes
        # We play a note whether or note we're recording. 
        self.synth_handler.handle_midi_message(message=message)
        
        # The Sequencer is responsible for recording the notes
        if self.mode == Sequencer.Mode.RECORD and self.is_recording:
            # recorded_time is in a factor of quantization_delta, and is based
            # on the scaled value of the message's note.
            # This makes playback very simple because for each invocation of 
            # the clock's callback, we can simply check for messages at the delta.
            recorded_time = (message.note % self.SEQUENCER_STEPS) * self.quantization_delta
            recorded_message = message.copy(time=recorded_time)
            self.recorded_notes[recorded_time].append(recorded_message)
    
    def start_playback(self) -> None:
        """Start playing back all of the tracks."""
        for track in self.tracks:
            track.start_playback()

    def stop_playback(self) -> None:
        for track in self.tracks:
            track.stop_playback()

    def start_recording(self) -> None:
        self.is_recording = True

    def stop_recording(self) -> None:
        self.is_recording = False