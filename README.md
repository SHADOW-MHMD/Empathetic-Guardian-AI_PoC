# Empathetic-Guardian-AI_PoC

A technical PoC exploring the intersection of Affective Computing and local AI. This repository implements a "Virtual Heart" in C and wraps it with Python to drive an empathetic response engine.

## What is included

- `somatic_engine_v2.c` — core C engine modeling biometrics, hormones, and felt states
- `human_sim.py` — synthetic human simulator for multiple emotional scenarios
- `main.py` — Python integration using `ctypes` and OpenRouter API
- `requirements.txt` — Python dependencies
- `.env` — environment variables for OpenRouter API key

## Requirements

- Linux / Ubuntu
- GCC
- Python 3.10+
- A valid OpenRouter API key

## Setup

1. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

2. Set your OpenRouter API key in `.env`:

```bash
# edit .env and replace your_openrouter_key_here with your real key
OPENROUTER_API_KEY=your_actual_key_here
```

3. Compile the shared C library:

```bash
gcc -shared -o somatic_engine_v2.so -fPIC -O2 -lm somatic_engine_v2.c
```

## How it Works

The system simulates physiological stress markers through a C-based biophysical engine that calculates hormone levels (cortisol, adrenaline) and felt emotional states (anxiety, tension, energy) based on sensor inputs like heart rate, voice analysis, and text sentiment.

These somatic markers are injected into the LLM system prompt to modulate the AI's response tone and empathy. For example:
- High cortisol scenarios trigger grounding, supportive responses
- Low energy states elicit gentle, patient communication

The system includes **graceful degradation**: if the OpenRouter API is unavailable (rate limits, network issues), it falls back to local somatic mirroring using the C-engine's hormone calculations for offline operation.

## Run the app

Start the PoC with:

```bash
python3 main.py
```

The application will run six simulated emotional scenarios:
- `calm`
- `panic`
- `anxious`
- `scared`
- `crying`
- `heavy_hearted`

Each scenario displays color-coded terminal output with C-engine hormone states and AI-generated empathetic responses. All data is logged to `somatic_logs.csv` for analysis.

## Notes

- `main.py` reads `OPENROUTER_API_KEY` from `.env`
- If the API key is missing, the system falls back to somatic mirroring
- The C-engine math and OpenRouter model configuration are stable and unchanged
