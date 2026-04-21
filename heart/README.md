# Heart Module

This folder contains the Virtual Heart Core used by the main empathy pipeline.

## Files

- `virtual_heart.c` - C implementation of the simulated emotional/physiological state machine.
- `virtual_heart_bridge.py` - ctypes bridge and Python fallback.

## What it does

1. Maintains a simulated internal state.
2. Updates stress, fear, sadness, happiness, motivation, overthinking, heart rate, and HRV.
3. Exposes a structured state dictionary for prompt injection.

## Notes

- This module is part of the current runtime path.
- The bridge is designed to continue working even if the C library cannot be compiled.
