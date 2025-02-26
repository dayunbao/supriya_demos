"""Play incoming MIDI Note On and Note Off messages.

This script creates a polyphonic synthesizer.  So
multiple notes can be played simultaneously.

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
import mido
from mido.ports import MultiPort

from supriya import Envelope, Server, synthdef, Synth
from supriya.conversions import midi_note_number_to_frequency
from supriya.ugens import EnvGen, Limiter, LFSaw, Out


def open_multi_inport() -> MultiPort:
    """Create a MultiPort that accepts all incoming MIDI messages.

    This is the easiest way to handle the fact that people using
    this script could have an input port named anything.
    """
    inports = [mido.open_input(p) for p in mido.get_input_names()]
    return MultiPort(inports)

def handle_midi_message(message: mido.Message, server: Server, notes: dict[int, Synth]) -> None:
    """Deal with a new MIDI message.

    This function currently only handles Note On and Note Off 
    messages.

    Args:
        message: a MIDI message.
    """
    if message.type == 'note_on':
        frequency = midi_note_number_to_frequency(midi_note_number=message.note)
        synth = server.add_synth(synthdef=saw, frequency=frequency)
        notes[message.note] = synth

    if message.type == 'note_off':
        if message.note in notes:
            notes[message.note].set(gate=0)
            del notes[message.note]

def initialize_supriya() -> Server:
    """Initialize the relevant Supriya objects."""
    server = Server().boot()
    _ = server.add_synthdefs(saw)
    # Wait for the server to fully load the SynthDef before proceeding.
    server.sync()

    return server

def listen_for_midi_messages(multi_inport: MultiPort, notes: dict[int, Synth], server: Server) -> None:
    """Listen for incoming MIDI messages in a non-blocking way.
    
    mido's iter_pending() is non-blocking.
    """
    while True:
        for message in multi_inport.iter_pending():
            handle_midi_message(message=message, notes=notes, server=server)

@synthdef()
def saw(frequency=440.0, amplitude=0.5, gate=1) -> None:
    """Create a SynthDef.  SynthDefs are used to create Synth instances
    that play the notes.

    WARNING: It is very easy to end up with a volume MUCH higher than
    intended when using SuperCollider.  I've attempted to help with
    this by adding a Limiter UGen to this SynthDef.  Depending on your
    OS, audio hardware, and possibly a few other factors, this might
    set the volume too low to be heard.  If so, first adjust the Limiter's
    `level` argument, then adjust the SynthDef's `amplitude` argument.
    NEVER set the `level` to anything higher than 1.  YOU'VE BEEN WARNED!

    Args:
        frequency: the frequency in hertz of a note.
        amplitude: the volume.
        gate: an int, 1 or 0, that controls the envelope.
    """
    signal = LFSaw.ar(frequency=[frequency, frequency - 2])
    signal *= amplitude
    signal = Limiter.ar(duration=0.01, level=0.1, source=signal)

    adsr = Envelope.adsr()
    env = EnvGen.kr(envelope=adsr, gate=gate, done_action=2)
    signal *= env

    Out.ar(bus=0, source=signal)

if __name__ == '__main__':
    server = initialize_supriya()
    multi_inport = open_multi_inport()
    notes: dict[int, Synth] = {}
    listen_for_midi_messages(multi_inport=multi_inport, notes=notes, server=server)