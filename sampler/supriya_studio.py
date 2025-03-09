"""A class that wraps various components .

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
from pathlib import Path

from midi_handler import MIDIHandler
from mixer import Mixer
from sampler import Sampler
from sequencer import Sequencer

from mido import Message

from supriya import Server

from synth_defs import sample_player

class SupriyaStudio:
    def __init__(self) -> None:
        self.bpm = 120
        self.server = Server().boot()
        self.sampler  = self._initialize_sampler()
        self.mixer = self._initialize_mixer()
        self.sequencer = self._initialize_sequencer()
        self.midi_handler = self._initialize_midi_handler()
    
    def exit(self) -> None:
        self.sequencer.exit()
        self.mixer.exit()
        self.midi_handler.exit()
        self.server.quit()

    def handle_midi_message(self, message: Message) -> None:
        if message.type == 'control_change':
            if message.is_cc(self.sampler.SAMPLE_SELECT_CC_NUM):
                self.sampler.on_control_change(message=message)
            
            if message.control in self.mixer.cc_nums:
                self.mixer.handle_control_change_message(message=message)
        
        if message.type == 'program_change':
            self.sampler.on_program_change(message=message)
            return
        
        if message.type == 'note_on':
            self.sequencer.handle_note_on(message=message)

    def _initialize_sampler(self) -> Sampler:
        tb_303_samples_path = Path(__file__).parent / 'samples/roland_tb_303'
        tr_909_samples_path = Path(__file__).parent / 'samples/roland_tr_909'
        sampler = Sampler(
            name='sampler',
            samples_paths=[tb_303_samples_path, tr_909_samples_path],
            server=self.server, 
            synthdef=sample_player,
        )

        return sampler
    
    def _initialize_midi_handler(self) -> MIDIHandler:
        return MIDIHandler(message_handler_callback=self.handle_midi_message)

    def _initialize_mixer(self) -> Mixer:
        return Mixer(
            instrument=self.sampler,
            server=self.server,
        )

    def _initialize_sequencer(self) -> Sequencer:
        return Sequencer(
            bpm=self.bpm, 
            sampler=self.sampler,
            server=self.server,
            start_recording_callback=self.mixer.start_recording,
            stop_recording_callback=self.mixer.stop_recording,
        )
    
    def start_playback(self) -> None:
        self.sequencer.start_playback()

    def stop_playback(self) -> None:
        self.sequencer.stop_playback()