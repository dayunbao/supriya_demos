"""A simple implementation of a mixer.

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

from mido import Message

from supriya import AddAction, Buffer, Bus, Group, Server, Synth

from channel import Channel
from helpers import scale_float
from sampler import Sampler
from synth_defs import audio_to_disk, main_audio_output

class Mixer:
    def __init__(
        self,
        instrument: Sampler, 
        server: Server
    ) -> None:
        self.server = server
        self._add_synthdefs()
        self.GAIN_AMPLITUDE_CC_NUM = 1
        self.PAN_POS_CC_NUM = 2
        self.CHANNEL_REVERB_CC_NUM = 3
        self.cc_nums = [
            self.GAIN_AMPLITUDE_CC_NUM,
            self.PAN_POS_CC_NUM,
            self.CHANNEL_REVERB_CC_NUM,
        ]
        # Recording settings
        self.BUFFER_CHANNELS = 2
        self.BUFFER_FRAME_COUNT = 262144
        self.recording_buffer: Buffer | None = None
        self.audio_to_disk_synth: Synth | None = None
        # Create the groups and buses needed.
        self.main_audio_out_bus: Bus = self.server.add_bus(calculation_rate='audio')
        self.mixer_group: Group = self.server.add_group() # Holds all of the other groups
        self.instrument_group = self.mixer_group.add_group(add_action=AddAction.ADD_TO_TAIL)
        self.instrument = instrument
        self.instrument.group = self.instrument_group
        self.channel_group = self.mixer_group.add_group(add_action=AddAction.ADD_TO_TAIL)
        self.channel: Channel = self._create_channel()
        # This needs to be at the very end, as all audio eventually makes its way here.
        self.main_audio_group = self.mixer_group.add_group(add_action=AddAction.ADD_TO_TAIL)
        self.main_audio_output_synth = self.main_audio_group.add_synth(
            in_bus=self.main_audio_out_bus,
            synthdef=main_audio_output, 
        )

    def _add_synthdefs(self) -> None:
        self.server.add_synthdefs(audio_to_disk, main_audio_output)
        self.server.sync()
    
    def _create_buffer(self) -> Buffer:
        buffer = self.server.add_buffer(
            channel_count=self.BUFFER_CHANNELS,
            frame_count=self.BUFFER_FRAME_COUNT,
        )

        self.server.sync()

        return buffer

    def _create_buffer_file_path(self) -> Path:
        file_path = Path(__file__).parent / 'recordings' / 'recording.wav'
        # Make sure we're staring with a few file each time.
        file_path.unlink(missing_ok=True)
        file_path.touch()
        
        return file_path

    def _create_channel(self) -> Channel:
        channel = Channel(
            bus=self.server.add_bus(calculation_rate='audio'),
            group=self.channel_group,
            out_bus=self.main_audio_out_bus,
            server=self.server
        )
        # Connect the instrument's audio output to the channel.
        self.instrument.out_bus = channel.in_bus
        channel.create_synths()
        
        return channel

    def exit(self) -> None:
        self.mixer_group.free()

    def handle_control_change_message(self, message: Message) -> None:
        if message.is_cc(self.GAIN_AMPLITUDE_CC_NUM):
            scaled_gain_amplitude = scale_float(
                value=message.value,
                target_min=0.0,
                target_max=1.0
            )
            self.channel.gain_amplitude = scaled_gain_amplitude

        if message.is_cc(self.PAN_POS_CC_NUM):
            scaled_pan_pos = scale_float(
                value=message.value,
                target_min=-1.0,
                target_max=1.0
            )
            self.channel.pan_position = scaled_pan_pos

        if message.is_cc(self.CHANNEL_REVERB_CC_NUM):
            scaled_reverb_mix = scale_float(
                value=message.value,
                target_min=0.0,
                target_max=1.0
            )
            self.channel.reverb_mix = scaled_reverb_mix

    def start_recording(self) -> None:
        self.recording_buffer = self._create_buffer()
        buffer_file_path = self._create_buffer_file_path()
        self.recording_buffer.write(
            file_path=buffer_file_path,
            frame_count=0,
            header_format='WAV',
            leave_open=True,
        )

        self.server.sync()

        # Need to place this in the same group as the main audio group
        # in order to capture the final output of the channel's processed
        # signal. 
        self.audio_to_disk_synth = self.main_audio_group.add_synth(
            add_action=AddAction.ADD_TO_TAIL,
            buffer_number=self.recording_buffer.id_,
            in_bus=0,
            synthdef=audio_to_disk,
        )
    
    def stop_recording(self) -> None:
        if self.recording_buffer is not None:
            self.audio_to_disk_synth.free()
            self.recording_buffer.close(on_completion=lambda _: self.recording_buffer.free())
            self.server.sync()
