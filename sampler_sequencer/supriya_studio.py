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
from class_lib import BaseEffect, BaseInstrument, Mixer

from .reverb import Reverb
from .sampler import Sampler
from .sequencer import Sequencer

from supriya import Server

from .synth_defs import reverb, sample_player

class SupriyaStudio:
    def __init__(self) -> None:
        self.bpm = 120
        self.quantization = '1/8'
        self.server = Server().boot()
        self.effects = self._initialize_effects()
        self.instruments  = self._initialize_instruments()
        self.sequencer = self._initialize_sequencer()
        self.mixer = self._initialize_mixer()
    
    def _initialize_effects(self) -> dict[str, BaseEffect]:
        reverb_synth =  Reverb(
            name='reverb',
            server=self.server,
            synth_def=reverb,
        )

        return {reverb_synth.name: reverb_synth}
    
    def _initialize_instruments(self) -> dict[str, BaseInstrument]:
        sampler = Sampler(
            midi_channels=[x for x in range(16)],
            server=self.server, 
            synth_definition=sample_player
        )

        return {sampler.name: sampler}
    
    def _initialize_mixer(self) -> Mixer:
        return Mixer(
            effects=self.effects, 
            instruments=self.instruments,
            server=self.server,
        )

    def _initialize_sequencer(self) -> Sequencer:
        return Sequencer(
            bpm=self.bpm, 
            instruments=self.instruments,
            quantization=self.quantization,
            server=self.server,
        )
    
    def start_playback(self) -> None:
        self.mixer.start_recording()
        self.sequencer.start_playback()

    def stop_playback(self) -> None:
        self.mixer.stop_recording()
        self.sequencer.stop_playback()