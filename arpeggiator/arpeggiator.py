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

import re
import sys
from typing import Union

import click

from supriya import Envelope, Server, synthdef
from supriya.clocks import Clock
from supriya.conversions import midi_note_number_to_frequency
from supriya.patterns import EventPattern, PatternPlayer, SequencePattern
from supriya.ugens import EnvGen, Limiter, LFSaw, Out


########################################
####### General Python functions #######
########################################

def get_note_offset(root: str, accidental: Union[str, None]) -> int:
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
        "C",
        ("C#", "Db"),
        "D",
        ("D#", "Eb"),
        "E",
        "F",
        ("F#", "Gb"),
        "G",
        ("G#", "Ab"),
        "A",
        ("A#", "Bb"),
        "B",
    ]

    note_index = 0
    for index, note in enumerate(notes):
        if accidental is not None:
            if type(note) is tuple:
                note_accidental = root + accidental
                if note_accidental in note:
                    note_index = index
        else:
            if root == note:
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
    if direction == "up":
        return [0, 2, 4, 6]
    elif direction == "down":
        return [6, 4, 2, 0]
    else:
        return [0, 2, 4, 6, 4, 2]

def parse_chord(chord: str) -> list:
    """Split the chord user input into relevant parts

    Args:
        chord: a string in the form C#m4

    Returns:
        The input split into a list, with None used in place
        of an accidental when one was not provided.
    """
    split_chord: list[Union[str, None]] = list(chord)
    if len(split_chord) < 4:
        split_chord.insert(1, None)

    split_chord[2] = "major" if split_chord[2] == "M" else "minor"

    return split_chord

def verify_arp_direction(direction: str) -> None:
    """Verify the direction input.

    Args:
        direction: a string indicating whether notes are played
        in ascending order, descending order, or both.
    """
    direction_regex = re.compile(r"^(up|down|up-and-down)$")
    if not direction_regex.fullmatch(direction):
        print("Incorrect direction provided.")
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
        print(f"Incorrect chord provided {chord}.")
        print("Please provide the chord in the folowing format: ")
        print("A-G, optional # or b, M or m, 0-8.  Example: BbM5")
        sys.exit(1)

@click.command()
@click.option("-c", "--chord", default="CM4", type=str)
@click.option("-d", "--direction", default="up", type=str)
def start(chord: str, direction: str) -> None:
    arp_direction = direction.lower()
    verify_arp_direction(direction=arp_direction)
    verify_chord(chord=chord)
    chord_data = parse_chord(chord=chord)
    arpeggiator_sequence = create_sequence(chord_data=chord_data, direction=arp_direction)
    arpeggiator_pattern = create_arpeggiator(arpeggiator_sequence=arpeggiator_sequence)
    server = initialize()
    clock = Clock()
    play_arpeggiator(arpeggiator_pattern=arpeggiator_pattern, clock=clock, server=server)

    while True:
        continue


########################################
###### Supriya specific functions ######
########################################

def create_sequence(chord_data: list, direction: str) -> SequencePattern:
    """Create the SequencePattern.

    Args:
        chord_data: a list of strings specifying the chord,
        accidental, key, and octave.  Note that the accidental
        might be None if the note is neither sharp nor flat.

        direction: a string indicating whether notes are played
        in ascending order, descending order, or both.
    """
    # A dictionary containing scale degrees for major and minor keys.
    # The list of ints represents how many half steps are required
    # to reach the note in the scale, where 0 represents the
    # starting note.
    major_minor_scale_degrees = {
        "major": [0, 2, 4, 5, 7, 9, 11],
        "minor": [0, 2, 3, 5, 7, 8, 10],
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
    frequencies = [midi_note_number_to_frequency(x) for x in midi_notes]
    # Finally create the SequencePlayer
    return SequencePattern(frequencies, iterations=None)

def create_arpeggiator(arpeggiator_sequence: SequencePattern) -> EventPattern:
    """Create an EventPattern.
    
    Args:
        arpeggiator_sequence: the sequence of notes to play.
    
    Returns:
        arpeggiator_pattern: the SequencePattern object that will
        be used to startplaying the arpeggio.
    """
    arpeggiator_pattern = EventPattern(
        frequency=arpeggiator_sequence,
        synthdef=saw,
        delta=0.125,
        duration=0.0625,
    )

    return arpeggiator_pattern

def initialize() -> Server:
    """Boot the server, and load the SynthDef."""
    server = Server().boot()
    _ = server.add_synthdefs(saw)
    # Wait for the server to fully load the SynthDef before proceeding.
    server.sync()

    return server

def play_arpeggiator(arpeggiator_pattern: EventPattern, clock: Clock, server: Server) -> PatternPlayer:
    """Create a PatternPlayer, and play it."""
    return arpeggiator_pattern.play(clock=clock, context=server)

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

def stop_arpeggiator(arpeggiator: PatternPlayer) -> None:
    """Stop the PatternPlayer.

    This isn't being called, since I'm just killing the program
    with Ctrl-C. However, if you want to handle exiting the
    program more gracefully, you could use this function as
    part of that.
    
    Args:
        arpeggiator: a PatternPlayer object that can be used
        to stop playing the arpeggio.
    """
    arpeggiator.stop()

if __name__ == "__main__":
    start()
