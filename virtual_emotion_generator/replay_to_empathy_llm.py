"""Replay synthetic rows into empathy LLM one-by-one with heart context."""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List

# Ensure repository root is importable when script is run directly.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from llm.emotion_override import detect_emotional_context
from llm.llm_interface import generate_response


DEFAULT_INPUT = Path(__file__).resolve().parent / "synthetic_emotion_dataset_with_llm.jsonl"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "synthetic_emotion_dataset_empathy.jsonl"


def read_jsonl(path: Path) -> List[Dict]:
    rows: List[Dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def iter_rows(rows: List[Dict], start: int, limit: int) -> Iterable[Dict]:
    end = len(rows) if limit < 0 else min(len(rows), start + limit)
    for i in range(start, end):
        yield rows[i]


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _normalize_heart_to_llm_state(heart_state: Dict[str, float]) -> Dict[str, float]:
    stress = _clamp(float(heart_state.get("stress", 20.0)) / 100.0, 0.0, 1.0)
    happiness = _clamp(float(heart_state.get("happiness", 50.0)) / 100.0, 0.0, 1.0)
    fear = _clamp(float(heart_state.get("fear", 20.0)) / 100.0, 0.0, 1.0)
    sadness = _clamp(float(heart_state.get("sadness", 20.0)) / 100.0, 0.0, 1.0)
    motivation = _clamp(float(heart_state.get("motivation", 50.0)) / 100.0, 0.0, 1.0)

    return {
        "cortisol": stress,
        "dopamine": happiness,
        "adrenaline": fear,
        "valence": _clamp(happiness - sadness, -1.0, 1.0),
        "arousal": _clamp((stress + fear) / 2.0, 0.0, 1.0),
        "dominance": motivation,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Send synthetic rows to empathy LLM one-by-one")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Input JSONL path")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output JSONL path")
    parser.add_argument("--start", type=int, default=0, help="Start index")
    parser.add_argument("--limit", type=int, default=-1, help="How many rows to process, -1 means all")
    parser.add_argument(
        "--text-field",
        type=str,
        default="human_sentence",
        choices=["human_sentence", "llm_response"],
        help="Which field to send as user text",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"Input JSONL not found: {args.input}")

    rows = read_jsonl(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with args.output.open("w", encoding="utf-8") as out:
        for row in iter_rows(rows, start=max(0, args.start), limit=args.limit):
            heart_state = row.get("heart_state", {})
            user_text = str(row.get(args.text_field, "")).strip()
            if not user_text:
                continue

            llm_state = _normalize_heart_to_llm_state(heart_state)
            emotional_context = detect_emotional_context(user_text)

            response = generate_response(
                user_input=user_text,
                state=llm_state,
                emotional_context=emotional_context,
                virtual_heart_state=heart_state,
            )

            record = {
                **row,
                "empathy_input_text": user_text,
                "empathy_emotional_context": emotional_context,
                "empathy_state_vector": llm_state,
                "empathy_response": response,
            }
            out.write(json.dumps(record, ensure_ascii=True) + "\n")
            count += 1
            print(f"[{count}] ok")

    print(f"Completed {count} rows -> {args.output}")


if __name__ == "__main__":
    main()
