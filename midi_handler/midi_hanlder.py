import threading

from mido import get_input_names, Message, open_input
from mido.ports import MultiPort

message_handler_callback: callable
multi_inport: MultiPort
stop_listening_for_input: threading.Event = threading.Event()

def open_multi_inport() -> None:
    """Create a MultiPort that accepts all incoming MIDI messages.

    This is the easiest way to handle the fact that people using
    this script could have an input port named anything.
    """
    global multi_inport
    
    inports = [open_input(p) for p in get_input_names()]
    multi_inport = MultiPort(inports)

def listen_for_midi_messages() -> Message:
    """Listen for incoming MIDI messages in a non-blocking way.
    
    Mido's iter_pending() is non-blocking.
    """
    global message_handler_callback
    global multi_inport

    while not stop_listening_for_input.is_set():
        for message in multi_inport.iter_pending():
            message_handler_callback(message)

def set_message_handler_callback(callback: callable) -> None:
    """Set the callback c=that's called when an incoming MIDI
    message is received.

    Args:
        callback: a callable that will handle the message
    """
    global message_handler_callback

    message_handler_callback = callback