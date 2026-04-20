"""Test-driven evaluation pipeline for empathy-focused LLM responses."""

import csv
import json
import time
from pathlib import Path
from typing import List, Dict, Any

from llm.llm_interface import generate_response
from llm.emotion_override import detect_emotional_context


SESSION_REPORT = Path("session_report.json")
PERFORMANCE_LOG = Path("performance_log.csv")


test_cases = [
    {
        "input": "my friend just died",
        "state": {
            "cortisol": 0.82,
            "dopamine": 0.3,
            "adrenaline": 0.6,
            "valence": -0.9,
            "arousal": 0.3,
            "dominance": 0.2,
        },
    },
    {
        "input": "I am so anxious and scared right now",
        "state": {
            "cortisol": 0.65,
            "dopamine": 0.3,
            "adrenaline": 0.7,
            "valence": -0.7,
            "arousal": 0.8,
            "dominance": 0.3,
        },
    },
    {
        "input": "what should I do with my career?",
        "state": {
            "cortisol": 0.3,
            "dopamine": 0.5,
            "adrenaline": 0.3,
            "valence": 0.1,
            "arousal": 0.4,
            "dominance": 0.5,
        },
    },
    {
        "input": "I just got promoted and I am so happy",
        "state": {
            "cortisol": 0.15,
            "dopamine": 0.8,
            "adrenaline": 0.4,
            "valence": 0.8,
            "arousal": 0.6,
            "dominance": 0.75,
        },
    },
]


def run_tests() -> List[Dict[str, Any]]:
    """Run all test cases and collect results."""
    print("=" * 80)
    print("EMPATHY-FOCUSED LLM RESPONSE TEST PIPELINE")
    print("=" * 80)

    results = []

    for i, tc in enumerate(test_cases, 1):
        emotion = detect_emotional_context(tc["input"])
        
        # Measure latency around response generation
        t0 = time.perf_counter()
        response = generate_response(tc["input"], tc["state"], emotional_context=emotion)
        latency = time.perf_counter() - t0
        
        result = {
            "test_case": i,
            "input": tc["input"],
            "detected_emotion": emotion["type"],
            "intensity": round(emotion["confidence"], 4),
            "state": tc["state"],
            "response": response,
            "latency": round(latency, 4),
            "response_length": len(response),
        }
        
        results.append(result)
        
        # Print to console
        print(f"\n[Case {i}] Input: {tc['input']}")
        print(
            f"Detected Emotion: {emotion['type']} "
            f"(intensity: {emotion['confidence']:.2f})"
        )
        print(f"State: V={tc['state']['valence']:.2f}, A={tc['state']['arousal']:.2f}, D={tc['state']['dominance']:.2f}")
        print(f"Response ({latency:.4f}s):\n  {response}")
        print(f"Response length: {len(response)} chars")
        print("-" * 80)

    return results


def save_session_report(results: List[Dict[str, Any]]) -> None:
    """Save results as structured JSON session report."""
    report = {
        "total_tests": len(results),
        "results": results,
    }
    with SESSION_REPORT.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nSession report saved: {SESSION_REPORT}")


def save_performance_log(results: List[Dict[str, Any]]) -> None:
    """Save performance metrics to CSV."""
    with PERFORMANCE_LOG.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "test_case",
                "input",
                "emotion",
                "intensity",
                "latency",
                "response_length",
            ],
        )
        writer.writeheader()
        for r in results:
            writer.writerow({
                "test_case": r["test_case"],
                "input": r["input"],
                "emotion": r["detected_emotion"],
                "intensity": r["intensity"],
                "latency": r["latency"],
                "response_length": r["response_length"],
            })
    print(f"Performance log saved: {PERFORMANCE_LOG}")


if __name__ == "__main__":
    results = run_tests()
    save_session_report(results)
    save_performance_log(results)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total test cases: {len(results)}")
    avg_latency = sum(r["latency"] for r in results) / len(results)
    print(f"Average latency: {avg_latency:.4f}s")
    print(f"Files generated:")
    print(f"  - {SESSION_REPORT}")
    print(f"  - {PERFORMANCE_LOG}")
    print("\nRun 'python3 plot_performance.py' to generate performance visualization.")


