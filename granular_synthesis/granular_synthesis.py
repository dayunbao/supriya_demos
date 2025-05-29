"""A script demonstrating how to do granular synthesis.


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
import time
from pathlib import Path

from supriya import AddAction, Bus, Envelope, Server, synthdef, UGenOperable
from supriya.clocks import Clock
from supriya.conversions import midi_note_number_to_frequency
from supriya.patterns import EventPattern, RandomPattern, SequencePattern
from supriya.ugens import (
    CombL,
    Envelope,
    EnvGen,
    FreeVerb,
    In,
    LFSaw,
    Out, 
    Pan2,
    SinOsc,
)
from supriya.ugens.bufio import PlayBuf
from supriya.ugens.core import UGenRecursiveInput
from supriya.ugens.dynamics import Limiter
from supriya.ugens.filters import HPF, RLPF
from supriya.ugens.granular import GrainBuf
from supriya.ugens.lines import LinExp
from supriya.ugens.noise import LFNoise1, LFNoise2, WhiteNoise
from supriya.ugens.osc import Impulse


@synthdef()
def sample_playback(
    buffer_id=0,
    out_bus=0,
) -> None:
    signal = PlayBuf.ar(
        buffer_id=buffer_id,
        done_action=2,
        rate=0.5,
    )

    Out.ar(bus=out_bus, source=signal)

def grain_generator_spooky(
        buffer_id: UGenRecursiveInput,
        grain_duration: UGenRecursiveInput,
        position: UGenRecursiveInput,
        trigger_frequency: UGenRecursiveInput,
) -> UGenOperable:
    duration_modulator = LFNoise1.ar(frequency=5).scale(-1.0, 1.0, -0.5, 0.5)
    grain_duration += duration_modulator

    position_modulator = LFNoise2.ar(frequency=50).scale(-1.0, 1.0, -0.05, 0.05)
    position += position_modulator
    
    signal = GrainBuf.ar(
        buffer_id=buffer_id,
        duration=grain_duration,
        position=position,
        rate=LFNoise1.ar(frequency=0.1).scale(-1, 1, 0, 1),
        trigger=Impulse.ar(frequency=trigger_frequency),
    )

    return signal

@synthdef()
def granular_synthesis_spooky(
    adsr=(0.01, 0.3, 0.5, 1.0),
    amplitude=0.5,
    buffer_id=0,
    gate=1,
    grain_duration=1,
    out_bus=0,
    position=0,
    trigger_frequency=440,
) -> None:
    envelope = EnvGen.kr(
        done_action=2,
        envelope=Envelope.adsr(
            attack_time=adsr[0],
            decay_time=adsr[1],
            sustain=adsr[2],
            release_time=adsr[3],
        ),
        gate=gate,
    )

    signal = grain_generator_spooky(
        buffer_id=buffer_id,
        grain_duration=grain_duration,
        position=position,
        trigger_frequency=trigger_frequency
    )
    signal = Limiter.ar(level=amplitude, source=signal)
    signal *= envelope
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def granular_synthesis_bass(
    amplitude=1.0,
    buffer_id=0,
    gate=1,
    grain_duration=1,
    out_bus=0,
    position=0,
    rate=1,
    trigger_frequency=440,
) -> None:
    envelope = EnvGen.kr(
        done_action=2,
        envelope=Envelope.percussive(release_time=2.5),
        gate=gate,
    )

    signal = GrainBuf.ar(
        buffer_id=buffer_id,
        duration=grain_duration,
        position=position,
        rate=rate,
        trigger=Impulse.ar(frequency=trigger_frequency),
    )
    mod_signal = SinOsc.ar(frequency=2)
    mod_signal *= 0.5
    # Convert output to frequency range.
    mod_freq = LinExp.ar(
        input_minimum=-1.0, 
        input_maximum=1.0, 
        output_minimum=100, 
        output_maximum=4000,
        source=mod_signal,
    )
    signal *= amplitude
    signal *= envelope
    signal = RLPF.ar(source=signal, frequency=mod_freq, reciprocal_of_q=0.15)
    signal = Pan2.ar(source=signal, position=-1.0)
    signal = Pan2.ar(source=signal, position=1.0)
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def granular_synthesis_pad(
    adsr=(0.01, 0.3, 0.5, 3.0),
    amplitude=1.0,
    buffer_id=0,
    curve=(-4),
    gate=1,
    grain_duration=1,
    out_bus=0,
    position=0,
    rate=1,
    trigger_frequency=440,
) -> None:
    envelope = EnvGen.kr(
        done_action=2,
        envelope=Envelope.adsr(
            attack_time=adsr[0],
            decay_time=adsr[1], 
            sustain=adsr[2],
            release_time=adsr[3],
            curve=curve[0],
        ),
        gate=gate,
    )

    signal = GrainBuf.ar(
        buffer_id=buffer_id,
        duration=grain_duration,
        position=position,
        rate=rate,
        trigger=Impulse.ar(frequency=trigger_frequency),
    )
    signal = HPF.ar(source=signal, frequency=800)
    signal = Limiter.ar(level=amplitude, source=signal)
    signal *= envelope
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def granular_synthesis_percussion(
    amplitude=1.0,
    buffer_id=0,
    gate=1,
    grain_duration=1,
    hpf_frequency=1000,
    out_bus=0,
    position=0,
    rate=1,
    release_time=(1.0),
    trigger_frequency=440,
) -> None:
    envelope = EnvGen.kr(
        done_action=2,
        envelope=Envelope.percussive(release_time=release_time[0]),
        gate=gate,
    )

    signal = GrainBuf.ar(
        buffer_id=buffer_id,
        duration=grain_duration,
        position=position,
        rate=rate,
        trigger=Impulse.ar(frequency=trigger_frequency),
    )
    
    noise = WhiteNoise.ar()
    signal += noise
    signal *= amplitude
    signal *= envelope
    signal = HPF.ar(source=signal, frequency=hpf_frequency)
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def granular_synthesis_melody(
    amplitude=1.0,
    buffer_id=0,
    gate=1,
    grain_duration=1,
    hpf_frequency=1000,
    out_bus=0,
    position=0,
    rate=1,
    release_time=(1.0),
    trigger_frequency=440,
) -> None:
    envelope = EnvGen.kr(
        done_action=2,
        envelope=Envelope.percussive(release_time=release_time[0]),
        gate=gate,
    )

    signal = GrainBuf.ar(
        buffer_id=buffer_id,
        duration=grain_duration,
        position=position,
        rate=rate,
        trigger=Impulse.ar(frequency=trigger_frequency),
    )
    
    saw = LFSaw.ar(frequency=trigger_frequency)
    signal += saw
    signal *= amplitude
    signal *= envelope
    signal = HPF.ar(source=signal, frequency=hpf_frequency)
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def delay(
    in_bus: 2, 
    out_bus: 0
):
    signal = In.ar(bus=in_bus, channel_count=1)
    signal = CombL.ar(
        delay_time=0.2,
        decay_time=3.5,
        maximum_delay_time=0.2,
        source=signal
    )
    Out.ar(bus=out_bus, source=signal)

@synthdef()
def reverb(
    in_bus=2,
    out_bus=0,
):
    signal = In.ar(bus=in_bus, channel_count=1)
    signal = FreeVerb.ar(source=signal, mix=0.65, room_size=0.55, damping=0.9)
    signal = Pan2.ar(source=signal)
    Out.ar(bus=out_bus, source=signal)

def main() -> None:
    server = Server().boot(memory_size=65536)
    server.add_synthdefs(
        delay, 
        granular_synthesis_bass, 
        granular_synthesis_melody,
        granular_synthesis_pad,
        granular_synthesis_percussion,
        granular_synthesis_spooky,
        reverb,
        sample_playback
    )
    server.sync()

    time_tombs_sample_path = Path(__file__).parent / 'samples/time_tombs.mp3'
    time_tombs_sample_buffer = server.add_buffer(file_path=str(time_tombs_sample_path))
    server.sync()

    delay_bus: Bus = server.add_bus(calculation_rate='audio')
    reverb_bus: Bus = server.add_bus(calculation_rate='audio')

    server.add_synth(
        add_action=AddAction.ADD_TO_TAIL,
        in_bus=int(delay_bus),
        out_bus=int(reverb_bus),
        synthdef=delay,
    )
    
    server.add_synth(
        add_action=AddAction.ADD_TO_TAIL,
        in_bus=int(reverb_bus),
        out_bus=0,
        synthdef=reverb,
    )

    time_tombs_start = 3.269/10.948
    time_tombs_grain_duration = 1.069
    
    ten_thousand_years_start = 9.882/10.948
    
    artifacts_start = 4.704

    spooky_pattern = EventPattern(
        delta=0.25,
        duration=0.25,
        amplitude=0.3,
        buffer_id=time_tombs_sample_buffer.id_,
        grain_duration=time_tombs_grain_duration,
        out_bus=delay_bus,
        position=time_tombs_start,
        synthdef=granular_synthesis_spooky,
        trigger_frequency=RandomPattern(minimum=10000, maximum=50000, iterations=None),
    )

    diminshed_bass_scale = [0, 3, 4, 1]
    root_note = 26
    bass_scale = [midi_note_number_to_frequency(root_note + n) for n in diminshed_bass_scale]
    sequence_pattern = SequencePattern(sequence=bass_scale, iterations=None)
    bass_pattern = EventPattern(
        delta=0.5,
        duration=0.5,
        amplitude=1.75,
        buffer_id=time_tombs_sample_buffer.id_,
        grain_duration=0.05,
        out_bus=delay_bus,
        position=ten_thousand_years_start,
        synthdef=granular_synthesis_bass,
        trigger_frequency=sequence_pattern,
    )

    pad_root_note = 62
    pad_scale = [
        [
            midi_note_number_to_frequency(6 + pad_root_note),
            midi_note_number_to_frequency(6 + pad_root_note + 3),
            midi_note_number_to_frequency(6 + pad_root_note + 12),
        ],
        [
            midi_note_number_to_frequency(3 + pad_root_note),
            midi_note_number_to_frequency(3 + pad_root_note + 3),
            midi_note_number_to_frequency(3 + pad_root_note + 12),
        ],
        [
            midi_note_number_to_frequency(4 + pad_root_note),
            midi_note_number_to_frequency(4 + pad_root_note + 3),
            midi_note_number_to_frequency(4 + pad_root_note + 12),
        ],
        [
            midi_note_number_to_frequency(7 + pad_root_note),
            midi_note_number_to_frequency(7 + pad_root_note + 3),
            midi_note_number_to_frequency(7 + pad_root_note + 12),
        ],
    ]
    
    pad_sequence_pattern = SequencePattern(sequence=pad_scale, iterations=None)
    pad_pattern = EventPattern(
        delta=0.5,
        duration=0.5,
        adsr=(0.01, 0.6, 0.2, 0.1),
        amplitude=2.0,
        buffer_id=time_tombs_sample_buffer.id_,
        grain_duration=0.015,
        out_bus=delay_bus,
        position=artifacts_start,
        synthdef=granular_synthesis_pad,
        trigger_frequency=pad_sequence_pattern,
    )

    high_hat_pattern = EventPattern(
        delta=0.0625,
        duration=0.0625,
        amplitude=RandomPattern(minimum=0.08, maximum=0.3, iterations=None),
        buffer_id=time_tombs_sample_buffer.id_,
        grain_duration=0.09,
        hpf_frequency=2000,
        out_bus=reverb_bus,
        position=ten_thousand_years_start,
        release_time=(0.05),
        synthdef=granular_synthesis_percussion,
        trigger_frequency=1000,
    )
    
    snare_gates = [0, 1]
    snare_sequence_pattern = SequencePattern(sequence=snare_gates, iterations=None)
    snare_pattern = EventPattern(
        delta=0.25,
        duration=0.25,
        amplitude=0.5,
        buffer_id=time_tombs_sample_buffer.id_,
        gate=snare_sequence_pattern,
        grain_duration=0.09,
        hpf_frequency=800,
        out_bus=reverb_bus,
        position=ten_thousand_years_start,
        release_time=(0.25),
        synthdef=granular_synthesis_percussion,
        trigger_frequency=200,
    )

    melody_root_note = 74
    melody_scale = [
        midi_note_number_to_frequency(6 + melody_root_note + 12),
        midi_note_number_to_frequency(6 + melody_root_note + 3),
        midi_note_number_to_frequency(6 + melody_root_note),
        midi_note_number_to_frequency(6 + melody_root_note - 12),
        
        midi_note_number_to_frequency(3 + melody_root_note + 12),
        midi_note_number_to_frequency(3 + melody_root_note + 3),
        midi_note_number_to_frequency(3 + melody_root_note),
        midi_note_number_to_frequency(3 + melody_root_note - 12),

        midi_note_number_to_frequency(4 + melody_root_note + 12),
        midi_note_number_to_frequency(4 + melody_root_note + 3),
        midi_note_number_to_frequency(4 + melody_root_note),
        midi_note_number_to_frequency(4 + melody_root_note - 12),

        midi_note_number_to_frequency(7 + melody_root_note + 12),
        midi_note_number_to_frequency(7 + melody_root_note + 3),
        midi_note_number_to_frequency(7 + melody_root_note),
        midi_note_number_to_frequency(7 + melody_root_note - 12),
    ]
    melody_sequence_pattern = SequencePattern(sequence=melody_scale, iterations=None)
    melody_pattern = EventPattern(
        delta=0.125,
        duration=0.125,
        amplitude=0.1,
        buffer_id=time_tombs_sample_buffer.id_,
        grain_duration=0.09,
        out_bus=delay_bus,
        position=ten_thousand_years_start,
        synthdef=granular_synthesis_melody,
        trigger_frequency=melody_sequence_pattern,
    )

    bpm = 80
    seconds_per_beat = 60/bpm
    seconds_per_measure = seconds_per_beat * 4

    clock = Clock()
    clock.start(beats_per_minute=bpm)
    # One-shot playback of the original sample
    server.add_synth(
        buffer_id=time_tombs_sample_buffer.id_,
        out_bus=int(delay_bus),
        synthdef=sample_playback,
    )
    time.sleep(seconds_per_measure * 3)
    spooky_pattern.play(clock=clock, context=server)
    time.sleep(seconds_per_measure * 2)
    bass_pattern.play(clock=clock, context=server)
    time.sleep(seconds_per_measure * 4)
    melody_pattern.play(clock=clock, context=server)
    high_hat_pattern.play(clock=clock, context=server)
    time.sleep(seconds_per_measure * 4)
    pad_pattern.play(clock=clock, context=server)
    snare_pattern.play(clock=clock, context=server)

    while True:
        time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)