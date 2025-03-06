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

from supriya import Buffer, Bus, Group, Server, Synth

from sampler_note import SamplerNote
from synth_defs import audio_to_disk

class Track:
    def __init__(
            self, 
            quantization_delta: float,
            # recording_bus: Bus | int, 
            sequencer_steps: int,
            track_number: int,
        ):
        self.quantization_delta = quantization_delta
        self.sequencer_steps =  sequencer_steps
        self.track_number = track_number
        # self.group = group
        # self.recording_bus = recording_bus
        self.recorded_notes: dict[float, list[SamplerNote]] = defaultdict(list)
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
    
    def record_midi_message(self, sampler_note: SamplerNote) -> None:
        recorded_time = (sampler_note.message.note % self.sequencer_steps) * self.quantization_delta
        recorded_message = sampler_note.message.copy(time=recorded_time)
        recorded_sampler_note = SamplerNote(
            message=recorded_message, 
            program=sampler_note.program,
            sample_index=sampler_note.sample_index
            )
        print(f'recorded_sampler_note = {recorded_sampler_note}')
        self.recorded_notes[recorded_time].append(recorded_sampler_note)

    # def _load_synthdef(self) -> None:
    #     self.server.add_synthdefs(audio_to_disk)
    
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

    # def stop_recording_to_disk(self) -> None:
    #     self.audio_to_disk_synth.free()
    #     self.recording_buffer.close(on_completion=lambda _: self.recording_buffer.free())
    #     self.server.sync()

