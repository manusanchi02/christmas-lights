from flask import Flask, render_template, request, redirect, url_for
from gpiozero import PWMLED
import RPi.GPIO as GPIO
from time import sleep
import threading
from enum import Enum
import os
from mido import MidiFile


class Mode(Enum):
    FIXED = 0
    FADE = 1
    SHOW = 2
    MORSE = 3
    MUSIC = 4


mode = Mode.FIXED
music_playing = False
music_stop_flag = False

# Directory per i file MIDI
MUSIC_DIR = os.path.join(os.path.dirname(__file__), 'music')

# Led config
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
    global mode
    # Ottieni la lista delle canzoni disponibili
    songs = get_available_songs()
    return render_template('index.html', mode=mode, songs=songs)


def get_available_songs():
    """Restituisce la lista dei file MIDI disponibili nella cartella music"""
    songs = []
    if os.path.exists(MUSIC_DIR):
        for filename in os.listdir(MUSIC_DIR):
            if filename.lower().endswith(('.mid', '.midi')):
                # Formatta il nome per la visualizzazione
                display_name = filename.rsplit('.', 1)[0].replace('-', ' ').title()
                songs.append({
                    'filename': filename,
                    'display_name': display_name
                })
    return sorted(songs, key=lambda x: x['display_name'])


@app.route('/toggle_fade', methods=['POST'])
def toggle_fade():
    global mode
    mode = Mode.FADE
    return redirect(url_for('index', mode=mode))


@app.route('/toggle_fixed', methods=['POST'])
def toggle_fixed():
    global mode
    mode = Mode.FIXED
    return redirect(url_for('index', mode=mode))


@app.route('/toggle_show', methods=['POST'])
def toggle_show():
    global mode
    mode = Mode.SHOW
    return redirect(url_for('index', mode=mode))


@app.route('/toggle_morse', methods=['POST'])
def toggle_morse():
    global mode
    mode = Mode.MORSE
    return redirect(url_for('index', mode=mode))


@app.route('/play_song', methods=['POST'])
def play_song():
    """
    Endpoint per riprodurre una canzone precaricata
    """
    global mode, music_stop_flag
    
    song_filename = request.form.get('song')
    if not song_filename:
        return 'Nessuna canzone selezionata', 400
    
    song_path = os.path.join(MUSIC_DIR, song_filename)
    
    if not os.path.exists(song_path):
        return 'Canzone non trovata', 404
    
    # Ferma musica precedente se in esecuzione
    music_stop_flag = True
    sleep(0.5)
    music_stop_flag = False
    
    # Imposta la modalità MUSIC
    mode = Mode.MUSIC
    
    # Avvia la riproduzione in un thread separato
    play_thread = threading.Thread(
        target=lambda: midi_play_with_lights(song_path),
        daemon=True
    )
    play_thread.start()
    
    return redirect(url_for('index'))


@app.route('/stop_music', methods=['POST'])
def stop_music():
    """
    Ferma la riproduzione musicale
    """
    global music_stop_flag, mode
    music_stop_flag = True
    mode = Mode.FIXED
    return redirect(url_for('index'))


def control_led():
    global mode, music_playing
    try:
        while True:
            if mode == Mode.MUSIC:
                # In modalità musica, le luci sono controllate dalla funzione di riproduzione
                if not music_playing:
                    pwm_led.value = 0
                sleep(0.1)
            elif mode == Mode.FIXED:
                pwm_led.value = 1
            elif mode == Mode.FADE:
                for val in range(1, 11):
                    pwm_led.value = val * 0.1
                    sleep(0.3)
                sleep(1)
                for val in range(0, 10):
                    pwm_led.value = 1 - (val * 0.1)
                    sleep(0.3)
                sleep(1)
            elif mode == Mode.SHOW:
                pwm_led.value = 1
                sleep(0.8)
                pwm_led.value = 0
                sleep(0.8)
                for i in range(0, 10):
                    pwm_led.value = 1
                    sleep(0.2)
                    pwm_led.value = 0
                    sleep(0.2)
                for val in range(1, 11):
                    pwm_led.value = val * 0.1
                    sleep(0.3)
                sleep(1)
                for val in range(0, 10):
                    pwm_led.value = 1 - (val * 0.1)
                    sleep(0.3)
                sleep(1)
            elif mode == Mode.MORSE:
                morse_code = "MERRY CHRISTMAS"
                for char in morse_code:
                    if char in morse_dict:
                        for symbol in morse_dict[char]:
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
    Converte un numero di nota MIDI in frequenza (Hz)
    La440 = nota MIDI 69
    """
    return 440.0 * (2.0 ** ((note_number - 69) / 12.0))


def play_frequency(frequency, duration):
    """
    Riproduce una frequenza sul buzzer passivo per una durata specificata
    """
    if frequency <= 0:
        sleep(duration)
        return
    
    period = 1.0 / frequency
    half_period = period / 2.0
    cycles = int(duration * frequency)
    
    for _ in range(cycles):
        GPIO.output(buzzerPin, GPIO.HIGH)
        sleep(half_period)
        GPIO.output(buzzerPin, GPIO.LOW)
        sleep(half_period)


def midi_play_with_lights(midi_file_path):
    """
    Riproduce un file MIDI sul buzzer passivo e sincronizza le luci.
    
    Args:
        midi_file_path: percorso del file MIDI da riprodurre
    """
    global music_playing, music_stop_flag
    
    try:
        music_playing = True
        print(f"Caricamento di {midi_file_path}...")
        
        # Leggi il file MIDI
        midi = MidiFile(midi_file_path)
        
        print("Riproduzione con sincronizzazione luci...")
        
        active_notes = set()  # Traccia le note attive
        
        # Itera attraverso tutte le tracce e messaggi MIDI
        for track in midi.tracks:
            if music_stop_flag:
                break
                
            for msg in track:
                if music_stop_flag:
                    break
                    
                # Converti il tempo MIDI in secondi
                time_in_seconds = msg.time / midi.ticks_per_beat * 0.5
                
                if msg.type == 'note_on' and msg.velocity > 0:
                    # Nota attiva
                    active_notes.add(msg.note)
                    frequency = midi_note_to_frequency(msg.note)
                    
                    # Sincronizza le luci con l'intensità della nota
                    # Note più alte = luci più brillanti
                    brightness = min(1.0, (msg.velocity / 127.0) * 1.5)
                    pwm_led.value = brightness
                    
                    # Riproduce la frequenza
                    play_frequency(frequency, 0.1)
                    
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    # Nota terminata
                    if msg.note in active_notes:
                        active_notes.remove(msg.note)
                    
                    # Se non ci sono note attive, abbassa le luci
                    if not active_notes:
                        pwm_led.value = 0.1
                    
                    sleep(time_in_seconds)
                else:
                    # Per altri messaggi, rispetta il timing
                    if time_in_seconds > 0:
                        sleep(time_in_seconds)
        
        print("Riproduzione completata!")
        
    except Exception as e:
        print(f"Errore durante la riproduzione: {e}")
        import traceback
        traceback.print_exc()
    finally:
        music_playing = False
        pwm_led.value = 0


# Separate thread to control the LED
led_thread = threading.Thread(target=control_led, daemon=True)
led_thread.start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
