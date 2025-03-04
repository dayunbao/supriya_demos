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
from .channel import Channel

from supriya import AddAction, Bus, Group, Server

from .base_effect import BaseEffect
from .base_instrument import BaseInstrument
from .effects_chain import EffectsChain
from .synthdefs import main_audio_output

class Mixer:
    def __init__(
        self, 
        effects: dict[str, BaseEffect],
        instruments: dict[str, BaseInstrument], 
        server: Server
    ) -> None:
        self.server = server
        self._add_synthdefs()
        
        self.main_audio_out_bus: Bus = self.server.add_bus(calculation_rate='audio')
        print()
        print(f'self.main_audio_out_bus={self.main_audio_out_bus}')
        print()
        self.effects_chain_bus: Bus = self.server.add_bus(calculation_rate='audio')

        # Holds all of the other groups
        self.mixer_group: Group = self.server.add_group()
        
        self.instruments = instruments
        self.instruments_group = self.mixer_group.add_group(add_action=AddAction.ADD_TO_TAIL)
        self._add_instruments_to_group()

        self.channel_group = self.mixer_group.add_group(add_action=AddAction.ADD_TO_TAIL)
        self.channels: dict[str, Channel] = self._create_channels()

        self.effects = effects
        self.effects_chain_group = self.mixer_group.add_group(add_action=AddAction.ADD_TO_TAIL)
        self.effects_chain = self._create_effects_chain()

        # This needs to be at the very end as all audio eventually makes its way here.
        self.main_audio_group = self.mixer_group.add_group(add_action=AddAction.ADD_TO_TAIL)
        self.main_audio_output_synth = self.main_audio_group.add_synth(
            amplitude=0.001,
            synthdef=main_audio_output, 
            in_bus=self.main_audio_out_bus,
        )

    def _add_instruments_to_group(self) -> None:
        for instrument in self.instruments.values():
            instrument.group = self.instruments_group

    def _add_synthdefs(self) -> None:
        self.server.add_synthdefs(main_audio_output)
        self.server.sync()
    
    def _create_channels(self) -> dict[str, Channel]:
        channels = {}
        for instrument in self.instruments.values():
            channel = Channel(
                bus=self.server.add_bus(calculation_rate='audio'),
                group=self.channel_group,
                name=instrument.name,
                out_bus=self.effects_chain_bus,
                server=self.server
            )
            
            # Put me in own method
            instrument.out_bus = channel.in_bus
            channel.create_synths()
            channels[instrument.name] = channel
        
        return channels
    
    def _create_effects_chain(self) -> EffectsChain:
        effects_chain =  EffectsChain(
            bus=self.effects_chain_bus,
            effects=list(self.effects.values()),
            group=self.effects_chain_group,
            out_bus=self.main_audio_out_bus,
            server=self.server,
        )

        effects_chain.create_synths()

        return effects_chain

    def start_recording(self) -> None:
        for channel in self.channels.values():
            channel.start_recording_to_disk()

    def stop_recording(self) -> None:
        for channel in self.channels.values():
            channel.stop_recording_to_disk()