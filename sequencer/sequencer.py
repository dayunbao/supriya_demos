"""
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

from collections import defaultdict
from enum import Enum
from sys import exit
from typing import get_args

from mido import Message

from supriya.clocks import Clock, ClockContext
from supriya.clocks.bases import Quantization
from supriya.clocks.ephemera import TimeUnit

from midi_handler import MidiHandler
from synth_hanlder import SynthHandler

class SequencerMode(Enum):
    # Used to track the current state of the sequencer
    PERFORM = 0
    PLAYBACK = 1
    RECORD = 2

clock: Clock
clock_event_id: int
midi_handler: MidiHandler
quantization_delta: float
recorded_notes: dict[float, list[Message]] = defaultdict(list)
sequencer_mode: Enum = SequencerMode.PERFORM
SEQUENCER_STEPS: int = 16
synth_handler: SynthHandler


def initialize_clock(bpm: int, quantization: str) -> None:
    """Initialize the Supriya's Clock."""
    global clock
    global quantization_delta
    
    clock = Clock()
    # Set the BPM of the clock
    clock.change(beats_per_minute=bpm)
    # This helper function converts a string like '1/16' into a numeric value
    # used by the clock.
    quantization_delta = clock.quantization_to_beats(quantization=quantization)
    clock.start()

def initialize_midi_handler() -> None:
    global midi_handler
    global synth_handler

    midi_handler.open_multi_inport()
    midi_handler.set_message_handler_callback(synth_handler.play_synth)

def initialize_synth_handler() -> None:
    global synth_handler

    pass

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
    global synth_handler

    recorded_notes_index = delta * (context.event.invocations % SEQUENCER_STEPS )

    midi_messages = recorded_notes[recorded_notes_index]
    for message in midi_messages:
        synth_handler.play_synth(message=message)

        if sequencer_mode == SequencerMode.RECORD:
            # recorded_time is in a factor of quantization_delta, and is based
            # on the scaled value of the message's note.
            # This makes playback very simple because for each invocation of 
            # the clock's callback, we can simply check for messages at the delta.
            recorded_time = (message.note % SEQUENCER_STEPS) * quantization_delta
            recorded_message = message.copy(time=recorded_time)
            recorded_notes[recorded_time].append(recorded_message)
    
    delta = quantization_delta 
    return delta, time_unit

def set_midi_handler(handler: MidiHandler) -> None:
    global midi_handler

    midi_handler = handler

def set_synth_handler(handler: SynthHandler) -> None:
    global synth_handler

    synth_handler = handler

def start_playback() -> None:
    """Start playing back the sequenced drum pattern."""
    global clock
    global clock_event_id
    
    clock_event_id = clock.cue(procedure=sequencer_clock_callback, quantization='1/4')

def stop_playback() -> None:
    """Stop playing back the sequenced drum pattern."""
    global clock

    clock.cancel(clock_event_id)

def verify_bpm(bpm: int) -> None:
    """Make sure the BPM is in a reasonable range.

    Args:
        bpm: the beats per minute.
    """
    if bpm < 60 or bpm > 220:
        exit(f'Invalid bpm {bpm}.\nPlease enter a BPM in the range 60-220.')

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
        exit(1)