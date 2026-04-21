# Empathetic Guardian AI PoC

Empathetic Guardian AI is a lightweight empathy-response prototype. It takes user text, detects coarse emotional context, builds an empathy-focused prompt, and asks an LLM to answer in a short, emotionally aligned way. When the API is unavailable, it falls back to deterministic templates so the pipeline still runs.

The repository now also includes an is2olated experimental synthetic dataset generator in `virtual_emotion_generator/`. That tree is separate from the core runtime and is used to create synthetic emotional trajectories and replay them into the LLM for training or evaluation.

## Project Overview

Core runtime flow:

1. User text enters the empathy pipeline.
2. `llm/emotion_override.py` detects a coarse semantic emotion.
3. `heart/virtual_heart_bridge.py` provides a simulated physiological/emotional state.
4. `llm/llm_interface.py` builds the final prompt using the user text, detected emotion, and virtual heart context.
5. OpenRouter is called when configured, otherwise a deterministic fallback response is returned.
6. `test_empathy_responses.py` runs the evaluation flow and writes reports.

Experimental synthetic data flow:

1. `virtual_emotion_generator/heart.c` produces a stochastic emotional time series.
2. `virtual_emotion_generator/bridge.py` collects sequential snapshots.
3. `virtual_emotion_generator/normalize.py` converts snapshots into consistent numeric features.
4. `virtual_emotion_generator/text_generator.py` creates short human-like emotional sentences.
5. `virtual_emotion_generator/builder.py` writes JSONL datasets.
6. `virtual_emotion_generator/replay_prompts.py` and `virtual_emotion_generator/replay_to_empathy_llm.py` replay rows into the LLM pipeline one by one.

## Architecture

### High-level data flow

```text
User Input
  -> Emotion Detection
  -> Virtual Heart State
  -> Prompt Builder
  -> LLM or Deterministic Fallback
  -> Response Output
  -> Session Logging
```

### Experimental generator flow

```text
Stochastic Heart Engine (C)
  -> Python Bridge
  -> Normalization Layer
  -> Sentence Generator
  -> JSONL Builder
  -> Optional LLM Replay
```

## Folder Structure

### Core runtime

- `llm/` - emotion detection and prompt construction for the empathy response engine.
- `heart/` - the virtual heart state used by the core pipeline.
- `test_empathy_responses.py` - the main evaluation and logging pipeline.
- `plot_performance.py` - lightweight CSV-to-ASCII/JSON trend reporting.

### Experimental synthetic data generator

- `virtual_emotion_generator/` - isolated synthetic emotional dataset generator and replay utilities.

### Generated artifacts

- `session_report.json` - structured run report from the empathy test pipeline.
- `performance_log.csv` - CSV metrics from the empathy test pipeline.
- `performance_trend.json` - lightweight trend summary from `plot_performance.py`.
- `virtual_emotion_generator/synthetic_emotion_dataset.jsonl` - generated synthetic heart-state dataset.
- `virtual_emotion_generator/synthetic_emotion_dataset_with_llm.jsonl` - dataset after first LLM sentence generation.
- `virtual_emotion_generator/synthetic_emotion_dataset_empathy.jsonl` - dataset after replaying rows into the empathy pipeline.

## Installation

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example file and add your OpenRouter key:

```bash
cp .env.example .env
```

Set:

```bash
OPENROUTER_API_KEY=your_key_here
```

If you use only fallback behavior, the key can be omitted and the pipeline will still run.

## How to Run Everything

This is the quickest end-to-end path from a clean checkout.

### Step 1: Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Step 2: Add your OpenRouter key

Edit `.env` and set:

```bash
OPENROUTER_API_KEY=your_key_here
```

### Step 3: Run the core empathy test pipeline

```bash
python3 test_empathy_responses.py
```

This writes:

- `session_report.json`
- `performance_log.csv`

### Step 4: Generate lightweight trend output

```bash
python3 plot_performance.py
```

This writes:

- `performance_trend.json`

### Step 5: Generate synthetic emotional data

```bash
python3 virtual_emotion_generator/builder.py --runs 8 --min-steps 10 --max-steps 20
```

This writes:

- `virtual_emotion_generator/synthetic_emotion_dataset.jsonl`

### Step 6: Replay synthetic prompts through the LLM

```bash
python3 virtual_emotion_generator/replay_prompts.py \
  --input virtual_emotion_generator/synthetic_emotion_dataset.jsonl \
  --output virtual_emotion_generator/synthetic_emotion_dataset_with_llm.jsonl \
  --model google/gemma-2-9b-it:free \
  --fallback-model openrouter/auto
```

### Step 7: Replay rows into the empathy pipeline one by one

Use the generated sentence field:

```bash
python3 virtual_emotion_generator/replay_to_empathy_llm.py \
  --input virtual_emotion_generator/synthetic_emotion_dataset_with_llm.jsonl \
  --output virtual_emotion_generator/synthetic_emotion_dataset_empathy.jsonl \
  --text-field human_sentence
```

Or use the raw LLM output field:

```bash
python3 virtual_emotion_generator/replay_to_empathy_llm.py \
  --input virtual_emotion_generator/synthetic_emotion_dataset_with_llm.jsonl \
  --output virtual_emotion_generator/synthetic_emotion_dataset_empathy.jsonl \
  --text-field llm_response
```

## Example Usage and Expected Output

### Core test pipeline

Expected console output includes case-by-case summaries like:

- detected emotion
- virtual heart state
- generated response
- tone alignment status

Expected files:

- `session_report.json`
- `performance_log.csv`

### Synthetic generator

Expected console output includes:

- number of rows generated
- target JSONL path

Expected files:

- `synthetic_emotion_dataset.jsonl`
- `synthetic_emotion_dataset_with_llm.jsonl`
- `synthetic_emotion_dataset_empathy.jsonl`

## Environment Setup

### Root `.env`

The root `.env` file is used by the core LLM runtime and helper scripts.

Required variable:

- `OPENROUTER_API_KEY`

Example file:

- [.env.example](.env.example)

### Experimental module `.env`

`virtual_emotion_generator/` also supports a local `.env` for replay scripts if you prefer to keep generator-specific configuration there.

## Module Docs

- [llm/README.md](llm/README.md) - core prompt and emotion detection notes.
- [heart/README.md](heart/README.md) - virtual heart context used by the runtime.
- [virtual_emotion_generator/README.md](virtual_emotion_generator/README.md) - synthetic dataset generator documentation.
- [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md) - short map of what is core, experimental, and generated.

## Troubleshooting

### `OPENROUTER_API_KEY is not set`

- Add the key to `.env`.
- Or pass `--api-key` to the replay scripts.
- If you only want offline behavior, the core empathy pipeline still works with deterministic fallbacks.

### `HTTP Error 404` from OpenRouter

- The requested model may not be available for your account or route.
- Try `openrouter/auto` or remove the `:free` suffix.
- Check whether your OpenRouter account can access the selected model.

### `ModuleNotFoundError: No module named 'llm'`

- Run scripts from the repository root.
- Use the provided script paths exactly as shown above.

### `builder.py` not found in repo root

- The synthetic generator lives in `virtual_emotion_generator/builder.py`.
- Run it with the full path shown in the commands above.

### GCC not installed

- The synthetic generator can still run using its Python fallback.
- Installing `gcc` enables the C engine path for the experimental dataset generator.

## Assumptions and Requirements

- Python 3.10+ is recommended.
- `gcc` is optional but enables the C-based synthetic heart engine.
- OpenRouter access is optional; fallback responses keep the system runnable without it.
- The experimental generator is separate from the core empathy test pipeline.
- Generated CSV and JSONL artifacts are outputs, not source files.

## Developer Notes

- Core runtime code lives in `llm/` and `heart/`.
- Experimental data generation lives in `virtual_emotion_generator/`.
- Treat the generated JSONL and CSV files as artifacts that can be regenerated at any time.
- Keep changes to the prompt-building logic backward compatible so the empathy test pipeline remains stable.
