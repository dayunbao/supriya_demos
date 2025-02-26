"""Create a polyphonic synthesizer with effects.

This script builds on the midi_synth.py script by
adding delay and reverb synths, and accepting MIDI
Control Change messages to change some of the effects'
parameters.

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


DELAY_CC_NUM: int = 0
REVERB_CC_NUM: int = 1

def create_buses(server: Server) -> tuple[Bus, Bus]:
    """Create buses.

    We need busses to route the saw synth's audio through,
    and groups to keep the order of execution correct on 
    the SuperCollider server.
    """
    delay_bus = server.add_bus(calculation_rate='audio')
    reverb_bus = server.add_bus(calculation_rate='audio')

    return delay_bus, reverb_bus

def create_effects_synths(delay_bus: Bus, effects_group: Group, reverb_bus: Bus) -> None:
    """Create the effects synths."""
    effects_group.add_synth(
        synthdef=delay,
        in_bus=delay_bus,
        maximum_delay_time=0.2, 
        delay_time=0.2, 
        decay_time=5.0,
        out_bus=reverb_bus
    )

    effects_group.add_synth(
        synthdef=reverb,
        in_bus=reverb_bus,
        mix=0.33,
        room_size=1.0,
        damping=0.5,
        out_bus=0,
    )

def create_groups(server: Server) -> tuple[Group, Group]:
    """Create groups to hold the various synths.

    This is done because the saw synths need to be at the 
    head of the SuperCollider server, while the effects synths
    need to be at the tail.  The order of the synths, or groups,
    affects the order in which the audio signals are processed.
    Using groups makes it easy to ensure this happens in the correct
    order, with the sound-producing synth's audio signal being at 
    the head, and the sound-consuming synths (effects) at the tail.
    """
    # All of the ephemeral saw synths will be added to this group.
    synth_group = server.add_group()
    effects_group = server.add_group(add_action=AddAction.ADD_AFTER)

    return synth_group, effects_group

def handle_midi_message(
        delay_bus: Bus, 
        effects_group: Group, 
        message: mido.Message, 
        notes: dict[int, Synth], 
        synth_group: Group
) -> None:
    """Deal with a new MIDI message., 

    This function currently only handles Note On, Note Off 
    and Control Change messages.
    """
    global DELAY_CC_NUM
    global REVERB_CC_NUM

    if message.type == 'note_on':
        frequency = midi_note_number_to_frequency(midi_note_number=message.note + 60)
        synth = synth_group.add_synth(synthdef=saw, frequency=frequency, out_bus=delay_bus)
        notes[message.note] = synth

    if message.type == 'note_off':
        notes[message.note].set(gate=0)
        del notes[message.note]
    
    if message.type == 'control_change':
        # Figure out which parameter should be changed based on the 
        # control number.
        if message.is_cc(DELAY_CC_NUM):
            scaled_decay_time = scale_float(value=message.value, target_min=0.0, target_max=10.0)
            effects_group.set(decay_time=scaled_decay_time)
            
        if message.is_cc(REVERB_CC_NUM):
            scaled_reverb_mix = scale_float(value=message.value, target_min=0.0, target_max=1.0)
            effects_group.set(mix=scaled_reverb_mix)

def initialize_server() -> Server:
    """Initialize the server."""
    server = Server().boot()
    _ = server.add_synthdefs(delay, reverb, saw)
    # Wait for the server to fully load the SynthDef before proceeding.
    server.sync()

    return server

def listen_for_midi_messages(
        delay_bus: Bus, 
        effects_group: Group, 
        multi_inport: MultiPort,
        notes: dict[int, Synth], 
        synth_group: Group
) -> None:
    """Listen for incoming MIDI messages."""
    while True:
        for message in multi_inport.iter_pending():
            handle_midi_message(
                delay_bus=delay_bus,
                effects_group=effects_group,
                message=message,
                notes=notes,
                synth_group=synth_group,
            )

def open_multi_inport() -> MultiPort:
    """Create a MultiPort that accepts all incoming MIDI messages.

    This is the easiest way to handle the fact that people using
    this script could have an input port named anything.
    """
    inports = [mido.open_input(p) for p in mido.get_input_names()]
    
    return MultiPort(inports)

def scale_float(value: int, target_min: float, target_max: float):
    """
    Linearly scale a value from one range to another.

    Args:
        source_value (float): The value to be scaled.

    Returns:
        float: The scaled value in the target range.
    """
    source_min = 0
    source_max = 127
    
    scaled_value = (value - source_min) * (target_max - target_min) / (source_max - source_min) + target_min
    return round(number=scaled_value, ndigits=2)

def main() -> None:
    server = initialize_server()
    synth_group, effects_group = create_groups(server=server)
    delay_bus, reverb_bus = create_buses(server=server)
    create_effects_synths(
        delay_bus=delay_bus, 
        effects_group=effects_group,
        reverb_bus=reverb_bus
    )
    multi_inport = open_multi_inport()
    notes: dict[int, Synth] = {}
    listen_for_midi_messages(
        delay_bus=delay_bus, 
        effects_group=effects_group,
        multi_inport=multi_inport,
        notes=notes,
        synth_group=synth_group
    )

if __name__ == '__main__':
    main()