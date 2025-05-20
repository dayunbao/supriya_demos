"""A script demonstrating how to do granular synthesis.


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
from pathlib import Path

from supriya import Buffer, Server, synthdef, UGenOperable
from supriya.clocks import Clock
from supriya.conversions import midi_note_number_to_frequency
from supriya.patterns import EventPattern, RandomPattern, SequencePattern
from supriya.ugens import (
    CombL,
    Envelope,
    EnvGen,
    FreeVerb,
    Out, 
    Pan2,
    SinOsc,
)
from supriya.ugens.granular import GrainBuf
from supriya.ugens.noise import IRand
from supriya.ugens.osc import Impulse


def create_buffer(file_path: Path, server: Server) -> Buffer:
    # sample_buffer = server.add_buffer(channel_indices=[0], file_path=str(file_path))
    sample_buffer = server.add_buffer(file_path=str(file_path))

    return sample_buffer

@synthdef()
def granular_synthesis(
    buffer_id=0,
    channel_count=2,
    duration=1,
    pan=0,
    position=0,
    rate=1,
) -> None:
    signal = GrainBuf.ar(
        # channel_count=channel_count,
        duration=duration,
        # envelope_buffer_id=-1,
        # interpolate=2,
        # maximum_overlap=512,
        pan=pan,
        position=position,
        rate=rate,
        buffer_id=buffer_id,
        trigger=Impulse.ar(frequency=1),
    )

    signal *= 0.5
    
    Out.ar(bus=0, source=signal)

def main() -> None:
    server = Server().boot()
    server.add_synthdefs(granular_synthesis)
    server.sync()

    # drum_sample_path = Path(__file__).parent / 'samples/drum_loop.mp3'
    time_tombs_sample_path = Path(__file__).parent / 'samples/time_tombs.mp3'
    print(time_tombs_sample_path)
    
    # drum_sample_buffer = create_buffer(file_path=drum_sample_path, server=server)
    time_tombs_sample_buffer = create_buffer(file_path=time_tombs_sample_path, server=server)
    print(time_tombs_sample_buffer)

    server.add_synth(
        buffer_id=time_tombs_sample_buffer.id_,
        duration=11.5,
        synthdef=granular_synthesis
    )

    while True:
        continue

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)