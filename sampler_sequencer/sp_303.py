from mido import Message

from supriya.conversions import midi_note_number_to_frequency

from class_lib import BaseInstrument

class SP303(BaseInstrument):
    def __init__(self, server, synth_definition, midi_channels):
        super().__init__(server, synth_definition, midi_channels)
        self._load_synthdefs()
        self._name = 'SP-303'
    
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
        self._synths[message.note].set(gate=0)
        del self._synths[message.note]

    def _on_note_on(self, message: Message) -> None:
        """Play a Note On message.
        
        Args:
            message: a Note On Message
        """
        frequency = midi_note_number_to_frequency(message.note + 60)
        synth = self._server.add_synth(
            synthdef=self._synth_definition,
            frequency=frequency
        )
        self._synths[message.note] = synth