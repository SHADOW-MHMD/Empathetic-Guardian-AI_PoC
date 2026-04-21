"""LLM-backed sentence generation for synthetic emotional states."""

import json
import os
import random
import urllib.error
import urllib.request
from typing import Dict, Tuple


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemma-2-9b-it:free"


PROMPT_TEMPLATE = (
    "You generate realistic human sentences based on emotional state.\n"
    "\n"
    "INPUT STATE:\n"
    "- stress: {stress:.4f}\n"
    "- happiness: {happiness:.4f}\n"
    "- sadness: {sadness:.4f}\n"
    "- fear: {fear:.4f}\n"
    "- motivation: {motivation:.4f}\n"
    "- overthinking: {overthinking:.4f}\n"
    "- heart_rate: {heart_rate:.4f}\n"
    "- hrv: {hrv:.4f}\n"
    "- emotional_drift: {emotional_drift:.4f}\n"
    "- valence: {valence:.4f}\n"
    "- arousal: {arousal:.4f}\n"
    "- intensity: {intensity:.4f}\n"
    "\n"
    "RULES:\n"
    "1. Output only 1-2 sentences.\n"
    "2. Reflect only emotional state and felt experience.\n"
    "3. Do not add external events or narrative details.\n"
    "4. Avoid contradictions and exaggeration.\n"
    "5. Keep language natural and human.\n"
)


def _fallback_sentence(derived: Dict[str, float]) -> str:
    valence = float(derived.get("valence", 0.0))
    arousal = float(derived.get("arousal", 0.0))
    intensity = float(derived.get("intensity", 0.0))

    calm_negative = [
        "I feel weighed down and quiet inside.",
        "It feels heavy, and my thoughts are moving slowly.",
    ]
    high_negative = [
        "I feel tense and overwhelmed, like my mind will not settle.",
        "Everything feels tight and urgent, and it is hard to think clearly.",
    ]
    high_positive = [
        "I feel energized and hopeful, like I can keep moving forward.",
        "There is a bright momentum in me, and I feel ready for what comes next.",
    ]
    neutral = [
        "I feel mixed right now, with some tension and some steadiness.",
        "My emotional state feels balanced but still a little unsettled.",
    ]

    if valence < -0.35 and arousal > 0.55:
        return random.choice(high_negative)
    if valence < -0.35 and arousal <= 0.55:
        return random.choice(calm_negative)
    if valence > 0.25 and intensity < 0.65:
        return random.choice(high_positive)
    return random.choice(neutral)


def _call_openrouter(prompt: str, model: str, api_key: str) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You produce short, emotionally coherent human sentences."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.8,
        "max_tokens": 80,
    }

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Virtual Emotional Data Generator System v3",
        },
    )

    with urllib.request.urlopen(req, timeout=25) as resp:
        body = resp.read().decode("utf-8")

    parsed = json.loads(body)
    choices = parsed.get("choices", [])
    if not choices:
        raise ValueError("No choices returned from OpenRouter")
    text = choices[0].get("message", {}).get("content", "").strip()
    if not text:
        raise ValueError("Empty response returned from OpenRouter")
    return text


def generate_sentence(
    normalized_state: Dict[str, float],
    derived_metrics: Dict[str, float],
    model: str = DEFAULT_MODEL,
) -> Tuple[str, str, str]:
    """Generate sentence, returning (text, prompt_used, model_used)."""
    prompt = PROMPT_TEMPLATE.format(
        stress=float(normalized_state.get("stress", 0.0)),
        happiness=float(normalized_state.get("happiness", 0.0)),
        sadness=float(normalized_state.get("sadness", 0.0)),
        fear=float(normalized_state.get("fear", 0.0)),
        motivation=float(normalized_state.get("motivation", 0.0)),
        overthinking=float(normalized_state.get("overthinking", 0.0)),
        heart_rate=float(normalized_state.get("heart_rate", 0.0)),
        hrv=float(normalized_state.get("hrv", 0.0)),
        emotional_drift=float(normalized_state.get("emotional_drift", 0.0)),
        valence=float(derived_metrics.get("valence", 0.0)),
        arousal=float(derived_metrics.get("arousal", 0.0)),
        intensity=float(derived_metrics.get("intensity", 0.0)),
    )

    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if api_key.startswith('"') and api_key.endswith('"'):
        api_key = api_key[1:-1].strip()

    if not api_key:
        return _fallback_sentence(derived_metrics), prompt, "fallback-template"

    try:
        text = _call_openrouter(prompt=prompt, model=model, api_key=api_key)
        return text, prompt, model
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError):
        return _fallback_sentence(derived_metrics), prompt, "fallback-template"
