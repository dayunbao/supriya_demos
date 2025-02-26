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
from typing import get_args

import click

from supriya.clocks.bases import Quantization

from drum_machine import DrumMachine

@click.command()
@click.option('-b', '--bpm', default=120, type=int, help='Beats per minute.')
@click.option('-q', '--quantization', default='1/16', type=str, help='The rhythmic value for sequenced notes.')
def start(bpm: int, quantization: str) -> None:
    verify_bpm(bpm=bpm)
    verify_quantization(quantization=quantization)

    drum_machine = DrumMachine(bpm=bpm, quantization=quantization)
    drum_machine.run()
    stop()

def stop() -> None:
    """Stop the program."""
    print('Exiting MIDI Drum Sequencer')
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

if __name__ == '__main__':
    start()