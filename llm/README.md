# LLM Module

This folder contains the core prompt-building and emotion-detection logic used by the empathy response pipeline.

## Files

- `llm_interface.py` - builds prompts and calls OpenRouter, with a deterministic fallback when the API is unavailable.
- `emotion_override.py` - detects simple semantic emotion cues from user text.

## What it does

1. Reads user input.
2. Detects high-level emotion cues.
3. Builds a response prompt.
4. Sends the prompt to the LLM or uses a fallback response.

## Notes

- This is core runtime code.
- Keep changes minimal and backward compatible.
