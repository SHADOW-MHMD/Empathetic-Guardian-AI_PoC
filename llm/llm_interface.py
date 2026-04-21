"""Emotion-conditioned language generation with OpenRouter + deterministic fallback."""

import json
import os
import urllib.error
import urllib.request
from typing import Dict, Tuple

from dotenv import load_dotenv


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openrouter/auto"


# Ensure API keys from .env are available even when not exported in shell.
load_dotenv()


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _safe_state(state: Dict[str, float]) -> Dict[str, float]:
    return {
        "cortisol": _clamp(float(state.get("cortisol", 0.2)), 0.0, 1.0),
        "dopamine": _clamp(float(state.get("dopamine", 0.5)), 0.0, 1.0),
        "adrenaline": _clamp(float(state.get("adrenaline", 0.2)), 0.0, 1.0),
        "valence": _clamp(float(state.get("valence", 0.0)), -1.0, 1.0),
        "arousal": _clamp(float(state.get("arousal", 0.3)), 0.0, 1.0),
        "dominance": _clamp(float(state.get("dominance", 0.5)), 0.0, 1.0),
    }


def _style_rules(state: Dict[str, float]) -> Dict[str, str]:
    cortisol = state["cortisol"]
    dopamine = state["dopamine"]
    arousal = state["arousal"]
    dominance = state["dominance"]
    valence = state["valence"]

    sentence_length = "medium"
    tone = "balanced"
    empathy = "moderate"
    verbosity = "concise"

    if cortisol > 0.6:
        sentence_length = "short"
        tone = "calm and reassuring"
        empathy = "high"
        verbosity = "very concise"
    elif dopamine > 0.6:
        sentence_length = "medium"
        tone = "energetic and encouraging"
        empathy = "supportive"

    if arousal > 0.7:
        sentence_length = "short"
        tone = f"{tone}, urgent pacing"

    if dominance < 0.3:
        empathy = "very high"
        tone = f"{tone}, gentle"

    if valence > 0.4:
        tone = f"{tone}, optimistic"
    elif valence < -0.4:
        tone = f"{tone}, validating"

    return {
        "sentence_length": sentence_length,
        "tone": tone,
        "empathy_level": empathy,
        "verbosity": verbosity,
    }


def _describe_virtual_heart(virtual_heart_state: Dict[str, float]) -> str:
    emotion = str(virtual_heart_state.get("emotion", "emotionally mixed but stable")).strip() or "emotionally mixed but stable"
    stress = float(virtual_heart_state.get("stress", 0.0))
    overthinking = float(virtual_heart_state.get("overthinking", 0.0))
    motivation = float(virtual_heart_state.get("motivation", 50.0))

    load_label = "moderate"
    if stress >= 65.0 or overthinking >= 65.0:
        load_label = "high"
    elif stress <= 25.0 and overthinking <= 25.0:
        load_label = "low"

    momentum_label = "steady"
    if motivation >= 65.0:
        momentum_label = "forward-leaning"
    elif motivation <= 35.0:
        momentum_label = "fragile"

    return (
        "You are an empathetic assistant connected to a virtual heart system. "
        f"The user is currently in a {emotion} state, with {load_label} emotional load "
        f"and {momentum_label} inner momentum."
    )


def _build_prompt(user_input: str, state: Dict[str, float], emotional_context: Dict = None, virtual_heart_state: Dict = None) -> Tuple[str, str]:
    if emotional_context is None:
        emotional_context = {
            "type": "none",
            "intensity": 0.0,
            "confidence": 0.0,
            "is_confident": False,
        }
    if virtual_heart_state is None:
        virtual_heart_state = {}
    
    rules = _style_rules(state)
    is_confident = emotional_context.get("is_confident", False)
    emotion_type = emotional_context.get("type", "none")
    
    system_prompt = (
        "You are an emotionally present, deeply empathetic companion.\n\n"
        "RESPONSE CONTRACT:\n"
        "- Maximum 2 sentences.\n"
        "- No lists, no suggestions, no advice unless explicitly asked.\n"
        "- Do NOT use phrases like: 'take care of yourself', 'seek support', 'consider professional help', 'engage in self-care'.\n"
        "- Do NOT explain emotions in a clinical way.\n"
        "- Speak like a calm, present human, not an assistant.\n"
        "- Prioritize emotional validation over solutions.\n"
        "- Use simple, natural language.\n"
        "- Do not invent external facts. Ground everything in what the user shared.\n\n"
    )
    system_prompt += _describe_virtual_heart(virtual_heart_state) + "\n\n"
    
    if emotion_type == "grief":
        system_prompt += (
            "SPECIAL RULE - GRIEF RESPONSE:\n"
            "- First sentence must acknowledge the loss directly.\n"
            "- Second sentence must express your presence, not solutions.\n"
            "- Avoid future-oriented advice or recovery narratives.\n\n"
        )
    
    if emotion_type == "none" or not is_confident:
        system_prompt += (
            "SPECIAL RULE - NEUTRAL/UNCERTAIN INPUT:\n"
            "- Do NOT assume the user's emotional state.\n"
            "- Do NOT say 'you feel...' or 'it sounds like you're...' when you don't know.\n"
            "- Stay neutral, curious, or gently exploratory.\n"
            "- Option: Ask a clarifying question to understand better.\n"
            "- Option: Reflect the situation without emotional labeling.\n\n"
        )
    
    system_prompt += (
        "NEGATIVE EXAMPLES (DO NOT OUTPUT LIKE THIS):\n"
        "BAD: 'It sounds like you're feeling lost.'\n"
        "BAD: 'I'm sorry for your loss. Take care of yourself and seek support.'\n"
        "BAD: 'That's difficult. Have you tried talking to someone?'\n\n"
        "POSITIVE EXAMPLES:\n"
        "GOOD (neutral): 'What's been weighing on you about your career lately?'\n"
        "GOOD (neutral): 'Are you exploring options or feeling stuck?'\n"
        "GOOD (grief): 'I'm really sorry. That's a heavy loss.'\n"
        "GOOD (grief): 'I'm here with you. You don't have to carry this alone right now.'\n"
    )

    confidence_label = "confident" if is_confident else "uncertain"
    user_prompt = (
        "STATE BLOCK:\n"
        f"- Cortisol: {state['cortisol']:.3f}\n"
        f"- Dopamine: {state['dopamine']:.3f}\n"
        f"- Adrenaline: {state['adrenaline']:.3f}\n"
        f"- Arousal: {state['arousal']:.3f}\n"
        f"- Valence: {state['valence']:.3f}\n"
        f"- Dominance: {state['dominance']:.3f}\n"
        f"- Detected Emotion: {emotion_type} ({confidence_label})\n\n"
        "INSTRUCTION:\n"
        "- Be emotionally present, minimal, and human-like.\n"
        "- Avoid sounding like a helper, advisor, or therapist.\n"
        f"- Sentence length: {rules['sentence_length']}\n"
        f"- Tone: {rules['tone']}\n"
        f"- Empathy level: {rules['empathy_level']}\n"
        "- Output maximum 2 sentences—short and genuine.\n\n"
        "USER INPUT:\n"
        f"{user_input}"
    )
    return system_prompt, user_prompt


def _fallback_response(user_input: str, state: Dict[str, float]) -> str:
    cortisol = state["cortisol"]
    dopamine = state["dopamine"]
    arousal = state["arousal"]
    dominance = state["dominance"]
    valence = state["valence"]

    if cortisol > 0.7:
        return "I can see this is stressful. Let us slow down and take one clear step at a time."
    if dopamine > 0.7:
        return "That is strong progress. Keep going and lock in your next step."
    if arousal > 0.7:
        return "This feels urgent. Let us focus on the immediate priority first."
    if dominance < 0.3:
        return "You are not alone in this. We can move gently and keep things manageable."
    if valence > 0.4:
        return "This is moving in a good direction. Build on what is already working."
    if valence < -0.4:
        return "That sounds really hard. Your reaction makes sense, and we can work through it step by step."
    return "I hear you. Let us choose one practical next step and do it now."


def _call_openrouter(system_prompt: str, user_prompt: str, api_key: str) -> str:
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.6,
        "max_tokens": 70,
    }
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Empathetic Guardian Runtime",
        },
    )

    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8")
    parsed = json.loads(body)
    choices = parsed.get("choices", [])
    if not choices:
        raise ValueError("No choices returned from OpenRouter")
    message = choices[0].get("message", {})
    content = message.get("content", "")
    if not content:
        raise ValueError("Empty content returned from OpenRouter")
    return content.strip()


def _normalized_api_key() -> str:
    raw = os.getenv("OPENROUTER_API_KEY", "").strip()
    if raw.startswith('"') and raw.endswith('"'):
        raw = raw[1:-1].strip()

    if "paste your api key here" in raw.lower() or raw.lower().startswith("your_"):
        return ""

    return raw


def generate_response(
    user_input: str,
    state: Dict[str, float],
    emotional_context: Dict = None,
    virtual_heart_state: Dict = None,
) -> str:
    """Generate an emotionally controlled response from user input + internal state."""
    if emotional_context is None:
        emotional_context = {"type": "none", "intensity": 0.0}
    
    safe = _safe_state(state)
    system_prompt, user_prompt = _build_prompt(
        user_input=user_input,
        state=safe,
        emotional_context=emotional_context,
        virtual_heart_state=virtual_heart_state,
    )

    api_key = _normalized_api_key()
    if not api_key:
        return _fallback_response(user_input=user_input, state=safe)

    try:
        return _call_openrouter(system_prompt=system_prompt, user_prompt=user_prompt, api_key=api_key)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError):
        return _fallback_response(user_input=user_input, state=safe)
