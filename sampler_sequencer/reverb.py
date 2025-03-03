from typing import Optional

from supriya import Bus, Group, Server, SynthDef

from class_lib import BaseEffect

class Reverb(BaseEffect):
    def __init__(self, 
        name: str, 
        server: Server, 
        synth_def: SynthDef, 
        group: Optional[Group | None]=None,
        out_bus: int | Bus=0,
    ) -> None:
        super().__init__(
            name=name, 
            server=server, 
            synth_def=synth_def, 
            group=group,
            out_bus=out_bus,
        )
        self.damping = 0.5
        self.mix = 0.33
        self.room_size = 0.5

    def get_parameters(self) -> dict[str, any]:
        return {
            'damping': self.damping,
            'in_bus': self.in_bus,
            'mix': self.mix,
            'out_bus': self._out_bus,
            'room_size': self.room_size,
            'synthdef': self.synth_def,
        }