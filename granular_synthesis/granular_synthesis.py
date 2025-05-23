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
import logging
import random
import sys
import time
from pathlib import Path

from supriya import Buffer, Envelope, Server, synthdef, UGenOperable
from supriya.clocks import Clock
from supriya.conversions import midi_note_number_to_frequency
from supriya.patterns import ChoicePattern, EventPattern, RandomPattern, SequencePattern
from supriya.ugens import (
    CombL,
    Envelope,
    EnvGen,
    FreeVerb,
    Out, 
    Pan2,
    SinOsc,
)
from supriya.ugens.core import UGenRecursiveInput
from supriya.ugens.granular import GrainBuf
from supriya.ugens.info import BufDur, BufSamples
from supriya.ugens.lines import Line
from supriya.ugens.noise import IRand
from supriya.ugens.osc import Impulse, Select


def create_buffer(file_path: Path, server: Server) -> Buffer:
    # sample_buffer = server.add_buffer(channel_indices=[0], file_path=str(file_path))
    sample_buffer = server.add_buffer(file_path=str(file_path))

    return sample_buffer

@synthdef()
def granular_synthesis_one_shot_playback(
    buffer_id=0,
    duration=1,
    pan=0,
    position=0,
    rate=1,
    trigger_frequency=440,
) -> None:
    buffer_duration = BufDur.kr(buffer_id=buffer_id)
    position = Line.ar(start=0, stop=1.0, duration=buffer_duration, done_action=2)
    duration = 2*(1/trigger_frequency)

    signal = GrainBuf.ar(
        # channel_count=2,
        duration=duration,
        pan=pan,
        position=position,
        rate=rate,
        buffer_id=buffer_id,
        trigger=Impulse.ar(frequency=trigger_frequency),
    )
    
    Out.ar(bus=0, source=signal)

def play_position(
        buffer_samples: UGenRecursiveInput, 
        direction: UGenRecursiveInput, 
        grain_duration: UGenRecursiveInput
) -> UGenOperable:
    if direction:
        return Line.ar(start=0, stop=1, duration=grain_duration, done_action=2)
    else:
        return Line.ar(start=grain_duration * buffer_samples, stop=0, duration=grain_duration, done_action=2)

@synthdef()
def granular_synthesis(
    buffer_id=0,
    duration=1,
    pan=0,
    position=0,
    rate=1,
    trigger_frequency=440,
) -> None:
    signal = GrainBuf.ar(
        channel_count=2,
        duration=duration,
        pan=pan,
        position=position,
        rate=rate,
        buffer_id=buffer_id,
        trigger=Impulse.ar(frequency=trigger_frequency),
    )
    
    Out.ar(bus=0, source=signal)

"""@synthdef()
def granular_synthesis_drums(
    buffer_id=0,
    direction=1.0,
    grain_duration=1.0,
    # position=0.0,
    # position_scalar=1.0,
    rand_max=1.0,
    # pan=0,
    # position=0,
    # rate=1,
    # start=0.0,
    # stop=1.0,
    # trigger_frequency=440,
) -> None:
    buffer_duration = BufDur.kr(buffer_id=buffer_id)
    # position = Line.ar(start=start, stop=stop, duration=buffer_duration, done_action=2)
    # buffer_samples = BufSamples.ir(buffer_id=buffer_id)

    # position = play_position(buffer_samples=buffer_samples, direction=direction, grain_duration=grain_duration)

    # positions = [
    #     Line.ar(start=0, stop=1, duration=grain_duration, done_action=2),
    #     Line.ar(start=grain_duration * buffer_samples, stop=1, duration=grain_duration, done_action=2)
    # ]

    # position = Select.ar(selector=direction, sources=positions)

    # position = Line.ar(start=0, stop=1, duration=grain_duration)

    sample_percentage = grain_duration / buffer_duration
    position_scalar = IRand.ir(minimum=1, maximum=rand_max) - 1
    position = sample_percentage * position_scalar

    # trigger_frequency = grain_duration/2
    trigger_frequency = 1/(grain_duration/2)

    signal = GrainBuf.ar(
        channel_count=2,
        duration=grain_duration,
        # duration = 2*(1/trigger_frequency),
        # pan=0.0,
        # position=0,
        position=position,
        rate=1.0,
        buffer_id=buffer_id,
        # trigger=Impulse.ar(frequency=trigger_frequency),
        trigger=Impulse.ar(frequency=trigger_frequency),
    )
    
    Out.ar(bus=0, source=signal)"""

@synthdef()
def granular_synthesis_drums(
    buffer_id=0,
    envelope_buffer_id=0,
    pattern_delta=1.0,
) -> None:
    buffer_duration = BufDur.kr(buffer_id=buffer_id)
    grain_duration = buffer_duration * pattern_delta
    irand_max = (1/pattern_delta) - 1
    position_scalar = IRand.ir(minimum=0, maximum=irand_max)
    position = position_scalar * pattern_delta
    trigger_frequency = 2/grain_duration

    signal = GrainBuf.ar(
        channel_count=2,
        duration=grain_duration,
        envelope_buffer_id=envelope_buffer_id,
        position=position,
        buffer_id=buffer_id,
        trigger=Impulse.ar(frequency=trigger_frequency),
    )
    
    Out.ar(bus=0, source=signal)

def calculate_time_duration_from_bpm(delta: float) -> float:
    whole_note = 240

    return whole_note * delta

def main() -> None:
    # logging.basicConfig(level=logging.INFO)
    server = Server().boot()
    server.add_synthdefs(granular_synthesis_drums, granular_synthesis_one_shot_playback)
    server.sync()

    drum_loop_bpm = 100

    # deltas = [1.0, 0.5, 0.25, 0.125, 0.0625]
    deltas = [1.0, 0.5, 0.25, 0.125]
    # deltas = [0.5]
    quantizations = {
        1.0: '1M', 
        0.5: '1/2', 
        0.25: '1/4', 
        0.125: '1/8', 
        0.0625: '1/16'
    }

    # measure_duration_seconds = calculate_time_duration_from_bpm(delta=1.0) / drum_loop_bpm

    # sample_duration = 60 / drum_loop_bpm

    # drum_sample_path = Path(__file__).parent / 'samples/drum_loop_85_bpm.mp3'
    # drum_sample_path = Path(__file__).parent / 'samples/drum_loop_one_bar_85_bpm_mono.mp3'
    drum_sample_path = Path(__file__).parent /'samples/drum_loop_one_measure_100_bpm_mono.mp3'
    drum_sample_buffer = create_buffer(file_path=drum_sample_path, server=server)
    envelope = Envelope.asr()
    envelope_buffer = server.add_buffer()
    envelope_buffer.generate(
        command_name='sine1',
        amplitudes=envelope.serialize(),
    )
    
    # time_tombs_sample_path = Path(__file__).parent / 'samples/time_tombs.mp3'
    # time_tombs_sample_buffer = create_buffer(file_path=time_tombs_sample_path, server=server)

    server.sync()

    # direction_sequence = SequencePattern([1.0, 0.0, 1.0, 0.0,], iterations=None)

    clock = Clock()
    clock.start(beats_per_minute=drum_loop_bpm)

    while True:
        delta = random.choices(deltas, weights=[0.30, 0.2, 0.30, 0.2], k=1)[0]
        grain_duration = 2.4 * delta
        position_scalar = random.randint(0, (1/delta) - 1)
        position = position_scalar * delta
        trigger_frequency = 1/(grain_duration/2)
        measure_duration_seconds = 2.4

        print()
        print(f'delta={delta}')
        print(f'grain_duration={grain_duration}')
        print(f'position_scalar={position_scalar}')
        print(f'position={position}')
        print(f'trigger_frequency={trigger_frequency}')
        
        drum_pattern = EventPattern(
            buffer_id=drum_sample_buffer.id_,
            delta=delta,
            duration=delta,
            envelope_buffer_id=envelope_buffer.id_,
            # direction=direction_sequence,
            # direction=ChoicePattern([0, 1], iterations=None, forbid_repetitions=True),
            # grain_duration=sample_duration,
            # position=position,
            # position_scalar=position_scalar,
            # rand_max=1/delta,
            pattern_delta=delta,
            synthdef=granular_synthesis_drums,
        )
        
        player = drum_pattern.play(clock=clock, context=server)
        print(server.dump_tree())
        time.sleep(measure_duration_seconds)
        # time.sleep(sample_duration)
        player.stop()
        # time.sleep(delta)
        # print(server.dump_tree())

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)