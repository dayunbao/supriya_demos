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
from typing import Optional

from mido import Message

from supriya.clocks import ClockContext
from supriya.clocks.ephemera import TimeUnit

from class_lib import MIDIHandler
from class_lib import BaseSequencer
from class_lib import BaseInstrument
from .track import Track

class Sequencer(BaseSequencer):    
    def __init__(
            self, 
            bpm: int, 
            instruments: dict[str, BaseInstrument],
            quantization: str,
    ):
        super().__init__(bpm, quantization)
        self._instruments = instruments
        self._midi_handler = self._initialize_midi_handler()
        self._is_recording = False
        self.previous_measure = 1
        self.playing_tracks: list[Track] = []
        self._tracks: dict[str, list[Track]] = self._initialize_tracks()
        self._selected_instrument = list(self._instruments.values())[0]
        self._selected_track = self._tracks[self._selected_instrument.name][0]

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
    def tracks(self) -> dict[str, list[Track]]:
        return self._tracks
    
    @tracks.setter
    def tracks(self, tracks: dict[str, list[Track]]) -> None:
        self._tracks = tracks

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

    def set_selected_instrument_by_name(self, name: str) -> None:
        self.selected_instrument = self.instruments[name]

    def set_selected_track_by_track_number(self, instrument_name: str, track_number: int) -> None:
        self.selected_track = self.tracks[instrument_name][track_number]

    def add_track(self, instrument_name: str) -> None:
        added_track_number = 0
        starting_measure = 0
        
        if len(self.tracks[instrument_name]) > 0:
            added_track_number = self.tracks[instrument_name][-1].track_number + 1
            starting_measure = self._track_length_in_measures * added_track_number
        
        self.tracks[instrument_name].append(
            Track(
                clock=self._clock,
                instrument=self.instruments[instrument_name],
                is_recording=self.is_recording,
                quantization_delta=self.quantization_delta,
                sequencer_steps=self._SEQUENCER_STEPS,
                starting_measure=starting_measure,
                track_number=added_track_number,
            )
        )

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

    def _initialize_midi_handler(self) -> MIDIHandler:
        return MIDIHandler(message_handler_callback=self.handle_midi_message)

    def _initialize_tracks(self) -> dict[str, list[Track]]:
        tracks_by_instrument = defaultdict(list)
        for instrument in self.instruments.values():
            tracks_by_instrument[instrument.name].append(
                Track(
                    clock=self._clock,
                    instrument=instrument,
                    is_recording=self.is_recording,
                    quantization_delta=self.quantization_delta,
                    sequencer_steps=self._SEQUENCER_STEPS,
                    starting_measure=0,
                    track_number=0,
                )
            )
        
        return tracks_by_instrument

    def handle_midi_message(self, message: Message) -> None:
        """
        If recording, we only want to play the selected instrument.
        During playback, we need to play all of the instruments.
        """
        if not self.is_recording:
            # Just play, don't record.
            self.selected_instrument.handle_midi_message(message=message)
        else:
            self.selected_track.handle_midi_message(message=message)
    
    def sequencer_clock_callback(
        self, 
        context=ClockContext, 
        delta=1.0, # 1 measure 
        time_unit=TimeUnit.BEATS,
    ) -> tuple[float, TimeUnit]:
        # print(f'context.event.invocations={context.event.invocations}')
        # print(f'context.desired_moment.measure={context.desired_moment.measure}')
        if context.event.invocations % self._track_length_in_measures == 0:
            self.stop_tracks_playback()
            self.start_tracks_playback(measure=context.event.invocations)

        return delta, time_unit

    def start_playback(self) -> None:
        self._clock.start()
        self._clock_event_id = self._clock.cue(procedure=self.sequencer_clock_callback)

    def start_tracks_playback(self, measure: int) -> None:
        # print(f'In start_tracks_playback on measure = {measure}')
        # if self.playing_tracks:
        #     self.playing_tracks.clear()
        
        for tracks in self.tracks.values():
            # if measure < len(tracks):
            self.playing_tracks.append(tracks[measure])
        
        if not self.playing_tracks:
            self.stop_tracks_playback()

        print(f'{[print(t.recorded_notes) for t in self.playing_tracks]}')

        for track in self.playing_tracks:
            track.start_playback()

    def stop_tracks_playback(self) -> None:
        for track in self.playing_tracks:
            track.stop_playback()

    def start_recording(self) -> None:
        self.is_recording = True

    def stop_recording(self) -> None:
        self.is_recording = False