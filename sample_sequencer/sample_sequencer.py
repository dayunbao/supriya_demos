import time
from collections import defaultdict
from pathlib import Path
from pprint import pprint

from supriya import Buffer, Server

from synth_defs import drum_sample, three_o_three

drum_buffers: dict[str, list[Buffer]] = defaultdict(list)
server: Server

def initialize_supriya() -> None:
    global server

    server = Server().boot()
    _ = server.add_synthdefs(drum_sample, three_o_three)
    server.sync()

def read_buffers() -> None:
    global drum_buffers
    global server
    
    samples_path: Path = Path(__file__).parent / 'samples'
    for sample_path in samples_path.rglob(pattern='*.WAV'):
        # Get the name of the directory that contains the wav file
        drum_buffers[sample_path.parent.name].append(server.add_buffer(file_path=str(sample_path)))

def play_buffers() -> None:
    global drum_buffers
    
    for drum, drum_buffs in sorted(drum_buffers.items()):
        print(drum)
        pprint(drum_buffs[0])
        for drum_buff in drum_buffs:
            _ = server.add_synth(synthdef=drum_sample, drum_buff=drum_buff)
            time.sleep(3)
        break

if __name__ == '__main__':
    initialize_supriya()
    read_buffers()
    play_buffers()
    while True:
        continue