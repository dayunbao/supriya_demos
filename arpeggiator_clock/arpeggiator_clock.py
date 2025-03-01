"""Play an arpeggio using Supriya's Clock class.

A version of arpeggio.py that uses Supriya's Clock class
instead of patterns.  Using Clock requires more code, but
gives a lot more fine level control over behavior, and
is more intuitive, as you can set BPM and quantization.

Typical usage example:

  python arpeggiator_clock.py -b 120 -q 1/16 -c C#m3 -d up -r 4

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

import fractions
import re
import sys
from concurrent.futures import Future
from typing import get_args

import click

from supriya import Envelope, Server, synthdef
from supriya.clocks import Clock, ClockContext, Quantization, TimeUnit
from supriya.conversions import midi_note_number_to_frequency
from supriya.ugens import EnvGen, Limiter, LFSaw, Out


########################################
####### General Python functions #######
########################################

def create_notes(chord_data: list, direction: str) -> list[float]:
    """Convert the chord and arpeggiator direction to a list of MIDI notes.

    Args:
        chord_data: a list of strings specifying the chord, 
        accidental, key, and octave.  Note that the accidental
        might be None if the note is neither sharp nor flat.

        direction: a string indicating whether notes are played
        in ascending order, descending order, or both.
    
    Returns:
        A list of floats that represent the frequencies of the notes to play in hertz.
    """
    # A dictionary containing scale degrees for major and minor keys.
    # The list of ints represents how many half steps are required
    # to reach the note in the scale, where 0 represents the
    # starting note.
    major_minor_scale_degrees = {
        'major': [0, 2, 4, 5, 7, 9, 11],
        'minor': [0, 2, 3, 5, 7, 8, 10],
    }

    chord, accidental, key, octave = chord_data

    scale_degrees = major_minor_scale_degrees[key]
    # Since this is an arpeggiator, we're not playing the whole scale.
    # So get the relevant scale degrees.
    scale_degrees_indices = get_scale_degrees_indices(direction=direction)
    degrees_to_play = [scale_degrees[x] for x in scale_degrees_indices]

    # Need to add one to octave since in MIDI octave 0 would be octave -1 in music.
    octave = int(octave) + 1
    note_offset = get_note_offset(root=chord, accidental=accidental)
    # Figure out the value of the base MIDI note, since once we have 
    # that we can simply add the scale degree to it to find the next MIDI Note.
    base_midi_note = note_offset + (12 * int(octave))

    midi_notes = []
    for degree in degrees_to_play:
        note = base_midi_note + degree 
        midi_notes.append(note)

    # SynthDefs take frequencies in hertz, not MIDI notes.
    # So we need to convert them.
    return [midi_note_number_to_frequency(x) for x in midi_notes]

def get_note_offset(root: str, accidental: str | None) -> int:
    """Get a offset from 0 (C natural).

    In order to convert something like Eb5 to a MIDI note, one thing that must 
    be known is where a note falls in the range 0-11.  This value can then be used
    with the octave and scale degree to find the corresponding MIDI note.

    Args:
        root: the first note (root) of a chord
        accidental: a string or None, indicates if the note is sharp (#),
        flat (b), or natural (None)
    
        Returns:
            int: the offset added to the scale degree octave to find the MIDI note.
    """
    notes = [
        'C', 
        ('C#', 'Db'), 
        'D', 
        ('D#', 'Eb'), 
        'E', 
        'F', 
        ('F#', 'Gb'), 
        'G', 
        ('G#', 'Ab'), 
        'A', 
        ('A#', 'Bb'), 
        'B'
    ]

    note_index = 0
    for index, note in enumerate(notes):
        if accidental is not None:
            if type(note) is tuple:
                note_accidental = root + accidental
                if note_accidental in note:
                    note_index = index
        else:
            if root ==  note:
                note_index = index

    return note_index

def get_scale_degrees_indices(direction: str) -> list[int]:
    """Get a list of indices based on direction.

    Args:
        direction: a string indicating whether notes are played
        in ascending order, descending order, or both.
    
    Returns:
        a list of ints that will be used to index an array
    """
    if direction == 'up':
        return [0, 2, 4, 6]
    elif direction == 'down':
        return [6, 4, 2, 0]
    else:
        return [0, 2, 4, 6, 4, 2]

def parse_chord(chord: str) -> list[str | None]:
    """Split the chord user input into relevant parts

    Args:
        chord: a string in the form C#m4
    
    Returns:
        The input split into a list, with None used in place
        of an accidental when one was not provided.
    """
    split_chord: list[str | None] = list(chord)
    if len(split_chord) < 4:
        split_chord.insert(1, None)

    split_chord[2] = 'major' if split_chord[2] == 'M' else 'minor'

    return split_chord

def verify_arp_direction(direction: str) -> None:
    """Verify the direction input.

    Args:
        direction: a string indicating whether notes are played
        in ascending order, descending order, or both.
    """
    direction_regex = re.compile(r"^(up|down|up-and-down)$")
    if not direction_regex.fullmatch(direction):
        print('Incorrect direction provided.')
        print("Please provide one of 'up', 'down', or 'up-and-down'.")
        sys.exit(1)

def verify_chord(chord: str) -> None:
    """Verify the chord input.

    Args:
        chord: a string that indicates the chord, an (optional) accidental,
        the key, and the octave.
        So BbM8 would be the B-flat major chord at octave 8.
    """
    chord_regex = re.compile(r"^[A-G](#|b)?[Mm][0-8]$")
    if not chord_regex.fullmatch(chord):
        print(f'Incorrect chord provided {chord}.')
        print("Please provide the chord in the following format: ")
        print("A-G, optional # or b, M or m, 0-8.  Example: BbM5")
        sys.exit(1)

@click.command()
@click.option('-b', '--bpm', default=120, type=int)
@click.option('-q', '--quantization', default='1/16', type=str)
@click.option('-c', '--chord', default='CM4', type=str)
@click.option('-d', '--direction', default='up', type=str)
@click.option('-r', '--repetitions', default=0, type=int)
def start(bpm: int, quantization: str, chord: str, direction: str, repetitions: int) -> None:
    """Reads user input, verifies it, and starts the arpeggiator.

    Args:
        bpm: beats per minute
        quantization: a string indication what rhythmic value each note in the arpeggio should have
        chord: a string in the form C#m4 that decides what the played notes will be
        direction: a string indicating whether notes are played in ascending order, descending order, or both.
        repetitions: how many times the arpeggio should play. 0 means to play infinitely.
    """
    arp_direction = direction.lower()
    
    verify_arp_direction(direction=arp_direction)
    verify_chord(chord=chord)
    verify_bpm(bpm=bpm)
    verify_quantization(quantization=quantization)
    
    iterations = repetitions
    chord_data = parse_chord(chord=chord)
    notes = create_notes(chord_data=chord_data, direction=arp_direction)
    server = initialize_server()
    clock = initialize_clock(bpm=bpm)
    quantization_delta = quantization_to_beats(quantization=quantization)
    future: Future = Future()
    clock_event_id = start_arpeggiator(
        clock=clock, 
        future=future,
        iterations=iterations, 
        notes=notes,
        quantization_delta=quantization_delta,
        server=server,
    )

    future.result()
    stop_arpeggiator(clock=clock, clock_event_id=clock_event_id, server=server)

########################################
###### Supriya specific functions ######
########################################

def arpeggiator_clock_callback(
        context:ClockContext, 
        delta: float, 
        future: Future,
        iterations: int,
        notes: list[float],
        server: Server,
) -> tuple[float, TimeUnit] | None:
    """The function that runs on each invocation.

    The callback is executed once every `delta`.  What delta means depends on time_unit.  
    Options for time_unit are BEATS or SECONDS.  If you want this function to called
    once every 1/4, 1/8, or 1/16 note, then time_unit should be BEATS.  Otherwise
    you can specify SECONDS as the time_unit to have it called outside of a 
    musical rhythmic context.
    """
    if iterations != 0 and context.event.invocations == (iterations * len(notes)):
        future.set_result(True)
        return None

    notes_index = context.event.invocations % len(notes)
    _ = server.add_synth(synthdef=saw, frequency=notes[notes_index])
    
    return delta, TimeUnit.BEATS

def initialize_server() -> Server:
    """Initialize the server and load the SynthDef."""
    server = Server().boot()
    _ = server.add_synthdefs(saw)
    # Wait for the server to fully load the SynthDef before proceeding.
    server.sync()

    return server

def initialize_clock(bpm: int) -> Clock:
    """Set up the clock."""
    clock = Clock()
    # Set the BPM of the clock
    clock.change(beats_per_minute=bpm)
    clock.start()

    return clock

def quantization_to_beats(quantization: str) -> float:
    fraction = fractions.Fraction(quantization.replace("T", ""))
    if "T" in quantization:
        fraction *= fractions.Fraction(2, 3)
    
    return float(fraction)

@synthdef()
def saw(frequency=440.0, amplitude=0.5) -> None:
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
    """
    signal = LFSaw.ar(frequency=[frequency, frequency - 2])
    signal *= amplitude
    signal = Limiter.ar(duration=0.01, level=0.1, source=signal)
    
    # Using a percussive envelope and setting the done_action to 2
    # means that SuperCollider will handle deallocating everything
    # for us.  No gate is needed.
    env = EnvGen.kr(envelope=Envelope.percussive(), done_action=2)
    signal *= env

    Out.ar(bus=0, source=signal)

def start_arpeggiator(
        clock: Clock, 
        iterations: int, 
        future: Future,
        notes: list[float], 
        quantization_delta: float, 
        server: Server
) -> int:
    """Start the arpeggiator by cueing the callback on the clock."""
    return clock.cue(
        procedure=arpeggiator_clock_callback, 
        quantization='1/4', # Set the arpeggiator to begin playing on the next quarter note.
        kwargs={
            'delta': quantization_delta, 
            'future': future,
            'iterations': iterations,
            'notes': notes,
            'server': server,
        }
    )

def stop_arpeggiator(clock: Clock, clock_event_id: int, server: Server) -> None:
    """Stop the clock and exit the program."""    
    clock.cancel(event_id=clock_event_id)
    clock.stop()
    server.quit()
    exit(0)

def verify_bpm(bpm: int) -> None:
    """Make sure the BPM is in a reasonable range.

    Args:
        bpm: the beats per minute
    """
    if bpm < 60 or bpm > 220:
        print(f'Invalid bpm {bpm}')
        print('Please enter a BPM in the range 60-220')
        sys.exit(1)

def verify_quantization(quantization: str) -> None:
    """Make sure the quantization is one that matches what's available.

    Args:
        quantization: a string in the form 1/4, 1/8T, etc.
    """
    if quantization not in get_args(Quantization):
        print(f'Invalid quantization {quantization}')
        print('Please provide one of the following: ')
        for q in get_args(Quantization):
            print(q)
        sys.exit(1)

if __name__ == '__main__':
    start()
