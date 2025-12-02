from flask import Flask, render_template, request, redirect, url_for
from gpiozero import PWMLED
import RPi.GPIO as GPIO
from time import sleep, time
import threading
from enum import Enum
import os
from mido import MidiFile, tempo2bpm


class Mode(Enum):
    FIXED = 0
    FADE = 1
    SHOW = 2
    MORSE = 3
    MUSIC = 4


mode = Mode.FIXED
current_song = None
music_stop_flag = False

# Music directory for MIDI files
MUSIC_DIR = os.path.join(os.path.dirname(__file__), 'music')

# LED config
GPIO.setmode(GPIO.BCM)
ledPin = 21
pwm_led = PWMLED(ledPin, active_high=True, initial_value=0, frequency=50)

# Buzzer config
buzzerPin = 18
GPIO.setup(buzzerPin, GPIO.OUT)

morse_dict = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
                    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
                    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
                    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
                    'Y': '-.--', 'Z': '--..', ' ': '/'
}

app = Flask(__name__)


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'


@app.route('/')
def index():
    global mode, current_song
    songs = get_available_songs()
    return render_template('index.html', mode=mode, songs=songs, current_song=current_song)


def get_available_songs():
    """Returns list of available MIDI files in the music folder"""
    songs = []
    if os.path.exists(MUSIC_DIR):
        for filename in os.listdir(MUSIC_DIR):
            if filename.lower().endswith(('.mid', '.midi')):
                # Format name for display
                display_name = filename.rsplit('.', 1)[0].replace('-', ' ').title()
                songs.append({
                    'filename': filename,
                    'display_name': display_name
                })
    return sorted(songs, key=lambda x: x['display_name'])


@app.route('/toggle_fade', methods=['POST'])
def toggle_fade():
    global mode, music_stop_flag
    music_stop_flag = True
    sleep(0.2)
    music_stop_flag = False
    mode = Mode.FADE
    return redirect(url_for('index'))


@app.route('/toggle_fixed', methods=['POST'])
def toggle_fixed():
    global mode, music_stop_flag
    music_stop_flag = True
    sleep(0.2)
    music_stop_flag = False
    mode = Mode.FIXED
    return redirect(url_for('index'))


@app.route('/toggle_show', methods=['POST'])
def toggle_show():
    global mode, music_stop_flag
    music_stop_flag = True
    sleep(0.2)
    music_stop_flag = False
    mode = Mode.SHOW
    return redirect(url_for('index'))


@app.route('/toggle_morse', methods=['POST'])
def toggle_morse():
    global mode, music_stop_flag
    music_stop_flag = True
    sleep(0.2)
    music_stop_flag = False
    mode = Mode.MORSE
    return redirect(url_for('index'))


@app.route('/toggle_music', methods=['POST'])
def toggle_music():
    """Toggle music mode with selected song"""
    global mode, music_stop_flag, current_song
    
    song_filename = request.form.get('song')
    if not song_filename:
        return 'No song selected', 400
    
    song_path = os.path.join(MUSIC_DIR, song_filename)
    if not os.path.exists(song_path):
        return 'Song not found', 404
    
    # Stop previous music if playing
    music_stop_flag = True
    sleep(0.3)
    music_stop_flag = False
    
    # Set MUSIC mode
    mode = Mode.MUSIC
    current_song = song_filename
    
    # Start playback in separate thread
    play_thread = threading.Thread(
        target=lambda: play_midi_with_lights(song_path),
        daemon=True
    )
    play_thread.start()
    
    return redirect(url_for('index'))


def control_led():
    """Main LED control loop for non-music modes"""
    global mode
    try:
        while True:
            if mode == Mode.MUSIC:
                # Music mode controls lights separately
                sleep(0.1)
            elif mode == Mode.FIXED:
                pwm_led.value = 1
                sleep(0.1)
            elif mode == Mode.FADE:
                for val in range(1, 11):
                    if mode != Mode.FADE:
                        break
                    pwm_led.value = val * 0.1
                    sleep(0.3)
                if mode != Mode.FADE:
                    continue
                sleep(1)
                for val in range(0, 10):
                    if mode != Mode.FADE:
                        break
                    pwm_led.value = 1 - (val * 0.1)
                    sleep(0.3)
                if mode != Mode.FADE:
                    continue
                sleep(1)
            elif mode == Mode.SHOW:
                pwm_led.value = 1
                sleep(0.8)
                if mode != Mode.SHOW:
                    continue
                pwm_led.value = 0
                sleep(0.8)
                if mode != Mode.SHOW:
                    continue
                for i in range(0, 10):
                    if mode != Mode.SHOW:
                        break
                    pwm_led.value = 1
                    sleep(0.2)
                    pwm_led.value = 0
                    sleep(0.2)
                if mode != Mode.SHOW:
                    continue
                for val in range(1, 11):
                    if mode != Mode.SHOW:
                        break
                    pwm_led.value = val * 0.1
                    sleep(0.3)
                if mode != Mode.SHOW:
                    continue
                sleep(1)
                for val in range(0, 10):
                    if mode != Mode.SHOW:
                        break
                    pwm_led.value = 1 - (val * 0.1)
                    sleep(0.3)
                if mode != Mode.SHOW:
                    continue
                sleep(1)
            elif mode == Mode.MORSE:
                morse_code = "MERRY CHRISTMAS"
                for char in morse_code:
                    if mode != Mode.MORSE:
                        break
                    if char in morse_dict:
                        for symbol in morse_dict[char]:
                            if mode != Mode.MORSE:
                                break
                            if symbol == '.':
                                pwm_led.value = 1
                                sleep(0.2)
                            elif symbol == '-':
                                pwm_led.value = 1
                                sleep(0.6)
                            elif symbol == '/':
                                sleep(1.4)  # Space between words
                            pwm_led.value = 0
                            sleep(0.2)
                        sleep(0.6)  # Space between letters
    except KeyboardInterrupt:
        pwm_led.close()


def midi_note_to_frequency(note_number):
    """
    Convert MIDI note number to frequency in Hz
    A440 = MIDI note 69
    """
    return 440.0 * (2.0 ** ((note_number - 69) / 12.0))


def play_tone(frequency, duration):
    """Play a tone on the passive buzzer"""
    if frequency <= 0 or duration <= 0:
        return
    
    period = 1.0 / frequency
    half_period = period / 2.0
    cycles = int(duration * frequency)
    
    for _ in range(cycles):
        GPIO.output(buzzerPin, GPIO.HIGH)
        sleep(half_period)
        GPIO.output(buzzerPin, GPIO.LOW)
        sleep(half_period)


def play_midi_with_lights(midi_file_path):
    """
    Play MIDI file on buzzer with synchronized light show
    Improved algorithm for better MIDI playback
    """
    global music_stop_flag, mode
    
    try:
        print(f"Loading {midi_file_path}...")
        midi = MidiFile(midi_file_path)
        
        print(f"Playing with light sync... (length: {midi.length:.1f}s)")
        
        # Merge all tracks into single timeline
        events = []
        for track in midi.tracks:
            current_time = 0
            for msg in track:
                current_time += msg.time
                if msg.type in ['note_on', 'note_off']:
                    events.append((current_time, msg))
        
        # Sort by time
        events.sort(key=lambda x: x[0])
        
        # Play events
        active_notes = {}
        last_time = 0
        tempo = 500000  # Default tempo (120 BPM)
        
        for event_time, msg in events:
            if music_stop_flag or mode != Mode.MUSIC:
                break
            
            # Calculate sleep time
            delta_ticks = event_time - last_time
            delta_seconds = (delta_ticks / midi.ticks_per_beat) * (tempo / 1000000.0)
            
            if delta_seconds > 0:
                sleep(delta_seconds)
            
            last_time = event_time
            
            if msg.type == 'note_on' and msg.velocity > 0:
                # Note on
                note = msg.note
                velocity = msg.velocity
                
                active_notes[note] = velocity
                
                # Play tone
                frequency = midi_note_to_frequency(note)
                
                # Light intensity based on velocity
                brightness = min(1.0, velocity / 100.0)
                pwm_led.value = brightness
                
                # Play short tone
                play_tone(frequency, 0.08)
                
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                # Note off
                if msg.note in active_notes:
                    del active_notes[msg.note]
                
                # Dim lights if no active notes
                if not active_notes:
                    pwm_led.value = 0.05
        
        print("Playback completed!")
        
    except Exception as e:
        print(f"Error during playback: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pwm_led.value = 0
        GPIO.output(buzzerPin, GPIO.LOW)


# Start LED control thread
led_thread = threading.Thread(target=control_led, daemon=True)
led_thread.start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
