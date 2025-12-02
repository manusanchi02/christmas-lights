# 🎄 Christmas Lights Controller

A Raspberry Pi project to control Christmas lights via a web interface with multiple lighting modes.

![Circuit Scheme](docs/scheme.png)

## 📋 Description

This project allows you to control Christmas lights through a Raspberry Pi using a simple web interface. The application offers different lighting modes that can be selected from any device connected to the same network as the Raspberry Pi.

### Main Features

- **Web Control**: Responsive web interface accessible from smartphones, tablets, or computers
- **Multiple Modes**: Various lighting modes to create festive atmospheres
- **PWM Control**: Precise brightness control through PWM modulation
- **Multi-threading**: Parallel management of web server and LED control
- **Remote Shutdown**: Ability to shut down the system from the web interface

## 🎨 Available Modes

### 🔆 Fixed
Lights remain on at constant maximum intensity.

### 🌊 Fade
Gradual fade effect: lights slowly increase in intensity to maximum, then decrease until they turn off, creating a continuous "breathing" cycle.

### ✨ Show
A complex sequence that combines different effects:
- Initial flash
- Rapid sequence of on/off switching
- Gradual fade in and fade out

### 📡 Morse
Lights transmit the message "MERRY CHRISTMAS" in Morse code, using:
- Dots (short signals) of 0.2 seconds
- Dashes (long signals) of 0.6 seconds
- Pauses between letters and words according to Morse standard

### 🎵 Music Player
Select from pre-loaded Christmas songs that will:
1. Play the melody through a passive buzzer connected to GPIO18
2. **Automatically synchronize the Christmas lights with the music**
3. Adjust brightness based on note intensity

**Available songs**:
- Jingle Bells
- Last Christmas
- We Wish You a Merry Christmas
- It's Beginning to Look a Lot Like Christmas

## 🔧 Required Hardware

- Raspberry Pi (any model with GPIO)
- Christmas lights or LED strip
- **Passive buzzer** (for music playback)
- Appropriate resistors
- Power supply for the lights (if needed)
- Connecting wires
- Transistor or LED driver (e.g., MOSFET) - only if required by your specific lights

### Pin Configuration

- **GPIO21**: LED/Christmas lights control (PWM)
- **GPIO18**: Passive buzzer for music playback

### Circuit Scheme

The complete circuit is available in the `docs/` folder both in Fritzing format (`.fzz`) and as a PNG image. 

**Important Notes:**
- The circuit uses **GPIO 21** because it supports hardware PWM. Changing to a different pin may result in poor performance or loss of PWM functionality.
- The **resistor value** shown in the schematic is arbitrary and must be calculated based on the actual lights you connect.
- The **red LED** in the diagram is just a placeholder. In the actual implementation, this should be replaced with your real Christmas lights (connected through an appropriate driver/transistor).

## 💻 Technologies Used

- **Python**: Main project language
- **Flask**: Web framework for the user interface
- **gpiozero**: Library for Raspberry Pi GPIO control
- **Bootstrap 5**: CSS framework for responsive interface
- **Threading**: For parallel management of web server and LED control
- **Mido**: MIDI file processing library

## 🚀 Installation

### Prerequisites

```bash
# Update the system
sudo apt update && sudo apt upgrade -y

# Install Python and pip if not already present
sudo apt install python3 python3-pip -y
```

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/manusanchi02/christmas-lights.git
cd christmas-lights

# Install all required Python libraries from requirements.txt
pip3 install -r requirements.txt
```

### Setup

1. Make sure your lights are correctly connected to **GPIO 21** through an appropriate driver circuit
2. Connect the passive buzzer to **GPIO 18** (positive terminal to GPIO18, negative to GND)

## 📱 Usage

### Starting the Application

```bash
python3 app.py
```

The application will be accessible from:
- Local: `http://localhost:5000`
- From other devices: `http://[RASPBERRY-PI-IP]:5000`

### Web Interface

The interface features:
- Current light status indicator
- Mode selection buttons (Fade, Fixed, Show, Morse)
- **MIDI upload form** for music playback on the buzzer
- Shutdown button to power off the system

### Using the Music Player

1. Access the web interface at `http://[RASPBERRY-PI-IP]:5000`
2. Scroll to the "Riproduci Melodia" section
3. Select a song from the dropdown menu
4. Click "Riproduci con Luci Sincronizzate"
5. The melody will play on the buzzer while the lights synchronize with the music!
6. Click "Ferma Musica" to stop playback at any time

**Light synchronization**:
- Lights brightness follows note intensity
- Higher notes create brighter flashes
- Lights dim during pauses
- Creates a dynamic light show matching the music rhythm

### iOS Shortcut for Quick Launch

For iOS users, you can create a Siri shortcut to start the application remotely via SSH:

1. Open the **Shortcuts** app on your iOS device
2. Tap **+** to create a new shortcut
3. Add the **"Run Script Over SSH"** action
4. Configure the SSH connection:
   - **Host**: Your Raspberry Pi's IP address
   - **Port**: 22 (default SSH port)
   - **User**: Your Raspberry Pi username (usually `pi`)
   - **Authentication**: Use password or SSH key
5. In the **Script** field, enter the command to start the application:
   ```bash
   cd ~/christmas-lights && python3 app.py
   ```
   Or use the full path if located elsewhere:
   ```bash
   cd /path/to/christmas-lights && python3 app.py
   ```
6. Name your shortcut (e.g., "Start Christmas Lights")
7. Optionally, add it to your home screen or use with Siri voice commands

**Tip**: You can create separate shortcuts for different modes by using curl commands to directly trigger specific endpoints:
```bash
curl -X POST http://[RASPBERRY-PI-IP]:5000/toggle_fade
```

## 🛠️ Advanced Configuration

### Changing GPIO Pins

In the `app.py` file, modify the variables:
```python
ledPin = 21     # Change to desired pin for lights
buzzerPin = 18  # Change to desired pin for buzzer
```

**⚠️ Warning**: GPIO 21 is used because it supports hardware PWM. Changing to a non-PWM pin may result in flickering or poor performance. Raspberry Pi hardware PWM pins are: GPIO 12, 13, 18, and 19. See [GPIO scheme](https://pinout.xyz/#)

### Tuning Music Playback

You can adjust the playback speed in the `midi_play()` function:

```python
time_in_seconds = msg.time / midi.ticks_per_beat * 0.5  # 0.5 = normal speed
```

- `0.25` = 2x faster
- `0.5` = normal speed  
- `1.0` = 2x slower

### Customizing Effects

All lighting effects are defined in the `control_led()` function in `app.py`. You can modify:
- Transition speeds (`sleep()` parameters)
- Maximum/minimum intensity (`pwm_led.value`)
- On/off sequences

### Custom Morse Message

Modify the string in `app.py`:
```python
morse_code = "MERRY CHRISTMAS"  # Customize your message
```

## 📁 Project Structure

```
christmas-lights/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── music/                 # Pre-loaded MIDI songs
│   ├── jingle-bells.mid
│   ├── last-christmas.mid
│   ├── we-wish-you-a-merry-christmas.MID
│   └── its-beginning-to-look-a-lot-like-christmas.mid
├── templates/
│   └── index.html        # Web interface
├── static/
│   └── style.css         # CSS styles
├── docs/
│   ├── scheme.fzz        # Fritzing scheme
│   └── scheme.png        # Circuit scheme image
├── LICENSE
└── README.md
```

## 🎶 Adding More Songs

To add more songs to your collection:

1. Download MIDI files from sites like [MIDIWorld](https://www.midiworld.com/) or [FreeMIDI](https://freemidi.org/)
2. Copy the `.mid` or `.midi` files to the `music/` folder
3. Restart the application
4. The new songs will appear automatically in the dropdown menu

## ⚚️ How It Works: Music & Light Synchronization

1. **Song Selection**: User selects a pre-loaded MIDI file from the dropdown
2. **MIDI Processing**: Mido reads the MIDI file and extracts note events, timing, and velocity
3. **Frequency Calculation**: Each MIDI note number is converted to its frequency in Hz
   - Formula: `f = 440 × 2^((n-69)/12)` where n is the MIDI note number
4. **Buzzer Playback**: GPIO18 is toggled at the calculated frequency to produce the tone
5. **Light Synchronization**: PWM LED brightness is adjusted based on:
   - Note velocity (how hard the note is played) = brightness intensity
   - Active notes = lights on, pauses = lights dim
   - Creates a dynamic visual effect matching the music rhythm

## 🔒 Security

- The application is configured to accept connections from any IP address on the local network (`host='0.0.0.0'`)
- Debug mode is disabled for security reasons
- It is recommended to use the application only on trusted networks

## 📝 License

This project is released under the license specified in the LICENSE file.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## 👤 Author

**manusanchi02**

- GitHub: [@manusanchi02](https://github.com/manusanchi02)

## 🎅 Happy Holidays!

Enjoy your Raspberry Pi-controlled Christmas lights! 🎄✨
