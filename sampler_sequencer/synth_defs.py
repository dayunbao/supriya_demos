from supriya import synthdef
from supriya.ugens import (
    Decay2, 
    Envelope, 
    EnvGen, 
    HPF,
    Lag, 
    LagUD, 
    LeakDC,
    LFDNoise3, 
    LFSaw, 
    Limiter, 
    LPF, 
    Out,
    PlayBuf, 
    RLPF,
)

@synthdef()
def sample_player(drum_buff):
    signal = PlayBuf.ar(buffer_id=drum_buff, channel_count=1, done_action=2)
    signal = Limiter.ar(duration=0.01, level=0.5, source=signal)
    Out.ar(bus=0, source=signal)

@synthdef()
def sp_303(
    frequency=440.0, 
    cutoff=5000, 
    resonance=0.5, 
    decay=0.1, 
    # env_mod=1.0, 
    gate=1,
):
    saw_pulse_mix = 0.1 # 0-1, mix between saw and pulse
    lag_frequency = LagUD.ar(source=frequency, lag_time_up=0.39, lag_time_down=0.09)
    lag_frequency *= LFDNoise3.ar(frequency=0.3) * 0.0156 + 1
    signal = LFSaw.ar(frequency=lag_frequency, initial_phase=0.5 + (saw_pulse_mix ** 4 * 550)).softclip()
    ampComp = (1.05 - saw_pulse_mix) ** 6 + 1
    signal *= 0.9 * ampComp * (LFDNoise3.ar(frequency=0.5) * 0.04 + 1)
    adsr = Envelope.adsr(decay_time=decay)
    envelope = EnvGen.ar(envelope=adsr, gate=gate, done_action=2)
    signal = RLPF.ar(source=signal, frequency=cutoff + (15000 - cutoff), reciprocal_of_q=resonance)
    signal = LeakDC.ar(source=signal, coefficient=0.995)
    signal += (HPF.ar(source=signal, frequency=400).softclip() * 10 * 0.04)
    # signal *= Lag.ar(source=gate, lag_time=0.001)
    signal *= envelope
    signal = Limiter.ar(duration=0.01, level=0.5, source=signal)
    Out.ar(bus=0, source=signal)

# @synthdef()
# def three_o_three(
#     cut_off=100,
#     decay=1.0,
#     envelope=1000,
#     frequency=440.0,
#     gate=0,
#     out=0,
#     resonance=0.2,
#     sustain=0,
#     oscillator_num=0,
# ):
#     """Adapted from https://sccode.org/1-4Wy"""
#     volume_envelope =  EnvGen.ar(
#         envelope=Envelope(
#             amplitudes=[10e-10, 1, 1, 10e-10], 
#             durations=[0.01, sustain, decay], 
#             curves=[EnvelopeShape.EXPONENTIAL, EnvelopeShape.EXPONENTIAL]
#         ), 
#         gate=gate,
#     )
#     filter_envelope =  EnvGen.ar(
#         envelope=Envelope(
#             amplitudes=[10e-10, 1, 10e-10], 
#             durations=[0.01, decay], 
#             curves=[EnvelopeShape.EXPONENTIAL, EnvelopeShape.EXPONENTIAL]
#         ), 
#         gate=gate,
#     )
#     oscillators = [Saw.ar(frequency=frequency), Pulse.ar(frequency=frequency, width=0.5)]
#     signal = Select.ar(selector=oscillator_num, sources=oscillators)
#     signal *= volume_envelope
#     signal = RLPF.ar(source=signal, frequency=cut_off+(filter_envelope*envelope), reciprocal_of_q=resonance)
#     signal = Limiter.ar(duration=0.01, level=0.5, source=signal)
#     Out.ar(bus=out, source=signal)
