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
from class_lib import BaseInstrument
from .track import Track

class Sequencer(BaseSequencer):    
    def __init__(
            self, 
            bpm: int, 
            instruments: list[BaseInstrument],
            quantization: str,
    ):
        super().__init__(bpm, quantization)
        self._instruments = instruments
        self._midi_handler = self._initialize_midi_handler()
        self._is_recording = False
        self._tracks: list[Track] = self._initialize_tracks()

    @property
    def bpm(self) -> int:
        return self._bpm
    
    @bpm.setter
    def bpm(self, bpm: int) -> None:
        self._bpm = bpm
        self._clock.change(beats_per_minute=self._bpm)

    @property
    def quantization(self) -> str:
        return self._quantization
    
    @quantization.setter
    def quantization(self, quantization: str) -> None:
        self._quantization = quantization

    @property
    def is_recording(self) -> bool:
        return self._is_recording
    
    @is_recording.setter
    def is_recording(self, is_recording: bool) -> None:
        self._is_recording = is_recording
        for t in self.tracks:
            t.is_recording = self._is_recording

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

    def add_track(self, instruments_index) -> None:
        track = Track(
            clock=self.clock,
            is_recording=self.is_recording,
            quantization=self.quantization,
            sequencer_steps=self.SEQUENCER_STEPS,
            instrument=self._instruments[instruments_index],
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
            clock=self._clock,
            is_recording=self.is_recording,
            quantization=self._quantization,
            sequencer_steps=self.SEQUENCER_STEPS,
            # Default to the first available
            instrument=self._instruments[0],
            track_number=0,
        )
        
        return [track]

    def handle_midi_message(self, message: Message) -> None:
        # The tracks' instrument are responsible for playing notes
        # We play a note whether or note we're recording. 
        for track in self.tracks:
            track.handle_midi_message(message=message)
    
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