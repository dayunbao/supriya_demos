from pathlib import Path

from mido import Message

from supriya import Buffer, Server, SynthDef

from class_lib import SynthHandler

class Sampler(SynthHandler):
    def __init__(self, server: Server, synth_definitions: dict[str, SynthDef]):
        super().__init__(server, synth_definitions)
        self.drum_samples_path: Path = Path(__file__).parent / 'samples/roland_tr_909'
        self.drum_buffers = self._load_buffers()
        self._load_synthdefs()

    def _load_buffers(self) -> list[Buffer]:
        drum_buffers = []
        for sample_path in sorted(self.drum_samples_path.rglob(pattern='*.wav')):
            drum_buffers.append(self.server.add_buffer(file_path=str(sample_path)))
        
        return drum_buffers

    def handle_midi_message(self, message: Message) -> None:
        if message.type == 'control_change':
            self._on_control_change(message=message)
        
        if message.type == 'note_off':
            self._on_note_off(message=message)
        
        if message.type == 'note_on':
            self._on_note_on(message=message)

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
        if message.channel < 12:
            drum_buff = self.drum_buffers[message.channel]
            _ = self.server.add_synth(
                synthdef=self.synth_definitions['sample_player'], 
                drum_buff=drum_buff
            )
        else:
            pass
