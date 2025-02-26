from sys import exit
from typing import get_args

from consolemenu import ConsoleMenu, MenuFormatBuilder
from consolemenu.items import FunctionItem, SubmenuItem, ExitItem
from consolemenu.prompt_utils import PromptUtils, UserQuit
from consolemenu.validators.base import BaseValidator

from supriya import Server
from supriya.clocks.bases import Quantization

from .sampler import Sampler
from .sequencer import Sequencer
from .sp_303 import SP303

from .synth_defs import sample_player #  , sp_303


class BPMValidator(BaseValidator):
    def validate(self, input_string):
        result = True
        if int(input_string) < 60 or int(input_string) > 220:
            result = False

        return result

class QuantizationValidator(BaseValidator):
    def validate(self, input_string):
        """Make sure the quantization is one that matches what's available.

        Args:
            quantization: a string in the form 1/4, 1/8T, etc.
        """
        result = True
        if input_string not in get_args(Quantization):
            result = False

        return result

class InstrumentNameValidator(BaseValidator):
    def __init__(self, instruments: list[str]):
        super().__init__()
        self.instruments = instruments
    
    def validate(self, input_string):
        result = True
        if input_string not in self.instruments:
            result = False

        return result

class TrackNumberValidator(BaseValidator):
    def __init__(self, number_of_tracks: int):
        super().__init__()
        self.number_of_tracks = number_of_tracks
    
    def validate(self, input_string):
        result = True
        if int(input_string) > self.number_of_tracks:
            result = False

        return result

menu: ConsoleMenu
sequencer: Sequencer
server: Server

def initialize_sequencer(bpm: int, quantization: str) -> None:
    global sequencer
    global server

    sampler = Sampler(
        midi_channels=[x for x in range(16)],
        server=server, 
        synth_definition=sample_player
    )

    # supriya_303 = SP303(
    #     midi_channels=[x for x in range(16)],
    #     server=server, 
    #     synth_definition=sp_303
    # )

    sequencer = Sequencer(
        bpm=bpm, 
        instruments={sampler.name: sampler}, #  , supriya_303.name: supriya_303},
        quantization=quantization,
    )

def create_menu() -> None:
    global menu
    global sequencer

    main_menu = ConsoleMenu(
        title='Sampler Sequencer', 
        subtitle='Choose an option',
        prologue_text='',
        formatter=MenuFormatBuilder()
        .set_title_align('center')
        .set_subtitle_align('center')
        .show_prologue_top_border(True),
        show_exit_option=False,
        clear_screen=False
    )

    ####################
    # Shared
    ####################
    back_to_main_menu_item = ExitItem(text='Back to main menu', menu=main_menu)
    
    ####################
    # Playback Menu
    ####################
    playback_menu = ConsoleMenu(
        title='Playback', 
        prologue_text='',
        formatter=MenuFormatBuilder()
        .set_title_align('center')
        .set_subtitle_align('center')
        .show_prologue_top_border(True),
        show_exit_option=False,
        clear_screen=False,
    )
    playback_start_menu_item = FunctionItem(
        text='Start', 
        function=sequencer.start_playback, 
        menu=playback_menu,
    )
    playback_stop_menu_item = FunctionItem(
        text='Stop', 
        function=sequencer.stop_playback,
        menu=playback_menu
    )

    playback_menu.append_item(playback_start_menu_item)
    playback_menu.append_item(playback_stop_menu_item)
    playback_menu.append_item(back_to_main_menu_item)
    # Add this to main_menu
    playback_menu_item = SubmenuItem(text='Playback', submenu=playback_menu, menu=main_menu)

    ####################
    # Record Menu
    ####################
    record_menu = ConsoleMenu(
        title='Record', 
        prologue_text=create_record_menu_prologue,
        formatter=MenuFormatBuilder()
        .set_title_align('center')
        .set_subtitle_align('center')
        .set_prologue_text_align('center')
        .show_prologue_bottom_border(True),
        show_exit_option=False,
        clear_screen=False,
    )

    record_change_instrument_menu_item = FunctionItem(
        text='Change instrument',
        function=change_instrument,
        menu=record_menu,
    )

    record_change_track_menu_item = FunctionItem(
        text='Change track',
        function=change_track,
        menu=record_menu,
    )

    record_change_both_menu_item = FunctionItem(
        text='Change instrument and track',
        function=change_both,
        menu=record_menu,
    )

    record_start_menu_item = FunctionItem(
        text='Start', 
        function=sequencer.start_recording,
        menu=record_menu,
    )
    record_stop_menu_item = FunctionItem(
        text='Stop', 
        function=sequencer.stop_recording,
        menu=record_menu,
    )

    record_menu.append_item(record_change_instrument_menu_item)
    record_menu.append_item(record_change_track_menu_item)
    record_menu.append_item(record_change_both_menu_item)
    record_menu.append_item(record_start_menu_item)
    record_menu.append_item(record_stop_menu_item)
    record_menu.append_item(back_to_main_menu_item)
    # Add this to main_menu
    record_menu_item = SubmenuItem(text='Record', submenu=record_menu, menu=main_menu)

    ####################
    # Sequencer Menu
    ####################
    sequencer_menu = ConsoleMenu(
        title='Sequencer Settings', 
        prologue_text=get_current_sequencer_settings,
        show_exit_option=False,
        clear_screen=True,
        formatter=MenuFormatBuilder()
        .set_title_align('center')
        .set_subtitle_align('center')
        .set_prologue_text_align('center')
        .show_prologue_bottom_border(True),
    )
    sequencer_change_bpm_menu_item = FunctionItem(
        text='Change BPM',
        function=get_bpm_input,
    )
    sequencer_change_quantization_menu_item = FunctionItem(
        text='Change quantization',
        function=get_quantization_input,
    )

    sequencer_menu.append_item(sequencer_change_bpm_menu_item)
    sequencer_menu.append_item(sequencer_change_quantization_menu_item)
    sequencer_menu.append_item(back_to_main_menu_item)
    # Add this to main_menu
    sequencer_menu_item = SubmenuItem(text='Sequencer', submenu=sequencer_menu, menu=main_menu)

    ####################
    # Tracks Menu
    ####################
    tracks_menu = ConsoleMenu(
        title='Tracks',
        prologue_text=get_current_number_of_tracks,
        formatter=MenuFormatBuilder()
        .set_title_align('center')
        .set_subtitle_align('center')
        .set_prologue_text_align('center')
        .show_prologue_bottom_border(True),
        show_exit_option=False,
        clear_screen=True,
    )

    tracks_add_menu_item = FunctionItem(text='Add track', function=add_track)
    track_delete_menu_item = FunctionItem(text='Delete', function=delete_track)

    tracks_menu.append_item(tracks_add_menu_item)
    tracks_menu.append_item(track_delete_menu_item)
    tracks_menu.append_item(back_to_main_menu_item)
    # Add this to main_menu
    tracks_menu_item = SubmenuItem(text='Tracks', submenu=tracks_menu, menu=main_menu)

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

def get_current_sequencer_settings() -> str:
    global sequencer
    
    return f'Current settings:\nBeats per minute(BPM) = {sequencer.bpm} * Quantization = {sequencer.quantization}'

def get_current_number_of_tracks() -> str:
    global sequencer

    
    instruments_num_tracks_str = ''
    for name, tracks in sequencer.tracks.items():
        instruments_num_tracks_str += f'{name}: {len(tracks)}\n'

    prologue_text = f'Current number of tracks\n{instruments_num_tracks_str}'

    return prologue_text

def create_record_menu_prologue() -> str:
    global sequencer

    selected_instrument_name = sequencer.get_selected_instrument_name()
    selected_track_number = f'{sequencer.get_selected_track_number() + 1}'
    record_menu_prologue_text = f'Selected instrument: {selected_instrument_name}\nSelected track number: {selected_track_number}'

    return record_menu_prologue_text

def change_instrument() -> None:
    global InstrumentNameValidator
    global sequencer

    prompt_util = PromptUtils(screen=menu.screen)
    instrument_names = [name for name in sequencer.instruments.keys()]
    instrument_name_validator = InstrumentNameValidator(instruments=instrument_names)

    joined_names = ', '.join(instrument_names)
    prompt = f'Enter one of the following instruments: {joined_names}'

    try:
        name, is_valid = prompt_util.input(
            prompt=prompt,
            enable_quit=True,
            validators=[instrument_name_validator]
        )
        if is_valid:
            sequencer.set_selected_instrument_by_name(name=name) 
        else:    
            prompt_util.println(f'Invalid instrument name provided: {name}')
            return
    except UserQuit:
        return

def change_track() -> None:
    global TrackNumberValidator
    global sequencer

    prompt_util = PromptUtils(screen=menu.screen)
    selected_instrument = sequencer.selected_instrument.name
    num_tracks = len(sequencer.tracks[selected_instrument])
    track_number_validator = TrackNumberValidator(number_of_tracks=num_tracks)

    prompt = 'Enter a number in the range '
    if num_tracks > 1:
        prompt += f'1-{num_tracks}'
    else:
        prompt += f'{num_tracks}'

    try:
        track_number, is_valid = prompt_util.input(
            prompt=prompt,
            enable_quit=True,
            validators=[track_number_validator]
        )
        if is_valid:
            sequencer.set_selected_track_by_track_number(
                instrument_name=selected_instrument,
                track_number=int(track_number) - 1
            )
        else:    
            prompt_util.println(f'Invalid track number provided: {track_number}')
            return
    except UserQuit:
        return

def change_both() -> None:
    change_instrument()
    change_track()

def add_track() -> None:
    global InstrumentNameValidator
    global sequencer

    prompt_util = PromptUtils(screen=menu.screen)
    instrument_names = [name for name in sequencer.instruments.keys()]
    track_add_validator = InstrumentNameValidator(instruments=instrument_names)

    joined_names = ', '.join(instrument_names)
    prompt = f'Enter one of the following instruments: {joined_names}'

    try:
        name, is_valid = prompt_util.input(
            prompt=prompt,
            enable_quit=True,
            validators=[track_add_validator]
        )
        if is_valid:
            sequencer.add_track(instrument_name=name)
        else:    
            prompt_util.println(f'Invalid instrument name provided: {name}')
            return
    except UserQuit:
        return

def delete_track() -> None:
    global TrackNumberValidator
    global sequencer

    prompt_util = PromptUtils(screen=menu.screen)

    instrument_names = [name for name in sequencer.instruments.keys()]
    track_add_validator = InstrumentNameValidator(instruments=instrument_names)

    joined_names = ', '.join(instrument_names)
    prompt = f'Enter one of the following instruments: {joined_names}'

    try:
        name, is_valid = prompt_util.input(
            prompt=prompt,
            enable_quit=True,
            validators=[track_add_validator]
        )
        if is_valid:
            pass
        else:    
            prompt_util.println(f'Invalid instrument name provided: {name}')
            return
    except UserQuit:
        return

    num_tracks = len(sequencer.tracks[name])
    track_delete_validator = TrackNumberValidator(number_of_tracks=num_tracks)

    prompt = 'Enter a number in the range '
    if num_tracks > 1:
        prompt += f'1-{num_tracks}'
    else:
        prompt += f'{num_tracks}'

    try:
        track_number, is_valid = prompt_util.input(
            prompt=prompt,
            enable_quit=True,
            validators=[track_delete_validator]
        )
        if is_valid:
            sequencer.delete_track(instrument_name=name, track_number=int(track_number) - 1)
        else:    
            prompt_util.println(f'Invalid track number provided: {track_number}')
            return
    except UserQuit:
        return

def get_bpm_input() -> None:
    global BPMValidator
    global menu
    global sequencer
    
    prompt_util = PromptUtils(screen=menu.screen)
    bpm_validator = BPMValidator()
    
    try:
        bpm, is_valid = prompt_util.input(
            prompt='Enter a BPM in the range 60-200',
            enable_quit=True,
            validators=[bpm_validator],
        )

        if is_valid:
            sequencer.bpm = int(bpm)
        else:    
            prompt_util.println(f'Invalid BPM provided: {bpm}')
            return
    except UserQuit:
        return

def get_quantization_input() -> None:
    global QuantizationValidator
    global menu

    prompt_util = PromptUtils(screen=menu.screen)
    quantization_validator = QuantizationValidator()
    valid_quantizations = ', '.join([q for q in get_args(Quantization)])
    
    try:
        quantization, is_valid = prompt_util.input(
            prompt=f'Enter one of {valid_quantizations}',
            enable_quit=True,
            validators=[quantization_validator],
        )

        if is_valid:
            sequencer.quantization = quantization
        else:
            prompt_util.println(f'Invalid quantization provided: {quantization}')
            return
    except UserQuit:
        return

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

def start() -> None:
    initialize_server()
    initialize_sequencer(bpm=120, quantization='1/8')
    create_menu()
    start_menu()
    exit_program()

if __name__ == '__main__':
    start()