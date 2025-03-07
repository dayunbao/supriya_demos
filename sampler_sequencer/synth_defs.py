"""
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
from supriya import synthdef
from supriya.ugens import (
    FreeVerb,
    In,
    Limiter, 
    LPF,
    Out,
    Pan2,
    PlayBuf,
    ReplaceOut,
)
from supriya.ugens.diskio import DiskOut

@synthdef()
def audio_to_disk(in_bus, buffer_number):
    input = In.ar(bus=in_bus, channel_count=2)
    DiskOut.ar(buffer_id=buffer_number, source=input)

@synthdef()
def gain(in_bus=2, amplitude=1.0, out_bus=0):
    signal = In.ar(bus=in_bus)
    signal *= amplitude
    ReplaceOut.ar(bus=out_bus, source=signal)

@synthdef()
def lpf(frequency=440.0, in_bus=2, out_bus=0):
    signal = In.ar(bus=in_bus)
    signal = LPF.ar(frequency=frequency, source=signal)
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def main_audio_output(in_bus=2, out_bus=0):
    """For the final signal that goes to the speakers."""
    signal = In.ar(bus=in_bus, channel_count=2)
    signal = Limiter.ar(duration=0.01, level=0.5, source=signal)
    ReplaceOut.ar(bus=out_bus, source=signal)

@synthdef()
def pan(in_bus=2, out_bus=0, pan_position=0.0):
    signal = In.ar(bus=in_bus)
    signal = Pan2.ar(level=1.0, position=pan_position, source=signal)
    ReplaceOut.ar(bus=out_bus, source=signal)

@synthdef()
def reverb(
    in_bus=2,
    mix=0.33,
    room_size=0.5,
    damping=0.5,
    out_bus=0,
):
    signal = In.ar(bus=in_bus)
    signal = FreeVerb.ar(source=signal, mix=mix, room_size=room_size, damping=damping)
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def sample_player(buffer, out_bus):
    signal = PlayBuf.ar(buffer_id=buffer, channel_count=1, done_action=2)
    Out.ar(bus=out_bus, source=signal)
