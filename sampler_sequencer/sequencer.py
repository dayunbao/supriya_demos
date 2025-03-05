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

from supriya import Server
from supriya.clocks import Clock, ClockContext, TimeUnit

from midi_handler import MIDIHandler
from sampler import Sampler
from sampler_note import SamplerNote
from track import Track

class Sequencer:    
    def __init__(
            self, 
            bpm: int, 
            sampler: Sampler,
            server: Server,
    ):
        self.bpm = bpm
        self._clock = self._initialize_clock()
        self._clock_event_id: int | None = None
        self.sampler = sampler
        self._SEQUENCER_STEPS: int = 16
        self.server = server
        self.quantization = '1/8'
        self.quantization_delta = 0.125
        self.is_recording = False
        self.tracks: list[Track] = self._initialize_tracks()
        self.playing_tracks: list[Track] = []
        self._track_length_in_measures = self._compute_track_length_in_measures()
        self.selected_track = self.tracks[0]
        self.midi_handler = self._initialize_midi_handler()

    def add_track(self) -> None:
        added_track_number = 0
        
        if len(self.tracks) > 0:
            added_track_number = self.tracks[-1].track_number + 1
        
        self.tracks.append(
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

    def _compute_track_length_in_measures(self) -> int:
        return self._SEQUENCER_STEPS // int(self.quantization.split('/')[1])

    def delete_track(self, track_number: int) -> None:
        removed_track_number = self.tracks[track_number].track_number
        del self.tracks[track_number]
        num_tracks = len(self.tracks)

        for tn in range(removed_track_number, num_tracks):
            self.tracks[tn].track_number = tn

    def exit(self) -> None:        
        self.midi_handler.exit()

    def get_selected_track_number(self) -> int:
        return self.selected_track.track_number

    def handle_midi_message(self, message: Message) -> None:
        """
        Entry point for MIDI messages.  Convert to SamplerNote here.

        If recording, we only want to play the selected instrument.
        During playback, we need to play all of the instruments.
        """
        if not self.is_recording:
            # Just play, don't record.
            sampler_note = SamplerNote(
                message=message,
                program=self.sampler.selected_program.name,
            )
            self.sampler.handle_midi_message(sampler_note=sampler_note)
        else:
            # The track will record and then send it to the instrument to play.
            sampler_note = SamplerNote(
                message=message,
                program=self.sampler.selected_program.name,
            )
            self.selected_track.handle_midi_message(sampler_note=sampler_note)

    def _initialize_clock(self) -> Clock:
        """Initialize the Supriya's Clock."""
        clock = Clock()
        clock.change(beats_per_minute=self.bpm)

        return clock

    def _initialize_midi_handler(self) -> MIDIHandler:
        return MIDIHandler(message_handler_callback=self.handle_midi_message)

    def _initialize_tracks(self) -> list[Track]:
        tracks =[]
        tracks.append(
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
        
        return tracks

    def sequencer_clock_callback(
        self, 
        context: ClockContext, 
        delta: float, 
    ) -> tuple[float, TimeUnit] | None:
        if context.event.invocations % self._track_length_in_measures == 0:
            track_index = context.event.invocations // self._track_length_in_measures
            self.start_tracks_playback(track_index=track_index)

        return delta, TimeUnit.BEATS

    def run(self) -> None:
        pass

    def set_selected_track_by_track_number(self, track_number: int) -> None:
        self.selected_track = self.tracks[track_number]

    def start_playback(self) -> None:
        self._clock.start()
        self._clock_event_id = self._clock.cue(
            kwargs={'delta': 1.0},
            procedure=self.sequencer_clock_callback
        )

    def start_recording(self) -> None:
        self.is_recording = True
        for track in self.tracks:
            track.is_recording = self.is_recording

    def stop_playback(self) -> None:
        """Stop playing track."""
        self._clock.stop()
        if self._clock_event_id is not None:
            self._clock.cancel(self._clock_event_id)

    def stop_recording(self) -> None:
        self.is_recording = False
        for track in self.tracks:
            track.is_recording = self.is_recording
    
    def start_tracks_playback(self, track_index: int) -> None:
        print(f'Starting tracks playback at index {track_index}')
        self.stop_tracks_playback()
        if self.playing_tracks:
            self.playing_tracks.clear()
        
        if track_index < len(self.tracks):
            self.playing_tracks.append(self.tracks[track_index])
        
        if not self.playing_tracks:
            self.stop_tracks_playback()

        for track in self.playing_tracks:
            track.start_playback()

    def stop_tracks_playback(self) -> None:
        for track in self.playing_tracks:
            track.stop_playback()
