"""ctypes bridge for the Virtual Heart Core C engine with Python fallback."""

import ctypes
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple


ROOT_DIR = Path(__file__).resolve().parent.parent
HEART_DIR = Path(__file__).resolve().parent
C_SOURCE = HEART_DIR / "virtual_heart.c"
SO_PATH = HEART_DIR / "virtual_heart.so"


@dataclass
class _HeartState:
    stress: float = 20.0
    fear: float = 12.0
    sadness: float = 18.0
    happiness: float = 55.0
    motivation: float = 58.0
    overthinking: float = 20.0
    heart_rate: float = 72.0
    hrv: float = 62.0


class _CVirtualHeart(ctypes.Structure):
    _fields_ = [
        ("stress", ctypes.c_float),
        ("fear", ctypes.c_float),
        ("sadness", ctypes.c_float),
        ("happiness", ctypes.c_float),
        ("motivation", ctypes.c_float),
        ("overthinking", ctypes.c_float),
        ("heart_rate", ctypes.c_float),
        ("hrv", ctypes.c_float),
    ]


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _compile_c_engine() -> bool:
    cmd = [
        "gcc",
        "-O2",
        "-shared",
        "-fPIC",
        str(C_SOURCE),
        "-o",
        str(SO_PATH),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


class VirtualHeartBridge:
    """Bridge that prefers C runtime and falls back to a Python simulation."""

    def __init__(self) -> None:
        self._lib: Optional[ctypes.CDLL] = None
        self._state_py = _HeartState()
        self._state_c = _CVirtualHeart()
        self._using_c = self._load_c_library()

        if self._using_c and self._lib is not None:
            self._lib.init_heart.argtypes = [ctypes.POINTER(_CVirtualHeart)]
            self._lib.init_heart.restype = None
            self._lib.update_heart.argtypes = [ctypes.POINTER(_CVirtualHeart), ctypes.c_float, ctypes.c_float]
            self._lib.update_heart.restype = None
            self._lib.interpret_emotion.argtypes = [_CVirtualHeart]
            self._lib.interpret_emotion.restype = ctypes.c_char_p
            self._lib.init_heart(ctypes.byref(self._state_c))

    def _load_c_library(self) -> bool:
        if not SO_PATH.exists() and not _compile_c_engine():
            return False

        try:
            self._lib = ctypes.CDLL(str(SO_PATH))
            return True
        except OSError:
            self._lib = None
            return False

    def _update_python(self, stress_input: float, positive_input: float) -> Tuple[_HeartState, str]:
        s_in = _clamp(stress_input, 0.0, 1.0)
        p_in = _clamp(positive_input, 0.0, 1.0)

        st = self._state_py
        st.stress = _clamp((st.stress * 0.97) + (s_in * 18.0) - (p_in * 4.0), 0.0, 100.0)
        st.happiness = _clamp((st.happiness * 0.94) + (p_in * 20.0) - (s_in * 7.0), 0.0, 100.0)
        st.fear = _clamp((st.fear * 0.95) + (s_in * 16.0) + (st.stress * 0.05), 0.0, 100.0)
        st.sadness = _clamp((st.sadness * 0.96) + (s_in * 10.0) - (p_in * 6.0), 0.0, 100.0)

        st.overthinking = _clamp((0.65 * st.stress) + (0.35 * st.sadness), 0.0, 100.0)
        st.motivation = _clamp(50.0 + (0.60 * st.happiness) - (0.70 * st.stress), 0.0, 100.0)

        st.heart_rate = _clamp(70.0 + (0.32 * st.stress) + (0.24 * st.fear) - (0.08 * st.happiness), 48.0, 165.0)
        st.hrv = _clamp(82.0 - (0.48 * st.stress) - (0.25 * st.fear) + (0.12 * st.happiness), 10.0, 120.0)

        emotion = self._interpret_python(st)
        return st, emotion

    @staticmethod
    def _interpret_python(st: _HeartState) -> str:
        if st.stress > 70.0 or st.overthinking > 68.0:
            return "stressed and overwhelmed"
        if st.sadness > 64.0:
            return "sad and withdrawn"
        if st.fear > 62.0:
            return "anxious and fearful"
        if st.happiness > 70.0 and st.motivation > 60.0:
            return "hopeful and motivated"
        if st.motivation < 35.0:
            return "low-energy and discouraged"
        return "emotionally mixed but stable"

    def update(self, stress_input: float, positive_input: float) -> Dict[str, float]:
        """Update the virtual heart and return a structured state dictionary."""
        if self._using_c and self._lib is not None:
            self._lib.update_heart(ctypes.byref(self._state_c), ctypes.c_float(stress_input), ctypes.c_float(positive_input))
            emotion = (self._lib.interpret_emotion(self._state_c) or b"emotionally mixed but stable").decode("utf-8")
            return {
                "emotion": emotion,
                "stress": round(float(self._state_c.stress), 3),
                "fear": round(float(self._state_c.fear), 3),
                "sadness": round(float(self._state_c.sadness), 3),
                "happiness": round(float(self._state_c.happiness), 3),
                "motivation": round(float(self._state_c.motivation), 3),
                "overthinking": round(float(self._state_c.overthinking), 3),
                "heart_rate": round(float(self._state_c.heart_rate), 3),
                "hrv": round(float(self._state_c.hrv), 3),
            }

        st, emotion = self._update_python(stress_input, positive_input)
        data = asdict(st)
        data["emotion"] = emotion
        for key in ["stress", "fear", "sadness", "happiness", "motivation", "overthinking", "heart_rate", "hrv"]:
            data[key] = round(float(data[key]), 3)
        return {
            "emotion": data["emotion"],
            "stress": data["stress"],
            "fear": data["fear"],
            "sadness": data["sadness"],
            "happiness": data["happiness"],
            "motivation": data["motivation"],
            "overthinking": data["overthinking"],
            "heart_rate": data["heart_rate"],
            "hrv": data["hrv"],
        }


def default_bridge() -> VirtualHeartBridge:
    return VirtualHeartBridge()
