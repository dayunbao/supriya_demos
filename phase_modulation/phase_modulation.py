import sys
from math import pi

from supriya import Server, synthdef
from supriya.clocks import Clock
from supriya.conversions import midi_note_number_to_frequency
from supriya.patterns import EventPattern, RandomPattern, SequencePattern
from supriya.ugens import (
    Envelope,
    EnvGen,
    Out, 
    Pan2,
    SinOsc,
)
from supriya.ugens.filters import OnePole
from supriya.ugens.info import SampleDur, SampleRate
from supriya.ugens.inout import LocalIn, LocalOut
from supriya.ugens.lines import DC
from supriya.ugens.noise import IRand
from supriya.ugens.triggers import Phasor


TWO_PI = 2 * pi

@synthdef()
def phase_modulation_operator(
    amplitude=0.2,
    carrier_adsr=(0.01, 0.3, 0.5, 3.0),
    carrier_curve=(-4),
    carrier_frequency=440,
    carrier_phase_index=1.0,
    carrier_ratio=1,
    gate=1,
    modulator_adsr=(0.01, 0.3, 0.5, 3.0),
    modulator_curve=(-4),
    modulator_ratio=1,
    modulator_phase_index=1.0,
):
    carrier_envelope = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=carrier_adsr[0],
            decay_time=carrier_adsr[1], 
            sustain=carrier_adsr[2],
            release_time=carrier_adsr[3],
            curve=carrier_curve[0],
        ),
        done_action=2,
        gate=gate,
    )

    modulator_envelope = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=modulator_adsr[0],
            decay_time=modulator_adsr[1], 
            sustain=modulator_adsr[2],
            release_time=modulator_adsr[3],
            curve=modulator_curve[0],
        ),
        done_action=2,
        gate=gate,
    )
    ratio = IRand.ir(minimum=1, maximum=3)
    carrier_ratio = ratio
    modulator_ratio = ratio * 2

    modulator_frequency = carrier_frequency * modulator_ratio
    carrier_frequency *= carrier_ratio

    # Modulator
    phase = Phasor.ar(trigger=0, rate=modulator_frequency * SampleDur.ir())
    modulator = SinOsc.ar(frequency=DC.ar(source=0), phase=phase) / (TWO_PI * modulator_phase_index) * modulator_envelope

    nyquist = SampleRate.ir() / 2
    clipped_frequency = modulator_frequency.clip(-nyquist, nyquist)
    slope = abs(clipped_frequency) * SampleDur.ir()
    modulator = OnePole.ar(source=modulator, coefficient=(-TWO_PI * slope).exponential())
    
    # carrier
    phase = Phasor.ar(trigger=0, rate=carrier_frequency * SampleDur.ir())
    carrier = SinOsc.ar(frequency=DC.ar(source=0), phase=(phase + modulator) * TWO_PI * carrier_phase_index) * carrier_envelope

    pan = Pan2.ar(source=carrier, position=0.0, level=amplitude)
    Out.ar(bus=0, source=pan)

@synthdef()
def feedback_phase_modulation_operator(
    adsr=(0.01, 0.3, 0.5, 3.0),
    amplitude=0.2,
    curve=(-4),
    frequency=440,
    feedback_index=1.0,
    gate=1,
):
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

    feedback = LocalIn.ar(channel_count=1) * feedback_index

    # OnePole
    nyquist = SampleRate.ir() / 2
    clipped_frequency = frequency.clip(-nyquist, nyquist)
    slope = abs(clipped_frequency) * SampleDur.ir()
    modulator = OnePole.ar(source=feedback, coefficient=(-TWO_PI * slope).exponential())

    # Operator PM
    phase = Phasor.ar(trigger=0, rate=frequency * SampleDur.ir())
    signal = SinOsc.ar(frequency=DC.ar(source=0), phase=(phase + modulator) * TWO_PI)
    LocalOut.ar(source=signal)

    signal *= envelope

    pan = Pan2.ar(source=signal, position=0.0, level=amplitude)
    Out.ar(bus=0, source=pan)

def main() -> None:
    server = Server().boot(block_size=1)
    server.add_synthdefs(feedback_phase_modulation_operator, phase_modulation_operator)
    server.sync()

    minor_scale_arpeggio = [0, 3, 7, 10, 5, 7, 3]
    arpeggio_note = 51
    arpeggio_frequencies = [midi_note_number_to_frequency(n + arpeggio_note) for n in minor_scale_arpeggio]
    arpeggio_sequence = SequencePattern(arpeggio_frequencies, iterations=None)
    # arpeggio_pattern = EventPattern(
    #     frequency=arpeggio_sequence,
    #     synthdef=feedback_phase_modulation_operator,
    #     delta=0.0625, # 16th note
    #     duration=0.0625, # 16th note
    #     adsr_1=(0.01, 0.3, 0.1, 0.0),
    #     amplitude=0.03,
    #     # curve_1=(-16),
    #     feedback_index=5.0,
    # )

    arpeggio_pattern = EventPattern(
        carrier_frequency=arpeggio_sequence,
        synthdef=phase_modulation_operator,
        delta=0.0625, # 16th note
        duration=0.0625, # 16th note
        amplitude=0.03,
        carrier_adsr=(0.01, 0.3, 0.1, 0.1),
        carrier_curve=(-4),
        carrier_phase_index=RandomPattern(minimum=6.0, maximum=12.0),
        # modulator_adsr=(0.01, 0.1, 0.0, 0.01),
        modulator_curve=(-4),
        modulator_phase_index=RandomPattern(minimum=2.0, maximum=12.0),
    )

    clock = Clock()
    clock.start(beats_per_minute=80.0)
    arpeggio_pattern.play(clock=clock, context=server)

    while True:
        continue

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)