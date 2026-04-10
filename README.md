# Empathetic-Guardian-AI_PoC

A technical PoC exploring the intersection of Affective Computing and local AI. This repository implements a "Virtual Heart" in C and wraps it with Python to drive an empathetic response engine.

## What is included

- `somatic_engine_v2.c` — core C engine modeling biometrics, hormones, and felt states
- `compile.sh` — compiles the engine into `somatic_engine_v2.so`
- `human_sim.py` — synthetic human simulator for calm and panic scenarios
- `main.py` — Python integration using `ctypes` and Google Gemini
- `requirements.txt` — Python dependencies
- `.env.example` — example environment variables for Gemini credentials

## Requirements

- Linux / Ubuntu
- GCC
- Python 3.10+
- A valid Google Gemini API key

## Setup

1. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

2. Copy the example environment file and set your Gemini API key:

```bash
cp .env.example .env
# edit .env and replace YOUR_GEMINI_API_KEY_HERE with your real key
```

3. Compile the shared C library:

```bash
bash compile.sh
```

## Run the app

Start the PoC with:

```bash
python3 main.py
```

The application will run two simulated scenarios:
- `calm`
- `panic`

It prints the C engine hormone state and the Gemini-generated response for each.

## Notes

- `main.py` reads `GEMINI_API_KEY` from `.env`
- If you do not have a Gemini key, the integration will raise a configuration error
- The README is intentionally minimal to keep the PoC focused on the runtime flow
