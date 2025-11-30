from flask import Flask, render_template, request, redirect, url_for
from gpiozero import PWMLED
from time import sleep
import threading
from enum import Enum

class Mode(Enum):
    FIXED = 0
    FADE = 1
    SHOW = 2
    
mode = Mode.FIXED

# Configurazione del LED
ledPin = 21
pwm_led = PWMLED(ledPin, active_high=True, initial_value=0, frequency=50)

# Creazione dell'app Flask
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
 
# Funzione per il controllo del LED
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
                for i in range (0,10):
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
    except KeyboardInterrupt:
        pwm_led.close()

# Avvio della funzione di controllo LED in un thread separato
led_thread = threading.Thread(target=control_led, daemon=True)
led_thread.start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
