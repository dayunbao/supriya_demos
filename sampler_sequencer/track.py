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

from sampler_note import SamplerNote

class Track:
    def __init__(
            self, 
            quantization_delta: float,
            sequencer_steps: int,
            track_number: int,
        ):
        self.quantization_delta = quantization_delta
        self.sequencer_steps =  sequencer_steps
        self.track_number = track_number
        self.recorded_notes: dict[float, list[SamplerNote]] = defaultdict(list)

    def erase_recorded_notes(self) -> None:
        self.recorded_notes.clear()
    
    def record_midi_message(self, sampler_note: SamplerNote) -> None:
        recorded_time = (sampler_note.message.note % self.sequencer_steps) * self.quantization_delta
        recorded_message = sampler_note.message.copy(time=recorded_time)
        recorded_sampler_note = SamplerNote(
            message=recorded_message, 
            program=sampler_note.program,
            sample_index=sampler_note.sample_index
            )

        self.recorded_notes[recorded_time].append(recorded_sampler_note)
