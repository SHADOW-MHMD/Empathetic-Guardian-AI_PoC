"""Normalization layer for virtual emotional time-series states."""

from typing import Dict


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def normalize_state(raw_state: Dict[str, float]) -> Dict[str, Dict[str, float]]:
    """Clamp and derive metrics from a raw heart snapshot."""
    clamped_100 = {
        "stress": _clamp(float(raw_state.get("stress", 0.0)), 0.0, 100.0),
        "happiness": _clamp(float(raw_state.get("happiness", 0.0)), 0.0, 100.0),
        "sadness": _clamp(float(raw_state.get("sadness", 0.0)), 0.0, 100.0),
        "fear": _clamp(float(raw_state.get("fear", 0.0)), 0.0, 100.0),
        "motivation": _clamp(float(raw_state.get("motivation", 0.0)), 0.0, 100.0),
        "overthinking": _clamp(float(raw_state.get("overthinking", 0.0)), 0.0, 100.0),
        "heart_rate": _clamp(float(raw_state.get("heart_rate", 0.0)), 40.0, 200.0),
        "hrv": _clamp(float(raw_state.get("hrv", 0.0)), 0.0, 200.0),
        "emotional_drift": _clamp(float(raw_state.get("emotional_drift", 0.0)), -50.0, 50.0),
    }

    normalized = {
        "stress": clamped_100["stress"] / 100.0,
        "happiness": clamped_100["happiness"] / 100.0,
        "sadness": clamped_100["sadness"] / 100.0,
        "fear": clamped_100["fear"] / 100.0,
        "motivation": clamped_100["motivation"] / 100.0,
        "overthinking": clamped_100["overthinking"] / 100.0,
        "heart_rate": (clamped_100["heart_rate"] - 40.0) / 160.0,
        "hrv": clamped_100["hrv"] / 200.0,
        "emotional_drift": (clamped_100["emotional_drift"] + 50.0) / 100.0,
    }

    valence = _clamp(normalized["happiness"] - normalized["sadness"], -1.0, 1.0)
    arousal = _clamp((normalized["stress"] + normalized["fear"]) / 2.0, 0.0, 1.0)
    intensity = _clamp(
        (0.24 * normalized["stress"])
        + (0.20 * normalized["fear"])
        + (0.18 * normalized["sadness"])
        + (0.12 * normalized["overthinking"])
        + (0.10 * (1.0 - normalized["motivation"]))
        + (0.08 * abs(valence))
        + (0.08 * arousal),
        0.0,
        1.0,
    )

    derived = {
        "valence": round(valence, 4),
        "arousal": round(arousal, 4),
        "intensity": round(intensity, 4),
    }

    return {
        "heart_state": {k: round(v, 4) for k, v in clamped_100.items()},
        "normalized_state": {k: round(v, 4) for k, v in normalized.items()},
        "derived_metrics": derived,
    }
