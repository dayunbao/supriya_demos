import threading
from sys import exit
from typing import get_args

import click

from supriya import Server
from supriya.clocks.bases import Quantization

from midi_handler import MIDIHandler
from sampler import Sampler
from sequencer import Sequencer

from synth_defs import sample_player

sequencer: Sequencer
server: Server
stop_listening_for_input: threading.Event = threading.Event()

def initialize_sequencer(bpm: int, quantization: str) -> None:
    global sequencer
    global server

    synth_definitions = {
        "sample_player": sample_player
    }
    
    sampler = Sampler(server=server, synth_definitions=synth_definitions)
    sequencer = Sequencer(
        bpm=bpm, 
        quantization=quantization,
        synth_handler=sampler
    )

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
    global sequencer
    global stop_listening_for_input

    input_prompt = 'Enter a command:\n'

    while not stop_listening_for_input.is_set():
        input_options = 'Options are:\n*Perform\n*Playback\n*Record\n*Exit\n'

        if sequencer.mode == Sequencer.Mode.PLAYBACK:
            input_options = 'Options are:\n*Stop\n*Exit\n'

        if sequencer.mode == Sequencer.Mode.RECORD:
            input_options = 'Options are:\n*Stop\n*Clear\n*Exit\n'

        command = input(f'{input_prompt}(Current mode is {Sequencer.Mode(sequencer.mode).name})\n{input_options}> ')
        command = command.upper()
        
        if command == "STOP":
            if sequencer.mode == Sequencer.Mode.PLAYBACK:
                sequencer.stop_playback()
            
            # Set mode to PERFORM when stopping either PLAYBACK or RECORD.
            sequencer.mode = Sequencer.Mode.PERFORM
        
        if command == "CLEAR":
            # Delete all recorded notes.
            sequencer.erase_recorded_notes()

        if command == "EXIT":
            # Quit the program.
            exit_program()
        
        if command not in Sequencer.Mode.__members__:
                print('Incorrect command.  Please try again.')
        else:
            if sequencer.mode == Sequencer.Mode[command]:
                # No need to reassign.
                continue
            
            if sequencer.mode == Sequencer.Mode.PLAYBACK and Sequencer.Mode[command] != Sequencer.Mode.PLAYBACK:
                sequencer.stop_playback()

            sequencer.mode = Sequencer.Mode[command]

        if sequencer.mode == Sequencer.Mode.PLAYBACK:
            sequencer.start_playback()

def exit_program() -> None:
    """Exit the program."""
    global sequencer
    global server

    print('Exiting Sampler Sequencer')
    sequencer.exit()
    stop_listening_for_input.set()
    server.quit()
    # Calling this makes sure the SuperCollider server shuts down
    # and doesn't linger after the program exits.
    exit(0)

def initialize_server() -> None:
    global server

    server = Server().boot()

def listen_for_keyboard_input():
    """Starts the thread that listens for keyboard input."""
    consumer_thread = threading.Thread(target=consume_keyboard_input, daemon=True)
    consumer_thread.start()
    consumer_thread.join()

@click.command()
@click.option('-b', '--bpm', default=120, type=int, help='Beats per minute.')
@click.option('-q', '--quantization', default='1/16', type=str, help='The rhythmic value for sequenced notes.')
def start(bpm: int, quantization: str) -> None:
    verify_bpm(bpm=bpm)
    verify_quantization(quantization=quantization)

    initialize_server()
    initialize_sequencer(bpm=bpm, quantization=quantization)
    listen_for_keyboard_input()

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

if __name__ == '__main__':
    start()