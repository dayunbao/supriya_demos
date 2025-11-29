import sys

from supriya import (
    AddAction, 
    Bus, 
    Server, 
)
from supriya.clocks import Clock
from supriya.conversions import midi_note_number_to_frequency
from supriya.patterns import EventPattern, ShufflePattern

from synth_defs import plateau_reverb, saw

def main() -> None:
    server = Server().boot()
    server.add_synthdefs(plateau_reverb, saw)
    server.sync()

    reverb_bus: Bus = server.add_bus(calculation_rate='audio')
    
    # Create the effects synth.
    server.add_synth(
        add_action=AddAction.ADD_TO_TAIL,
        in_bus=reverb_bus,
        out_bus=0,
        synthdef=plateau_reverb,
        size=0.8,
        decay=0.5,
        diffusion=10.0,
        input_low_cut=0.5,
        input_high_cut=10.0,
        reverb_low_cut=1.0,
        reverb_high_cut=8.0,
        mod_speed=0.4,
        mod_depth=8.0,
        mod_shape=0.5,
        dry=0.7,
        wet=0.5
    )

    root_note = 53
    # F, A, C, Eb - 2 octaves
    arpeggio_notes = [
        midi_note_number_to_frequency(root_note + 0),
        midi_note_number_to_frequency(root_note + 4),
        midi_note_number_to_frequency(root_note + 7),
        midi_note_number_to_frequency(root_note + 11),
        midi_note_number_to_frequency(root_note + 12),
        midi_note_number_to_frequency(root_note + 16),
        midi_note_number_to_frequency(root_note + 19),
        midi_note_number_to_frequency(root_note + 23),
    ]
    arpeggio_sequence = ShufflePattern(
        forbid_repetitions=True,
        sequence=arpeggio_notes, 
        iterations=None,
    )
    
    arpeggio_pattern = EventPattern(
        frequency=arpeggio_sequence,
        synthdef=saw,
        delta=0.125,
        duration=0.0625,
        amplitude=0.1,
        out_bus=reverb_bus,
    )

    clock = Clock()
    clock.start(beats_per_minute=80.0)

    arpeggio_pattern.play(clock=clock, context=server)

    while True:
        continue

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)