"""A script demonstrating how to do phase modulation synthesis and build algorithms.


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
from math import pi

from supriya import Server, synthdef, UGenOperable
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
from supriya.ugens.core import UGenRecursiveInput
from supriya.ugens.filters import OnePole
from supriya.ugens.info import SampleDur, SampleRate
from supriya.ugens.inout import LocalIn, LocalOut
from supriya.ugens.lines import DC
from supriya.ugens.noise import IRand
from supriya.ugens.triggers import Phasor


TWO_PI = 2 * pi

def one_pole_filter(
    frequency: UGenRecursiveInput,
    modulator: UGenRecursiveInput, 
) -> UGenOperable:
    nyquist = SampleRate.ir() / 2
    clipped_frequency = frequency.clip(-nyquist, nyquist)
    slope = abs(clipped_frequency) * SampleDur.ir()
    return OnePole.ar(source=modulator, coefficient=(-TWO_PI * slope).exponential())

def phase_modulation(
    frequency: UGenRecursiveInput, 
    modulator: UGenRecursiveInput=0,
) -> UGenOperable:
    phase = Phasor.ar(trigger=0, rate=frequency * SampleDur.ir())
    return SinOsc.ar(frequency=DC.ar(source=0), phase=(phase + modulator) * TWO_PI)

def phase_modulation_operator(
    adsr=(0.01, 0.3, 0.5, 3.0),
    curve=(-4),
    frequency=440,
    gate=1,
    is_modulator=True,
    modulator=0,
    phase_index=1.0,
    ratio=1,
) -> UGenOperable:
    envelope = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr[0],
            decay_time=adsr[1], 
            sustain=adsr[2],
            release_time=adsr[3],
            curve=curve[0],
        ),
        done_action=2,
        gate=gate,
    )
    
    frequency *= ratio
    modulation = phase_modulation(frequency=frequency, modulator=modulator)

    if is_modulator:
        modulation /= TWO_PI * phase_index
        modulation = one_pole_filter(frequency=frequency, modulator=modulation)
    else:
        modulation *= phase_index    
    
    modulation *= envelope
    
    return modulation

def feedback_phase_modulation_operator(
    frequency=440,
    feedback_index=1.0,
) -> None:
    feedback = LocalIn.ar(channel_count=1) / TWO_PI * feedback_index
    modulator = one_pole_filter(frequency=frequency, modulator=feedback)
    
    signal = phase_modulation(frequency=frequency, modulator=modulator)
    LocalOut.ar(source=signal)

    return signal

@synthdef()
def algorithm_1(
    adsr_1=(0.01, 0.3, 0.5, 3.0),
    adsr_2=(0.01, 0.3, 0.5, 3.0),
    adsr_3=(0.01, 0.3, 0.5, 3.0),
    amplitude = 0.2,
    carrier_ratio=1, 
    curve_1=(-4),
    curve_2=(-4),
    curve_3=(-4),
    feedback_index=1.0,
    frequency=500, 
    gate=1,
    phase_index_2=1.0,
    phase_index_3=1.0,
    modulator_ratio_2=1,
    modulator_ratio_3=1,
    modulator_ratio_4=1,
) -> None:
    ratio = IRand.ir(minimum=1, maximum=2)
    carrier_ratio = ratio
    modulator_ratio_2 = ratio * 1
    modulator_ratio_3 = ratio * 2
    modulator_ratio_4 = ratio * 3

    modulator_4 = feedback_phase_modulation_operator(
        frequency=frequency * modulator_ratio_4,
        feedback_index=feedback_index
    )
    
    modulator_3 = phase_modulation_operator(
        adsr=adsr_3,
        curve=curve_3,
        frequency=frequency,
        gate=gate,
        modulator=modulator_4,
        phase_index=phase_index_3,
        ratio=modulator_ratio_3,
    )

    modulator_2 = phase_modulation_operator(
        adsr=adsr_2,
        curve=curve_2,
        frequency=frequency,
        gate=gate,
        phase_index=phase_index_2,
        ratio=modulator_ratio_2,
    )

    modulator_2 += modulator_3

    carrier = phase_modulation_operator(
        adsr=adsr_1,
        curve=curve_1,
        frequency=frequency,
        gate=gate,
        is_modulator=False,
        modulator=modulator_2,
        ratio=carrier_ratio,
    )
    carrier = FreeVerb.ar(source=carrier, mix=0.55, room_size=0.75, damping=0.5)
    carrier = CombL.ar(
        delay_time=0.2,
        decay_time=2.0,
        maximum_delay_time=0.2, 
        source=carrier
    )
    
    pan = Pan2.ar(source=carrier, position=0.0, level=amplitude)
    Out.ar(bus=0, source=pan)

@synthdef()
def algorithm_2(
    adsr_1=(0.01, 0.3, 0.5, 3.0),
    adsr_2=(0.01, 0.3, 0.5, 3.0),
    adsr_4=(0.01, 0.3, 0.5, 3.0),
    amplitude = 0.2,
    carrier_ratio=1, 
    curve_1=(-4),
    curve_2=(-4),
    curve_4=(-4),
    feedback_index=1.0,
    frequency=500, 
    gate=1,
    phase_index_2=1.0,
    phase_index_4=1.0,
    modulator_ratio_2=1,
    modulator_ratio_3=1,
    modulator_ratio_4=1,
) -> None:
    ratio = IRand.ir(minimum=1, maximum=2)
    carrier_ratio=ratio
    modulator_ratio_2=ratio * 4
    modulator_ratio_3=ratio * 2
    modulator_ratio_4=ratio * 8

    modulator_4 = phase_modulation_operator(
        adsr=adsr_4,
        curve=curve_4,
        frequency=frequency,
        gate=gate,
        phase_index=phase_index_4,
        ratio=modulator_ratio_4,
    )

    modulator_3 = feedback_phase_modulation_operator(
        frequency=frequency * modulator_ratio_3,
        feedback_index=feedback_index
    )

    modulator_3 += modulator_4

    modulator_2 = phase_modulation_operator(
        adsr=adsr_2,
        curve=curve_2,
        frequency=frequency,
        gate=gate,
        modulator=modulator_3,
        phase_index=phase_index_2,
        ratio=modulator_ratio_2,
    )

    carrier = phase_modulation_operator(
        adsr=adsr_1,
        curve=curve_1,
        frequency=frequency,
        gate=gate,
        is_modulator=False,
        modulator=modulator_2 + modulator_4,
        ratio=carrier_ratio,
    )
    carrier = FreeVerb.ar(source=carrier, mix=0.55, room_size=0.75, damping=0.5)
    carrier = CombL.ar(
        delay_time=0.2,
        decay_time=2.0,
        maximum_delay_time=0.2, 
        source=carrier
    )
    
    pan = Pan2.ar(source=carrier, position=0.0, level=amplitude)
    Out.ar(bus=0, source=pan)

@synthdef()
def algorithm_3(
    adsr_1=(0.01, 0.3, 0.5, 3.0),
    adsr_2=(0.01, 0.3, 0.5, 3.0),
    adsr_3=(0.01, 0.3, 0.5, 3.0),
    amplitude = 0.2,
    carrier_ratio=1, 
    curve_1=(-4),
    curve_2=(-4),
    curve_3=(-4),
    feedback_index=1.0,
    frequency=500, 
    gate=1,
    phase_index_2=1.0,
    phase_index_3=1.0,
    modulator_ratio_2=1,
    modulator_ratio_3=1,
    modulator_ratio_4=1,
) -> None:
    ratio = IRand.ir(minimum=1, maximum=2)
    carrier_ratio = ratio
    modulator_ratio_2 = ratio + 4
    modulator_ratio_3 = ratio + 2
    modulator_ratio_4 = ratio + 1

    modulator_3 = phase_modulation_operator(
        adsr=adsr_3,
        curve=curve_3,
        frequency=frequency,
        gate=gate,
        phase_index=phase_index_3,
        ratio=modulator_ratio_3,
    )

    modulator_2 = phase_modulation_operator(
        adsr=adsr_2,
        curve=curve_2,
        frequency=frequency,
        gate=gate,
        modulator=modulator_3,
        phase_index=phase_index_2,
        ratio=modulator_ratio_2,
    )

    modulator_4 = feedback_phase_modulation_operator(
        frequency=frequency * modulator_ratio_4,
        feedback_index=feedback_index
    )

    carrier = phase_modulation_operator(
        adsr=adsr_1,
        curve=curve_1,
        frequency=frequency,
        gate=gate,
        is_modulator=False,
        modulator=modulator_2 + modulator_4,
        ratio=carrier_ratio,
    )
    carrier = FreeVerb.ar(source=carrier, mix=0.55, room_size=0.65, damping=0.5)
    carrier = CombL.ar(
        delay_time=0.2,
        decay_time=2.0,
        maximum_delay_time=0.2, 
        source=carrier
    )
    
    pan = Pan2.ar(source=carrier, position=0.0, level=amplitude)
    Out.ar(bus=0, source=pan)    

@synthdef()
def algorithm_4(
    adsr_1=(0.01, 0.3, 0.5, 3.0),
    adsr_2=(0.01, 0.3, 0.5, 3.0),
    adsr_3=(0.01, 0.3, 0.5, 3.0),
    amplitude = 0.2,
    carrier_ratio=1, 
    curve_1=(-4),
    curve_2=(-4),
    curve_3=(-4),
    feedback_index=1.0,
    frequency=500, 
    gate=1,
    phase_index_2=1.0,
    phase_index_3=1.0,
    modulator_ratio_2=1,
    modulator_ratio_3=1,
    modulator_ratio_4=1,
) -> None:
    ratio = IRand.ir(minimum=1, maximum=2)
    carrier_ratio = ratio
    modulator_ratio_2 = ratio * 4
    modulator_ratio_3 = ratio * 2
    modulator_ratio_4 = ratio + 1

    modulator_4 = feedback_phase_modulation_operator(
        frequency=frequency * modulator_ratio_4,
        feedback_index=feedback_index
    )

    modulator_3 = phase_modulation_operator(
        adsr=adsr_3,
        curve=curve_3,
        frequency=frequency,
        gate=gate,
        modulator=modulator_4,
        phase_index=phase_index_3,
        ratio=modulator_ratio_3,
    )

    modulator_2 = phase_modulation_operator(
        adsr=adsr_2,
        curve=curve_2,
        frequency=frequency,
        gate=gate,
        modulator=modulator_3,
        phase_index=phase_index_2,
        ratio=modulator_ratio_2,
    )

    carrier = phase_modulation_operator(
        adsr=adsr_1,
        curve=curve_1,
        frequency=frequency,
        gate=gate,
        is_modulator=False,
        modulator=modulator_2 + modulator_3,
        ratio=carrier_ratio,
    )
    carrier = FreeVerb.ar(source=carrier, mix=0.55, room_size=0.65, damping=0.5)
    
    pan = Pan2.ar(source=carrier, position=0.0, level=amplitude)
    Out.ar(bus=0, source=pan)    

@synthdef()
def algorithm_5(
    adsr_1=(0.01, 0.3, 0.5, 3.0),
    adsr_2=(0.01, 0.3, 0.5, 3.0),
    adsr_3=(0.01, 0.3, 0.5, 3.0),
    amplitude = 0.2,
    carrier_ratio_1=1, 
    carrier_ratio_3=1, 
    curve_1=(-4),
    curve_2=(-4),
    curve_3=(-4),
    feedback_index=1.0,
    frequency=500, 
    gate=1,
    phase_index_2=1.0,
    modulator_ratio_2=1,
    modulator_ratio_4=1,
) -> None:
    ratio = IRand.ir(minimum=1, maximum=2)
    carrier_ratio_1 = carrier_ratio_3 = ratio
    modulator_ratio_2 = ratio * 4
    modulator_ratio_4 = ratio + 2

    modulator_4 = feedback_phase_modulation_operator(
        frequency=frequency * modulator_ratio_4,
        feedback_index=feedback_index
    )

    modulator_2 = phase_modulation_operator(
        adsr=adsr_2,
        curve=curve_2,
        frequency=frequency,
        gate=gate,
        phase_index=phase_index_2,
        ratio=modulator_ratio_2,
    )

    carrier_1 = phase_modulation_operator(
        adsr=adsr_1,
        curve=curve_1,
        frequency=frequency,
        gate=gate,
        is_modulator=False,
        modulator=modulator_2,
        ratio=carrier_ratio_1,
    )

    carrier_3 = phase_modulation_operator(
        adsr=adsr_3,
        curve=curve_3,
        frequency=frequency,
        gate=gate,
        is_modulator=False,
        modulator=modulator_4,
        ratio=carrier_ratio_3,
    )

    output = carrier_1 + carrier_3

    output = FreeVerb.ar(source=output, mix=0.55, room_size=0.75, damping=0.5)
    output = CombL.ar(
        delay_time=0.2,
        decay_time=2.0,
        maximum_delay_time=0.2, 
        source=output
    )
    
    pan = Pan2.ar(source=output, position=0.0, level=amplitude)
    Out.ar(bus=0, source=pan)  

@synthdef()
def algorithm_6(
    adsr_1=(0.01, 0.3, 0.5, 3.0),
    adsr_2=(0.01, 0.3, 0.5, 3.0),
    adsr_3=(0.01, 0.3, 0.5, 3.0),
    amplitude = 0.2,
    carrier_ratio_1=1,
    carrier_ratio_2=1,
    carrier_ratio_3=1,
    curve_1=(-4),
    curve_2=(-4),
    curve_3=(-4),
    feedback_index=1.0,
    frequency=500, 
    gate=1,
    modulator_ratio=1, 
) -> None:
    ratio = IRand.ir(minimum=1, maximum=2)
    carrier_ratio_1 = ratio * 2
    carrier_ratio_2 = ratio * 4
    carrier_ratio_3 = ratio * 8

    modulator_ratio = ratio + 2

    modulator_4 = feedback_phase_modulation_operator(
        frequency=frequency * modulator_ratio,
        feedback_index=feedback_index
    )

    carrier_1 = phase_modulation_operator(
        adsr=adsr_1,
        curve=curve_1,
        frequency=frequency,
        gate=gate,
        is_modulator=False,
        ratio=carrier_ratio_1,
    )

    carrier_2 = phase_modulation_operator(
        adsr=adsr_2,
        curve=curve_2,
        frequency=frequency,
        gate=gate,
        is_modulator=False,
        modulator=modulator_4,
        ratio=carrier_ratio_2,
    )

    carrier_3 = phase_modulation_operator(
        adsr=adsr_3,
        curve=curve_3,
        frequency=frequency,
        gate=gate,
        is_modulator=False,
        ratio=carrier_ratio_3,
    )

    output = carrier_1 + carrier_2 + carrier_3

    output = FreeVerb.ar(source=output, mix=0.55, room_size=0.75, damping=0.5)
    output = CombL.ar(
        delay_time=0.2,
        decay_time=2.0,
        maximum_delay_time=0.2, 
        source=output
    )
    
    pan = Pan2.ar(source=output, position=0.0, level=amplitude)
    Out.ar(bus=0, source=pan)

@synthdef()
def algorithm_7(
    adsr_1=(0.01, 0.3, 0.5, 3.0),
    adsr_2=(0.01, 0.3, 0.5, 3.0),
    adsr_3=(0.01, 0.3, 0.5, 3.0),
    amplitude = 0.2,
    carrier_ratio_1=1, 
    carrier_ratio_2=1, 
    carrier_ratio_3=1, 
    curve_1=(-4),
    curve_2=(-4),
    curve_3=(-4),
    feedback_index=1.0,
    frequency=500, 
    gate=1,
    modulator_ratio=1, 
) -> None:
    ratio = IRand.ir(minimum=1, maximum=2)
    carrier_ratio_1 = ratio
    carrier_ratio_2 = ratio + 2
    carrier_ratio_3 = ratio + 4

    modulator_ratio = ratio + 1

    modulator_4 = feedback_phase_modulation_operator(
        frequency=frequency * modulator_ratio,
        feedback_index=feedback_index
    )

    carrier_1 = phase_modulation_operator(
        adsr=adsr_1,
        curve=curve_1,
        frequency=frequency,
        gate=gate,
        is_modulator=False,
        ratio=carrier_ratio_1,
    )

    carrier_2 = phase_modulation_operator(
        adsr=adsr_2,
        curve=curve_2,
        frequency=frequency,
        gate=gate,
        is_modulator=False,
        ratio=carrier_ratio_2,
    )

    carrier_3 = phase_modulation_operator(
        adsr=adsr_3,
        curve=curve_3,
        frequency=frequency,
        gate=gate,
        is_modulator=False,
        modulator=modulator_4,
        ratio=carrier_ratio_3,
    )

    output = carrier_1 + carrier_2 + carrier_3

    output = FreeVerb.ar(source=output, mix=0.75, room_size=0.75, damping=0.5)
    output = CombL.ar(
        delay_time=0.2,
        decay_time=4.0,
        maximum_delay_time=0.2, 
        source=output
    )
    
    pan = Pan2.ar(source=output, position=0.0, level=amplitude)
    Out.ar(bus=0, source=pan)

@synthdef()
def algorithm_8(
    adsr_1=(0.01, 0.3, 0.5, 3.0),
    adsr_2=(0.01, 0.3, 0.5, 3.0),
    adsr_3=(0.01, 0.3, 0.5, 3.0),
    adsr_4=(0.01, 0.3, 0.5, 3.0),
    amplitude = 0.2,
    carrier_ratio_1=1, 
    carrier_ratio_2=1, 
    carrier_ratio_3=1, 
    carrier_ratio_4=1, 
    curve_1=(-4),
    curve_2=(-4),
    curve_3=(-4),
    curve_4=(-4),
    feedback_index=1.0,
    frequency=500, 
    gate=1,
) -> None:
    ratio = IRand.ir(minimum=1, maximum=2)
    carrier_ratio_1 = ratio * 1
    carrier_ratio_2 = ratio * 2
    carrier_ratio_3 = ratio * 4
    carrier_ratio_4 = ratio * 6

    carrier_1 = phase_modulation_operator(
        adsr=adsr_1,
        curve=curve_1,
        frequency=frequency,
        gate=gate,
        is_modulator=False,
        ratio=carrier_ratio_1,
    )

    carrier_2 = phase_modulation_operator(
        adsr=adsr_2,
        curve=curve_2,
        frequency=frequency,
        gate=gate,
        is_modulator=False,
        ratio=carrier_ratio_2,
    )

    carrier_3 = phase_modulation_operator(
        adsr=adsr_3,
        curve=curve_3,
        frequency=frequency,
        gate=gate,
        is_modulator=False,
        ratio=carrier_ratio_3,
    )

    # Special case where a carrier has feedback
    carrier_4 = feedback_phase_modulation_operator(
        frequency=frequency * carrier_ratio_4,
        feedback_index=feedback_index
    )
    envelope_4 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_4[0],
            decay_time=adsr_4[1], 
            sustain=adsr_4[2],
            release_time=adsr_4[3],
            curve=curve_4[0],
        ),
        done_action=2,
        gate=gate,
    )
    carrier_4 *= envelope_4

    output = carrier_1 + carrier_2 + carrier_3 + carrier_4

    output = FreeVerb.ar(source=output, mix=0.75, room_size=0.65, damping=0.5)
    output = CombL.ar(
        delay_time=0.2,
        decay_time=4.0,
        maximum_delay_time=0.2, 
        source=output
    )
    
    pan = Pan2.ar(source=output, position=0.0, level=amplitude)
    Out.ar(bus=0, source=pan)


def main() -> None:
    server = Server().boot(block_size=1)
    server.add_synthdefs( 
        algorithm_4,
        algorithm_6,
        algorithm_7,
    )
    server.sync()

    # [ 0,  2,  3,  5,  7,  8,  10 ]
    # [ 12, 14, 15, 17, 19, 20, 22 ]
    bass_note = 27
    bass_scale = [0, 3, 8, 12, 3, 7, 10, 14]
    bass_frequencies = [midi_note_number_to_frequency(n + bass_note) for n in bass_scale]
    bass_sequence = SequencePattern(bass_frequencies, iterations=None)


    # minor_scale_arpeggio = [0, 3, 7, 10, 5, 7, 3]
    minor_scale_arpeggio = [
        0, 3, 7, 10, 
        7, 3, 0, 10, 
        8, 12, 15, 19, 
        8, 19, 15, 12, 
        3, 7, 12, 15, 
        12, 7, 3, 15, 
        10, 14, 17, 20, 
        14, 10, 20, 17,
    ]
    arpeggio_note = 51
    arpeggio_frequencies = [midi_note_number_to_frequency(n + arpeggio_note) for n in minor_scale_arpeggio]
    arpeggio_sequence = SequencePattern(arpeggio_frequencies, iterations=None)

    pad_sequence = SequencePattern(
        [
            [
                midi_note_number_to_frequency(arpeggio_note + 0),
                midi_note_number_to_frequency(arpeggio_note + 3),
                midi_note_number_to_frequency(arpeggio_note + 7),
                midi_note_number_to_frequency(arpeggio_note + 10),
            ],
            [
                midi_note_number_to_frequency(arpeggio_note + 8),
                midi_note_number_to_frequency(arpeggio_note + 12),
                midi_note_number_to_frequency(arpeggio_note + 15),
                midi_note_number_to_frequency(arpeggio_note + 19),
            ],
            [
                midi_note_number_to_frequency(arpeggio_note + 3),
                midi_note_number_to_frequency(arpeggio_note + 7),
                midi_note_number_to_frequency(arpeggio_note + 12),
                midi_note_number_to_frequency(arpeggio_note + 15),
            ],
            [
                midi_note_number_to_frequency(arpeggio_note + 10),
                midi_note_number_to_frequency(arpeggio_note + 14),
                midi_note_number_to_frequency(arpeggio_note + 17),
                midi_note_number_to_frequency(arpeggio_note + 20),
            ],
        ], 
        iterations=None,
    )

    algorithm_4_pattern = EventPattern(
        frequency=bass_sequence,
        synthdef=algorithm_4,
        delta=0.25,
        duration=0.25,
        adsr_1=(0.01, 0.5, 0.01, 0.01),
        adsr_2=(0.01, 0.5, 0.01, 0.01),
        adsr_3=(0.01, 0.5, 0.01, 0.01),
        amplitude=0.25,
        feedback_index=3.832276,
        phase_index_2=0.197109,
        phase_index_3=2.11338,
    )

    algorithm_6_pattern = EventPattern(
        frequency=arpeggio_sequence,
        synthdef=algorithm_6,
        delta=0.0625,
        duration=0.0625,
        amplitude=0.2,
        feedback_index=RandomPattern(minimum=0.0, maximum=15.0),
    )

    algorithm_7_pattern = EventPattern(
        frequency=pad_sequence,
        synthdef=algorithm_7,
        delta=0.5,
        duration=0.5,
        amplitude=0.06,
        adsr_1=(2.0, 0.5, 0.01, 1.0),
        adsr_2=(1.0, 0.3, 0.01, 1.2),
        adsr_3=(0.5, 0.1, 0.01, 1.5),
        curve_1=(-8),
        curve_2=(-4),
        curve_3=(8),
        feedback_index=RandomPattern(minimum=0.0, maximum=25.0),
    )

    clock = Clock()
    clock.start(beats_per_minute=40.0)
    
    algorithm_4_pattern.play(clock=clock, context=server, quantization='1/4')
    algorithm_6_pattern.play(clock=clock, context=server, quantization='1/4')
    algorithm_7_pattern.play(clock=clock, context=server, quantization='1/4')

    while True:
        continue

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)