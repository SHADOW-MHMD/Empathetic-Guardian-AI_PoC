import os
import ctypes
from ctypes import Structure, c_float, c_int, c_uint32, POINTER, byref
from human_sim import SyntheticHuman

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()
else:
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as env_file:
            for line in env_file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    value = value.strip()
                    # Strip surrounding quotes if present
                    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    os.environ.setdefault(key.strip(), value)

try:
    import google.generativeai as genai
except ImportError as exc:
    raise ImportError(
        "google.generativeai is required. install with: pip install google-generativeai"
    ) from exc

GEMINI_MODEL = "gemini-2.0-flash"

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


def configure_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing from the environment. Add it to a .env file.")
    genai.configure(api_key=api_key)
    return api_key


def ask_gemini(prompt: str) -> str:
    try:
        configure_gemini()
        model = genai.GenerativeModel(model_name=GEMINI_MODEL)
        response = model.generate_content(prompt)
        if hasattr(response, "text") and response.text:
            return response.text
        if hasattr(response, "output") and response.output:
            return response.output
        return str(response)
    except Exception as exc:
        return f"[Gemini call failed: {exc}]"


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
    raise ValueError(f"Unsupported scenario: {scenario}")


def build_system_prompt(cortisol: float, adrenaline: float, anxiety: float, text: str) -> str:
    return (
        f"You are an Empathetic Guardian AI. You have a simulated biological body. "
        f"Right now, your internal Cortisol is {cortisol:.2f}, your Adrenaline is {adrenaline:.2f}, "
        f"and your Felt Anxiety is {anxiety:.2f}. The user says: '{text}'. "
        "Modulate your response tone, length, and warmth based strictly on your internal hormones. "
        "Do not explicitly mention your hormone levels to the user, just act accordingly."
    )


def run_simulation(scenario_name: str, lib):
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
    prompt = build_system_prompt(cortisol, adrenaline, anxiety, state["text"])
    response = ask_gemini(prompt)

    print("\n=== Scenario: {} ===".format(scenario_name))
    print(f"C-Engine -> Cortisol: {cortisol:.3f}, Adrenaline: {adrenaline:.3f}, Felt Anxiety: {anxiety:.3f}")
    print("User text:", state["text"])
    print("--- Gemini response ---")
    print(response)


def main():
    configure_gemini()
    lib = load_library()
    run_simulation("calm", lib)
    run_simulation("panic", lib)


if __name__ == "__main__":
    main()
