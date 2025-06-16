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
from supriya import AddAction, Buffer, BufferGroup, Bus, Envelope, Server, synthdef, UGenOperable
from supriya.clocks import Clock
from supriya.conversions import midi_note_number_to_frequency
from supriya.enums import EnvelopeShape
from supriya.patterns import EventPattern, RandomPattern, SequencePattern
from supriya.patterns.structure import ParallelPattern
from supriya.ugens import (
    CombL,
    Envelope,
    EnvGen,
    FreeVerb,
    In,
    Limiter,
    LinLin, 
    Out, 
    Pan2,
    SinOsc,
)
from supriya.ugens.core import UGenRecursiveInput
from supriya.ugens.filters import LeakDC
from supriya.ugens.noise import LFNoise1
from supriya.ugens.panning import Splay
from supriya.ugens.osc import COsc, Osc, VOsc


@synthdef()
def wavetable_osc(
    buffer_id, 
    amplitude=1.0, 
    frequency=440.0, 
    gate=1,
    initial_phase=0.0,
    out_bus=0,
) -> None:
    signal = Osc.ar(buffer_id=buffer_id, frequency=frequency, initial_phase=initial_phase)
    signal = LeakDC.ar(source=signal)
    envelope = EnvGen.kr(
        envelope=Envelope.percussive(),
        done_action=2,
        gate=gate,
    )
    signal *= envelope
    signal = Pan2.ar(source=signal, level=amplitude)
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def wavetable_cosc(
    buffer_id, 
    adsr=(0.01, 0.3, 0.5, 1.0),
    amplitude=1.0, 
    frequency=440.0,
    gate=1,
    out_bus=0,
) -> None:
    signal = COsc.ar(
        buffer_id=buffer_id, 
        frequency=frequency, 
        # beats=0.5,
        beats=SinOsc.ar(frequency=1).scale(
            input_minimum=-1.0,
            input_maximum=1.0,
            output_minimum=0.1,
            output_maximum=1.0,
        ),
    )
    signal = LeakDC.ar(source=signal)
    envelope = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr[0],
            decay_time=adsr[1],
            sustain=adsr[2],
            release_time=adsr[3],
        ), 
        done_action=2, 
        gate=gate
    )
    signal *= envelope
    signal = Pan2.ar(source=signal, level=amplitude)
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def variable_wavetable(
    buf_start_num, 
    num_buffs, 
    adsr=(0.01, 0.3, 0.5, 1.0),
    amplitude=1.0,
    frequency=440.0, 
    gate=1,
    out_bus=0,
    phase=0.0
) -> None:
    # signal = Osc.ar(buffer_id=buffer_id, frequency=frequency, initial_phase=initial_phase)
    # modulator = LFNoise1.kr(frequency=1)
    # modulator = SinOsc.ar(frequency=0.5)
    # buf_pos = LinLin.kr(
    #     source=modulator,
    #     input_minimum=-1.0,
    #     input_maximum=1.0,
    #     output_minimum=buf_start_num,
    #     output_maximum=num_buffs - 1,
    # )
    signal = VOsc.ar(
        buffer_id=SinOsc.ar(frequency=0.5).scale(
            input_minimum=-1.0,
            input_maximum=1.0,
            output_minimum=buf_start_num,
            output_maximum=num_buffs - 1,
        ), 
        frequency=frequency, 
        phase=phase
    )
    signal = LeakDC.ar(source=signal)
    envelope = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr[0],
            decay_time=adsr[1],
            sustain=adsr[2],
            release_time=adsr[3],
        ), 
        done_action=2, 
        gate=gate
    )
    signal *= envelope
    signal = Pan2.ar(source=signal, level=amplitude)
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def delay(in_bus: 2, out_bus=0) -> None:
    input = In.ar(bus=in_bus, channel_count=2)
    signal = CombL.ar(
        delay_time=0.2,
        decay_time=2.5,
        maximum_delay_time=0.2, 
        source=input
    )
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def reverb(in_bus: 2, out_bus=0) -> None:
    input = In.ar(bus=in_bus, channel_count=2)
    signal= FreeVerb.ar(source=input, mix=0.55, room_size=0.95, damping=0.5)
    Out.ar(bus=out_bus, source=signal)

def convert_to_wavetable(envelope_array):
    size = len(envelope_array)
    wavetable = []
    
    for i in range(size - 1):
        val1 = envelope_array[i]
        val2 = envelope_array[i + 1]
        wavetable.append(2.0 * val1 - val2)
        wavetable.append(val2 - val1)
    
    # Handle the wrap-around case
    val1 = envelope_array[-1]
    val2 = envelope_array[0]
    wavetable.append(2.0 * val1 - val2)
    wavetable.append(val2 - val1)
    
    return wavetable

def create_wavetable_buffer(server: Server) -> Buffer:
    num_segments = random.randrange(4, 20)
    amplitudes = [random.uniform(-1.0, 1.0) for _ in range(num_segments + 1)]
    durations = [random.randint(1, 20) for _ in range(num_segments)]
    # curves = [random.uniform(-20.0, 20.0) for _ in range(num_segments)]
    curves = [EnvelopeShape.WELCH for _ in range(num_segments)]

    # buffer.generate(
    #     command_name='sine1',
    #     # amplitudes=amps.serialize(),
    #     amplitudes=amps,
    #     should_normalize=True,
    #     as_wavetable=True,
    # )
    
    buffer = server.add_buffer(channel_count=1, frame_count=2048)

    env = Envelope(
        # amplitudes=[0, 0.6, -0.9, 0.3, 0],
        # durations=[4, 3, 2, 1],
        # curves=EnvelopeShape.LINEAR,
        amplitudes=amplitudes,
        durations=durations,
        curves=curves,
    )

    # length = 1024 (default)
    env_as_array = env.to_array()
    wavetable = convert_to_wavetable(envelope_array=env_as_array)

    buffer.zero()
    server.sync()
    buffer.set_range(index=0, values=wavetable)
    
    # supriya.plot(buffer)

    return buffer

def create_vosc_buffers(num_buffers: int, server: Server) -> BufferGroup:
    buffer_group = server.add_buffer_group(count=num_buffers, channel_count=1, frame_count=2048)

    for b in buffer_group.buffers:
        num_segments = random.randint(4, 20)
        amplitudes = [random.uniform(-1.0, 1.0) for _ in range(num_segments + 1)]
        durations = [random.randint(1, 20) for _ in range(num_segments)]
        # curves = [random.uniform(-20.0, 20.0) for _ in range(segments)]
        curves = [EnvelopeShape.WELCH for _ in range(num_segments)]

        env = Envelope(
            amplitudes=amplitudes,
            durations=durations,
            curves=curves,
        )

        # length = 1024 (default)
        env_as_array = env.to_array()
        wavetable = convert_to_wavetable(envelope_array=env_as_array)

        b.zero()
        server.sync()
        b.set_range(index=0, values=wavetable)

    return buffer_group

def main() -> None:
    server = Server().boot()
    server.add_synthdefs(delay, reverb, wavetable_cosc, wavetable_osc, variable_wavetable)
    server.sync()

    # Set up buses.
    delay_bus: Bus = server.add_bus(calculation_rate='audio')
    reverb_bus: Bus = server.add_bus(calculation_rate='audio')
    
    # Create the effects synths.
    server.add_synth(
        add_action=AddAction.ADD_TO_TAIL,
        in_bus=delay_bus,
        out_bus=reverb_bus,
        synthdef=delay,
    )
    
    server.add_synth(
        add_action=AddAction.ADD_TO_TAIL,
        in_bus=reverb_bus,
        out_bus=0,
        synthdef=reverb,
    )
    
    chorusing_wavetable_buffer = create_wavetable_buffer(server=server)
    wavetable_buffer = create_wavetable_buffer(server=server)
    vosc_buffers = create_vosc_buffers(num_buffers=3, server=server)

    # server.add_synth(
    #     amplitude=0.2,
    #     buf_start_num=vosc_buffers[0].id_, 
    #     frequency=midi_note_number_to_frequency(33),
    #     num_buffs=vosc_buffers.count, 
    #     synthdef=variable_wavetable,
    # )

    # server.add_synth(
    #     buffer_id=wavetable_buffer.id_,
    #     synthdef=wavetable_osc,
    # )

    augmented_scale_degrees = [
        0, 3, 4, 7, 8, 11,
        12, 15, 16, 19, 20, 23
    ]

    root_note = 51
    chord = [
        [
            midi_note_number_to_frequency(root_note + 0),
            midi_note_number_to_frequency(root_note + 4),
            midi_note_number_to_frequency(root_note + 8), 
            midi_note_number_to_frequency(root_note + 12), 
        ],
        [
            midi_note_number_to_frequency(root_note + 11),
            midi_note_number_to_frequency(root_note + 15),
            midi_note_number_to_frequency(root_note + 19), 
            midi_note_number_to_frequency(root_note + 23), 
        ],
        [
            midi_note_number_to_frequency(root_note + 7),
            midi_note_number_to_frequency(root_note + 11),
            midi_note_number_to_frequency(root_note + 15), 
            midi_note_number_to_frequency(root_note + 19), 
        ],
        [
            midi_note_number_to_frequency(root_note + 8),
            midi_note_number_to_frequency(root_note + 12),
            midi_note_number_to_frequency(root_note + 16), 
            midi_note_number_to_frequency(root_note + 20), 
        ],
    ]
    chord_sequence = SequencePattern(sequence=chord, iterations=None)
    chord_pattern = EventPattern(
        frequency=chord_sequence,
        synthdef=wavetable_cosc,
        delta=1.0,
        duration=1.0,
        adsr=(0.5, 0.3, 0.5, 0.4),
        amplitude=0.07,
        buf_start_num=chorusing_wavetable_buffer.id_,
        out_bus=reverb_bus,
    )

    melody_root_note = 75
    root_1 = [
        midi_note_number_to_frequency(melody_root_note + 0),
        midi_note_number_to_frequency(melody_root_note + 8), 
    ]
    root_2 = [
        midi_note_number_to_frequency(melody_root_note + 4),
        midi_note_number_to_frequency(melody_root_note + 0), 
    ]
    sixth_1 = [
        midi_note_number_to_frequency(melody_root_note + 11),
        midi_note_number_to_frequency(melody_root_note + 19), 
    ]
    sixth_2 = [
        midi_note_number_to_frequency(melody_root_note + 15),
        midi_note_number_to_frequency(melody_root_note + 11), 
    ]
    fourth_1 = [
        midi_note_number_to_frequency(melody_root_note + 7),
        midi_note_number_to_frequency(melody_root_note + 15), 
    ]
    fourth_2 = [
        midi_note_number_to_frequency(melody_root_note + 15),
        midi_note_number_to_frequency(melody_root_note + 11), 
    ]
    fifth_1 = [
        midi_note_number_to_frequency(melody_root_note + 8),
        midi_note_number_to_frequency(melody_root_note + 16), 
    ]
    fifth_2 = [
        midi_note_number_to_frequency(melody_root_note + 12),
        midi_note_number_to_frequency(melody_root_note + 8), 
    ]
    melody_notes = [
        root_1,
        root_1,
        root_1,
        root_1,
        root_2,
        root_2,
        root_2,
        root_2,
        sixth_1,
        sixth_1,
        sixth_1,
        sixth_1,
        sixth_2,
        sixth_2,
        sixth_2,
        sixth_2,
        fourth_1,
        fourth_1,
        fourth_1,
        fourth_1,
        fourth_2,
        fourth_2,
        fourth_2,
        fourth_2,
        fifth_1,
        fifth_1,
        fifth_1,
        fifth_1,
        fifth_2,
        fifth_2,
        fifth_2,
        fifth_2,
    ]
    melody_sequence = SequencePattern(sequence=melody_notes, iterations=None)
    melody_pattern = EventPattern(
        frequency=melody_sequence,
        synthdef=wavetable_osc,
        delta=0.125,
        duration=0.125,
        amplitude=0.15,
        buffer_id=wavetable_buffer.id_,
        out_bus=reverb_bus,
    )

    bass_note = 27
    bass_scale = [0, 8, 3, 4, 7, 15, 16, 8]
    bass_frequencies = [midi_note_number_to_frequency(n + bass_note) for n in bass_scale]
    bass_sequence = SequencePattern(bass_frequencies, iterations=None)

    bass_pattern = EventPattern(
        frequency=bass_sequence,
        synthdef=variable_wavetable,
        delta=0.5,
        duration=0.5,
        adsr=(0.01, 0.3, 0.2, 0.3),
        amplitude=0.09,
        buf_start_num=vosc_buffers[0].id_,
        num_buffs=vosc_buffers.count,
        out_bus=reverb_bus,
    )

    clock = Clock()
    clock.start(beats_per_minute=80.0)

    parallel_pattern = ParallelPattern(patterns=[bass_pattern, chord_pattern, melody_pattern])
    # parallel_pattern = ParallelPattern(patterns=[bass_pattern])
    parallel_pattern.play(clock=clock, context=server)

    while True:
        continue

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
