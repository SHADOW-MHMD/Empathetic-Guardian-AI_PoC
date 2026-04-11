import os
import ctypes
import time
import csv
from datetime import datetime
from ctypes import Structure, c_float, c_int, c_uint32, POINTER, byref
from human_sim import SyntheticHuman
from dotenv import load_dotenv

# Force load .env at the very top
load_dotenv()

try:
    from colorama import init, Fore, Style
    init(autoreset=True)  # Initialize colorama
except ImportError as exc:
    raise ImportError(
        "colorama is required. install with: pip install colorama"
    ) from exc

try:
    from openai import OpenAI
except ImportError as exc:
    raise ImportError(
        "openai is required. install with: pip install openai"
    ) from exc

# Color mapping for scenarios
color_map = {
    "calm": Fore.CYAN,
    "panic": Fore.RED,
    "anxious": Fore.YELLOW,
    "scared": Fore.RED,
    "crying": Fore.GREEN,
    "heavy_hearted": Fore.GREEN
}

def log_somatic_data(timestamp, scenario, cortisol, adrenaline, anxiety, response_preview):
    file_exists = os.path.isfile('somatic_logs.csv')
    with open('somatic_logs.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(['Timestamp', 'Scenario', 'Cortisol', 'Adrenaline', 'Anxiety_Level', 'AI_Response_Preview'])
        writer.writerow([timestamp, scenario, cortisol, adrenaline, anxiety, response_preview])

class SensorInputV2(Structure):
    _fields_ = [
        ("heart_rate_bpm", c_float),
        ("systolic_bp", c_float),
        ("diastolic_bp", c_float),
        ("hrv_rmssd_ms", c_float),
        ("voice_pitch_hz", c_float),
        ("voice_energy_db", c_float),
        ("voice_tempo_wpm", c_float),
        ("voice_tremor", c_float),
        ("voice_valence", c_float),
        ("text_sentiment", c_float),
        ("text_arousal", c_float),
        ("text_certainty", c_float),
        ("typing_speed_cpm", c_float),
        ("typing_pause_ratio", c_float),
        ("backspace_rate", c_float),
        ("sensor_confidence", c_float),
        ("baseline_hr", c_float),
        ("baseline_hrv", c_float),
        ("baseline_pitch", c_float),
        ("baseline_tempo", c_float),
        ("baseline_typing_speed", c_float),
    ]

class VirtualBodyV2(Structure):
    _fields_ = [
        ("virtual_heart_rate", c_float),
        ("virtual_blood_pressure", c_float),
        ("virtual_hrv", c_float),
        ("virtual_cortisol", c_float),
        ("virtual_adrenaline", c_float),
        ("virtual_dopamine", c_float),
        ("virtual_serotonin", c_float),
        ("virtual_oxytocin", c_float),
        ("virtual_norepinephrine", c_float),
        ("virtual_muscle_tension", c_float),
        ("virtual_breathing_rate", c_float),
        ("virtual_gsr", c_float),
        ("felt_anxiety", c_float),
        ("felt_urgency", c_float),
        ("felt_warmth", c_float),
        ("felt_exhaustion", c_float),
        ("felt_alertness", c_float),
        ("felt_trust", c_float),
        ("felt_connection", c_float),
        ("felt_loneliness", c_float),
        ("felt_safety", c_float),
        ("felt_tension", c_float),
        ("felt_energy", c_float),
        ("confidence", c_float),
        ("noise_seed_float", c_float),
        ("_noise_seed", c_uint32),
    ]

class SocialEmotionalState(Structure):
    _fields_ = [
        ("trust_level", c_float),
        ("trust_velocity", c_float),
        ("betrayal_count", c_int),
        ("trust_recovery_rate", c_float),
        ("bond_strength", c_float),
        ("bond_decay_rate", c_float),
        ("shared_experience_score", c_float),
        ("interaction_count", c_int),
        ("emotional_baseline_shift", c_float),
        ("trauma_residue", c_float),
        ("joy_reservoir", c_float),
        ("emotional_inertia", c_float),
        ("phase", c_int),
    ]

def load_library():
    lib_path = os.path.join(os.path.dirname(__file__), "somatic_engine_v2.so")
    lib = ctypes.CDLL(lib_path)
    lib.init_social_state.argtypes = [POINTER(SocialEmotionalState)]
    lib.init_social_state.restype = None
    lib.fuse_sensors_v2.argtypes = [POINTER(SensorInputV2), POINTER(VirtualBodyV2), POINTER(SocialEmotionalState)]
    lib.fuse_sensors_v2.restype = None
    lib.compute_felt_v2.argtypes = [POINTER(VirtualBodyV2), POINTER(SocialEmotionalState)]
    lib.compute_felt_v2.restype = None
    return lib


def somatic_mirror_response(cortisol: float, adrenaline: float, text: str) -> str:
    """
    Fallback responder that generates empathetic responses based on C-Engine hormone levels.
    Demonstrates somatic mirroring when Gemini API is unavailable.
    """
    if cortisol > 0.1:
        # HIGH STRESS mode
        return (
            "[SOMATIC STATE: HIGH STRESS] I can feel your heart racing through the C-Engine. "
            "I'm shifting to grounding mode. Focus on my words: Breathe in for 4 seconds, "
            "hold for 4, exhale for 4. Your nervous system is activated. Let's bring it back to center. "
            "Tell me: what's the ONE thing you can control right now?"
        )
    else:
        # STABLE/CALM mode
        return (
            "[SOMATIC STATE: STABLE] My sensors show you are calm. I'm here to listen. "
            "Tell me more about what you shared. I'm tracking your emotional baseline—everything seems grounded. "
            "What feels most important for you to explore right now?"
        )


def call_grok(prompt: str, cortisol: float = 0.0, adrenaline: float = 0.0, user_text: str = "") -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or api_key == "your_openrouter_key_here":
        return "[Grok call failed: OPENROUTER_API_KEY is missing or not configured. Add it to a .env file.]"

    print(f"Using OpenRouter API Key: {api_key[:5]}***")
    
    # Initialize OpenAI client configured for OpenRouter
    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Empathetic Guardian PoC"
        }
    )

    # Try primary model first, then fallback to secondary
    models_to_try = [
        "openai/gpt-oss-120b:free",  # Primary
        "meta-llama/llama-3.3-70b-instruct:free"  # Fallback
    ]

    for model_name in models_to_try:
        try:
            print(f"Trying model: {model_name}...", end=" ")
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}]
            )

            if response.choices and response.choices[0].message.content:
                print("✓ Success")
                return response.choices[0].message.content

            return str(response)

        except Exception as exc:
            error_str = str(exc)
            print(f"✗ Failed")
            # If this isn't the last model, continue to next
            if model_name == models_to_try[-1]:
                # Last model failed - fall back to somatic mirroring
                print(f"[API Error: {error_str[:100]}... Falling back to Somatic Mirroring]")
                return somatic_mirror_response(cortisol, adrenaline, user_text)
            # Otherwise continue to next model in the loop


def build_sensor_input(state: dict, scenario: str) -> SensorInputV2:
    if scenario == "calm":
        return SensorInputV2(
            heart_rate_bpm=state["hr"],
            systolic_bp=110.0,
            diastolic_bp=72.0,
            hrv_rmssd_ms=state["hrv"],
            voice_pitch_hz=170.0,
            voice_energy_db=-12.0,
            voice_tempo_wpm=100.0,
            voice_tremor=state["voice_tremor"],
            voice_valence=0.75,
            text_sentiment=state["sentiment"],
            text_arousal=0.12,
            text_certainty=0.85,
            typing_speed_cpm=220.0,
            typing_pause_ratio=0.08,
            backspace_rate=2.0,
            sensor_confidence=0.95,
            baseline_hr=70.0,
            baseline_hrv=60.0,
            baseline_pitch=165.0,
            baseline_tempo=105.0,
            baseline_typing_speed=220.0,
        )
    if scenario == "panic":
        return SensorInputV2(
            heart_rate_bpm=state["hr"],
            systolic_bp=155.0,
            diastolic_bp=95.0,
            hrv_rmssd_ms=state["hrv"],
            voice_pitch_hz=220.0,
            voice_energy_db=12.0,
            voice_tempo_wpm=180.0,
            voice_tremor=state["voice_tremor"],
            voice_valence=-0.85,
            text_sentiment=state["sentiment"],
            text_arousal=0.95,
            text_certainty=0.25,
            typing_speed_cpm=180.0,
            typing_pause_ratio=0.45,
            backspace_rate=18.0,
            sensor_confidence=0.85,
            baseline_hr=70.0,
            baseline_hrv=60.0,
            baseline_pitch=165.0,
            baseline_tempo=105.0,
            baseline_typing_speed=220.0,
        )
    if scenario == "anxious":
        return SensorInputV2(
            heart_rate_bpm=state["hr"],
            systolic_bp=125.0,
            diastolic_bp=80.0,
            hrv_rmssd_ms=state["hrv"],
            voice_pitch_hz=185.0,
            voice_energy_db=-5.0,
            voice_tempo_wpm=120.0,
            voice_tremor=state["voice_tremor"],
            voice_valence=-0.1,
            text_sentiment=state["sentiment"],
            text_arousal=0.5,
            text_certainty=0.6,
            typing_speed_cpm=200.0,
            typing_pause_ratio=0.2,
            backspace_rate=8.0,
            sensor_confidence=0.9,
            baseline_hr=70.0,
            baseline_hrv=60.0,
            baseline_pitch=165.0,
            baseline_tempo=105.0,
            baseline_typing_speed=220.0,
        )
    if scenario == "scared":
        return SensorInputV2(
            heart_rate_bpm=state["hr"],
            systolic_bp=145.0,
            diastolic_bp=90.0,
            hrv_rmssd_ms=state["hrv"],
            voice_pitch_hz=210.0,
            voice_energy_db=8.0,
            voice_tempo_wpm=160.0,
            voice_tremor=state["voice_tremor"],
            voice_valence=-0.6,
            text_sentiment=state["sentiment"],
            text_arousal=0.8,
            text_certainty=0.4,
            typing_speed_cpm=190.0,
            typing_pause_ratio=0.35,
            backspace_rate=12.0,
            sensor_confidence=0.88,
            baseline_hr=70.0,
            baseline_hrv=60.0,
            baseline_pitch=165.0,
            baseline_tempo=105.0,
            baseline_typing_speed=220.0,
        )
    if scenario == "crying":
        return SensorInputV2(
            heart_rate_bpm=state["hr"],
            systolic_bp=115.0,
            diastolic_bp=75.0,
            hrv_rmssd_ms=state["hrv"],
            voice_pitch_hz=175.0,
            voice_energy_db=-8.0,
            voice_tempo_wpm=110.0,
            voice_tremor=state["voice_tremor"],
            voice_valence=-0.7,
            text_sentiment=state["sentiment"],
            text_arousal=0.6,
            text_certainty=0.5,
            typing_speed_cpm=180.0,
            typing_pause_ratio=0.25,
            backspace_rate=6.0,
            sensor_confidence=0.92,
            baseline_hr=70.0,
            baseline_hrv=60.0,
            baseline_pitch=165.0,
            baseline_tempo=105.0,
            baseline_typing_speed=220.0,
        )
    if scenario == "heavy_hearted":
        return SensorInputV2(
            heart_rate_bpm=state["hr"],
            systolic_bp=105.0,
            diastolic_bp=68.0,
            hrv_rmssd_ms=state["hrv"],
            voice_pitch_hz=160.0,
            voice_energy_db=-15.0,
            voice_tempo_wpm=95.0,
            voice_tremor=state["voice_tremor"],
            voice_valence=-0.4,
            text_sentiment=state["sentiment"],
            text_arousal=0.2,
            text_certainty=0.7,
            typing_speed_cpm=150.0,
            typing_pause_ratio=0.15,
            backspace_rate=4.0,
            sensor_confidence=0.95,
            baseline_hr=70.0,
            baseline_hrv=60.0,
            baseline_pitch=165.0,
            baseline_tempo=105.0,
            baseline_typing_speed=220.0,
        )
    raise ValueError(f"Unsupported scenario: {scenario}")


def build_system_prompt(scenario: str, cortisol: float, adrenaline: float, anxiety: float, tension: float, energy: float, text: str) -> str:
    status_descriptions = {
        "calm": "User Status: [Calm]. Adrenaline: Low. Energy: Moderate.",
        "panic": "User Status: [Panic]. Adrenaline: High. Energy: High.",
        "anxious": "User Status: [Anxious]. Adrenaline: Low. Tension: High.",
        "scared": "User Status: [Scared]. Adrenaline: High. Heart Rate: High.",
        "crying": "User Status: [Crying]. Adrenaline: Low. Oxytocin: High (distress-driven).",
        "heavy_hearted": "User Status: [Heavy Hearted]. Adrenaline: Low. Energy: Low."
    }
    status = status_descriptions.get(scenario, f"User Status: [{scenario}].")
    
    return (
        f"You are an Empathetic Guardian AI. You have a simulated biological body. "
        f"{status} "
        f"Your internal Cortisol is {cortisol:.2f}, Adrenaline is {adrenaline:.2f}, "
        f"Felt Anxiety is {anxiety:.2f}, Felt Tension is {tension:.2f}, Felt Energy is {energy:.2f}. "
        f"The user says: '{text}'. "
        "Modulate your response tone, length, and warmth based strictly on your internal hormones and user status. "
        "For Heavy Hearted: be silent/gentle. For Scared: be alert/protective. For Anxious: be patient/grounding. "
        "Do not explicitly mention your hormone levels to the user, just act accordingly."
    )


def run_simulation(scenario_name: str, lib):
    # Separator line
    print("\n" + "="*80)
    
    human = SyntheticHuman()
    state = human.get_state(scenario_name)
    sensor = build_sensor_input(state, scenario_name)
    body = VirtualBodyV2()
    social = SocialEmotionalState()
    lib.init_social_state(byref(social))
    lib.fuse_sensors_v2(byref(sensor), byref(body), byref(social))
    lib.compute_felt_v2(byref(body), byref(social))

    cortisol = float(body.virtual_cortisol)
    adrenaline = float(body.virtual_adrenaline)
    anxiety = float(body.felt_anxiety)
    tension = float(body.felt_tension)
    energy = float(body.felt_energy)
    prompt = build_system_prompt(scenario_name, cortisol, adrenaline, anxiety, tension, energy, state["text"])
    response = call_grok(prompt, cortisol=cortisol, adrenaline=adrenaline, user_text=state["text"])

    # Get color for scenario
    color = color_map.get(scenario_name, Fore.WHITE)
    
    print(f"{color}=== Scenario: {scenario_name.upper()} ===")
    print(f"{color}C-Engine -> Cortisol: {cortisol:.3f}, Adrenaline: {adrenaline:.3f}, Felt Anxiety: {anxiety:.3f}")
    print(f"{color}Felt Tension: {tension:.3f}, Felt Energy: {energy:.3f}")
    print(f"{color}User text: {state['text']}")
    print(f"{color}--- Grok response ---")
    print(f"{color}{response}")

    # Log to CSV
    timestamp = datetime.now().isoformat()
    response_preview = response[:50] if response else ""
    log_somatic_data(timestamp, scenario_name, f"{cortisol:.3f}", f"{adrenaline:.3f}", f"{anxiety:.3f}", response_preview)


def main():
    lib = load_library()
    scenarios = ["calm", "panic", "anxious", "scared", "crying", "heavy_hearted"]
    for scenario in scenarios:
        run_simulation(scenario, lib)
        time.sleep(15)


if __name__ == "__main__":
    main()
