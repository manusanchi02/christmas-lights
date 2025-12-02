#!/usr/bin/env python3
"""Test MIDI file quality and analyze tracks"""

from mido import MidiFile
import os

MUSIC_DIR = 'music'

for filename in os.listdir(MUSIC_DIR):
    if filename.lower().endswith(('.mid', '.midi')):
        filepath = os.path.join(MUSIC_DIR, filename)
        print(f"\n{'='*60}")
        print(f"Analyzing: {filename}")
        print('='*60)
        
        midi = MidiFile(filepath)
        print(f"Type: {midi.type}")
        print(f"Ticks per beat: {midi.ticks_per_beat}")
        print(f"Length: {midi.length:.2f} seconds")
        print(f"Number of tracks: {len(midi.tracks)}")
        
        for i, track in enumerate(midi.tracks):
            note_count = sum(1 for msg in track if msg.type == 'note_on')
            print(f"  Track {i}: {track.name if hasattr(track, 'name') else 'Unnamed'} - {note_count} notes")
            
            # Show first few messages
            print(f"    First messages:")
            for j, msg in enumerate(track[:5]):
                print(f"      {msg}")
