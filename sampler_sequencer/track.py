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
from pathlib import Path

from mido import Message

from supriya import Buffer, Bus, Group, Server, Synth
from supriya.clocks import Clock, ClockContext, TimeUnit

from rest import Rest
from sampler import Sampler
from sampler_note import SamplerNote
from synth_defs import audio_to_disk

class Track:
    def __init__(
            self, 
            clock: Clock,
            # group: Group,
            instrument: Sampler,
            is_recording: bool,
            quantization_delta: float,
            # recording_bus: Bus | int, 
            sequencer_steps: int,
            server: Server,
            track_number: int,
        ):
        self.clock = clock
        self.clock_event_id: int | None = None
        self.instrument = instrument
        self.quantization_delta = quantization_delta
        self.sequencer_steps =  sequencer_steps
        self.track_number = track_number
        # self.group = group
        self.is_recording = is_recording
        # self.recording_bus = recording_bus
        self.recorded_notes: dict[float, list[SamplerNote]] = defaultdict(list)
        self.server = server
        # self._load_synthdef()
        # self.BUFFER_CHANNELS = 2
        # self.BUFFER_FRAME_COUNT = 262144
        # self.buffer_file_path = self._create_buffer_file_path()
        # self.recording_buffer: Buffer | None = None
        # self.audio_to_disk_synth: Synth | None = None

    # def _create_buffer(self) -> Buffer:
    #     buffer = self.server.add_buffer(
    #         channel_count=self.BUFFER_CHANNELS,
    #         frame_count=self.BUFFER_FRAME_COUNT,
    #     )

    #     self.server.sync()

    #     return buffer

    # def _create_buffer_file_path(self) -> Path:
    #     track_recordings_dir_path = Path(__file__).parent / 'track_recordings'
    #     if not track_recordings_dir_path.exists():
    #         track_recordings_dir_path.mkdir()
        
    #     instrument_dir_path = Path(__file__).parent / track_recordings_dir_path / self._instrument.name
    #     if not instrument_dir_path.exists():
    #         instrument_dir_path.mkdir()

    #     file_path =  instrument_dir_path / f'track_{self.track_number}.wav'
        
    #     if not file_path.exists():
    #         file_path.touch()
        
    #     return file_path

    def erase_recorded_notes(self) -> None:
        self.recorded_notes.clear()
    
    def handle_midi_message(self, sampler_note: SamplerNote) -> None:
        """Decide how to handle incoming MIDI notes based on the mode."""
        # The SynthHandler is responsible for playing notes
        # We play a note whether or note we're recording. 
        self.instrument.handle_midi_message(sampler_note=sampler_note)
        
        # The Sequencer is responsible for recording the notes
        if self.is_recording and sampler_note.message.type == 'note_on':
            # recorded_time is in a factor of quantization_delta, and is based
            # on the scaled value of the message's note.
            # This makes playback very simple because for each invocation of 
            # the clock's callback, we can simply check for messages at the delta.
            recorded_time = (sampler_note.message.note % self.sequencer_steps) * self.quantization_delta
            recorded_message = sampler_note.message.copy(time=recorded_time)
            recorded_sampler_note = SamplerNote(program=sampler_note.program, message=recorded_message)
            self.recorded_notes[recorded_time].append(recorded_sampler_note)

    # def _load_synthdef(self) -> None:
    #     self.server.add_synthdefs(audio_to_disk)

    def start_playback(self) -> None:
        # self.start_recording_to_disk()

        self.clock_event_id = self.clock.cue(
            kwargs={'delta': self.quantization_delta},
            procedure=self.track_clock_callback
        )
    
    # def start_recording_to_disk(self) -> None:
    #     self.recording_buffer = self._create_buffer()
    #     self.recording_buffer.write(
    #         file_path=self.buffer_file_path,
    #         frame_count=0,
    #         header_format='WAV',
    #         leave_open=True,
    #     )

    #     self.server.sync()

    #     self.audio_to_disk_synth = self.group.add_synth(
    #         synthdef=audio_to_disk,
    #         buffer_number=self.recording_buffer.id_,
    #         in_bus=self.recording_bus,
    #     )

    def stop_playback(self) -> None:
        """Stop playing track."""
        if self.clock_event_id is not None:
            self.clock.cancel(self.clock_event_id)
        # self.stop_recording_to_disk()

    # def stop_recording_to_disk(self) -> None:
    #     self.audio_to_disk_synth.free()
    #     self.recording_buffer.close(on_completion=lambda _: self.recording_buffer.free())
    #     self.server.sync()

    def track_clock_callback(
        self, 
        context:ClockContext, 
        delta: float,
    ) -> tuple[float, TimeUnit]:
        """The function that runs on each invocation.

        The callback is executed once every `delta`.  What delta means depends on time_unit.  
        Options for time_unit are BEATS or SECONDS.  If you want this function to called
        once every 1/4, 1/8, or 1/16 note, then time_unit should be BEATS.  Otherwise
        you can specify SECONDS as the time_unit to have it called outside of a 
        musical rhythmic context.
        """
        recorded_notes_index = delta * (context.event.invocations % self.sequencer_steps )

        sampler_notes = self.recorded_notes.get(recorded_notes_index, Rest)
        if sampler_notes is not Rest:
            for sampler_note in sampler_notes:
                self.instrument.handle_midi_message(sampler_note=sampler_note)
        
        return delta, TimeUnit.BEATS
