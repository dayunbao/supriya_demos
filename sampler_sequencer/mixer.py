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

from supriya import AddAction, Bus, Group, Server

from channel import Channel
from helpers import scale_float
from sampler import Sampler
from synth_defs import main_audio_output

class Mixer:
    def __init__(
        self,
        instrument: Sampler, 
        server: Server
    ) -> None:
        self.server = server
        self._add_synthdefs()
        self.gain_amplitude_cc_num = 1
        # self.channel_eq_cc_num = 2
        self.pan_pos_cc_num = 2
        self.channel_reverb_cc_num = 3
        self.cc_nums = [
            self.gain_amplitude_cc_num,
            # self.channel_eq_cc_num,
            self.pan_pos_cc_num,
            self.channel_reverb_cc_num,
        ]
        
        self.main_audio_out_bus: Bus = self.server.add_bus(calculation_rate='audio')
        self.effects_chain_bus: Bus = self.server.add_bus(calculation_rate='audio')

        # Holds all of the other groups
        self.mixer_group: Group = self.server.add_group()
        
        self.instrument = instrument
        self.instrument_group = self.mixer_group.add_group(add_action=AddAction.ADD_TO_TAIL)
        self._add_instrument_to_group()

        self.channel_group = self.mixer_group.add_group(add_action=AddAction.ADD_TO_TAIL)
        self.channel: Channel = self._create_channel()

        # This needs to be at the very end as all audio eventually makes its way here.
        self.main_audio_group = self.mixer_group.add_group(add_action=AddAction.ADD_TO_TAIL)
        self.main_audio_output_synth = self.main_audio_group.add_synth(
            synthdef=main_audio_output, 
            in_bus=self.main_audio_out_bus,
        )

    def _add_instrument_to_group(self) -> None:
        self.instrument.group = self.instrument_group

    def _add_synthdefs(self) -> None:
        self.server.add_synthdefs(main_audio_output)
        self.server.sync()
    
    def _create_channel(self) -> Channel:
        channel = Channel(
            bus=self.server.add_bus(calculation_rate='audio'),
            group=self.channel_group,
            name=self.instrument.name,
            out_bus=self.main_audio_out_bus,
            server=self.server
        )
        
        # Put me in own method
        self.instrument.out_bus = channel.in_bus
        channel.create_synths()
        
        return channel

    def handle_control_change_message(self, message: Message) -> None:
        if message.is_cc(self.gain_amplitude_cc_num):
            scaled_gain_amplitude = scale_float(
                value=message.value,
                target_min=0.0,
                target_max=1.0
            )
            self.channel.gain_amplitude = scaled_gain_amplitude

        # if message.is_cc(self.channel_eq_cc_num):
        #     scaled_eq_gain = scale_float(
        #         value=message.value,
        #         target_min=0.0,
        #         target_max=1.0
        #     )
        #     self.channel.eq_gain = scaled_eq_gain

        if message.is_cc(self.pan_pos_cc_num):
            scaled_pan_pos = scale_float(
                value=message.value,
                target_min=-1.0,
                target_max=1.0
            )
            self.channel.pan_position = scaled_pan_pos

        if message.is_cc(self.channel_reverb_cc_num):
            scaled_reverb_mix = scale_float(
                value=message.value,
                target_min=0.0,
                target_max=1.0
            )
            self.channel.reverb_mix = scaled_reverb_mix

    def start_recording(self) -> None:
        self.channel.start_recording_to_disk()

    def stop_recording(self) -> None:
        self.channel.stop_recording_to_disk()