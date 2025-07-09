# ChronOBS 

A tool to help with synchronization between observers in League of Legends productions

## 🚀 Installation

TBD

## 💻 Usage

### Prerequisites
- You need an MQTT Broker running and accessible for all your team. We recommend using [Eclipse Mosquitto](https://mosquitto.org/)
- Observers will need to enable the [_Replay API_](https://developer.riotgames.com/docs/lol#game-client-api_replay-api)

### 1. Set up the MQTT Broker Connection
- Enter the MQTT broker URL (default: localhost)
- Enter the port (default: 1883)
- Click "CONNECT"

### 2. Mode Selection

#### 🏭 Producer Mode
This is the producer mode, designed to be used by the producer (the one who is receiving the feeds from the observers):
- A 5-character room ID is automatically generated
- Will see the connected observers
- Can assign the main observer role

#### 👁️ Observer Mode
This is the observer mode, designed to be used by the observers (the ones _in-game_ who will send the video feed to the producer):
- Join a room by specifying the room ID (provided by the producer)
- "SYNC" button will update your League of Legends game 

## 🔧 Contribution

Want to modify the code and add your own features? Here are the steps:

1. Install the prerequisites:
- Python 3.12 or higher
- MQTT Broker running
- Replay API enabled in your League of Legends installation

2. Set up the Python environment

We recommend using a virtual environment. Create one with:
```sh
python -m venv {ENV_PATH}
```

Activate the virtual environment based on your OS:
```sh
# Windows
./{ENV_PATH}/Scripts/activate

# Linux || macOS
source {ENV_PATH}/bin/activate
```

Then install the dependencies:
```sh
python -m pip install -r requirements.txt
```

3. Compile the program:
```bash
pyinstaller --onefile --name ChronobsPY src/main.py
```
