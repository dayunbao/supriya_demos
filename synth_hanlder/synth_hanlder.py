from abc import ABC, abstractmethod
from sys import exit

from mido import Message

from supriya import Server, SynthDef


class SynthHandler(ABC):
    def __init__(self, server: Server, provided_synthdefs: SynthDef | list[SynthDef]):
        self.server = server
        self.synthdefs = self._add_synthdefs(provided_synthdefs=provided_synthdefs)
        self._load_synthdefs()
        self.synths = {}
    
    def _add_synthdefs(self, provided_synthdefs: SynthDef | list[SynthDef]) -> list[SynthDef]:
        if not provided_synthdefs:
            exit('You must supply SynthDefs before initializing the SynthHandler!')
        
        temp_synthdefs = []
        if type(provided_synthdefs, list):
            temp_synthdefs.extend(provided_synthdefs)
        
        if type(provided_synthdefs, SynthDef):
            temp_synthdefs.append(provided_synthdefs)
        
        return temp_synthdefs
    
    @abstractmethod
    def _handle_note_on_message(self, message: Message) -> None:
        """Play a Note On message.
        
        Args:
            message: a Note On Message
        """
        pass

    @abstractmethod
    def _handle_note_off_message(self, message: Message) -> None:
        """Play a Note Off message.
        
        Args:
            message: a Note Off Message
        """
        pass

    @abstractmethod
    def _handle_control_change_message(self, message: Message) -> None:
        """Handle a Control Change message.
        
        Args:
            message: a Control Change Message
        """
        pass

    def _load_synthdefs(self) -> None:
        _ = self.server.add_synthdefs(self.synth_defs)
        # Wait for the server to fully load the SynthDef before proceeding.
        self.server.sync()
    
    def play_synth(self, message: Message) -> None:
        if message.type == 'note_on':
            self._handle_note_on_message(message=message)
        
        if message.type == 'note_off':
            self._handle_note_off_message(message=message)
        
        if message.type == 'control_change':
            self._handle_control_change_message(message=message)