"""End-to-end JSONL dataset builder for Virtual Emotional Data Generator System v3."""

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

try:
    from .bridge import VirtualHeartBridge
    from .normalize import normalize_state
    from .text_generator import DEFAULT_MODEL, generate_sentence
except ImportError:
    from bridge import VirtualHeartBridge
    from normalize import normalize_state
    from text_generator import DEFAULT_MODEL, generate_sentence


DEFAULT_OUTPUT = Path(__file__).resolve().parent / "synthetic_emotion_dataset.jsonl"


def build_dataset(
    output_path: Path = DEFAULT_OUTPUT,
    runs: int = 8,
    min_steps: int = 10,
    max_steps: int = 20,
    model: str = DEFAULT_MODEL,
) -> List[Dict]:
    """Generate synthetic emotional dataset rows and write JSONL."""
    rows: List[Dict] = []
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as out:
        for _ in range(runs):
            bridge = VirtualHeartBridge()
            steps = random.randint(min_steps, max_steps)
            snapshots = bridge.collect_snapshots(steps=steps)

            for snapshot in snapshots:
                normalized = normalize_state(snapshot)
                sentence, prompt_used, model_used = generate_sentence(
                    normalized_state=normalized["normalized_state"],
                    derived_metrics=normalized["derived_metrics"],
                    model=model,
                )

                row = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "heart_state": normalized["heart_state"],
                    "derived_metrics": normalized["derived_metrics"],
                    "human_sentence": sentence,
                    "prompt_used": prompt_used,
                    "model": model_used,
                }

                out.write(json.dumps(row, ensure_ascii=True) + "\n")
                rows.append(row)

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Build synthetic emotional dataset JSONL")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output JSONL path")
    parser.add_argument("--runs", type=int, default=8, help="How many independent trajectories to generate")
    parser.add_argument("--min-steps", type=int, default=10, help="Minimum snapshots per trajectory")
    parser.add_argument("--max-steps", type=int, default=20, help="Maximum snapshots per trajectory")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="OpenRouter model id")
    args = parser.parse_args()

    if args.min_steps <= 0 or args.max_steps <= 0 or args.max_steps < args.min_steps:
        raise ValueError("Invalid steps range: ensure 0 < min_steps <= max_steps")

    rows = build_dataset(
        output_path=args.output,
        runs=max(1, args.runs),
        min_steps=args.min_steps,
        max_steps=args.max_steps,
        model=args.model,
    )
    print(f"Generated {len(rows)} rows in {args.output}")


if __name__ == "__main__":
    main()
