from collections import defaultdict
from pathlib import Path

from mido import Message

from supriya import Buffer, Bus, Group, Server, Synth
from supriya.clocks import Clock, ClockContext, TimeUnit

from class_lib import BaseTrack, BaseInstrument
from .synth_defs import audio_to_disk

class Track(BaseTrack):
    def __init__(
            self, 
            clock: Clock,
            # group: Group,
            instrument: BaseInstrument,
            is_recording: bool,
            quantization_delta: float,
            # recording_bus: Bus | int, 
            sequencer_steps: int,
            server: Server,
            track_number: int,
        ):
        super().__init__(
            clock, 
            instrument, 
            quantization_delta, 
            sequencer_steps,
            track_number,
        )
        # self.group = group
        self.is_recording = is_recording
        # self.recording_bus = recording_bus
        self._recorded_notes: dict[float, list[Message]] = defaultdict(list)
        self.server = server
        self._load_synthdef()
        # self.BUFFER_CHANNELS = 2
        # self.BUFFER_FRAME_COUNT = 262144
        # self.buffer_file_path = self._create_buffer_file_path()
        # self.recording_buffer: Buffer | None = None
        # self.audio_to_disk_synth: Synth | None = None

    @property
    def recorded_notes(self) -> dict[float, list[Message]]:
        return self._recorded_notes
    
    @recorded_notes.setter
    def recorded_notes(self, notes: dict[float, list[Message]]):
        self._recorded_notes = notes

    # def _create_buffer(self) -> Buffer:
    #     buffer = self.server.add_buffer(
    #         channel_count=self.BUFFER_CHANNELS,
    #         frame_count=self.BUFFER_FRAME_COUNT,
    #     )

    #     self.server.sync()

    #     return buffer

    # def _create_buffer_file_path(self) -> Path:
    #     track_recordings_dir_path = Path(__file__).parent / 'track_recordings'
    #     if not track_recordings_dir_path.exists():
    #         track_recordings_dir_path.mkdir()
        
    #     instrument_dir_path = Path(__file__).parent / track_recordings_dir_path / self._instrument.name
    #     if not instrument_dir_path.exists():
    #         instrument_dir_path.mkdir()

    #     file_path =  instrument_dir_path / f'track_{self.track_number}.wav'
        
    #     if not file_path.exists():
    #         file_path.touch()
        
    #     return file_path

    def erase_recorded_notes(self) -> None:
        self._recorded_notes.clear()
    
    def handle_midi_message(self, message: Message) -> None:
        """Decide how to handle incoming MIDI notes based on the mode."""
        # The SynthHandler is responsible for playing notes
        # We play a note whether or note we're recording. 
        self._instrument.handle_midi_message(message=message)
        
        # The Sequencer is responsible for recording the notes
        if self.is_recording:
            # recorded_time is in a factor of quantization_delta, and is based
            # on the scaled value of the message's note.
            # This makes playback very simple because for each invocation of 
            # the clock's callback, we can simply check for messages at the delta.
            recorded_time = (message.note % self._sequencer_steps) * self.quantization_delta
            recorded_message = message.copy(time=recorded_time)
            self.recorded_notes[recorded_time].append(recorded_message)

    def _load_synthdef(self) -> None:
        self.server.add_synthdefs(audio_to_disk)

    def start_playback(self) -> None:
        # self.start_recording_to_disk()

        self._clock_event_id = self._clock.cue(
            kwargs={'delta': self.quantization_delta},
            procedure=self.track_clock_callback
        )
    
    # def start_recording_to_disk(self) -> None:
    #     self.recording_buffer = self._create_buffer()
    #     self.recording_buffer.write(
    #         file_path=self.buffer_file_path,
    #         frame_count=0,
    #         header_format='WAV',
    #         leave_open=True,
    #     )

    #     self.server.sync()

    #     self.audio_to_disk_synth = self.group.add_synth(
    #         synthdef=audio_to_disk,
    #         buffer_number=self.recording_buffer.id_,
    #         in_bus=self.recording_bus,
    #     )

    def stop_playback(self) -> None:
        super().stop_playback()
        # self.stop_recording_to_disk()

    # def stop_recording_to_disk(self) -> None:
    #     self.audio_to_disk_synth.free()
    #     self.recording_buffer.close(on_completion=lambda _: self.recording_buffer.free())
    #     self.server.sync()

    def track_clock_callback(
        self, 
        context:ClockContext, 
        delta: float,
    ) -> tuple[float, TimeUnit]:
        """The function that runs on each invocation.

        The callback is executed once every `delta`.  What delta means depends on time_unit.  
        Options for time_unit are BEATS or SECONDS.  If you want this function to called
        once every 1/4, 1/8, or 1/16 note, then time_unit should be BEATS.  Otherwise
        you can specify SECONDS as the time_unit to have it called outside of a 
        musical rhythmic context.
        """
        recorded_notes_index = delta * (context.event.invocations % self._sequencer_steps )

        midi_messages = self.recorded_notes[recorded_notes_index]
        for message in midi_messages:
            self._instrument.handle_midi_message(message=message)
        
        return delta, TimeUnit.BEATS
