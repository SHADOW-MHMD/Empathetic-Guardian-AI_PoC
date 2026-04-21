"""Replay dataset prompts to an LLM one-by-one and save responses."""

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Iterable, List

from dotenv import load_dotenv


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemma-2-9b-it:free"
DEFAULT_INPUT = Path(__file__).resolve().parent / "synthetic_emotion_dataset.jsonl"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "synthetic_emotion_dataset_with_llm.jsonl"
MODULE_ENV = Path(__file__).resolve().parent / ".env"
ROOT_ENV = Path(__file__).resolve().parent.parent / ".env"


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


def _decode_http_error(exc: urllib.error.HTTPError) -> str:
    try:
        raw = exc.read().decode("utf-8", errors="replace").strip()
    except Exception:
        raw = ""
    if not raw:
        return f"HTTP {exc.code}: {exc.reason}"

    compact = re.sub(r"\s+", " ", raw)
    if len(compact) > 300:
        compact = compact[:300] + "..."
    return f"HTTP {exc.code}: {compact}"


def call_openrouter(prompt: str, model: str, api_key: str) -> str:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You produce short, emotionally coherent human responses.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.8,
        "max_tokens": 120,
    }

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Virtual Emotional Prompt Replay",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(_decode_http_error(exc)) from exc

    parsed = json.loads(body)
    choices = parsed.get("choices", [])
    if not choices:
        raise ValueError("No choices returned from OpenRouter")
    text = choices[0].get("message", {}).get("content", "").strip()
    if not text:
        raise ValueError("Empty response returned from OpenRouter")
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay dataset prompts to LLM one-by-one")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Input dataset JSONL path")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output JSONL path with LLM responses")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="OpenRouter model ID")
    parser.add_argument("--fallback-model", type=str, default="openrouter/auto", help="Fallback model if primary fails")
    parser.add_argument("--start", type=int, default=0, help="Start index in JSONL")
    parser.add_argument("--limit", type=int, default=-1, help="How many rows to run, -1 means all")
    parser.add_argument("--api-key", type=str, default="", help="OpenRouter API key override")
    args = parser.parse_args()

    # Load env from both repository root and local module directory.
    load_dotenv(ROOT_ENV)
    load_dotenv(MODULE_ENV)

    api_key = (args.api_key or os.getenv("OPENROUTER_API_KEY", "")).strip()
    if api_key.startswith('"') and api_key.endswith('"'):
        api_key = api_key[1:-1].strip()
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Provide --api-key, or set OPENROUTER_API_KEY in "
            f"{ROOT_ENV} or {MODULE_ENV}."
        )

    if not args.input.exists():
        raise FileNotFoundError(f"Input JSONL not found: {args.input}")

    rows = read_jsonl(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with args.output.open("w", encoding="utf-8") as out:
        for row in iter_rows(rows, start=max(0, args.start), limit=args.limit):
            prompt = str(row.get("prompt_used", "")).strip()
            if not prompt:
                continue

            candidate_models: List[str] = []
            primary = args.model.strip()
            if primary:
                candidate_models.append(primary)
            if ":free" in primary:
                candidate_models.append(primary.replace(":free", ""))
            fallback = args.fallback_model.strip()
            if fallback:
                candidate_models.append(fallback)

            # Preserve order while removing duplicates.
            deduped_models: List[str] = []
            for m in candidate_models:
                if m not in deduped_models:
                    deduped_models.append(m)

            response = ""
            status = "error"
            used_model = args.model
            last_error = "unknown error"
            try:
                for model_id in deduped_models:
                    try:
                        response = call_openrouter(prompt=prompt, model=model_id, api_key=api_key)
                        status = "ok"
                        used_model = model_id
                        break
                    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError, RuntimeError) as exc:
                        last_error = str(exc)
                if status != "ok":
                    response = f"ERROR: {last_error}"
            except Exception as exc:
                response = f"ERROR: {exc}"
                status = "error"

            record = {
                **row,
                "llm_response": response,
                "llm_model_used": used_model,
                "llm_status": status,
            }
            out.write(json.dumps(record, ensure_ascii=True) + "\n")
            count += 1
            print(f"[{count}] {status}")

    print(f"Completed {count} prompts -> {args.output}")


if __name__ == "__main__":
    main()
