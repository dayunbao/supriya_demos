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

from supriya import AddAction, Bus, Group, Server, Synth
from supriya.conversions import midi_note_number_to_frequency

from synth_defs import delay, reverb, saw

delay_synth: Synth
effects_group: Group
multi_inport: MultiPort
notes: dict[int, Synth] = {}
delay_bus: Bus
reverb_synth: Synth
server: Server
synth_group: Group

def create_effects_synths() -> None:
    """Create the effects synths.

    We need busses to route the saw synth's audio through,
    and groups to keep the order of execution correct on 
    the SuperCollider server.
    """
    global delay_synth
    global effects_group
    global delay_bus
    global reverb_synth
    global server
    
    delay_bus = server.add_bus(calculation_rate='audio')
    reverb_bus = server.add_bus(calculation_rate='audio')

    delay_synth = effects_group.add_synth(
        synthdef=delay,
        in_bus=delay_bus,
        maximum_delay_time=0.2, 
        delay_time=0.2, 
        decay_time=5.0,
        out_bus=reverb_bus
    )

    reverb_synth = effects_group.add_synth(
        synthdef=reverb,
        in_bus=reverb_bus,
        mix=1.0,
        room_size=0.7,
        damping=0.5,
        out_bus=0,
    )

def create_groups() -> None:
    """Create groups to hold the various synths.

    This is done because the saw synths need to be at the 
    head of the SuperCollider server, while the effects synths
    need to be at the tail.  The order of the synths, or groups,
    affects the order in which the audio signals are processed.
    Using groups makes it easy to ensure this happens.
    """
    global effects_group
    global server
    global synth_group

    # All of the ephemeral saw synths will be added to this group.
    synth_group = server.add_group()
    effects_group = server.add_group(add_action=AddAction.ADD_AFTER)

def handle_midi_message(message: mido.Message) -> None:
    """Deal with a new MIDI message.

    This function currently only handles Note On and Note Off 
    messages.

    Args:
        message: a MIDI message.
    """
    global delay_bus
    global notes
    global synth_group

    if message.type == 'note_on':
        frequency = midi_note_number_to_frequency(midi_note_number=message.note + 60)
        synth = synth_group.add_synth(synthdef=saw, frequency=frequency, out_bus=delay_bus)
        notes[message.note] = synth

    if message.type == 'note_off':
        if message.note in notes:
            notes[message.note].set(gate=0)
            del notes[message.note]

def initialize_supriya() -> None:
    """Initialize the relevant Supriya objects."""
    global server
    
    server = Server().boot()
    _ = server.add_synthdefs(delay, reverb, saw)
    # Wait for the server to fully load the SynthDef before proceeding.
    server.sync()

def listen_for_midi_messages() -> None:
    """Listen for incoming MIDI messages in a non-blocking way.
    
    mido's iter_pending() is non-blocking.
    """
    global multi_inport

    while True:
        for message in multi_inport.iter_pending():
            handle_midi_message(message=message)

def open_multi_inport() -> None:
    """Create a MultiPort that accepts all incoming MIDI messages.

    This is the easiest way to handle the fact that people using
    this script could have an input port named anything.
    """
    global multi_inport
    
    inports = [mido.open_input(p) for p in mido.get_input_names()]
    multi_inport = MultiPort(inports)

if __name__ == '__main__':
    initialize_supriya()
    create_groups()
    create_effects_synths()
    open_multi_inport()
    listen_for_midi_messages()