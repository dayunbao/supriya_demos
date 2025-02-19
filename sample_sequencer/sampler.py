from synth_handler import SynthHandler

from mido import Message

from supriya import Server, SynthDef

class Sampler(SynthHandler):
    def __init__(self, server: Server, provided_synthdefs: SynthDef | list[SynthDef]):
        super().__init__(server, provided_synthdefs)
    
    def _handle_note_on_message(self, message: Message) -> None:
        """Play a Note On message.
        
        Args:
            message: a Note On Message
        """
        pass

    def _handle_note_off_message(self, message: Message) -> None:
        """Play a Note Off message.
        
        Args:
            message: a Note Off Message
        """
        pass

    def _handle_control_change_message(self, message: Message) -> None:
        """Handle a Control Change message.
        
        Args:
            message: a Control Change message'
             
               Message
        """
        pass