from supriya import Envelope, synthdef
from supriya.ugens import CombL, EnvGen, FreeVerb, In, Limiter, LFSaw, Out


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
def saw(frequency=440.0, amplitude=0.5, gate=1, out_bus=0) -> None:
    """Create a SynthDef.  SynthDefs are used to create Synth instances
    that play the notes.

    WARNING: It is very easy to end up with a volume MUCH higher than
    intended when using SuperCollider.  I've attempted to help with
    this by adding a Limiter UGen to this SynthDef.  Depending on your
    OS, audio hardware, and possibly a few other factors, this might
    set the volume too low to be heard.  If so, first adjust the Limiter's
    `level` argument, then adjust the SynthDef's `amplitude` argument.
    NEVER set the `level` to anything higher than 1.  YOU'VE BEEN WARNED!

    Args:
        frequency: the frequency in hertz of a note.
        amplitude: the volume.
        gate: an int, 1 or 0, that controls the envelope.
    """
    signal = LFSaw.ar(frequency=[frequency, frequency - 2])
    signal *= amplitude
    signal = Limiter.ar(duration=0.01, level=0.1, source=signal)

    adsr = Envelope.adsr()
    env = EnvGen.kr(envelope=adsr, gate=gate, done_action=2)
    signal *= env

    Out.ar(bus=out_bus, source=signal)