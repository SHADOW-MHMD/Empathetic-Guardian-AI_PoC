"""Semantic emotion detection for response-state overrides."""

from typing import Dict, List


_KEYWORDS = {
    "grief": [
        "passed away",
        "died",
        "lost my",
        "funeral",
        "grief",
        "mourning",
    ],
    "distress": [
        "scared",
        "anxious",
        "panic",
        "terrified",
        "overwhelmed",
        "i cannot cope",
    ],
    "anger": [
        "hate",
        "angry",
        "furious",
        "rage",
        "mad",
    ],
    "positive": [
        "happy",
        "excited",
        "great",
        "awesome",
        "good news",
        "proud",
    ],
}

_PRIORITY: List[str] = ["grief", "distress", "anger", "positive"]


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def detect_emotional_context(text: str) -> Dict[str, float]:
    """Detect emotionally significant semantic context from user text.

    Returns:
    {
        "type": <category or "none">,
        "intensity": float in [0, 1],
        "confidence": float in [0, 1],
        "is_confident": bool (True if intensity >= 0.4)
    }
    """
    content = (text or "").strip().lower()
    if not content:
        return {
            "type": "none",
            "intensity": 0.0,
            "confidence": 0.0,
            "is_confident": False,
        }

    best_type = "none"
    best_score = 0

    for category in _PRIORITY:
        terms = _KEYWORDS[category]
        score = sum(1 for term in terms if term in content)
        if score > best_score:
            best_score = score
            best_type = category

    if best_type == "none":
        return {
            "type": "none",
            "intensity": 0.0,
            "confidence": 0.0,
            "is_confident": False,
        }

    # Deterministic scaling based on match count.
    # 1 match: 0.6, 2 matches: 0.85, 3+ matches: 1.0
    intensity = _clamp(0.5 + 0.25 * best_score, 0.0, 1.0)
    confidence = intensity
    is_confident = confidence >= 0.4
    
    return {
        "type": best_type,
        "intensity": intensity,
        "confidence": confidence,
        "is_confident": is_confident,
    }
