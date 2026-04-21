"""Test-driven evaluation pipeline for empathy-focused LLM responses."""

import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

from heart.virtual_heart_bridge import default_bridge
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


def _normalize_heart_to_llm_state(heart_state: Dict[str, float]) -> Dict[str, float]:
    """Map heart metrics into the existing LLM state vector format."""
    stress = heart_state["stress"] / 100.0
    happiness = heart_state["happiness"] / 100.0
    fear = heart_state["fear"] / 100.0
    sadness = heart_state["sadness"] / 100.0
    motivation = heart_state["motivation"] / 100.0

    return {
        "cortisol": min(1.0, max(0.0, stress)),
        "dopamine": min(1.0, max(0.0, happiness)),
        "adrenaline": min(1.0, max(0.0, fear)),
        "valence": min(1.0, max(-1.0, happiness - sadness)),
        "arousal": min(1.0, max(0.0, (stress + fear) / 2.0)),
        "dominance": min(1.0, max(0.0, motivation)),
    }


def _stimulus_from_emotion(emotion_type: str, intensity: float) -> Dict[str, float]:
    """Convert semantic emotion class to heart engine stimulus values in [0, 1]."""
    stress = 0.15
    positive = 0.20

    if emotion_type in {"grief", "distress", "anger"}:
        stress = 0.55 + (0.40 * intensity)
        positive = 0.05
    elif emotion_type == "positive":
        stress = 0.05
        positive = 0.55 + (0.40 * intensity)

    return {
        "stress_input": min(1.0, max(0.0, stress)),
        "positive_input": min(1.0, max(0.0, positive)),
    }


def _is_tone_aligned(response: str, inferred_emotion: str) -> bool:
    """Lightweight heuristic to verify empathy-tone alignment."""
    text = (response or "").lower()

    shared = ["i hear", "i'm here", "with you", "that sounds", "makes sense"]
    if inferred_emotion in {"grief", "distress", "anger", "sad and withdrawn", "stressed and overwhelmed", "anxious and fearful"}:
        return any(token in text for token in shared + ["sorry", "overwhelming", "heavy", "hard"])
    if inferred_emotion in {"positive", "hopeful and motivated"}:
        return any(token in text for token in ["congrat", "glad", "proud", "happy", "celebrate", "great"]) \
            or any(token in text for token in shared)
    return any(token in text for token in shared)


def run_tests() -> List[Dict[str, Any]]:
    """Run all test cases and collect results."""
    print("=" * 80)
    print("EMPATHY-FOCUSED LLM RESPONSE TEST PIPELINE")
    print("=" * 80)

    results = []
    heart = default_bridge()

    for i, tc in enumerate(test_cases, 1):
        emotion = detect_emotional_context(tc["input"])
        stimulus = _stimulus_from_emotion(emotion["type"], emotion["confidence"])
        heart_state = heart.update(
            stress_input=stimulus["stress_input"],
            positive_input=stimulus["positive_input"],
        )
        llm_state = _normalize_heart_to_llm_state(heart_state)
        
        # Measure latency around response generation
        t0 = time.perf_counter()
        response = generate_response(
            tc["input"],
            llm_state,
            emotional_context=emotion,
            virtual_heart_state=heart_state,
        )
        latency = time.perf_counter() - t0
        tone_aligned = _is_tone_aligned(response, heart_state["emotion"])
        
        result = {
            "test_case": i,
            "input": tc["input"],
            "detected_emotion": emotion["type"],
            "inferred_emotion": heart_state["emotion"],
            "intensity": round(emotion["confidence"], 4),
            "stimulus": stimulus,
            "heart_state": heart_state,
            "state": llm_state,
            "response": response,
            "latency": round(latency, 4),
            "response_length": len(response),
            "tone_aligned": tone_aligned,
        }
        
        results.append(result)
        
        # Print to console
        print(f"\n[Case {i}] Input: {tc['input']}")
        print(
            f"Detected Emotion: {emotion['type']} "
            f"(intensity: {emotion['confidence']:.2f})"
        )
        print(
            "Heart State: "
            f"emotion={heart_state['emotion']}, "
            f"stress={heart_state['stress']:.1f}, hr={heart_state['heart_rate']:.1f}, hrv={heart_state['hrv']:.1f}"
        )
        print(f"Stimulus: stress={stimulus['stress_input']:.2f}, positive={stimulus['positive_input']:.2f}")
        print(f"Response ({latency:.4f}s):\n  {response}")
        print(f"Response length: {len(response)} chars")
        print(f"Tone aligned: {tone_aligned}")
        print("-" * 80)

    return results


def save_session_report(results: List[Dict[str, Any]]) -> None:
    """Save results as structured JSON session report."""
    stress_trend = [round(float(r["heart_state"]["stress"]), 3) for r in results]
    heart_snapshots = [r["heart_state"] for r in results]
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_tests": len(results),
        "stress_trend": stress_trend,
        "heart_state_snapshots": heart_snapshots,
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
                "inferred_emotion",
                "intensity",
                "latency",
                "response_length",
                "tone_aligned",
                "heart_stress",
                "heart_rate",
                "hrv",
            ],
        )
        writer.writeheader()
        for r in results:
            writer.writerow({
                "test_case": r["test_case"],
                "input": r["input"],
                "emotion": r["detected_emotion"],
                "inferred_emotion": r["inferred_emotion"],
                "intensity": r["intensity"],
                "latency": r["latency"],
                "response_length": r["response_length"],
                "tone_aligned": r["tone_aligned"],
                "heart_stress": r["heart_state"]["stress"],
                "heart_rate": r["heart_state"]["heart_rate"],
                "hrv": r["heart_state"]["hrv"],
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


