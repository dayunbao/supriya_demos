"""A class representing a channel on a mixer.


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
from supriya import AddAction, Bus, Group, Server

from synth_defs import gain, pan, reverb

class Channel:
    def __init__(
        self, 
        bus: Bus,
        group: Group, 
        out_bus: Bus,
        server: Server,
    ) -> None:
        self.group = group
        self.server = server
        self._add_synthdefs()
        # Defaults
        self._gain_amplitude = 0.5
        self._pan_position = 0.0
        self._reverb_mix = 0.33
        # The bus that receives audio from instruments.
        self.in_bus = bus
        # The bus audio is sent out on after it's been fully processed by the channel.
        self.out_bus = out_bus
        self.pan_bus = self.server.add_bus(calculation_rate='audio')
        self.reverb_bus = self.server.add_bus(calculation_rate='audio')

    @property
    def gain_amplitude(self) -> float:
        return self._gain_amplitude
    
    @gain_amplitude.setter
    def gain_amplitude(self, gain_amplitude: float) -> None:
        self._gain_amplitude = gain_amplitude
        # Update synth
        self.group.set(amplitude=self._gain_amplitude)

    @property
    def pan_position(self) -> float:
        return self._pan_position
    
    @pan_position.setter
    def pan_position(self, pan_position: float) -> None:
        self._pan_position = pan_position
        # Update synth
        self.group.set(pan_position=self._pan_position)

    @property
    def reverb_mix(self) -> float:
        return self._reverb_mix
    
    @reverb_mix.setter
    def reverb_mix(self, reverb_mix: float) -> None:
        self._reverb_mix = reverb_mix
        # Update synth
        self.group.set(mix=self._reverb_mix)

    def _add_synthdefs(self) -> None:
        self.server.add_synthdefs(
            gain, 
            pan, 
            reverb
        )
        self.server.sync()

    def create_synths(self) -> None:
        self.group.add_synth(
            add_action=AddAction.ADD_TO_TAIL,
            amplitude=self.gain_amplitude,
            in_bus=self.in_bus,
            out_bus = self.pan_bus,
            synthdef=gain, 
        )
        
        self.group.add_synth(
            add_action=AddAction.ADD_TO_TAIL,
            in_bus = self.pan_bus,
            out_bus = self.reverb_bus,
            pan_position=self.pan_position,
            synthdef=pan,
        )

        self.group.add_synth(
            add_action=AddAction.ADD_TO_TAIL,
            damping=0.5,
            in_bus=self.reverb_bus,
            mix=self._reverb_mix,
            out_bus=self.out_bus,
            synthdef=reverb,
        )
