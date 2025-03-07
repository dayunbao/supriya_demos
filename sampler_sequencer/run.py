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
from sys import exit
from functools import partial

from consolemenu import ConsoleMenu, MenuFormatBuilder
from consolemenu.items import FunctionItem, SubmenuItem, ExitItem
from consolemenu.prompt_utils import PromptUtils, UserQuit
from consolemenu.validators.base import BaseValidator

from supriya import Server

from sequencer import Sequencer
from supriya_studio import SupriyaStudio


class BPMValidator(BaseValidator):
    def validate(self, input_string):
        result = True
        if int(input_string) < 60 or int(input_string) > 220:
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

def add_track(menu: ConsoleMenu, sequencer: Sequencer) -> None:
    prompt_util = PromptUtils(screen=menu.screen)
    sequencer.add_track()
    prompt_util.println(f'Added track number: {sequencer.tracks[-1].track_number + 1}.')

def create_menu(sequencer: Sequencer, supriya_studio: SupriyaStudio) -> ConsoleMenu:
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
        function=supriya_studio.start_playback, 
        menu=playback_menu,
    )
    playback_stop_menu_item = FunctionItem(
        text='Stop', 
        function=supriya_studio.stop_playback,
        menu=playback_menu
    )

    playback_menu.append_item(playback_start_menu_item)
    playback_menu.append_item(playback_stop_menu_item)
    playback_menu.append_item(back_to_main_menu_item)
    # Add this to main_menu
    playback_menu_item = SubmenuItem(text='Playback', submenu=playback_menu, menu=main_menu)

    ####################
    # Sequencing Menu
    ####################
    sequencing_menu = ConsoleMenu(
        title='Sequencing', 
        prologue_text=partial( create_sequencing_menu_prologue, sequencer),
        formatter=MenuFormatBuilder()
        .set_title_align('center')
        .set_subtitle_align('center')
        .set_prologue_text_align('center')
        .show_prologue_bottom_border(True),
        show_exit_option=False,
        clear_screen=False,
    )

    sequencing_change_track_menu_item = FunctionItem(
        text='Change track',
        function=change_track,
        kwargs={'menu': sequencing_menu, 'sequencer': sequencer},
        menu=sequencing_menu,
    )

    sequencing_start_menu_item = FunctionItem(
        text='Start', 
        function=sequencer.start_sequencing,
        menu=sequencing_menu,
    )
    sequencing_stop_menu_item = FunctionItem(
        text='Stop', 
        function=sequencer.stop_sequencing,
        menu=sequencing_menu,
    )

    sequencing_menu.append_item(sequencing_change_track_menu_item)
    sequencing_menu.append_item(sequencing_start_menu_item)
    sequencing_menu.append_item(sequencing_stop_menu_item)
    sequencing_menu.append_item(back_to_main_menu_item)
    # Add this to main_menu
    sequencing_menu_item = SubmenuItem(text='Sequencing', submenu=sequencing_menu, menu=main_menu)

    ####################
    # Sequencer Menu
    ####################
    sequencer_menu = ConsoleMenu(
        title='Sequencer Settings', 
        prologue_text=partial(get_current_sequencer_settings, sequencer),
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
        kwargs={'menu': sequencer_menu, 'sequencer': sequencer}
    )

    sequencer_menu.append_item(sequencer_change_bpm_menu_item)
    sequencer_menu.append_item(back_to_main_menu_item)
    # Add this to main_menu
    sequencer_menu_item = SubmenuItem(text='Sequencer', submenu=sequencer_menu, menu=main_menu)

    ####################
    # Tracks Menu
    ####################
    tracks_menu = ConsoleMenu(
        title='Tracks',
        prologue_text=partial(get_current_number_of_tracks, sequencer),
        formatter=MenuFormatBuilder()
        .set_title_align('center')
        .set_subtitle_align('center')
        .set_prologue_text_align('center')
        .show_prologue_bottom_border(True),
        show_exit_option=False,
        clear_screen=True,
    )

    tracks_add_menu_item = FunctionItem(
        text='Add track', 
        function=add_track,
        kwargs={'menu': tracks_menu, 'sequencer': sequencer},
    )
    track_delete_menu_item = FunctionItem(
        text='Delete', 
        function=delete_track,
        kwargs={'menu': tracks_menu, 'sequencer': sequencer},
    )

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
    main_menu.append_item(sequencing_menu_item)
    main_menu.append_item(sequencer_menu_item)
    main_menu.append_item(tracks_menu_item)
    main_menu.append_item(exit_menu_item)
    
    return main_menu

def create_sequencing_menu_prologue(sequencer: Sequencer) -> str:
    selected_track_number = f'{sequencer.get_selected_track_number() + 1}'
    sequencing_menu_prologue_text = f'Selected track number: {selected_track_number}'

    return sequencing_menu_prologue_text

def change_track(menu: ConsoleMenu, sequencer: Sequencer) -> None:
    prompt_util = PromptUtils(screen=menu.screen)
    num_tracks = len(sequencer.tracks)
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
                track_number=int(track_number) - 1
            )
        else:    
            prompt_util.println(f'Invalid track number provided: {track_number}')
            return
    except UserQuit:
        return

def delete_track(menu: ConsoleMenu, sequencer: Sequencer) -> None:
    prompt_util = PromptUtils(screen=menu.screen)
    num_tracks = len(sequencer.tracks)
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
            sequencer.delete_track(track_number=int(track_number) - 1)
        else:    
            prompt_util.println(f'Invalid track number provided: {track_number}')
            return
    except UserQuit:
        return

def exit_program(supriya_studio: SupriyaStudio, server: Server) -> None:
    """Exit the program."""
    print('Exiting Supriya Studio')
    supriya_studio.exit()
    server.quit()
    # Calling this makes sure the SuperCollider server shuts down
    # and doesn't linger after the program exits.
    exit(0)

def get_bpm_input(menu: ConsoleMenu, sequencer: Sequencer) -> None:
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

def get_current_number_of_tracks(sequencer: Sequencer) -> str:
    prologue_text = f'Current number of tracks\n{len(sequencer.tracks)}'

    return prologue_text

def get_current_sequencer_settings(sequencer: Sequencer) -> str:
    return f'Current settings:\nBeats per minute(BPM) = {sequencer.bpm} * Quantization = {sequencer.QUANTIZATION}'

def start() -> None:
    supriya_studio = SupriyaStudio()

    main_menu = create_menu(sequencer=supriya_studio.sequencer, supriya_studio=supriya_studio)
    main_menu.show()
    exit_program(supriya_studio=supriya_studio, server=supriya_studio.server)

if __name__ == '__main__':
    start()