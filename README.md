Empathetic Guardian AI

Minimal empathy testing pipeline for deterministic LLM evaluation.

## Run Tests

```bash
python3 test_empathy_responses.py
```

This generates `session_report.json` and `performance_log.csv`.

## Generate Performance Plots

```bash
python3 plot_performance.py
```

This reads `performance_log.csv` and writes `performance_plot.png`.

## Repository Layout

- `llm/` - emotion detection and response generation
- `test_empathy_responses.py` - main evaluation pipeline
- `plot_performance.py` - performance chart generator
- `session_report.json` - generated test report
- `performance_log.csv` - generated metrics log
- `performance_plot.png` - generated visualization
- `requirements.txt` - Python dependencies

## Notes

- Set `OPENROUTER_API_KEY` in `.env` if you want live API responses.
- If the API is unavailable, the pipeline falls back to deterministic templates.
- The repository intentionally keeps the runtime surface small so the empathy test flow is easy to run, audit, and commit.
