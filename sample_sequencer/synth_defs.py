from supriya import synthdef
from supriya.enums import EnvelopeShape
from supriya.ugens import Envelope, EnvGen, Limiter, Out, PlayBuf, Pulse, RLPF, Saw, Select

@synthdef()
def drum_sample(drum_buff):
    signal = PlayBuf.ar(buffer_id=drum_buff, channel_count=1, done_action=2)
    signal = Limiter.ar(duration=0.01, level=0.5, source=signal)
    Out.ar(bus=0, source=signal)

@synthdef()
def three_o_three(
    cut_off=100,
    decay=1.0,
    envelope=1000,
    frequency=440.0,
    gate=0,
    out=0,
    resonance=0.2,
    sustain=0,
    oscillator_num=0,
):
    """Adapted from https://sccode.org/1-4Wy"""
    volume_envelope =  EnvGen.ar(
        envelope=Envelope(
            amplitudes=[10e-10, 1, 1, 10e-10], 
            durations=[0.01, sustain, decay], 
            curves=[EnvelopeShape.EXPONENTIAL, EnvelopeShape.EXPONENTIAL]
        ), 
        gate=gate,
    )
    filter_envelope =  EnvGen.ar(
        envelope=Envelope(
            amplitudes=[10e-10, 1, 10e-10], 
            durations=[0.01, decay], 
            curves=[EnvelopeShape.EXPONENTIAL, EnvelopeShape.EXPONENTIAL]
        ), 
        gate=gate,
    )
    oscillators = [Saw.ar(frequency=frequency), Pulse.ar(frequency=frequency, width=0.5)]
    signal = Select.ar(selector=oscillator_num, sources=oscillators)
    signal *= volume_envelope
    signal = RLPF.ar(source=signal, frequency=cut_off+(filter_envelope*envelope), reciprocal_of_q=resonance)
    signal = Limiter.ar(duration=0.01, level=0.5, source=signal)
    Out.ar(bus=out, source=signal)