from flask import Flask, render_template, request, redirect, url_for
from gpiozero import PWMLED
import RPi.GPIO as GPIO
from time import sleep
import threading
from enum import Enum
import os
import tempfile
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH
from mido import MidiFile
import numpy as np


class Mode(Enum):
    FIXED = 0
    FADE = 1
    SHOW = 2
    MORSE = 3


mode = Mode.FIXED

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
    return render_template('index.html', mode=mode)


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


@app.route('/play_mp3', methods=['POST'])
def play_mp3():
    """
    Endpoint per caricare un file MP3, convertirlo in MIDI e riprodurlo sul buzzer
    """
    if 'mp3_file' not in request.files:
        return 'Nessun file caricato', 400
    
    file = request.files['mp3_file']
    
    if file.filename == '':
        return 'Nessun file selezionato', 400
    
    if file and file.filename.endswith('.mp3'):
        # Salva temporaneamente il file MP3
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file_path = temp_file.name
            file.save(temp_file_path)
        
        # Avvia la conversione e riproduzione in un thread separato
        play_thread = threading.Thread(
            target=lambda: [mp3_to_midi_and_play(temp_file_path), os.unlink(temp_file_path)],
            daemon=True
        )
        play_thread.start()
        
        return redirect(url_for('index'))
    
    return 'Formato file non valido. Usa un file MP3.', 400


def control_led():
    global mode
    try:
        while True:
            if mode == Mode.FIXED:
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


def mp3_to_midi_and_play(mp3_file_path):
    """
    Converte un file MP3 in MIDI usando BasicPitch e riproduce le frequenze
    sul buzzer passivo.
    
    Args:
        mp3_file_path: percorso del file MP3 da convertire
    """
    try:
        print(f"Conversione di {mp3_file_path} in MIDI...")
        
        # Crea una directory temporanea per i file MIDI
        with tempfile.TemporaryDirectory() as temp_dir:
            # Usa BasicPitch per convertire MP3 in MIDI
            # onset_threshold e frame_threshold sono ottimizzati per la melodia
            model_output, midi_data, note_events = predict(
                mp3_file_path,
                ICASSP_2022_MODEL_PATH,
                onset_threshold=0.5,  # Soglia per rilevare l'inizio delle note
                frame_threshold=0.3,   # Soglia per mantenere le note
                minimum_note_length=100,  # Lunghezza minima nota in ms
                minimum_frequency=None,
                maximum_frequency=None,
                multiple_pitch_bends=False,
                melodia_trick=True,  # Importante: ottimizza per la melodia
                debug_file=None,
            )
            
            # Salva il MIDI in un file temporaneo
            midi_file_path = os.path.join(temp_dir, "output.mid")
            midi_data.write(midi_file_path)
            print(f"MIDI salvato temporaneamente in {midi_file_path}")
            
            # Leggi il file MIDI
            midi = MidiFile(midi_file_path)
            
            print("Riproduzione delle note sul buzzer...")
            
            # Itera attraverso tutte le tracce e messaggi MIDI
            for track in midi.tracks:
                time_elapsed = 0
                
                for msg in track:
                    time_elapsed += msg.time
                    
                    # Converti il tempo MIDI in secondi
                    time_in_seconds = msg.time / midi.ticks_per_beat * 0.5  # Tempo base
                    
                    if msg.type == 'note_on' and msg.velocity > 0:
                        # Nota attiva con velocità > 0
                        frequency = midi_note_to_frequency(msg.note)
                        print(f"Nota: {msg.note}, Frequenza: {frequency:.2f} Hz")
                        # Riproduce la frequenza per un breve momento
                        play_frequency(frequency, 0.1)
                    
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        # Pausa breve tra le note
                        sleep(time_in_seconds)
                    
                    else:
                        # Per altri messaggi, rispetta il timing
                        if time_in_seconds > 0:
                            sleep(time_in_seconds)
            
            print("Riproduzione completata!")
            
    except Exception as e:
        print(f"Errore durante la conversione/riproduzione: {e}")
        import traceback
        traceback.print_exc()


# Separate thread to control the LED
led_thread = threading.Thread(target=control_led, daemon=True)
led_thread.start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
