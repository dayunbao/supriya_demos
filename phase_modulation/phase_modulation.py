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
    modulator_ratio_2 = ratio * 4
    modulator_ratio_3 = ratio * 2
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

    output = FreeVerb.ar(source=output, mix=0.55, room_size=0.75, damping=0.5)
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
        algorithm_1, 
        algorithm_2, 
        algorithm_3, 
        algorithm_4,
        algorithm_5,
        algorithm_6,
        algorithm_7,
        algorithm_8,
    )
    server.sync()

    minor_scale_arpeggio = [0, 3, 7, 10, 5, 7, 3]
    arpeggio_note = 51
    arpeggio_frequencies = [midi_note_number_to_frequency(n + arpeggio_note) for n in minor_scale_arpeggio]
    arpeggio_sequence = SequencePattern(arpeggio_frequencies, iterations=None)

    pad_sequence = SequencePattern(
        [
            [
                midi_note_number_to_frequency(arpeggio_note + 0),
                midi_note_number_to_frequency(arpeggio_note + 3),
                midi_note_number_to_frequency(arpeggio_note + 7)
            ],
            [
                midi_note_number_to_frequency(arpeggio_note + 0 + 5),
                midi_note_number_to_frequency(arpeggio_note + 3 + 5),
                midi_note_number_to_frequency(arpeggio_note + 7 + 5)
            ],
            [
                midi_note_number_to_frequency(arpeggio_note + 0 + 7),
                midi_note_number_to_frequency(arpeggio_note + 3 + 7),
                midi_note_number_to_frequency(arpeggio_note + 7 + 7)
            ],
        ], 
        iterations=None,
    )
    
    arpeggio_pattern_1 = EventPattern(
        frequency=arpeggio_sequence,
        synthdef=feedback_phase_modulation_operator,
        delta=0.0625, # 16th note
        duration=0.0625, # 16th note
        adsr=(0.01, 0.3, 0.1, 0.0),
        amplitude=0.01,
        curve_1=(-4),
        feedback_index=RandomPattern(minimum=1.0, maximum=25.0),
    )

    arpeggio_pattern_2 = EventPattern(
        carrier_frequency=arpeggio_sequence,
        synthdef=phase_modulation_operator,
        delta=0.0625, # 16th note
        duration=0.0625, # 16th note
        amplitude=0.001,
        carrier_adsr=(0.01, 0.3, 0.1, 0.1),
        carrier_curve=(-4),
        carrier_phase_index=RandomPattern(minimum=6.0, maximum=12.0),
        # modulator_adsr=(0.01, 0.1, 0.0, 0.01),
        modulator_curve=(-4),
        modulator_phase_index=RandomPattern(minimum=2.0, maximum=12.0),
    )

    algorithm_1_pattern = EventPattern(
        frequency=arpeggio_sequence,
        synthdef=algorithm_1,
        delta=0.0625, # 16th note
        duration=0.0625, # 16th note
        amplitude=0.2,
        curve_1=(-32),
        curve_2=(-16),
        curve_4=(-8),
        feedback_index=RandomPattern(minimum=1.0, maximum=10.0),
        phase_index_2=RandomPattern(minimum=1.0, maximum=15.0),
        phase_index_4=RandomPattern(minimum=5.0, maximum=15.0),
    )

    algorithm_2_pattern = EventPattern(
        frequency=arpeggio_sequence,
        synthdef=algorithm_2,
        delta=0.0625, # 16th note
        duration=0.0625, # 16th note
        amplitude=0.2,
        curve_1=(-32),
        curve_2=(-16),
        curve_4=(-8),
        feedback_index=RandomPattern(minimum=1.0, maximum=10.0),
        phase_index_2=RandomPattern(minimum=1.0, maximum=15.0),
        phase_index_3=RandomPattern(minimum=5.0, maximum=15.0),
    )

    algorithm_3_pattern = EventPattern(
        frequency=arpeggio_sequence,
        synthdef=algorithm_3,
        delta=0.0625, # 16th note
        duration=0.0625, # 16th note
        amplitude=0.2,
        # curve_1=(-8),
        # curve_2=(-16),
        # curve_3=(-8),
        feedback_index=RandomPattern(minimum=0.0, maximum=5.0),
        phase_index_2=RandomPattern(minimum=0.0, maximum=7.5),
        phase_index_3=RandomPattern(minimum=7.6, maximum=15.0),
    )

    algorithm_4_pattern = EventPattern(
        frequency=arpeggio_sequence,
        synthdef=algorithm_4,
        delta=0.0625, # 16th note
        duration=0.0625, # 16th note
        amplitude=0.2,
        # curve_1=(-8),
        # curve_2=(-16),
        # curve_4=(-8),
        feedback_index=RandomPattern(minimum=0.0, maximum=5.0),
        phase_index_2=RandomPattern(minimum=0.0, maximum=7.5),
        phase_index_3=RandomPattern(minimum=7.6, maximum=15.0),
    )

    algorithm_5_pattern = EventPattern(
        frequency=arpeggio_sequence,
        synthdef=algorithm_5,
        delta=0.0625, # 16th note
        duration=0.0625, # 16th note
        amplitude=0.1,
        # curve_1=(-8),
        # curve_2=(-16),
        # curve_4=(-8),
        feedback_index=RandomPattern(minimum=0.0, maximum=15.0),
        phase_index_2=RandomPattern(minimum=0.0, maximum=5.0),
    )

    algorithm_6_pattern = EventPattern(
        frequency=arpeggio_sequence,
        synthdef=algorithm_6,
        delta=0.0625, # 16th note
        duration=0.0625, # 16th note
        amplitude=0.1,
        # curve_1=(-8),
        # curve_2=(-16),
        # curve_4=(-8),
        feedback_index=RandomPattern(minimum=0.0, maximum=15.0),
    )

    algorithm_7_pattern = EventPattern(
        frequency=pad_sequence,
        synthdef=algorithm_7,
        delta=0.5,
        duration=0.5,
        amplitude=0.2,
        adsr_1=(4.0, 0.3, 0.01, 1.0),
        adsr_2=(4.0, 0.3, 0.01, 1.0),
        adsr_3=(4.0, 0.3, 0.01, 1.0),
        curve_1=(0),
        curve_2=(0),
        curve_3=(0),
        # feedback_index=RandomPattern(minimum=0.0, maximum=5.0),
    )

    algorithm_8_pattern = EventPattern(
        frequency=pad_sequence,
        synthdef=algorithm_8,
        delta=0.5,
        duration=0.5,
        amplitude=0.1,
        adsr_1=(1.0, 0.3, 0.1, 1.5),
        adsr_2=(1.0, 0.3, 0.1, 1.5),
        adsr_3=(1.0, 0.3, 0.1, 1.5),
        adsr_4=(1.0, 0.3, 0.1, 1.5),
        curve_1=(-4),
        curve_2=(-8),
        curve_3=(-16),
        curve_4=(4),
        feedback_index=RandomPattern(minimum=0.0, maximum=5.0),
    )
    

    clock = Clock()
    clock.start(beats_per_minute=40.0)
    # arpeggio_pattern_1.play(clock=clock, context=server)
    # arpeggio_pattern_2.play(clock=clock, context=server)
    # algorithm_1_pattern.play(clock=clock, context=server)
    # algorithm_2_pattern.play(clock=clock, context=server)
    # algorithm_3_pattern.play(clock=clock, context=server)
    # algorithm_4_pattern.play(clock=clock, context=server)
    # algorithm_5_pattern.play(clock=clock, context=server)
    # algorithm_6_pattern.play(clock=clock, context=server)
    # algorithm_7_pattern.play(clock=clock, context=server)
    algorithm_8_pattern.play(clock=clock, context=server)

    while True:
        continue

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)