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
from pathlib import Path

from supriya import AddAction, Buffer, Bus, Group, Server, Synth

from synth_defs import audio_to_disk, gain, pan, reverb

class Channel:
    def __init__(
        self, 
        bus: Bus,
        group: Group, 
        name: str,
        out_bus: Bus,
        server: Server,
    ) -> None:
        self.group = group
        self.name = f'{name}_channel'
        self.server = server
        self._add_synthdefs()

        self._gain_amplitude = 0.5
        self._pan_position = 0.0
        self._reverb_mix = 0.33
        
        self.gain_synth: Synth | None = None
        self.pan_synth: Synth | None = None
        self.reverb_synth: Synth | None = None
        # The bus that instruments send audio to.
        self.bus = bus
        self.in_bus = self.bus
        self.out_bus = out_bus
        self.pan_bus = self.server.add_bus(calculation_rate='audio')
        self.reverb_bus = self.server.add_bus(calculation_rate='audio')
        # Recording settings
        self.BUFFER_CHANNELS = 2
        self.BUFFER_FRAME_COUNT = 262144
        self.buffer_file_path = self._create_buffer_file_path()
        self.recording_buffer: Buffer | None = None
        self.audio_to_disk_synth: Synth | None = None

    @property
    def gain_amplitude(self) -> float:
        return self._gain_amplitude
    
    @gain_amplitude.setter
    def gain_amplitude(self, gain_amplitude: float) -> None:
        self._gain_amplitude = gain_amplitude
        if self.gain_synth is not None:
            print(f'Setting gain amplitude to {self._gain_amplitude}')
            self.group.set(amplitude=self._gain_amplitude)

    @property
    def pan_position(self) -> float:
        return self._pan_position
    
    @pan_position.setter
    def pan_position(self, pan_position: float) -> None:
        self._pan_position = pan_position
        if self.pan_synth is not None:
            print(f'Setting pan position to {self._pan_position}')
            self.group.set(pan_position=self._pan_position)

    @property
    def reverb_mix(self) -> float:
        return self._reverb_mix
    
    @reverb_mix.setter
    def reverb_mix(self, reverb_mix: float) -> None:
        self._reverb_mix = reverb_mix
        if self.reverb_synth is not None:
            print(f'Setting reverb mix to {self._reverb_mix}')
            self.group.set(mix=self._reverb_mix)

    def _add_synthdefs(self) -> None:
        self.server.add_synthdefs(
            audio_to_disk, 
            gain, 
            pan, 
            reverb
        )
        self.server.sync()
    
    def _create_buffer(self) -> Buffer:
        buffer = self.server.add_buffer(
            channel_count=self.BUFFER_CHANNELS,
            frame_count=self.BUFFER_FRAME_COUNT,
        )

        self.server.sync()

        return buffer

    def _create_buffer_file_path(self) -> Path:
        channel_recordings_dir_path = Path(__file__).parent.parent / 'sampler_sequencer' / 'channel_recordings'
        if not channel_recordings_dir_path.exists():
            channel_recordings_dir_path.mkdir()

        file_path =  channel_recordings_dir_path / f'{self.name}.wav'
        
        if not file_path.exists():
            file_path.touch()
        
        return file_path

    def create_synths(self) -> None:
        self.gain_synth = self.group.add_synth(
            synthdef=gain, 
            amplitude=self.gain_amplitude,
            in_bus=self.in_bus,
            out_bus = self.pan_bus,
            add_action=AddAction.ADD_TO_TAIL,
        )
        
        self.pan_synth = self.group.add_synth(
            synthdef=pan,
            in_bus = self.pan_bus,
            out_bus = self.reverb_bus,
            pan_position=self.pan_position,
            add_action=AddAction.ADD_TO_TAIL,
        )

        self.reverb_synth = self.group.add_synth(
            damping=0.5,
            in_bus=self.reverb_bus,
            mix=self._reverb_mix,
            out_bus=self.out_bus,
            synthdef=reverb,
            add_action=AddAction.ADD_TO_TAIL,
        )
    
    def start_recording_to_disk(self) -> None:
        self.recording_buffer = self._create_buffer()
        self.recording_buffer.write(
            file_path=self.buffer_file_path,
            frame_count=0,
            header_format='WAV',
            leave_open=True,
        )

        self.server.sync()

        self.audio_to_disk_synth = self.group.add_synth(
            synthdef=audio_to_disk,
            buffer_number=self.recording_buffer.id_,
            in_bus=0, # Temporarily hardcoded, change later
            add_action=AddAction.ADD_TO_TAIL,
        )
    
    def stop_recording_to_disk(self) -> None:
        self.audio_to_disk_synth.free()
        self.recording_buffer.close(on_completion=lambda _: self.recording_buffer.free())
        self.server.sync()