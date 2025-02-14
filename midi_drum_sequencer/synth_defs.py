"""A collection of SynthDefs the mimic TR-808 drums.

Adapted to Supriya by me from Yoshinosuke Horiuchi's 
sclang implementation that can be found here for free:
https://www.patreon.com/posts/sc-808-free-40121526

Props to Yoshinosuke Horiuchi for sharing this!

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
    env = EnvGen.kr(envelope=Envelope(amplitudes=[0.11, 1, 0], durations=[0, 30], curves=[-225.0]), done_action=2)
    trienv = EnvGen.kr(envelope=Envelope(amplitudes=[0.11, 0.6, 0], durations=[0, 30], curves=[-230.0]), done_action=0)
    fenv = EnvGen.kr(envelope=Envelope(amplitudes=[56*7, 56*1.35, 56], durations=[0.05, 0.6], curves=[-14.0]))
    pfenv = EnvGen.kr(envelope=Envelope(amplitudes=[56*7, 56*1.35, 56], durations=[0.03, 0.6], curves=[-10.0]))
    
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
    sum = (osc1 + osc2) * atkEnv * amplitude_2
    sig = Pan2.ar(source=(noise + sum) * amplitude * 2.5, position=0.0)
    sig = HPF.ar(source=sig, frequency=340)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def clap_dry(
    amplitude=0.5, 
    out_bus=0,
) -> None:
    atkenv = EnvGen.kr(envelope=Envelope(amplitudes=[0.5,1,0], durations=[0, 0.3], curves=[-160.0]), done_action=2)
    denv = EnvGen.kr(envelope=Envelope.adsr(0, 6, 0, 1, 1, curve=-157), done_action=0)
    atk = WhiteNoise.ar() * atkenv * 1.4
    decay = DelayN.ar(source=WhiteNoise.ar(), maximum_delay_time=0.026, delay_time=0.026) * denv
    sum = atk + decay * amplitude
    sum = HPF.ar(source=sum, frequency=500)
    sum = BPF.ar(source=sum, frequency=1062, reciprocal_of_q=0.5)
    Out.ar(bus=out_bus, source=Pan2.ar(source=sum * 1.5, position=0))

@synthdef()
def low_tom(
    amplitude=0.5, 
    out_bus=0
) -> None:
    env = EnvGen.kr(envelope=Envelope(amplitudes=[0.4, 1, 0], durations=[0, 20], curves=[-250]), done_action=2)
    fenv = EnvGen.kr(envelope=Envelope(amplitudes=[80*1.25, 80*1.125, 80], durations=[0.1, 0.5], curves=[-4.0]))
    sig = SinOsc.ar(frequency=fenv, phase=pi/2) * env
    sig = Pan2.ar(source=sig * amplitude * 3, position=0.0)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def medium_tom(
    amplitude=0.5, 
    out_bus=0
) -> None:
    env = EnvGen.kr(envelope=Envelope(amplitudes=[0.4, 1, 0], durations=[0, 16], curves=[-250.0]), done_action=2)
    fenv = EnvGen.kr(envelope=Envelope(amplitudes=[120*1.33333, 120*1.125, 120], durations=[0.1, 0.5], curves=[-4.0]))
    sig = SinOsc.ar(frequency=fenv, phase=pi/2)
    sig = Pan2.ar(source=sig * env * amplitude * 2, position=0.0)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def high_tom(
    amplitude=0.5, 
    out_bus=0
) -> None:
    env = EnvGen.kr(envelope=Envelope(amplitudes=[0.4, 1, 0], durations=[0, 11], curves=[-250.0]), done_action=2)
    fenv = EnvGen.kr(envelope=Envelope(amplitudes=[165*1.333333, 165*1.121212, 165], durations=[0.1, 0.5], curves=[-4.0]))
    sig = SinOsc.ar(frequency=fenv, phase=pi/2)
    sig = Pan2.ar(source=sig * env * amplitude * 2, position=0.0)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def low_conga(
    amplitude=0.5, 
    out_bus=0
) -> None:
    env = EnvGen.kr(envelope=Envelope(amplitudes=[0.15, 1, 0], durations=[0, 18], curves=[-250.0]), done_action=2)
    fenv = EnvGen.kr(envelope=Envelope(amplitudes=[165*1.333333, 165*1.121212, 165], durations=[0.1, 0.5], curves=[-4.0]))
    sig = SinOsc.ar(frequency=fenv, phase=pi/2) * env
    sig = Pan2.ar(source=sig * amplitude * 3, position=0.0)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def medium_conga(
    amplitude=0.5, 
    out_bus=0
) -> None:
    env = EnvGen.kr(envelope=Envelope(amplitudes=[0.15, 1, 0], durations=[0, 9], curves=[-250.0]), done_action=2)
    fenv = EnvGen.kr(envelope=Envelope(amplitudes=[250*1.24, 250*1.12, 250], durations=[0.1, 0.5], curves=[-4.0]))
    sig = SinOsc.ar(frequency=fenv, phase=pi/2)
    sig = Pan2.ar(source=sig * env * amplitude * 2, position=0)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def high_conga(
    amplitude=0.5, 
    out_bus=0
) -> None:
    env = EnvGen.kr(envelope=Envelope(amplitudes=[0.15, 1, 0], durations=[0, 6], curves=[-250.0]), done_action=2)
    fenv = EnvGen.kr(envelope=Envelope(amplitudes=[370*1.22972, 370*1.08108, 370], durations=[0.1, 0.5], curves=[-4.0]))
    sig = SinOsc.ar(frequency=fenv, phase=pi/2)
    sig = Pan2.ar(source=sig * env * amplitude * 2, position=0.0)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def rim_shot(
    amplitude=0.5, 
    out_bus=0
) -> None:
    env = EnvGen.kr(envelope=Envelope(amplitudes=[1, 1, 0], durations=[0.00272, 0.07], curves=[-42.0]), done_action=2)
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
    env = EnvGen.kr(envelope=Envelope(amplitudes=[1, 1, 0], durations=[0, 0.1], curves=[-20.0]), done_action=2)
    sig = SinOsc.ar(frequency=2500, phase=pi/2) * env * amplitude
    sig = Pan2.ar(source=sig, position=0.0)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def maracas(
    amplitude=0.5, 
    out_bus=0
) -> None:
    env = EnvGen.kr(envelope=Envelope(amplitudes=[0.3, 1, 0], durations=[0.027, 0.07], curves=[-250.0]), done_action=2)
    sig = WhiteNoise.ar() * env * amplitude
    sig = HPF.ar(source=sig, frequency=5500)
    sig = Pan2.ar(source=sig, position=0.0)
    Out.ar(bus=out_bus, source=sig)

@synthdef()
def cow_bell(
    amplitude=0.5, 
    out_bus=0
) -> None:
    atkenv = EnvGen.kr(envelope=Envelope.percussive(0, 1, 1, -215.0), done_action=0)
    env = EnvGen.kr(envelope=Envelope.percussive(0.01, 9.5, 1, -90.0), done_action=2)
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
    env2 = EnvGen.kr(envelope=Envelope(amplitudes=[0, 1, 0], durations=[0, 0.5*5], curves=[-150.0]), done_action=0)
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
    env2 = EnvGen.kr(envelope=Envelope(amplitudes=[0, 0.6, 0], durations=[0.1, 2.0*0.7], curves=[-5.0]), done_action=0)
    env2b = EnvGen.kr(envelope=Envelope(amplitudes=[0, 0.3, 0], durations=[0.1, 2.0*20], curves=[-120.0]), done_action=0)
    env3 = EnvGen.kr(envelope=Envelope(amplitudes=[0, 1, 0], durations=[0, 2.0*5], curves=[-150.0]), done_action=0)

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