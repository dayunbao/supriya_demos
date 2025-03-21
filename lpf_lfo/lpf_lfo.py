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

import sys
from math import pi

from supriya import AddAction, Bus, Envelope, Server, synthdef
from supriya.ugens import (
    EnvGen, 
    FreeVerb,
    In, 
    LFSaw, 
    Limiter, 
    LinExp, 
    Out, 
    Pan2, 
    ReplaceOut, 
    RLPF, 
    SinOsc,
)

@synthdef()
def filter(in_bus=2, lfo_rate=1, resonance=0.05, out_bus=0) -> None:
    signal = In.ar(bus=in_bus, channel_count=2)
    # A sine wave LFO. 
    # Setting phase to 1.5 * pi starts it from the bottom of the sine wave.
    mod_signal = SinOsc.ar(frequency=lfo_rate, phase=(1.5 * pi))
    # Convert output to frequency range.
    mod_freq = LinExp.ar(
        input_minimum=-1.0, 
        input_maximum=1.0, 
        output_minimum=100, 
        output_maximum=4000,
        source=mod_signal,
    )
    signal = RLPF.ar(frequency=mod_freq, reciprocal_of_q=resonance, source=signal)
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def reverb(
    in_bus=2,
    mix=0.33,
    room_size=0.5,
    damping=0.5,
    out_bus=0,
) -> None:
    signal = In.ar(bus=in_bus)
    signal = FreeVerb.ar(source=signal, mix=mix, room_size=room_size, damping=damping)
    signal = Pan2.ar(source=signal, position=0.0)
    signal = Limiter.ar(duration=0.01, level=0.1, source=signal)
    ReplaceOut.ar(bus=out_bus, source=signal)

@synthdef()
def saw(frequency=440.0, amplitude=0.5, gate=1, out_bus=0) -> None:
    signal = LFSaw.ar(frequency=frequency)
    signal *= amplitude
    adsr = Envelope.adsr()
    env = EnvGen.kr(envelope=adsr, gate=gate, done_action=2)
    signal *= env
    Out.ar(bus=out_bus, source=signal)


def main() -> None:
    server = Server().boot()
    server.add_synthdefs(filter, reverb, saw)
    server.sync()
    # Create buses to route audio between UGens.
    filter_bus: Bus = server.add_bus(calculation_rate='audio')
    reverb_bus: Bus = server.add_bus(calculation_rate='audio')
    
    # Add Synths in the correct order.  First the sound producer,
    # then the sound consumers.
    server.add_synth(
        frequency=43.654,
        out_bus=filter_bus,
        synthdef=saw,
    )
    # Apply filter before reverb.
    server.add_synth(
        add_action=AddAction.ADD_TO_TAIL,
        in_bus=filter_bus,
        lfo_rate=0.1,
        out_bus=reverb_bus,
        resonance=0.01,
        synthdef=filter,
    )
    # Add some reverb to sweeten up the sound a bit.
    server.add_synth(
        add_action=AddAction.ADD_TO_TAIL,
        damping=0.1,
        in_bus=reverb_bus,
        mix=0.5,
        room_size=0.6,
        synthdef=reverb,
    )

    # Loop infinitely.
    while True:
        continue

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)