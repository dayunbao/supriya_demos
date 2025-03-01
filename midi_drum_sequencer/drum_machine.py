"""A class for a simple drum machine with a 16-step sequencer.

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

import fractions
import threading
from collections import defaultdict
from enum import Enum

from mido import get_input_names, Message, open_input
from mido.ports import MultiPort

from supriya import Server, SynthDef
from supriya.clocks import Clock, ClockContext, TimeUnit

from synth_defs import (
    bass_drum,
    clap_dry,
    claves,
    closed_high_hat,
    cow_bell,
    cymbal,
    high_conga,
    high_tom,
    low_conga,
    low_tom,
    maracas,
    medium_conga,
    medium_tom,
    open_high_hat,
    rim_shot,
    snare,
)


class SequencerMode(Enum):
    # Used to track the current state of the sequencer
    PERFORM = 0
    PLAYBACK = 1
    RECORD = 2


class DrumMachine:
    def __init__(self, bpm: int, quantization: str):
        self.bpm = bpm
        self.clock: Clock = self._init_clock()
        self.clock_event_id: int | None = None
        self.MIDI_CHANNEL_TO_SYNTHDEF: list[SynthDef] = [
            bass_drum,
            snare,
            low_tom,
            medium_tom,
            high_tom,
            low_conga,
            medium_conga,
            high_conga,
            rim_shot,
            clap_dry,
            claves,
            maracas,
            cow_bell,
            cymbal,
            open_high_hat,
            closed_high_hat,
        ]
        self.multiport = self._open_multiport()
        self.quantization_delta = self._quantization_to_beats(quantization=quantization)
        self.recorded_notes: dict[float, list[Message]] = defaultdict(list)
        self.sequencer_mode: Enum = SequencerMode.PERFORM
        self.SEQUENCER_STEPS: int = 16
        self.server: Server = self._init_server()
        self.stop_listening_for_input: threading.Event = threading.Event()

    def _init_server(self) -> Server:
        """Start the server and load SynthDefs"""
        server = Server().boot()
        server.add_synthdefs(
            bass_drum,
            clap_dry,
            claves,
            closed_high_hat,
            cow_bell,
            cymbal,
            high_conga,
            high_tom,
            low_conga,
            low_tom,
            maracas,
            medium_conga,
            medium_tom,
            open_high_hat,
            rim_shot,
            snare,
        )
        # Wait for the server to fully load the SynthDef before proceeding.
        server.sync()

        return server
    
    def _init_clock(self) -> Clock:
        """Create the clock and set the BPM."""
        clock = Clock()
        # Set the BPM of the clock
        clock.change(beats_per_minute=self.bpm)
        # This helper function converts a string like '1/16' into a numeric value
        # used by the clock.
        clock.start()

        return clock
    
    def _open_multiport(self) -> MultiPort:
        """Open all MIDI input ports."""
        inports = [open_input(p) for p in get_input_names()]
        
        return MultiPort(inports)

    def consume_keyboard_input(self) -> None:
        """The thread that receives user keyboard input.
        
        Four options are presented to the user on the command line:
        1) `Perform` - simply handles incoming MIDI messages
        2) `Playback` - plays a recorded sequence of MIDI messages
        3) `Record` - records incoming MIDI messages
        4) `Exit` - exit the program entirely.
        
        The whole word must be entered when choosing a mode, but case
        doesn't matter.

        If setting the sequencer to Perform mode, two options are
        available:
        1) `Stop` - stop playing the recorded sequence, and change to Perform mode.
        2) `Exit` - exit the program entirely

        If setting the sequencer to Record mode, three options are
        available:
        1) `Stop` - stop recording a sequence, and change to Perform mode.
        2) `Clear` - delete all recorded sequences
        3) `Exit` - exit the program entirely
        """
        input_prompt = 'Enter a command:\n'

        while not self.stop_listening_for_input.is_set():
            input_options = 'Options are:\n*Perform\n*Playback\n*Record\n*Exit\n'

            if self.sequencer_mode == SequencerMode.PLAYBACK:
                input_options = 'Options are:\n*Stop\n*Exit\n'

            if self.sequencer_mode == SequencerMode.RECORD:
                input_options = 'Options are:\n*Stop\n*Clear\n*Exit\n'

            command = input(f'{input_prompt}(Current mode is {SequencerMode(self.sequencer_mode).name})\n{input_options}> ')
            command = command.upper()
            
            if command == "STOP":
                if self.sequencer_mode == SequencerMode.PLAYBACK:
                    self.stop_playback()
                
                # Set mode to PERFORM when stopping either PLAYBACK or RECORD.
                self.sequencer_mode = SequencerMode.PERFORM
            
            if command == "CLEAR":
                # Delete all recorded notes.
                self.recorded_notes.clear()

            if command == "EXIT":
                # Quit the program.
                self.exit()
                break
            
            if command not in SequencerMode.__members__:
                    print('Incorrect command.  Please try again.')
            else:
                if self.sequencer_mode == SequencerMode[command]:
                    # No need to reassign.
                    continue
                
                if self.sequencer_mode == SequencerMode.PLAYBACK and SequencerMode[command] != SequencerMode.PLAYBACK:
                    self.stop_playback()

                self.sequencer_mode = SequencerMode[command]

            if self.sequencer_mode == SequencerMode.PLAYBACK:
                self.start_playback()
    
    def handle_midi_message(self, message: Message) -> None:
        """Deal with a new MIDI message.

        This function currently only handles Note On messages.

        Args:
            message: a MIDI message.
        """
        if message.type == 'note_on':
            self.on_note_on(message=message)

    def listen_for_keyboard_input(self):
        """Starts the thread that listens for keyboard input."""
        consumer_thread = threading.Thread(target=self.consume_keyboard_input, daemon=True)
        consumer_thread.start()
    
    def listen_for_midi_messages(self) -> None:
        """Listen for incoming MIDI messages in a non-blocking way.
        
        Mido's iter_pending() is non-blocking.
        """
        while not self.stop_listening_for_input.is_set():
            for message in self.multiport.iter_pending():
                self.handle_midi_message(message=message)
    
    def on_note_on(self, message: Message) -> None:
        """Handle MIDI Note On messages.

        The MIDI channel need to be different for each drum.
        It also need to be in the range 0-15, as the channel
        is used as an index into an array of SynthDefs.

        There is no restriction on the MIDI note value,
        other than it be in the usual 0-127 MIDI note range.
        Whatever the value, it will be converted into 
        the range 0-15.  This is done so that each MIDI
        note value corresponds to a 1/6th note.

        Args:
            message: a MIDI Note On message.
        """
        # Use the MIDI channel as the index into an array of SynthDefs
        # to choose the right one.
        drum_synthdef = self.MIDI_CHANNEL_TO_SYNTHDEF[message.channel]
        _ = self.server.add_synth(synthdef=drum_synthdef)

        if self.sequencer_mode == SequencerMode.RECORD:
            # recorded_time is in a factor of quantization_delta, and is based
            # on the scaled value of the message's note.
            # This makes playback very simple because for each invocation of 
            # the clock's callback, we can simply check for messages at the delta.
            recorded_time = (message.note % self.SEQUENCER_STEPS) * self.quantization_delta
            recorded_message = message.copy(time=recorded_time)
            self.recorded_notes[recorded_time].append(recorded_message)

    def _quantization_to_beats(self, quantization: str) -> float:
        fraction = fractions.Fraction(quantization.replace("T", ""))
        if "T" in quantization:
            fraction *= fractions.Fraction(2, 3)
        
        return float(fraction)

    def run(self) -> None:
        """Start the drum machine and sequencer."""
        self.listen_for_keyboard_input()
        self.listen_for_midi_messages()

    def sequencer_clock_callback(
        self,
        context: ClockContext, 
        delta: float, 
    ) -> tuple[float, TimeUnit]:
        """The function that runs on each invocation.

        The callback is executed once every `delta`.  What delta means depends on time_unit.  
        Options for time_unit are BEATS or SECONDS.  If you want this function to called
        once every 1/4, 1/8, or 1/16 note, then time_unit should be BEATS.  Otherwise
        you can specify SECONDS as the time_unit to have it called outside of a 
        musical rhythmic context.
        """
        recorded_notes_index = delta * (context.event.invocations % self.SEQUENCER_STEPS )

        midi_messages = self.recorded_notes[recorded_notes_index]
        for message in midi_messages:
            self.handle_midi_message(message)
        
        return delta, TimeUnit.BEATS

    def start_playback(self) -> None:
        """Start playing back the sequenced drum pattern."""
        self.clock_event_id = self.clock.cue(
            procedure=self.sequencer_clock_callback, 
            kwargs={'delta': self.quantization_delta},
            quantization='1/4'
        )

    def stop_playback(self) -> None:
        """Stop playing back the sequenced drum pattern."""
        if self.clock_event_id is not None:
            self.clock.cancel(self.clock_event_id)

    def exit(self) -> None:
        """Exit the drum machine and sequencer."""
        self.stop_listening_for_input.set()
        self.multiport.close()
        self.server.quit()
