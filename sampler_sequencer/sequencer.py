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

from mido import Message

from supriya import AddAction, Server
from supriya.clocks import ClockContext, TimeUnit

from class_lib import BaseEffect
from class_lib import MIDIHandler
from class_lib import BaseSequencer
from class_lib import BaseInstrument
from .track import Track

class Sequencer(BaseSequencer):    
    def __init__(
            self, 
            bpm: int, 
            effects: list[BaseEffect],
            instruments: dict[str, BaseInstrument],
            quantization: str,
            server: Server,
    ):
        super().__init__(bpm, quantization)
        self._instruments = instruments
        self.effects = effects
        self._route_effects_signals()
        self._route_instruments_signals()
        self._midi_handler = self._initialize_midi_handler()
        self._is_recording = False
        self.playing_tracks: list[Track] = []
        self.server = server
        
        # Need these here
        self.instruments_group = self.server.add_group()
        self.effects_group = self.instruments_group.add_group(add_action=AddAction.ADD_AFTER)
        self.tracks_group = self.effects_group.add_group(add_action=AddAction.ADD_AFTER)
        
        self._tracks: dict[str, list[Track]] = self._initialize_tracks()
        self._selected_instrument = list(self._instruments.values())[0]
        self._selected_track = self._tracks[self._selected_instrument.name][0]        
        self._add_effects_to_group()
        self._add_instruments_to_group()
        self._create_effects_synths()

    @property
    def instruments(self) -> dict[str, BaseInstrument]:
        return self._instruments
    
    @instruments.setter
    def instruments(self, instruments: dict[str, BaseInstrument]) -> None:
        self._instruments = instruments

    @property
    def is_recording(self) -> bool:
        return self._is_recording
    
    @is_recording.setter
    def is_recording(self, is_recording: bool) -> None:
        self._is_recording = is_recording
        for tracks in self.tracks.values():
            for track in tracks:
                track.is_recording = self._is_recording

    @property
    def midi_handler(self) -> MIDIHandler:
        return self._midi_handler
    
    @midi_handler.setter
    def midi_handler(self, midi_handler: MIDIHandler) -> None:
        self._midi_handler = midi_handler

    @property
    def quantization(self) -> str:
        return self._quantization
    
    @quantization.setter
    def quantization(self, quantization: str) -> None:
        self._quantization = quantization
        self.quantization_delta = self._convert_quantization_to_delta(quantization=self._quantization)
        self._track_length_in_measures = self._compute_track_length_in_measures()

    @property
    def quantization_delta(self) -> float:
        return self._quantization_delta

    @quantization_delta.setter
    def quantization_delta(self, quantization_delta: float) -> None:
        self._quantization_delta = quantization_delta
        for tracks in self.tracks.values():
            for track in tracks:
                track.quantization_delta = self._quantization_delta

    @property
    def selected_instrument(self) -> BaseInstrument:
        return self._selected_instrument

    @selected_instrument.setter
    def selected_instrument(self, instrument: BaseInstrument) -> None:
        self._selected_instrument = instrument

    @property
    def selected_track(self) -> Track:
        return self._selected_track
    
    @selected_track.setter
    def selected_track(self, track: Track) -> None:
        self._selected_track = track

    @property
    def tracks(self) -> dict[str, list[Track]]:
        return self._tracks
    
    @tracks.setter
    def tracks(self, tracks: dict[str, list[Track]]) -> None:
        self._tracks = tracks

    def _add_effects_to_group(self) -> None:
        for effect in self.effects:
            effect.group = self.effects_group
    
    def _add_instruments_to_group(self) -> None:
        for instrument in self.instruments.values():
            instrument.group = self.instruments_group

    def add_track(self, instrument_name: str) -> None:
        added_track_number = 0
        
        if len(self.tracks[instrument_name]) > 0:
            added_track_number = self.tracks[instrument_name][-1].track_number + 1
        
        self.tracks[instrument_name].append(
            Track(
                clock=self._clock,
                group=self.tracks_group,
                instrument=self.instruments[instrument_name],
                is_recording=self.is_recording,
                quantization_delta=self.quantization_delta,
                sequencer_steps=self._SEQUENCER_STEPS,
                server=self.server,
                track_number=added_track_number,
            )
        )

    def _create_effects_synths(self) -> None:
        for effect in self.effects:
            effect.create_synth()

    def delete_track(self, instrument_name: str, track_number: int) -> None:
        removed_track_number = self.tracks[instrument_name][track_number].track_number
        del self.tracks[instrument_name][track_number]
        num_tracks = len(self.tracks[instrument_name])

        for tn in range(removed_track_number, num_tracks):
            self.tracks[instrument_name][tn].track_number = tn

    def get_selected_instrument_name(self) -> str:
        return self._selected_instrument.name
    
    def get_selected_track_number(self) -> int:
        return self._selected_track.track_number

    def handle_midi_message(self, message: Message) -> None:
        """
        If recording, we only want to play the selected instrument.
        During playback, we need to play all of the instruments.
        """
        if not self.is_recording:
            # Just play, don't record.
            self.selected_instrument.handle_midi_message(message=message)
        else:
            # The track will record and then send it to the instrument to play.
            self.selected_track.handle_midi_message(message=message)
    
    def _initialize_midi_handler(self) -> MIDIHandler:
        return MIDIHandler(message_handler_callback=self.handle_midi_message)

    def _initialize_tracks(self) -> dict[str, list[Track]]:
        tracks_by_instrument = defaultdict(list)
        for instrument in self.instruments.values():
            tracks_by_instrument[instrument.name].append(
                Track(
                    clock=self._clock,
                    group=self.tracks_group,
                    instrument=instrument,
                    is_recording=self.is_recording,
                    quantization_delta=self.quantization_delta,
                    recording_bus=self.effects[-1].out_bus,
                    sequencer_steps=self._SEQUENCER_STEPS,
                    server=self.server,
                    track_number=0,
                )
            )
        
        return tracks_by_instrument
    
    def _route_effects_signals(self) -> None:
        for index, effect in enumerate(self.effects):
            if index + 1 < len(self.effects) - 1:
                effect.out_bus = self.effects[index + 1].in_bus

    def _route_instruments_signals(self) -> None:
        for instrument in self.instruments.values():
            instrument.out_bus = self.effects[0].in_bus

    def sequencer_clock_callback(
        self, 
        context: ClockContext, 
        delta: float, 
    ) -> tuple[float, TimeUnit]:
        if context.event.invocations % self._track_length_in_measures == 0:
            index = context.event.invocations // self._track_length_in_measures
            self.start_tracks_playback(track_index=index)

        return delta, TimeUnit.BEATS

    def set_selected_instrument_by_name(self, name: str) -> None:
        self.selected_instrument = self.instruments[name]

    def set_selected_track_by_track_number(self, instrument_name: str, track_number: int) -> None:
        self.selected_track = self.tracks[instrument_name][track_number]

    def start_playback(self) -> None:
        self._clock.start()
        self._clock_event_id = self._clock.cue(
            kwargs={'delta': 1.0},
            procedure=self.sequencer_clock_callback
        )

    def start_recording(self) -> None:
        self.is_recording = True

    def stop_recording(self) -> None:
        self.is_recording = False
    
    def start_tracks_playback(self, track_index: int) -> None:
        self.stop_tracks_playback()
        if self.playing_tracks:
            self.playing_tracks.clear()
        
        for tracks in self.tracks.values():
            if track_index < len(tracks):
                self.playing_tracks.append(tracks[track_index])
        
        if not self.playing_tracks:
            self.stop_tracks_playback()

        for track in self.playing_tracks:
            track.start_playback()

    def stop_tracks_playback(self) -> None:
        for track in self.playing_tracks:
            track.stop_playback()
