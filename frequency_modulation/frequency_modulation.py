import sys

from supriya import Server, synthdef
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
from supriya.ugens.inout import LocalIn, LocalOut
from supriya.ugens.noise import IRand


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
    modulation_index_2=1.0,
    modulation_index_3=1.0,
    modulator_ratio_2=1,
    modulator_ratio_3=1,
    modulator_ratio_4=1,
) -> None:
    ratio = IRand.ir(minimum=1, maximum=2)
    carrier_ratio = ratio
    modulator_ratio_2 = ratio + 1
    modulator_ratio_3 = ratio + 2
    modulator_ratio_4 = ratio + 3

    envelope_1 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_1[0],
            decay_time=adsr_1[1], 
            sustain=adsr_1[2],
            release_time=adsr_1[3],
            curve=curve_1[0],
        ),
        done_action=2,
        gate=gate,
    )

    envelope_2 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_2[0],
            decay_time=adsr_2[1], 
            sustain=adsr_2[2],
            release_time=adsr_2[3],
            curve=curve_2[0],
        ),
        done_action=2,
        gate=gate,
    )

    envelope_3 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_3[0],
            decay_time=adsr_3[1], 
            sustain=adsr_3[2],
            release_time=adsr_3[3],
            curve=curve_3[0],
        ),
        done_action=2,
        gate=gate,
    )

    feedback = LocalIn.ar(channel_count=1) * feedback_index
    modulator_4 = SinOsc.ar(frequency=frequency * modulator_ratio_4 + feedback)
    LocalOut.ar(source=modulator_4)
    
    modulator_3 = SinOsc.kr(frequency=frequency * modulator_ratio_3 + modulator_4) * (frequency * modulator_ratio_3) * (envelope_3 * modulation_index_3)
    
    modulator_2 = SinOsc.ar(frequency=frequency * modulator_ratio_2) * (frequency * modulator_ratio_2) * (envelope_2 * modulation_index_2)
    modulator_2 += modulator_3
    
    carrier = SinOsc.ar(frequency=frequency * carrier_ratio + modulator_2) * envelope_1
    carrier = FreeVerb.ar(source=carrier, mix=0.25, room_size=0.5, damping=0.5)
    carrier = CombL.ar(
        delay_time=0.2,
        decay_time=1.5,
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
    modulation_index_2=1.0,
    modulation_index_4=1.0,
    modulator_ratio_2=1,
    modulator_ratio_3=1,
    modulator_ratio_4=1,
) -> None:
    envelope_1 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_1[0],
            decay_time=adsr_1[1], 
            sustain=adsr_1[2],
            release_time=adsr_1[3],
            curve=curve_1[0],
        ),
        done_action=2,
        gate=gate,
    )

    envelope_2 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_2[0],
            decay_time=adsr_2[1], 
            sustain=adsr_2[2],
            release_time=adsr_2[3],
            curve=curve_2[0],
        ),
        done_action=2,
        gate=gate,
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

    ratio = IRand.ir(minimum=1, maximum=2)
    carrier_ratio=ratio
    modulator_ratio_2=ratio * 4
    modulator_ratio_3=ratio * 2
    modulator_ratio_4=ratio * 8
    
    modulator_4 = SinOsc.ar(frequency=frequency * modulator_ratio_4) * (frequency * modulator_ratio_4) * (envelope_4 * modulation_index_4)
    
    feedback = LocalIn.ar(channel_count=1) * feedback_index
    modulator_3 = SinOsc.ar(frequency=frequency * modulator_ratio_3 + feedback)
    LocalOut.ar(source=modulator_3)

    modulator_3 += modulator_4

    modulator_2 = SinOsc.ar(frequency=frequency * modulator_ratio_2 + modulator_3) * (frequency * modulator_ratio_2) * (envelope_2 * modulation_index_2)

    carrier = SinOsc.ar(frequency=frequency * carrier_ratio + modulator_2 + modulator_4) * envelope_1
    carrier = FreeVerb.ar(source=carrier, mix=0.25, room_size=0.5, damping=0.5)
    pan = Pan2.ar(source=carrier, position=0.0, level=amplitude)
    Out.ar(bus=0, source=pan)

@synthdef()
def algorithm_3(
    adsr_1=(0.01, 0.3, 0.5, 3.0),
    adsr_2=(0.01, 0.3, 0.5, 3.0),
    adsr_3=(0.01, 0.3, 0.5, 3.0),
    amplitude = 0.2,
    carrier_ratio=1, 
    curve=(-4),
    feedback_index=1.0,
    frequency=500, 
    gate=1,
    modulation_index_2=1.0,
    modulation_index_3=1.0,
    modulator_ratio_2=1,
    modulator_ratio_3=1,
    modulator_ratio_4=1,
) -> None:
    envelope_1 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_1[0],
            decay_time=adsr_1[1], 
            sustain=adsr_1[2],
            release_time=adsr_1[3],
            curve=curve[0],
        ),
        done_action=2,
        gate=gate,
    )

    envelope_2 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_2[0],
            decay_time=adsr_2[1], 
            sustain=adsr_2[2],
            release_time=adsr_2[3],
            curve=curve[0],
        ),
        done_action=2,
        gate=gate,
    )

    envelope_3 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_3[0],
            decay_time=adsr_3[1], 
            sustain=adsr_3[2],
            release_time=adsr_3[3],
            curve=curve[0],
        ),
        done_action=2,
        gate=gate,
    )

    modulator_3 = SinOsc.ar(frequency=frequency * modulator_ratio_3) * (frequency * modulator_ratio_3) * (envelope_3 * modulation_index_3)
    modulator_2 = SinOsc.ar(frequency=frequency * modulator_ratio_2 + modulator_3) * (frequency * modulator_ratio_2) * (envelope_2 * modulation_index_2)

    feedback = LocalIn.ar(channel_count=1) * feedback_index
    modulator_4 = SinOsc.ar(frequency=frequency * modulator_ratio_4 + feedback)
    LocalOut.ar(source=modulator_4)
    
    carrier = SinOsc.ar(frequency=frequency * carrier_ratio + modulator_2 + modulator_4) * envelope_1
    
    pan = Pan2.ar(source=carrier, position=0.0, level=amplitude)
    Out.ar(bus=0, source=pan)

@synthdef()
def algorithm_4(
    adsr_1=(0.01, 0.3, 0.5, 3.0),
    adsr_2=(0.01, 0.3, 0.5, 3.0),
    adsr_3=(0.01, 0.3, 0.5, 3.0),
    amplitude = 0.2,
    carrier_ratio=1, 
    curve=(-4),
    feedback_index=1.0,
    frequency=500, 
    gate=1,
    modulation_index_2=1.0,
    modulation_index_3=1.0,
    modulator_ratio_2=1,
    modulator_ratio_3=1,
    modulator_ratio_4=1,
) -> None:
    envelope_1 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_1[0],
            decay_time=adsr_1[1], 
            sustain=adsr_1[2],
            release_time=adsr_1[3],
            curve=curve[0],
        ),
        done_action=2,
        gate=gate,
    )

    envelope_2 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_2[0],
            decay_time=adsr_2[1], 
            sustain=adsr_2[2],
            release_time=adsr_2[3],
            curve=curve[0],
        ),
        done_action=2,
        gate=gate,
    )

    envelope_3 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_3[0],
            decay_time=adsr_3[1], 
            sustain=adsr_3[2],
            release_time=adsr_3[3],
            curve=curve[0],
        ),
        done_action=2,
        gate=gate,
    )


    feedback = LocalIn.ar(channel_count=1) * feedback_index
    modulator_4 = SinOsc.ar(frequency=frequency * modulator_ratio_4 + feedback)
    LocalOut.ar(source=modulator_4)

    modulator_3 = SinOsc.ar(frequency=frequency * modulator_ratio_3 + modulator_4) * (frequency * modulator_ratio_3) * (envelope_3 * modulation_index_3)
    modulator_2 = SinOsc.ar(frequency=frequency * modulator_ratio_2 ) * (frequency * modulator_ratio_2) * (envelope_2 * modulation_index_2)

    carrier = SinOsc.ar(frequency=frequency * carrier_ratio + modulator_2 + modulator_3) * envelope_1
    
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
    curve=(-4),
    feedback_index=1.0,
    frequency=500, 
    gate=1,
    modulation_index_2=1.0,
    modulator_ratio_2=1,
    modulator_ratio_4=1,
) -> None:
    envelope_1 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_1[0],
            decay_time=adsr_1[1], 
            sustain=adsr_1[2],
            release_time=adsr_1[3],
            curve=curve[0],
        ),
        done_action=2,
        gate=gate,
    )

    envelope_2 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_2[0],
            decay_time=adsr_2[1], 
            sustain=adsr_2[2],
            release_time=adsr_2[3],
            curve=curve[0],
        ),
        done_action=2,
        gate=gate,
    )

    envelope_3 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_3[0],
            decay_time=adsr_3[1], 
            sustain=adsr_3[2],
            release_time=adsr_3[3],
            curve=curve[0],
        ),
        done_action=2,
        gate=gate,
    )

    modulator_2 = SinOsc.ar(frequency=frequency * modulator_ratio_2) * (frequency * modulator_ratio_2) * (envelope_2 * modulation_index_2)
    carrier_1 = SinOsc.kr(frequency=frequency * carrier_ratio_1 + modulator_2) * envelope_1

    feedback = LocalIn.ar(channel_count=1) * feedback_index
    modulator_4 = SinOsc.ar(frequency=frequency * modulator_ratio_4 + feedback)
    LocalOut.ar(source=modulator_4)
    
    carrier_3 = SinOsc.ar(frequency=frequency * carrier_ratio_3 + modulator_4) * envelope_3
    output = carrier_3 + carrier_1
    
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
    curve=(-4),
    feedback_index=1.0,
    frequency=500, 
    gate=1,
    modulator_ratio=1, 
) -> None:
    envelope_1 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_1[0],
            decay_time=adsr_1[1], 
            sustain=adsr_1[2],
            release_time=adsr_1[3],
            curve=curve[0],
        ),
        done_action=2,
        gate=gate,
    )

    envelope_2 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_2[0],
            decay_time=adsr_2[1], 
            sustain=adsr_2[2],
            release_time=adsr_2[3],
            curve=curve[0],
        ),
        done_action=2,
        gate=gate,
    )

    envelope_3 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_3[0],
            decay_time=adsr_3[1], 
            sustain=adsr_3[2],
            release_time=adsr_3[3],
            curve=curve[0],
        ),
        done_action=2,
        gate=gate,
    )

    feedback = LocalIn.ar(channel_count=1) * feedback_index
    modulator_4 = SinOsc.ar(frequency=frequency * modulator_ratio + feedback)
    LocalOut.ar(source=modulator_4)

    carrier_1 = SinOsc.ar(frequency=frequency * carrier_ratio_1) * envelope_1
    carrier_2 = SinOsc.ar(frequency=frequency * carrier_ratio_2 + modulator_4) * envelope_2
    
    carrier_3 = SinOsc.ar(frequency=frequency * carrier_ratio_3 + modulator_4) * envelope_3
    output = carrier_1 + carrier_2 + carrier_3
    
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
    curve=(-4),
    feedback_index=1.0,
    frequency=500, 
    gate=1,
    modulator_ratio=1, 
) -> None:
    envelope_1 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_1[0],
            decay_time=adsr_1[1], 
            sustain=adsr_1[2],
            release_time=adsr_1[3],
            curve=curve[0],
        ),
        done_action=2,
        gate=gate,
    )

    envelope_2 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_2[0],
            decay_time=adsr_2[1], 
            sustain=adsr_2[2],
            release_time=adsr_2[3],
            curve=curve[0],
        ),
        done_action=2,
        gate=gate,
    )

    envelope_3 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_3[0],
            decay_time=adsr_3[1], 
            sustain=adsr_3[2],
            release_time=adsr_3[3],
            curve=curve[0],
        ),
        done_action=2,
        gate=gate,
    )

    feedback = LocalIn.ar(channel_count=1) * feedback_index
    modulator_4 = SinOsc.ar(frequency=frequency * modulator_ratio + feedback)
    LocalOut.ar(source=modulator_4)

    carrier_1 = SinOsc.ar(frequency=frequency * carrier_ratio_1) * envelope_1
    carrier_2 = SinOsc.ar(frequency=frequency * carrier_ratio_2) * envelope_2
    carrier_3 = SinOsc.ar(frequency=frequency * carrier_ratio_3 + modulator_4) * envelope_3
    output = carrier_1 + carrier_2 + carrier_3
    
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
    carrier_ratio_4 = ratio * 8 
    feedback_index = IRand.ir(minimum=10000, maximum=15000)

    envelope_1 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_1[0],
            decay_time=adsr_1[1], 
            sustain=adsr_1[2],
            release_time=adsr_1[3],
            curve=curve_1[0],
        ),
        done_action=2,
        gate=gate,
    )

    envelope_2 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_2[0],
            decay_time=adsr_2[1], 
            sustain=adsr_2[2],
            release_time=adsr_2[3],
            curve=curve_2[0],
        ),
        done_action=2,
        gate=gate,
    )

    envelope_3 = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr_3[0],
            decay_time=adsr_3[1], 
            sustain=adsr_3[2],
            release_time=adsr_3[3],
            curve=curve_3[0],
        ),
        done_action=2,
        gate=gate,
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

    carrier_1 = SinOsc.ar(frequency=frequency * carrier_ratio_1) * envelope_1
    carrier_2 = SinOsc.ar(frequency=frequency * carrier_ratio_2) * envelope_2
    carrier_3 = SinOsc.ar(frequency=frequency * carrier_ratio_3) * envelope_3
    
    feedback = LocalIn.ar(channel_count=1) * feedback_index
    carrier_4 = SinOsc.ar(frequency=frequency * carrier_ratio_4 + feedback) * envelope_4
    LocalOut.ar(source=carrier_4)

    output = carrier_1 + carrier_2 + carrier_3 + carrier_4
    
    output = FreeVerb.ar(source=output, mix=0.60, room_size=0.55, damping=0.5)
    output = CombL.ar(
        delay_time=0.2,
        decay_time=5.5,
        maximum_delay_time=0.2, 
        source=output,
    )

    pan = Pan2.ar(source=output, position=0.0, level=amplitude)
    Out.ar(bus=0, source=pan)

def main() -> None:
    server = Server().boot(block_size=1)
    server.add_synthdefs(algorithm_1, algorithm_2, algorithm_8)
    server.sync()

    minor_scale_bass = [0, 3, 10, 7]
    bass_note = 29 # F1
    bass_frequencies = [midi_note_number_to_frequency(n + bass_note) for n in minor_scale_bass]
    bass_sequence = SequencePattern(bass_frequencies, iterations=None)
    bass_pattern = EventPattern(
        frequency=bass_sequence,
        synthdef=algorithm_1,
        delta=0.5, # Half note
        duration=0.5, # Half note
        adsr_1=(0.01, 0.9, 0.0, 0.0),
        adsr_2=(0.01, 0.5, 0.0, 0.0),
        adsr_3=(0.01, 0.5, 0.0, 0.0),
        amplitude=0.05,
        curve_1=(-32),
        curve_2=(-16),
        curve_3=(-8),
        modulation_index_2=RandomPattern(minimum=6.0, maximum=12.0),
        modulation_index_3=RandomPattern(minimum=6.0, maximum=12.0),
    )

    minor_scale_arpeggio = [0, 3, 7, 10, 5, 7, 3]
    arpeggio_note = 41 # F2
    arpeggio_frequencies = [midi_note_number_to_frequency(n + arpeggio_note) for n in minor_scale_arpeggio]
    arpeggio_sequence = SequencePattern(arpeggio_frequencies, iterations=None)
    arpeggio_pattern = EventPattern(
        frequency=arpeggio_sequence,
        synthdef=algorithm_2,
        delta=0.0625, # 16th note
        duration=0.0625, # 16th note
        amplitude=0.09,
        curve_1=(-16),
        curve_2=(-8),
        curve_4=(-4),
        modulation_index_2=RandomPattern(minimum=1.0, maximum=6.0),
        modulation_index_4=RandomPattern(minimum=1.0, maximum=8.0),
    )

    minor_scale_pad = [7, 0, 3, 10]
    pad_note = 53 # F3
    pad_frequencies = [midi_note_number_to_frequency(n + pad_note) for n in minor_scale_pad]
    pad_sequence = SequencePattern(pad_frequencies, iterations=None)
    pad_pattern = EventPattern(
        frequency=pad_sequence,
        synthdef=algorithm_8,
        delta=1.0, # Whole note
        duration=1.0, # Whole note
        adsr_1=(0.01, 0.7, 0.1, 0.5),
        adsr_2=(0.7, 0.6, 0.08, 0.9),
        adsr_3=(0.5, 0.5, 0.05, 1.0),
        adsr_4=(0.3, 0.4, 0.04, 1.3),
        amplitude=0.025,
        curve_1=(16),
        curve_2=(-8),
        curve_3=(4),
        curve_4=(-2),
    )

    clock = Clock()
    clock.start(beats_per_minute=80.0)
    bass_pattern.play(clock=clock, context=server)
    arpeggio_pattern.play(clock=clock, context=server)
    pad_pattern.play(clock=clock, context=server)

    while True:
        continue

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
