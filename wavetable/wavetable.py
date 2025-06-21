"""A script demonstrating wavetable synthesis.

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
import random
import sys
from math import pi

from supriya import (
    AddAction, 
    Buffer, 
    BufferGroup, 
    Bus, 
    Envelope, 
    Server, 
    synthdef, 
    UGenOperable
)
from supriya.clocks import Clock
from supriya.conversions import midi_note_number_to_frequency
from supriya.enums import EnvelopeShape
from supriya.patterns import EventPattern, SequencePattern
from supriya.patterns.structure import ParallelPattern
from supriya.ugens import (
    CombL,
    Envelope,
    EnvGen,
    FreeVerb,
    In,
    Out, 
    Pan2,
)
from supriya.ugens.core import UGenRecursiveInput
from supriya.ugens.filters import LeakDC, RLPF
from supriya.ugens.noise import LFNoise1
from supriya.ugens.osc import COsc, Osc, VOsc

# SynthDefs
@synthdef()
def delay(in_bus=2, out_bus=0) -> None:
    input = In.ar(bus=in_bus, channel_count=2)
    
    signal = CombL.ar(
        delay_time=0.2,
        decay_time=2.5,
        maximum_delay_time=0.2, 
        source=input
    )
    
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def reverb(in_bus=2, out_bus=0) -> None:
    input = In.ar(bus=in_bus, channel_count=2)
    
    signal= FreeVerb.ar(source=input, mix=0.55, room_size=0.95, damping=0.5)
    
    Out.ar(bus=out_bus, source=signal)

def modulating_phase_wavetable(
    buffer_id: UGenRecursiveInput, 
    frequency: UGenRecursiveInput, 
    modulate_phase: UGenRecursiveInput
) -> UGenOperable:
    """A helper function that makes it possible to modulate the phase of the Osc based on a condition.
    This was done since using a conditional in a SynthDef is tricky.

    The SynthDef requires this to be defined before it.
    """
    if modulate_phase:
        return Osc.ar(
            buffer_id=buffer_id, 
            frequency=frequency, 
            initial_phase=LFNoise1.ar(frequency=1).scale(
                input_minimum=-1.0,
                input_maximum=1.0,
                output_minimum=-(8*pi),
                output_maximum=(8*pi),
            ))
    
    return Osc.ar(buffer_id=buffer_id, frequency=frequency)

@synthdef()
def wavetable_osc(
    buffer_id, 
    adsr=(0.01, 0.3, 0.5, 1.0),
    amplitude=1.0, 
    frequency=440.0, 
    gate=1,
    modulate_phase=False,
    out_bus=0,
) -> None:
    signal = modulating_phase_wavetable(buffer_id=buffer_id, frequency=frequency, modulate_phase=modulate_phase)
    
    # Make sure the signal doesn't have any DC bias.
    signal = LeakDC.ar(source=signal)
    
    envelope = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr[0],
            decay_time=adsr[1],
            sustain=adsr[2],
            release_time=adsr[3],
        ), 
        done_action=2,
        gate=gate,
    )
    
    signal *= envelope
    signal = Pan2.ar(source=signal, level=amplitude)
    
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def wavetable_cosc(
    buffer_id, 
    adsr=(0.01, 0.3, 0.5, 1.0),
    amplitude=1.0, 
    frequency=440.0,
    gate=1,
    out_bus=0,
) -> None:
    signal = COsc.ar(
        buffer_id=buffer_id, 
        frequency=frequency, 
        beats=0.1,
    )
    
    # Make sure the signal doesn't have any DC bias.
    signal = LeakDC.ar(source=signal)
    
    envelope = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=adsr[0],
            decay_time=adsr[1],
            sustain=adsr[2],
            release_time=adsr[3],
        ), 
        done_action=2, 
        gate=gate
    )
    
    signal *= envelope
    signal = Pan2.ar(source=signal, level=amplitude)
    
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def variable_wavetable(
    buf_start_num, 
    num_buffs, 
    amplitude_adsr=(0.01, 0.3, 0.5, 1.0),
    amplitude=1.0,
    cutoff=400,
    frequency=440.0, 
    gate=1,
    out_bus=0,
) -> None:
    signal = VOsc.ar(
        buffer_id=LFNoise1.ar(frequency=1).scale(
            input_minimum=-1.0,
            input_maximum=1.0,
            output_minimum=buf_start_num,
            output_maximum=num_buffs - 1,
        ), 
        frequency=frequency, 
        phase=LFNoise1.ar(frequency=0.3).scale(
            input_minimum=-1.0,
            input_maximum=1.0,
            output_minimum=-(8*pi),
            output_maximum=(8*pi),
        )
    )

    # Make sure the signal doesn't have any DC bias.
    signal = LeakDC.ar(source=signal)
    
    # An envelope to control the resonant low-pass filter's frequency_cutoff.
    filter_envelope = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=1.0,
            decay_time=0.5,
            sustain=0.5,
            release_time=0.3,
        ), 
    )

    # Apply the envelope to the cutoff frequency.
    # Taken from https://scsynth.org/t/modulate-an-lpf-freq-cutoff-using-an-envelope-or-lfo/5098/2.
    signal = RLPF.ar(
        source=signal, 
        frequency=cutoff + filter_envelope.scale(
            input_minimum=0.0,
            input_maximum=1.0,
            output_minimum=0,
            output_maximum=800,
        ), 
        reciprocal_of_q=0.1,
    )
    
    amplitude_envelope = EnvGen.kr(
        envelope=Envelope.adsr(
            attack_time=amplitude_adsr[0],
            decay_time=amplitude_adsr[1],
            sustain=amplitude_adsr[2],
            release_time=amplitude_adsr[3],
        ), 
        done_action=2, 
        gate=gate
    )

    signal *= amplitude_envelope
    signal = Pan2.ar(source=signal, level=amplitude)
    
    Out.ar(bus=out_bus, source=signal)

# Helper functions
def convert_to_wavetable(envelope_array) -> list[float]:
    """Converts a list of floats into a new list in the wavetable format expected by SuperCollider.
    Taken from:
      https://github.com/supercollider/supercollider/blob/5c8b58dc36aafd03d656da0a1126810aa95eb04a/lang/LangPrimSource/PyrSignalPrim.cpp#L371
    """
    size = len(envelope_array)
    wavetable = []
    
    for i in range(size - 1):
        val1 = envelope_array[i]
        val2 = envelope_array[i + 1]
        wavetable.append(2.0 * val1 - val2)
        wavetable.append(val2 - val1)
    
    # Handle the wrap-around case
    val1 = envelope_array[-1]
    val2 = envelope_array[0]
    wavetable.append(2.0 * val1 - val2)
    wavetable.append(val2 - val1)
    
    return wavetable

def create_random_envelope() -> Envelope:
    num_segments = random.randrange(4, 20)
    amplitudes = [random.uniform(-1.0, 1.0) for _ in range(num_segments + 1)]
    durations = [random.randint(1, 20) for _ in range(num_segments)]
    curves = [EnvelopeShape.WELCH for _ in range(num_segments)]

    return Envelope(
        amplitudes=amplitudes,
        durations=durations,
        curves=curves,
    )

def create_wavetable(buffer: Buffer, server: Server) -> None:
    envelope = create_random_envelope()
    envelope_array = envelope.to_array(length=1024)
    
    wavetable = convert_to_wavetable(envelope_array=envelope_array)
    
    buffer.zero()
    server.sync()
    # Load the wavtetable into the buffer.
    buffer.set_range(index=0, values=wavetable)

def create_vosc_buffers(num_buffers: int, server: Server) -> BufferGroup:
    buffer_group = server.add_buffer_group(count=num_buffers, channel_count=1, frame_count=2048)

    for b in buffer_group.buffers:
        create_wavetable(buffer=b, server=server)

    return buffer_group

def main() -> None:
    server = Server().boot()
    server.add_synthdefs(delay, reverb, wavetable_cosc, wavetable_osc, variable_wavetable)
    server.sync()

    # Set up buses.
    delay_bus: Bus = server.add_bus(calculation_rate='audio')
    reverb_bus: Bus = server.add_bus(calculation_rate='audio')
    
    # Create the effects synths.
    server.add_synth(
        add_action=AddAction.ADD_TO_TAIL,
        in_bus=delay_bus,
        out_bus=reverb_bus,
        synthdef=delay,
    )
    
    server.add_synth(
        add_action=AddAction.ADD_TO_TAIL,
        in_bus=reverb_bus,
        out_bus=0,
        synthdef=reverb,
    )
    
    # Create wavetables
    chorusing_wavetable_buffer = server.add_buffer(channel_count=1, frame_count=2048)
    create_wavetable(buffer=chorusing_wavetable_buffer, server=server)
    
    wavetable_buffer = server.add_buffer(channel_count=1, frame_count=2048)
    create_wavetable(buffer=wavetable_buffer, server=server)
    
    vosc_wavetable_buffers = create_vosc_buffers(num_buffers=12, server=server)

    # Create patterns
    root_note = 51
    chord = [
        [
            midi_note_number_to_frequency(root_note + 0),
            midi_note_number_to_frequency(root_note + 4),
            midi_note_number_to_frequency(root_note + 8), 
            midi_note_number_to_frequency(root_note + 12), 
        ],
        [
            midi_note_number_to_frequency(root_note + 11),
            midi_note_number_to_frequency(root_note + 15),
            midi_note_number_to_frequency(root_note + 19), 
            midi_note_number_to_frequency(root_note + 23), 
        ],
        [
            midi_note_number_to_frequency(root_note + 7),
            midi_note_number_to_frequency(root_note + 11),
            midi_note_number_to_frequency(root_note + 15), 
            midi_note_number_to_frequency(root_note + 19), 
        ],
        [
            midi_note_number_to_frequency(root_note + 8),
            midi_note_number_to_frequency(root_note + 12),
            midi_note_number_to_frequency(root_note + 16), 
            midi_note_number_to_frequency(root_note + 20), 
        ],
    ]
    chord_sequence = SequencePattern(sequence=chord, iterations=None)
    chord_pattern = EventPattern(
        frequency=chord_sequence,
        synthdef=wavetable_cosc,
        delta=1.0,
        duration=1.0,
        adsr=(0.5, 0.3, 0.5, 0.4),
        amplitude=0.1,
        buffer_id=chorusing_wavetable_buffer.id_,
        out_bus=reverb_bus,
    )

    melody_root_note = 75
    root_1 = [
        midi_note_number_to_frequency(melody_root_note + 0),
        midi_note_number_to_frequency(melody_root_note + 8), 
    ]
    root_2 = [
        midi_note_number_to_frequency(melody_root_note + 4),
        midi_note_number_to_frequency(melody_root_note + 0), 
    ]
    sixth_1 = [
        midi_note_number_to_frequency(melody_root_note + 11),
        midi_note_number_to_frequency(melody_root_note + 19), 
    ]
    sixth_2 = [
        midi_note_number_to_frequency(melody_root_note + 15),
        midi_note_number_to_frequency(melody_root_note + 11), 
    ]
    fourth_1 = [
        midi_note_number_to_frequency(melody_root_note + 7),
        midi_note_number_to_frequency(melody_root_note + 15), 
    ]
    fourth_2 = [
        midi_note_number_to_frequency(melody_root_note + 15),
        midi_note_number_to_frequency(melody_root_note + 11), 
    ]
    fifth_1 = [
        midi_note_number_to_frequency(melody_root_note + 8),
        midi_note_number_to_frequency(melody_root_note + 16), 
    ]
    fifth_2 = [
        midi_note_number_to_frequency(melody_root_note + 12),
        midi_note_number_to_frequency(melody_root_note + 8), 
    ]
    melody_notes = [
        root_1,
        root_1,
        root_1,
        root_1,
        root_2,
        root_2,
        root_2,
        root_2,
        sixth_1,
        sixth_1,
        sixth_1,
        sixth_1,
        sixth_2,
        sixth_2,
        sixth_2,
        sixth_2,
        fourth_1,
        fourth_1,
        fourth_1,
        fourth_1,
        fourth_2,
        fourth_2,
        fourth_2,
        fourth_2,
        fifth_1,
        fifth_1,
        fifth_1,
        fifth_1,
        fifth_2,
        fifth_2,
        fifth_2,
        fifth_2,
    ]

    melody_sequence = SequencePattern(sequence=melody_notes, iterations=None)
    melody_pattern = EventPattern(
        frequency=melody_sequence,
        synthdef=wavetable_osc,
        delta=0.125,
        duration=0.125,
        amplitude=0.15,
        buffer_id=wavetable_buffer.id_,
        out_bus=reverb_bus,
    )

    drone_note = 27
    drone_sequence = SequencePattern(
        sequence=[
            midi_note_number_to_frequency(drone_note + 0),
            midi_note_number_to_frequency(drone_note + 11),
            midi_note_number_to_frequency(drone_note + 7),
            midi_note_number_to_frequency(drone_note + 8),
        ], 
        iterations=None
    )
    drone_pattern = EventPattern(
        frequency=drone_sequence,
        synthdef=variable_wavetable,
        delta=1.0,
        duration=1.0,
        amplitude_adsr=(0.5, 0.3, 0.5, 0.4),
        amplitude=0.3,
        buf_start_num=vosc_wavetable_buffers[0].id_,
        num_buffs=vosc_wavetable_buffers.count,
        out_bus=delay_bus,
    )

    bass_note = 39
    bass_scale = [0, 8, -1, 3, 7, 15, 16, 8]
    bass_frequencies = [midi_note_number_to_frequency(n + bass_note) for n in bass_scale]
    bass_sequence = SequencePattern(bass_frequencies, iterations=None)
    bass_pattern = EventPattern(
        frequency=bass_sequence,
        synthdef=wavetable_cosc,
        delta=0.5,
        duration=0.5,
        adsr=(0.1, 0.3, 0.2, 0.3),
        amplitude=0.09,
        buffer_id=chorusing_wavetable_buffer.id_,
        out_bus=reverb_bus,
    )

    clock = Clock()
    clock.start(beats_per_minute=80.0)

    # ParallelPattern makes sure all patterns start playing at the same time.
    parallel_pattern = ParallelPattern(patterns=[bass_pattern, chord_pattern, drone_pattern, melody_pattern])
    parallel_pattern.play(clock=clock, context=server)

    while True:
        continue

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
