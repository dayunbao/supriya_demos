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

from supriya import Server
from supriya.clocks import ClockContext, TimeUnit

from class_lib import MIDIHandler
from class_lib import BaseSequencer
from .sampler import Sampler
from .track import Track

class Sequencer(BaseSequencer):    
    def __init__(
            self, 
            bpm: int, 
            quantization: str,
            sampler: Sampler,
            server: Server,
    ):
        super().__init__(bpm, quantization)
        self.sampler = sampler
        self._is_recording = False
        self.playing_tracks: list[Track] = []
        self.server = server
        self.tracks: dict[str, list[Track]] = self._initialize_tracks()
        self.selected_track = self.tracks[self.sampler.selected_program.name][0]
        self._midi_handler = self._initialize_midi_handler()

    @property
    def is_recording(self) -> bool:
        return self._is_recording
    
    @is_recording.setter
    def is_recording(self, is_recording: bool) -> None:
        self._is_recording = is_recording
        for tracks in self.tracks.values():
            for track in tracks:
                track.is_recording = self._is_recording

    @property
    def midi_handler(self) -> MIDIHandler:
        return self._midi_handler

    @midi_handler.setter
    def midi_handler(self, midi_handler: MIDIHandler) -> None:
        self._midi_handler = midi_handler

    @property
    def quantization(self) -> str:
        return self._quantization
    
    @quantization.setter
    def quantization(self, quantization: str) -> None:
        self._quantization = quantization
        self.quantization_delta = self._convert_quantization_to_delta(quantization=self._quantization)
        self._track_length_in_measures = self._compute_track_length_in_measures()

    @property
    def quantization_delta(self) -> float:
        return self._quantization_delta

    @quantization_delta.setter
    def quantization_delta(self, quantization_delta: float) -> None:
        self._quantization_delta = quantization_delta
        for tracks in self.tracks.values():
            for track in tracks:
                track.quantization_delta = self._quantization_delta

    def add_track(self, program_name: str) -> None:
        added_track_number = 0
        
        if len(self.tracks[program_name]) > 0:
            added_track_number = self.tracks[program_name][-1].track_number + 1
        
        self.tracks[program_name].append(
            Track(
                clock=self._clock,
                instrument=self.sampler,
                is_recording=self.is_recording,
                quantization_delta=self.quantization_delta,
                sequencer_steps=self._SEQUENCER_STEPS,
                server=self.server,
                track_number=added_track_number,
            )
        )

    def delete_track(self, program_name: str, track_number: int) -> None:
        removed_track_number = self.tracks[program_name][track_number].track_number
        del self.tracks[program_name][track_number]
        num_tracks = len(self.tracks[program_name])

        for tn in range(removed_track_number, num_tracks):
            self.tracks[program_name][tn].track_number = tn
    
    def get_selected_track_number(self) -> int:
        return self.selected_track.track_number

    def handle_midi_message(self, message: Message) -> None:
        """
        If recording, we only want to play the selected instrument.
        During playback, we need to play all of the instruments.
        """
        if not self.is_recording:
            # Just play, don't record.
            self.sampler.handle_midi_message(message=message)
        else:
            # The track will record and then send it to the instrument to play.
            self.selected_track.handle_midi_message(message=message)
    
    def _initialize_midi_handler(self) -> MIDIHandler:
        return MIDIHandler(message_handler_callback=self.handle_midi_message)

    def _initialize_tracks(self) -> dict[str, list[Track]]:
        tracks_by_program = defaultdict(list)
        for program in self.sampler.programs:
            tracks_by_program[program.name].append(
                Track(
                    clock=self._clock,
                    instrument=self.sampler,
                    is_recording=self.is_recording,
                    quantization_delta=self.quantization_delta,
                    sequencer_steps=self._SEQUENCER_STEPS,
                    server=self.server,
                    track_number=0,
                )
            )
        
        return tracks_by_program

    def sequencer_clock_callback(
        self, 
        context: ClockContext, 
        delta: float, 
    ) -> tuple[float, TimeUnit]:
        if context.event.invocations % self._track_length_in_measures == 0:
            index = context.event.invocations // self._track_length_in_measures
            self.start_tracks_playback(track_index=index)

        return delta, TimeUnit.BEATS

    def set_selected_track_by_track_number(self, program_name: str, track_number: int) -> None:
        self.selected_track = self.tracks[program_name][track_number]

    def start_playback(self) -> None:
        self._clock.start()
        self._clock_event_id = self._clock.cue(
            kwargs={'delta': 1.0},
            procedure=self.sequencer_clock_callback
        )

    def start_recording(self) -> None:
        self.is_recording = True

    def stop_recording(self) -> None:
        self.is_recording = False
    
    def start_tracks_playback(self, track_index: int) -> None:
        self.stop_tracks_playback()
        if self.playing_tracks:
            self.playing_tracks.clear()
        
        for tracks in self.tracks.values():
            if track_index < len(tracks):
                self.playing_tracks.append(tracks[track_index])
        
        if not self.playing_tracks:
            self.stop_tracks_playback()

        for track in self.playing_tracks:
            track.start_playback()

    def stop_tracks_playback(self) -> None:
        for track in self.playing_tracks:
            track.stop_playback()
