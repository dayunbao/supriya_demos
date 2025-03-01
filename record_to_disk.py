import time
from pathlib import Path

from supriya import synthdef
from supriya import AddAction, Buffer, Server, Synth
from supriya.ugens import Envelope, EnvGen, In, LFSaw, Limiter, Out, Pan2
from supriya.ugens.diskio import DiskOut

@synthdef()
def audio_to_disk(in_bus, buffer_number):
    input = In.ar(bus=in_bus, channel_count=2)
    DiskOut.ar(buffer_id=buffer_number, source=input)

@synthdef()
def saw(frequency=440.0, amplitude=0.5, gate=1, out_bus=0):
    signal = LFSaw.ar(frequency=[frequency, frequency - 2])
    signal *= amplitude
    signal = Limiter.ar(duration=0.01, level=0.1, source=signal)
    adsr = Envelope.adsr()
    env = EnvGen.kr(envelope=adsr, gate=gate, done_action=2)
    signal *= env
    signal = Pan2.ar(source=signal, position=0.0, level=1.0)
    Out.ar(bus=out_bus, source=signal)

def create_buffer(server: Server) -> Buffer:
    buffer = server.add_buffer(
        channel_count=2,
        frame_count=262144,
    )

    server.sync()

    return buffer

def create_buffer_file_path() -> Path:
    dir_path = Path(__file__).parent / 'recordings'
    if not dir_path.exists():
        dir_path.mkdir()

    file_path =  dir_path / 'recording.wav'
    
    if not file_path.exists():
        file_path.touch()
    
    return file_path

def main() -> None:
    server = Server().boot()
    server.add_synthdefs(audio_to_disk, saw)
    server.sync()
    saw_synth = start_playing_synth(server=server)
    file_path = create_buffer_file_path()
    recording_buffer = create_buffer(server=server)
    start_writing_buffer(recording_buffer=recording_buffer, file_path=file_path)
    audio_to_disk_synth = start_writing_audio_to_disk(server=server, recording_buffer=recording_buffer)
    print(server.dump_tree())
    time.sleep(5)
    audio_to_disk_synth.free()
    saw_synth.set(gate=0)
    saw_synth.free()
    recording_buffer.close(on_completion=lambda _: recording_buffer.free())

def start_playing_synth(server: Server) -> Synth:
    saw_synth: Synth = server.add_synth(
        synthdef=saw,
        in_bus=0,
    )

    return saw_synth

def start_writing_audio_to_disk(server: Server, recording_buffer: Buffer) -> Synth:
    audio_to_disk_synth: Synth = server.add_synth(
        synthdef=audio_to_disk,
        buffer_number=recording_buffer.id_,
        in_bus=0,
        add_action=AddAction.ADD_TO_TAIL,
    )

    return audio_to_disk_synth

def start_writing_buffer(recording_buffer: Buffer, file_path: Path) -> None:
    recording_buffer.write(
        file_path=file_path,
        header_format='WAV',
        leave_open=True,
    )


if __name__ == '__main__':
    main()