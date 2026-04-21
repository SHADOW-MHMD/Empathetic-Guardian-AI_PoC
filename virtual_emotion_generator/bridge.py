"""Python bridge for the stochastic Virtual Heart C engine."""

import ctypes
import random
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


BASE_DIR = Path(__file__).resolve().parent
C_FILE = BASE_DIR / "heart.c"
SO_FILE = BASE_DIR / "heart.so"


class CVirtualHeart(ctypes.Structure):
    _fields_ = [
        ("stress", ctypes.c_float),
        ("happiness", ctypes.c_float),
        ("sadness", ctypes.c_float),
        ("fear", ctypes.c_float),
        ("motivation", ctypes.c_float),
        ("overthinking", ctypes.c_float),
        ("heart_rate", ctypes.c_float),
        ("hrv", ctypes.c_float),
        ("emotional_drift", ctypes.c_float),
    ]


@dataclass
class PyHeartState:
    stress: float
    happiness: float
    sadness: float
    fear: float
    motivation: float
    overthinking: float
    heart_rate: float
    hrv: float
    emotional_drift: float


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _compile() -> bool:
    cmd = ["gcc", "-O2", "-shared", "-fPIC", str(C_FILE), "-o", str(SO_FILE)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


class VirtualHeartBridge:
    """Continuous, stateful heart simulator with C-first execution."""

    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = random.Random(seed)
        self._lib: Optional[ctypes.CDLL] = None
        self._using_c = self._load_c_engine()
        self._state_c = CVirtualHeart()
        self._state_py = PyHeartState(
            stress=self._rng.uniform(15.0, 45.0),
            happiness=self._rng.uniform(35.0, 65.0),
            sadness=self._rng.uniform(10.0, 40.0),
            fear=self._rng.uniform(10.0, 35.0),
            motivation=self._rng.uniform(35.0, 70.0),
            overthinking=self._rng.uniform(10.0, 40.0),
            heart_rate=self._rng.uniform(62.0, 84.0),
            hrv=self._rng.uniform(48.0, 82.0),
            emotional_drift=self._rng.uniform(-4.0, 4.0),
        )
        self._last_inputs = (0.25, 0.25)

        if self._using_c and self._lib is not None:
            self._lib.init_heart.argtypes = [ctypes.POINTER(CVirtualHeart)]
            self._lib.init_heart.restype = None
            self._lib.update_heart.argtypes = [ctypes.POINTER(CVirtualHeart), ctypes.c_float, ctypes.c_float]
            self._lib.update_heart.restype = None
            self._lib.get_state.argtypes = [ctypes.POINTER(CVirtualHeart)]
            self._lib.get_state.restype = CVirtualHeart
            self._lib.init_heart(ctypes.byref(self._state_c))

    def _load_c_engine(self) -> bool:
        if not SO_FILE.exists() and not _compile():
            return False
        try:
            self._lib = ctypes.CDLL(str(SO_FILE))
            return True
        except OSError:
            self._lib = None
            return False

    def _sample_inputs(self) -> Dict[str, float]:
        prev_stress, prev_positive = self._last_inputs
        stress_input = _clamp(self._rng.gauss(prev_stress, 0.14), 0.0, 1.0)
        positive_input = _clamp(self._rng.gauss(prev_positive, 0.14), 0.0, 1.0)

        # Keep opposing pushes plausible but not mutually exclusive.
        coupling = self._rng.uniform(0.6, 1.0)
        if stress_input > positive_input:
            positive_input *= coupling
        else:
            stress_input *= coupling

        self._last_inputs = (stress_input, positive_input)
        return {
            "stress_input": stress_input,
            "positive_input": positive_input,
        }

    def _python_step(self, stress_input: float, positive_input: float) -> None:
        s = self._state_py
        ns = self._rng.uniform(-1.0, 1.0)
        nh = self._rng.uniform(-1.0, 1.0)

        s.emotional_drift = _clamp(
            (s.emotional_drift * 0.985)
            + (0.15 * (s.stress - s.happiness) / 100.0)
            + (0.10 * (s.sadness + s.fear) / 100.0)
            + (self._rng.uniform(-1.0, 1.0) * 1.2),
            -50.0,
            50.0,
        )

        s.stress = _clamp(
            s.stress
            + (-0.03 * s.stress)
            + (22.0 * stress_input)
            - (9.0 * positive_input)
            + (0.08 * s.overthinking)
            + (4.0 * ns)
            + (0.6 * s.emotional_drift),
            0.0,
            100.0,
        )
        s.happiness = _clamp(
            s.happiness
            + (-0.05 * s.happiness)
            + (20.0 * positive_input)
            - (11.0 * stress_input)
            - (0.04 * s.stress)
            + (3.2 * nh)
            - (0.45 * s.emotional_drift),
            0.0,
            100.0,
        )
        s.sadness = _clamp(
            s.sadness
            + (-0.035 * s.sadness)
            + (9.5 * stress_input)
            - (6.0 * positive_input)
            + (0.055 * s.stress)
            + (2.3 * self._rng.uniform(-1.0, 1.0))
            + (0.35 * s.emotional_drift),
            0.0,
            100.0,
        )
        s.fear = _clamp(
            s.fear
            + (-0.045 * s.fear)
            + (12.0 * stress_input)
            - (4.5 * positive_input)
            + (0.060 * s.stress)
            + (2.0 * self._rng.uniform(-1.0, 1.0))
            + (0.30 * s.emotional_drift),
            0.0,
            100.0,
        )
        s.overthinking = _clamp(
            s.overthinking
            + (-0.04 * s.overthinking)
            + (0.26 * s.sadness)
            + (0.16 * s.stress)
            - (0.08 * s.happiness)
            + (2.4 * self._rng.uniform(-1.0, 1.0))
            + (0.8 * s.emotional_drift),
            0.0,
            100.0,
        )
        s.motivation = _clamp(
            s.motivation
            + (-0.05 * s.motivation)
            + (0.34 * s.happiness)
            - (0.23 * s.stress)
            - (0.11 * s.sadness)
            + (2.2 * self._rng.uniform(-1.0, 1.0))
            - (0.5 * s.emotional_drift),
            0.0,
            100.0,
        )

        target_hr = 64.0 + (0.34 * s.stress) + (0.22 * s.fear) - (0.12 * s.happiness) + (0.10 * s.emotional_drift)
        target_hrv = 78.0 - (0.42 * s.stress) - (0.20 * s.fear) + (0.16 * s.happiness) - (0.08 * s.emotional_drift)

        s.heart_rate = _clamp((s.heart_rate * 0.75) + (target_hr * 0.25) + self._rng.uniform(-1.4, 1.4), 45.0, 180.0)
        s.hrv = _clamp((s.hrv * 0.80) + (target_hrv * 0.20) + self._rng.uniform(-1.0, 1.0), 5.0, 130.0)

    def tick(self, stress_input: Optional[float] = None, positive_input: Optional[float] = None) -> Dict[str, float]:
        inputs = self._sample_inputs() if stress_input is None or positive_input is None else {
            "stress_input": _clamp(float(stress_input), 0.0, 1.0),
            "positive_input": _clamp(float(positive_input), 0.0, 1.0),
        }
        self._last_inputs = (inputs["stress_input"], inputs["positive_input"])

        if self._using_c and self._lib is not None:
            self._lib.update_heart(
                ctypes.byref(self._state_c),
                ctypes.c_float(inputs["stress_input"]),
                ctypes.c_float(inputs["positive_input"]),
            )
            current = self._lib.get_state(ctypes.byref(self._state_c))
            state = {
                "stress": float(current.stress),
                "happiness": float(current.happiness),
                "sadness": float(current.sadness),
                "fear": float(current.fear),
                "motivation": float(current.motivation),
                "overthinking": float(current.overthinking),
                "heart_rate": float(current.heart_rate),
                "hrv": float(current.hrv),
                "emotional_drift": float(current.emotional_drift),
            }
        else:
            self._python_step(inputs["stress_input"], inputs["positive_input"])
            s = self._state_py
            state = {
                "stress": s.stress,
                "happiness": s.happiness,
                "sadness": s.sadness,
                "fear": s.fear,
                "motivation": s.motivation,
                "overthinking": s.overthinking,
                "heart_rate": s.heart_rate,
                "hrv": s.hrv,
                "emotional_drift": s.emotional_drift,
            }

        state.update(inputs)
        return {k: round(v, 4) for k, v in state.items()}

    def collect_snapshots(self, steps: Optional[int] = None) -> List[Dict[str, float]]:
        total_steps = steps if steps is not None else self._rng.randint(10, 20)
        snapshots: List[Dict[str, float]] = []
        for i in range(total_steps):
            snapshot = self.tick()
            snapshot["tick"] = i + 1
            snapshots.append(snapshot)
        return snapshots
