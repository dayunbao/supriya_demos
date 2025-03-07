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
from concurrent.futures import Future

from mido import Message

from supriya import Server
from supriya.clocks import Clock, ClockContext, TimeUnit

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
        self.SEQUENCER_STEPS: int = 16
        self.server = server
        self.QUANTIZATION = '1/8'
        self.DELTA = 0.125
        self.is_recording = False
        self.tracks: list[Track] = self._initialize_tracks()
        self.playing_tracks: list[Track] = []
        self.playing_track: Track = None
        self.TRACK_LEN_IN_MEASURES = 2 # 1/8 * 16 = 2 measures
        self.selected_track = self.tracks[0]

    def add_track(self) -> None:
        added_track_number = 0
        
        if len(self.tracks) > 0:
            added_track_number = self.tracks[-1].track_number + 1
        
        self.tracks.append(
            Track(
                quantization_delta=self.DELTA,
                sequencer_steps=self.SEQUENCER_STEPS,
                track_number=added_track_number,
            )
        )

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
        if message.type == 'control_change':
            self.sampler.on_control_change(message=message)
            return
        
        if message.type == 'program_change':
            self.sampler.on_program_change(message=message)
            return
        
        if message.type == 'note_on':
            sampler_note = SamplerNote(
                message=message,
                program=self.sampler.selected_program.name,
                sample_index=self.sampler.selected_program.selected_sample_index,
            )
            
            self.sampler.on_note_on(sampler_note=sampler_note)
            
            if self.is_recording:
                self.selected_track.record_midi_message(sampler_note=sampler_note)
    
    def handle_note_on(self, message: Message) -> None:
        sampler_note = SamplerNote(
            message=message,
            program=self.sampler.selected_program.name,
            sample_index=self.sampler.selected_program.selected_sample_index,
        )
        
        self.sampler.on_note_on(sampler_note=sampler_note)
        
        if self.is_recording:
            self.selected_track.record_midi_message(sampler_note=sampler_note)

    def _initialize_clock(self) -> Clock:
        """Initialize the Supriya's Clock."""
        clock = Clock()
        clock.change(beats_per_minute=self.bpm)

        return clock

    def _initialize_tracks(self) -> list[Track]:
        tracks =[]
        tracks.append(
            Track(
                quantization_delta=self.DELTA,
                sequencer_steps=self.SEQUENCER_STEPS,
                track_number=0,
            )
        )
        
        return tracks

    def sequencer_clock_callback(
        self, 
        context: ClockContext, 
        delta: float, 
        future: Future,
    ) -> tuple[float, TimeUnit] | None:
        track_index = 0
        if context.event.invocations == 0:
            self.playing_track = self.tracks[track_index]
        
        if (delta * (context.event.invocations + 1)) % self.TRACK_LEN_IN_MEASURES == 0:
            track_index = context.desired_moment.measure // self.TRACK_LEN_IN_MEASURES
            
            if track_index == len(self.tracks):
                future.set_result(True)
                return None
            
            self.playing_track = self.tracks[track_index]

        recorded_notes_index = delta * (context.event.invocations % self.SEQUENCER_STEPS )
        notes: list[SamplerNote] = self.playing_track.recorded_notes[recorded_notes_index]
        for note in notes:
            self.sampler.on_note_on(sampler_note=note)

        return delta, TimeUnit.BEATS

    def run(self) -> None:
        pass

    def set_selected_track_by_track_number(self, track_number: int) -> None:
        self.selected_track = self.tracks[track_number]

    def start_playback(self) -> None:
        self._clock.start()
        future = Future()
        self._clock_event_id = self._clock.cue(
            kwargs={'delta': self.DELTA, 'future': future},
            procedure=self.sequencer_clock_callback
        )
        future.result()
        self.stop_playback()

    def start_recording(self) -> None:
        self.is_recording = True

    def stop_playback(self) -> None:
        """Stop playing track."""
        self._clock.stop()
        if self._clock_event_id is not None:
            self._clock.cancel(self._clock_event_id)

    def stop_recording(self) -> None:
        self.is_recording = False

