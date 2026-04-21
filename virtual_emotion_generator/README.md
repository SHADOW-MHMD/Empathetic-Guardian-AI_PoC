# Virtual Emotional Data Generator System v3

This folder is an isolated experimental dataset generator for synthetic emotional training data.

## Files

- `heart.c` - stochastic virtual heart engine.
- `bridge.py` - Python bridge with C-first execution and fallback simulation.
- `normalize.py` - clamps and derives normalized emotional metrics.
- `text_generator.py` - generates human-like emotional sentences.
- `builder.py` - builds JSONL datasets end to end.
- `replay_prompts.py` - replays generated prompts to OpenRouter one by one.
- `replay_to_empathy_llm.py` - sends generated rows into the empathy LLM flow.

## Outputs

- `synthetic_emotion_dataset.jsonl`
- `synthetic_emotion_dataset_with_llm.jsonl`
- `synthetic_emotion_dataset_empathy.jsonl`

## Notes

- This tree is experimental and isolated from the main runtime pipeline.
- It should not be required to run the existing empathy test flow.
