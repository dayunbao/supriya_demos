"""A sequencer.

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
import threading
from copy import deepcopy

from mido import Message

from supriya import Server
from supriya.clocks import Clock, ClockContext, TimeUnit

from rest import Rest
from sampler import Sampler
from sampler_note import SamplerNote
from track import Track

class Sequencer:    
    def __init__(
            self, 
            bpm: int, 
            sampler: Sampler,
            server: Server,
            start_recording_callback: callable,
            stop_recording_callback: callable,
    ):
        self.bpm = bpm
        self.clock = self._initialize_clock()
        self.clock_event_id: int | None = None
        self.DELTA = 0.125
        self.QUANTIZATION = '1/8'
        self.is_sequencing = False
        self.playback_track_index = 0
        self.playing_tracks: list[Track] = []
        self.playing_track: Track = None
        self.sampler = sampler
        self.SEQUENCER_STEPS: int = 16
        self.server = server
        self.stop_callback: bool = False
        self.tracks: list[Track] = self._initialize_tracks()
        self.TRACK_LEN_IN_MEASURES = 2 # 1/8 * 16 = 2 measures
        self.selected_track = self.tracks[0]

        self.monitor_clock_callback_thread = None
        self.monitor_clock_callback_event = threading.Event()
        self.start_recording_callback = start_recording_callback
        self.stop_recording_callback = stop_recording_callback

    def add_track(self) -> None:
        self.tracks.append(
            Track(
                quantization_delta=self.DELTA,
                sequencer_steps=self.SEQUENCER_STEPS,
            )
        )

    def copy_track(self, track_number: int) -> None:
        track_to_copy = self.tracks[track_number]
        new_track = deepcopy(track_to_copy)
        self.tracks.append(new_track)
    
    def _create_monitor_clock_callback_thread(self) -> None:
        self.monitor_clock_callback_thread = threading.Thread(target=self._monitor_clock_callback, daemon=True)
        self.monitor_clock_callback_thread.start()

    def delete_track(self, track_number: int) -> None:
        del self.tracks[track_number]
        
        if len(self.tracks) == 0:
            self.add_track()
        
        self.selected_track = self.tracks[-1]

    def erase_track(self, track_number: int) -> None:
        self.tracks[track_number].erase_recorded_notes()

    def exit(self) -> None:        
        self.stop_playback()

    def get_selected_track_number(self) -> int:
        index = self.tracks.index(self.selected_track)
        return index

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
            
            if self.is_sequencing:
                self.selected_track.record_midi_message(sampler_note=sampler_note)
    
    def handle_note_on(self, message: Message) -> None:
        sampler_note = SamplerNote(
            message=message,
            program=self.sampler.selected_program.name,
            sample_index=self.sampler.selected_program.selected_sample_index,
        )
        
        self.sampler.on_note_on(sampler_note=sampler_note)
        
        if self.is_sequencing:
            self.selected_track.record_midi_message(sampler_note=sampler_note)

    def _initialize_clock(self) -> Clock:
        clock = Clock()
        clock.change(beats_per_minute=self.bpm)

        return clock

    def _initialize_tracks(self) -> list[Track]:
        tracks =[]
        tracks.append(
            Track(
                quantization_delta=self.DELTA,
                sequencer_steps=self.SEQUENCER_STEPS,
            )
        )
        
        return tracks

    def _monitor_clock_callback(self) -> None:
        """Need some way to stop the callback from outside itself,
        and in a non-blocking way."""
        while not self.monitor_clock_callback_event.is_set():
            pass

        self.stop_playback()

    def sequencer_clock_callback(
        self, 
        context: ClockContext, 
        delta: float, 
    ) -> tuple[float, TimeUnit] | None:
        if context.event.invocations % self.SEQUENCER_STEPS == 0:
            if self.playback_track_index == len(self.tracks):
                self.monitor_clock_callback_event.set()
                return None
            
            self.playing_track = self.tracks[self.playback_track_index]
            self.playback_track_index += 1
                    

        recorded_notes_index = delta * (context.event.invocations % self.SEQUENCER_STEPS )
        # Make sure we don't cause recorded_notes to grow needlessly.
        notes: list[SamplerNote] = self.playing_track.recorded_notes.get(recorded_notes_index, Rest)
        if notes is not Rest:
            for note in notes:
                self.sampler.on_note_on(sampler_note=note)

        return delta, TimeUnit.BEATS

    def set_selected_track_by_track_number(self, track_number: int) -> None:
        self.selected_track = self.tracks[track_number]

    def start_playback(self) -> None:
        if len(self.tracks) >= 1 and len(self.tracks[0].recorded_notes.keys()) > 0:
            self.start_recording_callback()
            self._create_monitor_clock_callback_thread()
            self.clock.start()
            self.clock_event_id = self.clock.cue(
                kwargs={'delta': self.DELTA},
                procedure=self.sequencer_clock_callback
            )

    def start_sequencing(self) -> None:
        self.is_sequencing = True

    def stop_playback(self) -> None:
        if self.clock.is_running:
            self.stop_recording_callback()
            self.playback_track_index = 0
            if not self.monitor_clock_callback_event.is_set():
                self.monitor_clock_callback_event.set()
            if self.clock_event_id is not None:
                self.clock.cancel(self.clock_event_id)
                self.clock.stop()

    def stop_sequencing(self) -> None:
        self.is_sequencing = False

