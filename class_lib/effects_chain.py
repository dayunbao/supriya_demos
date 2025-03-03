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
        self._group = group
    
    @property
    def group(self) -> Group:
        return self._group

    @group.setter
    def group(self, group: Group) -> None:
        self._group = group

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
                # out over the chain's bus.
                effect.out_bus = self.out_bus
