"""A script demonstrating a low-pass filter with an LFO assigned to the cutoff frequency.


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
import random
import sys

import supriya
from supriya import Buffer, Envelope, Server, synthdef
from supriya.ugens import (
    CombL,
    Envelope,
    FreeVerb,
    LinLin, 
    Out, 
)
from supriya.ugens.filters import LeakDC
from supriya.ugens.mac import MouseX
from supriya.ugens.noise import  LFNoise1
from supriya.ugens.osc import Osc, VOsc

@synthdef()
def wavetable(buffer_id, frequency=440.0, initial_phase=0.0) -> None:
    # signal = Osc.ar(buffer_id=buffer_id, frequency=frequency, initial_phase=initial_phase)
    signal = Osc.ar(
        buffer_id=buffer_id, 
        frequency=MouseX.kr(minimum=10, maximum=1000, warp=1), 
        initial_phase=initial_phase
    )
    signal *= 0.1
    signal = LeakDC.ar(source=signal)
    Out.ar(bus=0, source=[signal, signal])

@synthdef()
def variable_wavetable(buf_start_num, num_buffs, frequency=440.0, phase=0.0) -> None:
    # signal = Osc.ar(buffer_id=buffer_id, frequency=frequency, initial_phase=initial_phase)
    noise = LFNoise1.kr(frequency=0.5)
    buf_pos = LinLin.kr(
        source=noise,
        input_minimum=0.0,
        input_maximum=1.0,
        output_minimum=buf_start_num,
        output_maximum=num_buffs - 1,
    )
    signal = VOsc.ar(
        buffer_id=buf_pos, 
        frequency=frequency, 
        phase=phase
    )
    signal= FreeVerb.ar(source=signal, mix=0.75, room_size=0.6, damping=0.5)
    signal = CombL.ar(
        delay_time=0.5,
        decay_time = 1.0,
        maximum_delay_time=1.5, 
        source=signal
    )
    signal = LeakDC.ar(source=signal)
    signal *= 0.1
    Out.ar(bus=0, source=[signal, signal])

def create_wavetable_buffer(server) -> Buffer:
    buffer = server.add_buffer(channel_count=1, frame_count=2048)
    # amps = [1]
    # for _ in range(31):
    #     amps.append(random.uniform(0.05, 0.5))

    # amps = Envelope(
    #     amplitudes=[0, 0.6, -0.9, 0.3, 0],
    #     durations=[4, 3, 2, 1],
    #     curves=EnvelopeShape.LINEAR,
    # )

    # amps = Envelope(
    #     amplitudes=[0, 0.6, -0.9, 0.3, 0],
    #     durations=[4, 3, 2, 1],
    #     # curves=EnvelopeShape.SINE,
    #     curves=[random.randrange(-20, 20) for x in range(4)]
    # )

    num_segments = random.randrange(4, 20)
    print(f"num_segments={num_segments}")
    amplitudes = [random.uniform(-1.0, 1.0) for x in range(num_segments + 1)]
    # for _ in range(num_segments + 1):
    #     amplitudes.append(random.uniform(-1.0, 1.0))
    
    durations = []
    curves = []
    durations = [random.uniform(1.0, 20.0) for _ in range(num_segments)]
    curves = [random.uniform(-20.0, 20.0) for _ in range(num_segments)]
    # for _ in range(num_segments):
    #     durations.append(random.uniform(1.0, 20.0))
    #     curves.append(random.uniform(-20.0, 20.0))
    
    print(f"amplitudes={amplitudes}")
    print(f"durations={durations}")
    print(f"curves={curves}")

    amps = Envelope(
        amplitudes=amplitudes,
        durations=durations,
        curves=curves,
    )
    

    buffer.generate(
        command_name='sine1',
        # amplitudes=amps.serialize(),
        amplitudes=amps,
        should_normalize=True,
        as_wavetable=True,
    )
    supriya.plot(buffer)

    return buffer

def main() -> None:
    server = Server().boot()
    server.add_synthdefs(variable_wavetable)
    server.sync()
    
    buffer_1 = create_wavetable_buffer(server=server)
    buffer_2 = create_wavetable_buffer(server=server)
    buffer_3 = create_wavetable_buffer(server=server)
    buffer_4 = create_wavetable_buffer(server=server)

    server.add_synth(
        buf_start_num=0, 
        frequency=120.0,
        num_buffs=4, 
        synthdef=variable_wavetable,
    )

    while True:
        continue

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
