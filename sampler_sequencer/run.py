from sys import exit
from typing import get_args

import click

from consolemenu import ConsoleMenu
from consolemenu.items import FunctionItem, SubmenuItem, ExitItem

from supriya import Server
from supriya.clocks.bases import Quantization

from .sampler import Sampler
from .sequencer import Sequencer

from .synth_defs import sample_player

menu: ConsoleMenu
sequencer: Sequencer
server: Server

def initialize_sequencer(bpm: int, quantization: str) -> None:
    global sequencer
    global server
    
    print(f'quantization={quantization}')

    sampler = Sampler(server=server, synth_definition=sample_player)
    sequencer = Sequencer(
        bpm=bpm, 
        instruments=[sampler],
        quantization=quantization,
    )

def create_menu() -> None:
    global menu
    global sequencer

    main_menu = ConsoleMenu(
        title='Sampler Sequencer', 
        subtitle='Choose an option',
        show_exit_option=False,
    )

    ####################
    # Shared
    ####################
    back_menu_item = ExitItem(text='Back to main menu')
    
    ####################
    # Playback Sub-menu
    ####################
    playback_submenu = ConsoleMenu(title='Playback', show_exit_option=False)
    playback_start_menu_item = FunctionItem(
        text='Start', 
        function=sequencer.start_playback, 
        menu=playback_submenu,
    )
    playback_stop_menu_item = FunctionItem(
        text='Stop', 
        function=sequencer.stop_playback,
        menu=playback_submenu
    )

    playback_submenu.append_item(playback_start_menu_item)
    playback_submenu.append_item(playback_stop_menu_item)
    playback_submenu.append_item(back_menu_item)
    # Add this to main_menu
    playback_menu_item = SubmenuItem(text='Playback', submenu=playback_submenu, menu=main_menu)

    ####################
    # Record Sub-menu
    ####################
    record_submenu = ConsoleMenu(title='Record', show_exit_option=False)
    record_start_menu_item = FunctionItem(
        text='Start', 
        function=sequencer.start_recording,
        menu=playback_submenu,
    )
    record_stop_menu_item = FunctionItem(
        text='Stop', 
        function=sequencer.stop_recording,
        menu=playback_submenu,
    )

    record_submenu.append_item(record_start_menu_item)
    record_submenu.append_item(record_stop_menu_item)
    record_submenu.append_item(back_menu_item)
    # Add this to main_menu
    record_menu_item = SubmenuItem(text='Record', submenu=record_submenu, menu=main_menu)

    ####################
    # Sequencer Sub-menu
    ####################
    sequencer_submenu = ConsoleMenu(title='Sequencer settings', show_exit_option=False)

    sequencer_submenu.append_item(back_menu_item)
    # Add this to main_menu
    sequencer_menu_item = SubmenuItem(text='Sequencer', submenu=sequencer_submenu, menu=main_menu)

    ####################
    # Tracks Sub-menu
    ####################
    tracks_submenu = ConsoleMenu(title='Tracks', show_exit_option=False)

    tracks_submenu.append_item(back_menu_item)
    # Add this to main_menu
    tracks_menu_item = SubmenuItem(text='Tracks', submenu=tracks_submenu, menu=main_menu)

    ####################
    # Main Menu
    ####################
    exit_menu_item = ExitItem(text='Exit', menu=main_menu)
    
    main_menu.append_item(playback_menu_item)
    main_menu.append_item(record_menu_item)
    main_menu.append_item(sequencer_menu_item)
    main_menu.append_item(tracks_menu_item)
    main_menu.append_item(exit_menu_item)
    
    menu = main_menu

def start_menu() -> None:
    global menu
    
    menu.show()

def exit_program() -> None:
    """Exit the program."""
    global sequencer
    global server

    print('Exiting Sampler Sequencer')
    sequencer.exit()
    server.quit()
    # Calling this makes sure the SuperCollider server shuts down
    # and doesn't linger after the program exits.
    exit(0)
    
def initialize_server() -> None:
    global server

    server = Server().boot()

@click.command()
@click.option('-b', '--bpm', default=120, type=int, help='Beats per minute.')
@click.option('-q', '--quantization', default='1/16', type=str, help='The rhythmic value for sequenced notes.')
def start(bpm: int, quantization: str) -> None:
    verify_bpm(bpm=bpm)
    verify_quantization(quantization=quantization)

    initialize_server()
    initialize_sequencer(bpm=bpm, quantization=quantization)
    create_menu()
    start_menu()
    exit_program()

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