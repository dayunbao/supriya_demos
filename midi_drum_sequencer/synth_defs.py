from math import pi

from supriya import Envelope, synthdef
from supriya.ugens import (
    BBandPass,
    BHiPass,
    BHiShelf,
    BLowShelf,
    BPF,
    BPeakEQ, 
    DelayN,
    EnvGen,
    HPF,
    LFTri, 
    LFPulse,
    Limiter,
    LPF,
    Out,
    Pan2,
    SinOsc,
    WhiteNoise, 
)

@synthdef()
def bass_drum(
    amplitude=0.5,
    out_bus=0,
) -> None:
    env = EnvGen.kr(envelope=Envelope(amplitudes=[0.11, 1, 0], durations=[0, 30], curves=-225), done_action=2)
    trienv = EnvGen.kr(envelope=Envelope(amplitudes=[0.11, 0.6, 0], durations=[0, 30], curves=-230), done_action=0)
    fenv = EnvGen.kr(envelope=Envelope(amplitudes=[56*7, 56*1.35, 56], durations=[0.05, 0.6], curves=-14))
    pfenv = EnvGen.kr(envelope=Envelope(amplitudes=[56*7, 56*1.35, 56], durations=[0.03, 0.6], curves=-10))
    
    sig = SinOsc.ar(frequency=fenv, phase=pi/2) * env
    sub = LFTri.ar(frequency=fenv, initial_phase=pi/2) * trienv * 0.05
    punch = SinOsc.ar(frequency=pfenv, phase=pi/2) * env * 2
    punch = HPF.ar(source=punch, frequency=350)
    sig = (sig + sub + punch) * 2.5
    sig = Limiter.ar(source=sig, level=0.5) * amplitude
    sig = Pan2.ar(source=sig, position=0.0)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def snare(
    amplitude=0.5, 
    amplitude_2=0.5,
    out_bus=0,
    snappy=0.3, 
    tone=340.0, 
    tone_2=189.0, 
) -> None:
    noiseEnv = EnvGen.kr(envelope=Envelope.percussive(0.001, 4.2, 1, -115), done_action=2)
    atkEnv = EnvGen.kr(envelope=Envelope.percussive(0.001, 0.8, curve=-95), done_action=0)
    noise = WhiteNoise.ar()
    noise = HPF.ar(source=noise, frequency=1800)
    noise = LPF.ar(source=noise, frequency=8850)
    noise = noise * noiseEnv * snappy
    osc1 = SinOsc.ar(frequency=tone_2, phase=pi/2) * 0.6
    osc2 = SinOsc.ar(frequency=tone, phase=pi/2) * 0.7
    sum = (osc1+osc2) * atkEnv * amplitude_2
    sig = Pan2.ar(source=(noise + sum) * amplitude * 2.5, position=0.0)
    sig = HPF.ar(source=sig, frequency=340)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def clap_dry(
    amplitude=0.5, 
    out_bus=0,
) -> None:
    atkenv = EnvGen.kr(envelope=Envelope(amplitudes=[0.5,1,0],durations=[0, 0.3], curves=-160), done_action=2)
    denv = EnvGen.kr(envelope=Envelope.adsr(0, 6, 0, 1, 1, curve=-157), done_action=0)
    atk = WhiteNoise.ar() * atkenv * 1.4
    decay = DelayN.ar(source=WhiteNoise.ar(), maximum_delay_time=0.026, delay_time=0.026) * denv
    sum = atk + decay * amplitude
    sum = HPF.ar(source=sum, frequency=500)
    sum = BPF.ar(source=sum, frequency=1062, reciprocal_of_q=0.5)
    Out.ar(bus=out_bus, source=Pan2.ar(source=sum * 1.5, position=0))

@synthdef()
def clap_reverb(
    amplitude=0.5, 
    gate=0,
    out_bus=0,
) -> None:
    revgen = EnvGen.kr(envelope=Envelope.percussive(0.1, 4, curve=-9), gate=gate, done_action=2)
    reverb = WhiteNoise.ar() * revgen * 0.02
    reverb = HPF.ar(source=reverb, frequency=500)
    reverb = LPF.ar(source=reverb, frequency=1000)
    Out.ar(bus=out_bus, source=Pan2.ar(source=reverb * amplitude, position=0.0))

@synthdef()
def low_tom(
    amplitude=0.5, 
    out_bus=0
) -> None:
    env = EnvGen.kr(envelope=Envelope([0.4, 1, 0], [0, 20], -250), done_action=2)
    fenv = EnvGen.kr(envelope=Envelope([80*1.25, 80*1.125, 80], [0.1, 0.5], -4))
    sig = SinOsc.ar(frequency=fenv, phase=pi/2) * env
    sig = Pan2.ar(source=sig * amplitude * 3, position=0.0)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def medium_tom(
    amplitude=0.5, 
    out_bus=0
) -> None:
    env = EnvGen.kr(envelope=Envelope([0.4, 1, 0], [0, 16], -250), done_action=2)
    fenv = EnvGen.kr(envelope=Envelope([120*1.33333, 120*1.125, 120], [0.1, 0.5], -4))
    sig = SinOsc.ar(frequency=fenv, phase=pi/2)
    sig = Pan2.ar(source=sig * env * amplitude * 2, position=0.0)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def high_tom(
    amplitude=0.5, 
    out_bus=0
) -> None:
    env = EnvGen.kr(envelope=Envelope([0.4, 1, 0], [0, 11], -250), done_action=2)
    fenv = EnvGen.kr(envelope=Envelope([165*1.333333, 165*1.121212, 165], [0.1, 0.5], -4))
    sig = SinOsc.ar(frequency=fenv, phase=pi/2)
    sig = Pan2.ar(source=sig * env * amplitude * 2, position=0.0)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def low_conga(
    amplitude=0.5, 
    out_bus=0
) -> None:
    env = EnvGen.kr(envelope=Envelope([0.15, 1, 0], [0, 18], -250), done_action=2)
    fenv = EnvGen.kr(envelope=Envelope([165*1.333333, 165*1.121212, 165], [0.1, 0.5], -4))
    sig = SinOsc.ar(frequency=fenv, phase=pi/2) * env
    sig = Pan2.ar(source=sig * amplitude * 3, position=0.0)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def medium_conga(
    amplitude=0.5, 
    out_bus=0
) -> None:
    env = EnvGen.kr(envelope=Envelope([0.15, 1, 0], [0, 9], -250), done_action=2)
    fenv = EnvGen.kr(envelope=Envelope([250*1.24, 250*1.12, 250], [0.1, 0.5], -4))
    sig = SinOsc.ar(frequency=fenv, phase=pi/2)
    sig = Pan2.ar(source=sig * env * amplitude * 2, position=0)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def high_conga(
    amplitude=0.5, 
    out_bus=0
) -> None:
    env = EnvGen.kr(envelope=Envelope([0.15, 1, 0], [0, 6], -250), done_action=2)
    fenv = EnvGen.kr(envelope=Envelope([370*1.22972, 370*1.08108, 370], [0.1, 0.5], -4))
    sig = SinOsc.ar(frequency=fenv, phase=pi/2)
    sig = Pan2.ar(source=sig * env * amplitude * 2, position=0.0)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def rim_shot(
    amplitude=0.5, 
    out_bus=0
) -> None:
    env = EnvGen.kr(envelope=Envelope([1, 1, 0], [0.00272, 0.07], -42), done_action=2)
    tri1 = LFTri.ar(frequency=1667 * 1.1, initial_phase=1) * env
    tri2 = LFPulse.ar(frequency=455 * 1.1, width=0.8) * env
    punch = WhiteNoise.ar() * env * 0.46
    sig = tri1 + tri2 + punch
    sig = BPeakEQ.ar(source=sig, frequency=464, reciprocal_of_q=0.44, gain=8)
    sig = HPF.ar(source=sig, frequency=315)
    sig = LPF.ar(source=sig, frequency=7300)
    sig = Pan2.ar(source=sig * amplitude, position=0.0)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def claves(
    amplitude=0.5, 
    out_bus=0
) -> None:
    env = EnvGen.kr(envelope=Envelope([1, 1, 0], [0, 0.1], -20), done_action=2)
    sig = SinOsc.ar(frequency=2500, phase=pi/2) * env * amplitude
    sig = Pan2.ar(source=sig, position=0.0)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def maracas(
    amplitude=0.5, 
    out_bus=0
) -> None:
    env = EnvGen.kr(envelope=Envelope([0.3, 1, 0], [0.027, 0.07], -250), done_action=2)
    sig = WhiteNoise.ar() * env * amplitude
    sig = HPF.ar(source=sig, frequency=5500)
    sig = Pan2.ar(source=sig, position=0.0)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def cow_bell(
    amplitude=0.5, 
    out_bus=0
) -> None:
    atkenv = EnvGen.kr(envelope=Envelope.percussive(0, 1, 1, -215), done_action=0)
    env = EnvGen.kr(envelope=Envelope.percussive(0.01, 9.5, 1, -90), done_action=2)
    pul1 = LFPulse.ar(frequency=811.16)
    pul2 = LFPulse.ar(frequency=538.75)
    atk = (pul1 + pul2) * atkenv * 6
    datk = (pul1 + pul2) * env
    sig = (atk + datk) * amplitude
    sig = HPF.ar(source=sig, frequency=250)
    sig = LPF.ar(source=sig, frequency=4500)
    sig = Pan2.ar(source=sig, position=0.0)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def closed_high_hat(
    amplitude=0.5, 
    out_bus=0,
    pan=0.0,
) -> None:
    env = EnvGen.kr(envelope=Envelope.percussive(0.005, 0.42, 1, -30), done_action=2)
    osc1 = LFPulse.ar(frequency=203.52)
    osc2 = LFPulse.ar(frequency=366.31)
    osc3 = LFPulse.ar(frequency=301.77)
    osc4 = LFPulse.ar(frequency=518.19)
    osc5 = LFPulse.ar(frequency=811.16)
    osc6 = LFPulse.ar(frequency=538.75)
    sighi = osc1 + osc2 + osc3 + osc4 + osc5 + osc6
    siglow = osc1 + osc2 + osc3 + osc4 + osc5 + osc6
    sighi = BPF.ar(source=sighi, frequency=8900, reciprocal_of_q=1)
    sighi = HPF.ar(source=sighi, frequency=9000)
    siglow = BBandPass.ar(source=siglow, frequency=8900, bandwidth=0.8)
    siglow = BHiPass.ar(source=siglow, frequency=9000, reciprocal_of_q=0.3)
    sig = BPeakEQ.ar(source=(siglow+sighi), frequency=9700, reciprocal_of_q=0.8, gain=0.7)
    sig = sig * env * amplitude
    sig = Pan2.ar(source=sig, position=pan)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def open_high_hat(
    amplitude=0.5,
    out_bus=0,
) -> None:
    env1 = EnvGen.kr(envelope=Envelope.percussive(0.1, 0.5, curve=-3), done_action=2)
    env2 = EnvGen.kr(envelope=Envelope([0, 1, 0], [0, 0.5*5], curves=-150), done_action=0)
    osc1 = LFPulse.ar(frequency=203.52) * 0.6
    osc2 = LFPulse.ar(frequency=366.31) * 0.6
    osc3 = LFPulse.ar(frequency=301.77) * 0.6
    osc4 = LFPulse.ar(frequency=518.19) * 0.6
    osc5 = LFPulse.ar(frequency=811.16) * 0.6
    osc6 = LFPulse.ar(frequency=538.75) * 0.6
    sig = osc1 + osc2 + osc3 + osc4 + osc5 +osc6
    sig = BLowShelf.ar(source=sig, frequency=990, reciprocal_of_s=2, gain=-3)
    sig = BPF.ar(source=sig, frequency=7700)
    sig = BPeakEQ.ar(source=sig, frequency=7200, reciprocal_of_q=0.5, gain=5)
    sig = BHiPass.ar(source=sig, frequency=8100, reciprocal_of_q=0.7)
    sig = BHiShelf.ar(source=sig, frequency=9400, reciprocal_of_s=1, gain=5)
    siga = sig * env1 * 0.6
    sigb = sig * env2
    sum = siga + sigb
    sum = LPF.ar(source=sum, frequency=4000)
    sum = Pan2.ar(source=sum, position=0.0)
    sum = sum * amplitude * 2
    Out.ar(bus=out_bus, source=sum)

@synthdef()
def cymbal(
    amplitude=0.5, 
    out_bus=0,
    tone=0.002,
) -> None:
    env1 = EnvGen.kr(envelope=Envelope.percussive(0.3, 2.0, curve=-3), done_action=2)
    env2 = EnvGen.kr(envelope=Envelope([0, 0.6, 0], [0.1, 2.0*0.7], -5), done_action=0)
    env2b = EnvGen.kr(envelope=Envelope([0, 0.3, 0], [0.1, 2.0*20], -120), done_action=0)
    env3 = EnvGen.kr(envelope=Envelope([0, 1, 0], [0, 2.0*5], curves=-150), done_action=0)

    osc1 = LFPulse.ar(frequency=203.52) * 0.6
    osc2 = LFPulse.ar(frequency=366.31) * 0.6
    osc3 = LFPulse.ar(frequency=301.77) * 0.6
    osc4 = LFPulse.ar(frequency=518.19) * 0.6
    osc5 = LFPulse.ar(frequency=811.16) * 0.6
    osc6 = LFPulse.ar(frequency=538.75) * 0.6
    sig = osc1 + osc2 + osc3 + osc4 + osc5 +osc6
    sig1 = BLowShelf.ar(source=sig, frequency=2000, reciprocal_of_s=1, gain=5)
    sig1 = BPF.ar(source=sig1, frequency=3000)
    sig1 = BPeakEQ.ar(source=sig1, frequency=2400, reciprocal_of_q=0.5, gain=5)
    sig1 = BHiPass.ar(source=sig1, frequency=1550, reciprocal_of_q=0.7)
    sig1 = LPF.ar(source=sig1, frequency=3000)
    sig1 = BLowShelf.ar(source=sig1, frequency=1000, reciprocal_of_s=1, gain=0)
    sig1 = sig1 * env1 * tone
    sig2 = BLowShelf.ar(source=sig, frequency=990, reciprocal_of_s=2, gain=-5)
    sig2 = BPF.ar(source=sig2, frequency=7400)
    sig2 = BPeakEQ.ar(source=sig2, frequency=7200, reciprocal_of_q=0.5, gain=5)
    sig2 = BHiPass.ar(source=sig2, frequency=6800, reciprocal_of_q=0.7)
    sig2 = BHiShelf.ar(source=sig2, frequency=10000, reciprocal_of_s=1, gain=-4)
    sig2a = sig2 * env2 * 0.3
    sig2b = sig2 * env2b * 0.6
    sig3 = BLowShelf.ar(source=sig, frequency=990, reciprocal_of_s=2, gain=-15)
    sig3 = BPF.ar(source=sig3, frequency=6500)
    sig3 = BPeakEQ.ar(source=sig3, frequency=7400, reciprocal_of_q=0.35, gain=10)
    sig3 = BHiPass.ar(source=sig3, frequency=10500, reciprocal_of_q=0.8)
    sig3 = sig3 * env3
    sum = sig1 + sig2a + sig2b + sig3
    sum = LPF.ar(source=sum, frequency=4000)
    sum = Pan2.ar(source=sum, position=0.0)
    sum = sum * amplitude
    Out.ar(bus=out_bus, source=sum)