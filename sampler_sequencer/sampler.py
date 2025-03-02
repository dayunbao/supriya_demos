from pathlib import Path

from mido import Message

from supriya import Buffer, Group, Server, SynthDef

from class_lib import BaseInstrument

class Sampler(BaseInstrument):
    def __init__(
            self, 
            midi_channels: list[int],
            server: Server, 
            synth_definition: SynthDef,
        ):
        super().__init__(
            midi_channels,
            server, 
            synth_definition, 
        )
        self._group: Group | None = None
        self._drum_samples_path: Path = Path(__file__).parent / 'samples/roland_tr_909'
        self._drum_buffers = self._load_buffers()
        self._load_synthdefs()
        self._name = 'Sampler'

    @property
    def group(self) -> Group:
        return self._group
    
    @group.setter
    def group(self, group: Group) -> None:
        self._group = group

    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, name: str) -> str:
        self._name = name
    
    def handle_midi_message(self, message: Message) -> None:
        if message.type == 'control_change':
            self._on_control_change(message=message)
        
        if message.type == 'note_off':
            self._on_note_off(message=message)
        
        if message.type == 'note_on':
            self._on_note_on(message=message)

    def _load_buffers(self) -> list[Buffer]:
        drum_buffers = []
        for sample_path in sorted(self._drum_samples_path.rglob(pattern='*.wav')):
            drum_buffers.append(self._server.add_buffer(file_path=str(sample_path)))
        
        return drum_buffers

    def _on_control_change(self, message: Message) -> None:
        """Handle a Control Change message.
        
        Args:
            message: a Control Change message
        """
        pass

    def _on_note_off(self, message: Message) -> None:
        """Play a Note Off message.
        
        Args:
            message: a Note Off Message
        """
        pass

    def _on_note_on(self, message: Message) -> None:
        """Play a Note On message.
        
        Args:
            message: a Note On Message
        """
        if message.channel in self._midi_channels:
            drum_buff = self._drum_buffers[message.channel]
            self.group.add_synth(
                synthdef=self._synth_definition, 
                drum_buff=drum_buff,
                out_bus=self.out_bus,
            )

            print(self._server.dump_tree())
