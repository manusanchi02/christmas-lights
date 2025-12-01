from flask import Flask, render_template, request, redirect, url_for
from gpiozero import PWMLED
import RPi.GPIO as GPIO
from time import sleep
import threading
from enum import Enum


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


# Separate thread to control the LED
led_thread = threading.Thread(target=control_led, daemon=True)
led_thread.start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
