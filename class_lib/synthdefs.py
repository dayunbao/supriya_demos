from supriya import synthdef
from supriya.ugens import (
    BPeakEQ,
    CombL,
    FreeVerb,
    In,
    Limiter, 
    Out,
    Pan2,
)
from supriya.ugens.diskio import DiskOut

@synthdef()
def audio_to_disk(in_bus, buffer_number):
    input = In.ar(bus=in_bus, channel_count=2)
    DiskOut.ar(buffer_id=buffer_number, source=input)

@synthdef()
def delay(
    in_bus: 2, 
    maximum_delay_time: 0.2, 
    delay_time: 0.2, 
    decay_time: 1.0,
    out_bus: 0
):
    signal = In.ar(bus=in_bus, channel_count=2)
    signal = CombL.ar(
        delay_time=delay_time,
        decay_time = decay_time,
        maximum_delay_time=maximum_delay_time, 
        source=signal
    )
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def gain(in_bus=2, amplitude=1.0, out_bus=0):
    signal = In.ar(bus=in_bus, channel_count=2)
    signal *= amplitude
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def main_audio_output(amplitude=1.0, in_bus=2, out_bus=0):
    """For the final signal that goes to the speakers."""
    signal = In.ar(bus=in_bus, channel_count=2)
    # signal = Limiter.ar(duration=0.005, level=1.0, source=signal)
    signal *= amplitude
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def pan(in_bus=2, out_bus=0, pan_position=0.0):
    signal = In.ar(bus=in_bus, channel_count=2)
    signal = Pan2.ar(level=1.0, position=pan_position, source=signal)
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def parametric_equalizer(frequency=1200, gain=0, in_bus=2, out_bus=0, resonance=1.0):
    signal = In.ar(bus=in_bus, channel_count=2)
    signal = BPeakEQ.ar(frequency=frequency, gain=gain, reciprocal_of_q=resonance, source=signal)
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def reverb(
    in_bus=2,
    mix=0.33,
    room_size=0.5,
    damping=0.5,
    out_bus=0,
):
    signal = In.ar(bus=in_bus, channel_count=2)
    signal = FreeVerb.ar(source=signal, mix=mix, room_size=room_size, damping=damping)
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def routing(in_bus=2, out_bus=0):
    """Only used to capture and route a signal with no processing."""
    signal = In.ar(bus=in_bus, channel_count=2)
    Out.ar(bus=out_bus, source=signal)