"""A simple drum machine with a 16-step sequencer.

Typical usage example:

  python midi_drum_sequencer.py -b 60

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
import sys
import threading
from collections import defaultdict
from enum import Enum
from typing import get_args

import click

from mido import get_input_names, Message, open_input
from mido.ports import MultiPort

from supriya import Server, synthdef
from supriya.clocks import Clock, ClockContext
from supriya.clocks.bases import Quantization
from supriya.clocks.ephemera import TimeUnit

from synth_defs import (
    bass_drum,
    clap_dry,
    claves,
    closed_high_hat,
    cow_bell,
    cymbal,
    high_conga,
    high_tom,
    low_conga,
    low_tom,
    maracas,
    medium_conga,
    medium_tom,
    open_high_hat,
    rim_shot,
    snare,
)

class SequencerMode(Enum):
    # Used to track the current state of the sequencer
    PERFORM = 0
    PLAYBACK = 1
    RECORD = 2

clock: Clock
clock_event_id: int
midi_channel_to_synthdef: list[synthdef] = [
    bass_drum,
    snare,
    low_tom,
    medium_tom,
    high_tom,
    low_conga,
    medium_conga,
    high_conga,
    rim_shot,
    clap_dry,
    claves,
    maracas,
    cow_bell,
    cymbal,
    open_high_hat,
    closed_high_hat,
]
multi_inport: MultiPort
quantization_delta: float
recorded_notes: dict[float, list[Message]] = defaultdict(list)
sequencer_mode: Enum = SequencerMode.PERFORM
SEQUENCER_STEPS: int = 16
server: Server
stop_listening_for_input: threading.Event = threading.Event()


########################################
####### General Python functions #######
########################################

def consume_keyboard_input():
    """The thread that receives user keyboard input.
    
    Four options are presented to the user on the command line:
    1) `Perform` - simply handles incoming MIDI messages
    2) `Playback` - plays a recorded sequence of MIDI messages
    3) `Record` - records incoming MIDI messages
    4) `Exit` - exit the program entirely.
    
    The whole word must be entered when choosing a mode, but case
    doesn't matter.

    If setting the sequencer to Perform mode, two options are
    available:
    1) `Stop` - stop playing the recorded sequence, and change to Perform mode.
    2) `Exit` - exit the program entirely

    If setting the sequencer to Record mode, three options are
    available:
    1) `Stop` - stop recording a sequence, and change to Perform mode.
    2) `Clear` - delete all recorded sequences
    3) `Exit` - exit the program entirely
    """
    global recorded_notes
    global sequencer_mode
    global stop_listening_for_input

    input_prompt = 'Enter a command:\n'

    while not stop_listening_for_input.is_set():
        input_options = 'Options are:\n*Perform\n*Playback\n*Record\n*Exit\n'

        if sequencer_mode == SequencerMode.PLAYBACK:
            input_options = 'Options are:\n*Stop\n*Exit\n'

        if sequencer_mode == SequencerMode.RECORD:
            input_options = 'Options are:\n*Stop\n*Clear\n*Exit\n'

        command = input(f'{input_prompt}(Current mode is {SequencerMode(sequencer_mode).name})\n{input_options}> ')
        command = command.upper()
        
        if command == "STOP":
            if sequencer_mode == SequencerMode.PLAYBACK:
                stop_playback()
            
            # Set mode to PERFORM when stopping either PLAYBACK or RECORD.
            sequencer_mode = SequencerMode.PERFORM
        
        if command == "CLEAR":
            # Delete all recorded notes.
            recorded_notes = defaultdict(list)

        if command == "EXIT":
            # Quit the program.
            stop()
        
        if command not in SequencerMode.__members__:
                print('Incorrect command.  Please try again.')
        else:
            if sequencer_mode == SequencerMode[command]:
                # No need to reassign.
                continue
            
            if sequencer_mode == SequencerMode.PLAYBACK and SequencerMode[command] != SequencerMode.PLAYBACK:
                stop_playback()

            sequencer_mode = SequencerMode[command]

        if sequencer_mode == SequencerMode.PLAYBACK:
            start_playback()

def listen_for_keyboard_input():
    """Starts the thread that listens for keyboard input."""
    consumer_thread = threading.Thread(target=consume_keyboard_input, daemon=True)
    consumer_thread.start()

@click.command()
@click.option('-b', '--bpm', default=120, type=int, help='Beats per minute.')
@click.option('-q', '--quantization', default='1/16', type=str, help='The rhythmic value for sequenced notes.')
def start(bpm: int, quantization: str) -> None:
    verify_bpm(bpm=bpm)
    verify_quantization(quantization=quantization)

    listen_for_keyboard_input()

    initialize_supriya(bpm=bpm, quantization=quantization)
    open_multi_inport()
    listen_for_midi_messages()

def stop() -> None:
    """Stop the program."""
    global multi_inport
    global server
    global stop_listening_for_input

    print('Exiting MIDI Drum Sequencer')
    multi_inport.close()
    stop_listening_for_input.set()
    server.quit()
    # Calling this makes sure the SuperCollider server shuts down
    # and doesn't linger after the program exits.
    sys.exit(0)

def verify_bpm(bpm: int) -> None:
    """Make sure the BPM is in a reasonable range.

    Args:
        bpm: the beats per minute.
    """
    if bpm < 60 or bpm > 220:
        print(f'Invalid bpm {bpm}.')
        print('Please enter a BPM in the range 60-220.')
        sys.exit(1)

def verify_quantization(quantization: str) -> None:
    """Make sure the quantization is one that matches what's available.

    Args:
        quantization: a string in the form 1/4, 1/8T, etc.
    """
    if quantization not in get_args(Quantization):
        print(f'Invalid quantization {quantization}.')
        print('Please provide one of the following: ')
        for q in get_args(Quantization):
            print(q)
        sys.exit(1)

########################################
### Supriya/Mido specific functions  ###
########################################

def open_multi_inport() -> None:
    """Create a MultiPort that accepts all incoming MIDI messages.

    This is the easiest way to handle the fact that people using
    this script could have an input port named anything.
    """
    global multi_inport
    
    inports = [open_input(p) for p in get_input_names()]
    multi_inport = MultiPort(inports)

def handle_midi_message(message: Message) -> None:
    """Deal with a new MIDI message.

    This function currently only handles Note On messages.

    Args:
        message: a MIDI message.
    """
    if message.type == 'note_on':
        on_note_on(message=message)

def initialize_supriya(bpm: int, quantization: str) -> None:
    """Initialize the relevant Supriya objects."""
    global clock
    global quantization_delta
    global server
    
    server = Server().boot()
    _ = server.add_synthdefs(
        bass_drum,
        clap_dry,
        claves,
        closed_high_hat,
        cow_bell,
        cymbal,
        high_conga,
        high_tom,
        low_conga,
        low_tom,
        maracas,
        medium_conga,
        medium_tom,
        open_high_hat,
        rim_shot,
        snare,
    )
    # Wait for the server to fully load the SynthDef before proceeding.
    server.sync()

    clock = Clock()
    # Set the BPM of the clock
    clock.change(beats_per_minute=bpm)
    # This helper function converts a string like '1/16' into a numeric value
    # used by the clock.
    quantization_delta = clock.quantization_to_beats(quantization=quantization)
    clock.start()

def listen_for_midi_messages() -> None:
    """Listen for incoming MIDI messages in a non-blocking way.
    
    Mido's iter_pending() is non-blocking.
    """
    global multi_inport

    while not stop_listening_for_input.is_set():
        for message in multi_inport.iter_pending():
            handle_midi_message(message=message)

def on_note_on(message: Message) -> None:
    """Handle MIDI Note On messages.

    The MIDI channel need to be different for each drum.
    It also need to be in the range 0-15, as the channel
    is used as an index into an array of SynthDefs.

    There is no restriction on the MIDI note value,
    other than it be in the usual 0-127 MIDI note range.
    Whatever the value, it will be converted into 
    the range 0-15.  This is done so that each MIDI
    note value corresponds to a 1/6th note.

    Args:
        message: a MIDI Note On message.
    """
    global midi_channel_to_synthdef
    global quantization_delta
    global recorded_notes
    global sequencer_mode
    global SEQUENCER_STEPS
    
    # Use the MIDI channel as the index into an array of SynthDefs
    # to choose the right one.
    drum_synthdef = midi_channel_to_synthdef[message.channel]
    _ = server.add_synth(synthdef=drum_synthdef)

    if sequencer_mode == SequencerMode.RECORD:
        # recorded_time is in a factor of quantization_delta, and is based
        # on the scaled value of the message's note.
        # This makes playback very simple because for each invocation of 
        # the clock's callback, we can simply check for messages at the delta.
        recorded_time = (message.note % SEQUENCER_STEPS) * quantization_delta
        recorded_message = message.copy(time=recorded_time)
        recorded_notes[recorded_time].append(recorded_message)

def sequencer_clock_callback(context = ClockContext, delta=0.0625, time_unit=TimeUnit.BEATS) -> tuple[float, TimeUnit]:
    """The function that runs on each invocation.

    The callback is executed once every `delta`.  What delta means depends on time_unit.  
    Options for time_unit are BEATS or SECONDS.  If you want this function to called
    once every 1/4, 1/8, or 1/16 note, then time_unit should be BEATS.  Otherwise
    you can specify SECONDS as the time_unit to have it called outside of a 
    musical rhythmic context.
    """
    global quantization_delta
    global recorded_notes
    global SEQUENCER_STEPS

    recorded_notes_index = delta * (context.event.invocations % SEQUENCER_STEPS )

    midi_messages = recorded_notes[recorded_notes_index]
    for message in midi_messages:
        handle_midi_message(message)
    
    delta = quantization_delta 
    return delta, time_unit

def start_playback() -> None:
    """Start playing back the sequenced drum pattern."""
    global clock
    global clock_event_id
    
    clock_event_id = clock.cue(procedure=sequencer_clock_callback, quantization='1/4')

def stop_playback() -> None:
    """Stop playing back the sequenced drum pattern."""
    global clock

    clock.cancel(clock_event_id)


if __name__ == '__main__':
    start()