# Project Overview

## Core runtime

- `llm/` - the main empathy response engine.
- `heart/` - the virtual heart context used by the main pipeline.
- `test_empathy_responses.py` - the current test-driven pipeline.

## Experimental data generation

- `virtual_emotion_generator/` - synthetic dataset generator and replay tools.

## Generated artifacts

- `session_report.json`
- `performance_log.csv`
- `performance_trend.json`
- `virtual_emotion_generator/synthetic_emotion_dataset.jsonl`
- `virtual_emotion_generator/synthetic_emotion_dataset_with_llm.jsonl`
- `virtual_emotion_generator/synthetic_emotion_dataset_empathy.jsonl`

## Recommended editing rule

- Keep core runtime changes inside `llm/` and `heart/` only when necessary.
- Keep dataset generation changes inside `virtual_emotion_generator/`.
- Treat generated JSONL/CSV files as outputs, not source code.
