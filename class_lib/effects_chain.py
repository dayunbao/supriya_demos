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
from supriya import AddAction, Bus, Group, Server

from class_lib import BaseEffect

class EffectsChain:
    def __init__(
        self, 
        bus: Bus,
        effects: list[BaseEffect],
        group: Group,
        out_bus: Bus,
        server: Server,
    ) -> None:
        self.effects = effects
        self.server = server
        self.bus = bus
        self.out_bus = out_bus
        self.group = group

    def create_synths(self) -> None:
        self._route_effects_signals()
        for effect in self.effects:
            self.group.add_synth(
                **effect.get_parameters(),
                add_action=AddAction.ADD_AFTER,
            )

    def _route_effects_signals(self) -> None:
        for effect in self.effects:
            if effect.priority == 0:
                # First effect in the chain should be the one to receive
                # the dry audio signal.
                effect.in_bus = self.bus
            
            if effect.priority + 1 < len(self.effects) - 1:
                effect.out_bus = self.effects[effect.priority + 1].in_bus
            
            if effect.priority == len(self.effects) - 1:
                # The last effect in the chain should send its audio signal
                # out over the provided bus.
                effect.out_bus = self.out_bus
