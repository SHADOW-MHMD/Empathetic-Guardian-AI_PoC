"""Generate lightweight performance trend output from CSV results."""

import csv
import json
import sys
from pathlib import Path


PERFORMANCE_LOG = Path("performance_log.csv")
OUTPUT_JSON = Path("performance_trend.json")


def _ascii_bar(value: float, maximum: float, width: int = 24) -> str:
    if maximum <= 0:
        return ""
    filled = int((value / maximum) * width)
    return "#" * filled + "." * (width - filled)


def plot_performance() -> None:
    """Print ASCII trend lines and write a JSON trend summary."""
    if not PERFORMANCE_LOG.exists():
        print(f"Error: {PERFORMANCE_LOG} not found.")
        print("Run 'python3 test_empathy_responses.py' first to generate performance data.")
        sys.exit(1)

    test_cases = []
    latencies = []
    response_lengths = []
    stress_values = []
    hrv_values = []

    with PERFORMANCE_LOG.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            test_cases.append(row["test_case"])
            latencies.append(float(row["latency"]))
            response_lengths.append(int(row["response_length"]))
            stress_values.append(float(row.get("heart_stress", 0.0)))
            hrv_values.append(float(row.get("hrv", 0.0)))

    if not test_cases:
        print(f"No data found in {PERFORMANCE_LOG}")
        sys.exit(1)

    max_latency = max(latencies)
    max_len = max(response_lengths)
    max_stress = max(stress_values) if stress_values else 0.0
    max_hrv = max(hrv_values) if hrv_values else 0.0

    print("Latency Trend")
    for case_id, value in zip(test_cases, latencies):
        print(f"Case {case_id:>2}: {_ascii_bar(value, max_latency)} {value:.4f}s")

    print("\nResponse Length Trend")
    for case_id, value in zip(test_cases, response_lengths):
        print(f"Case {case_id:>2}: {_ascii_bar(float(value), float(max_len))} {value} chars")

    if stress_values:
        print("\nStress Trend")
        for case_id, value in zip(test_cases, stress_values):
            print(f"Case {case_id:>2}: {_ascii_bar(value, max_stress)} {value:.2f}")

    trend_data = {
        "source": str(PERFORMANCE_LOG),
        "cases": len(test_cases),
        "latency": {
            "values": latencies,
            "average": round(sum(latencies) / len(latencies), 4),
            "max": max_latency,
        },
        "response_length": {
            "values": response_lengths,
            "average": round(sum(response_lengths) / len(response_lengths), 2),
            "max": max_len,
        },
        "heart_stress": {
            "values": stress_values,
            "max": max_stress,
        },
        "hrv": {
            "values": hrv_values,
            "max": max_hrv,
        },
    }

    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(trend_data, f, indent=2)

    print(f"\nTrend JSON saved: {OUTPUT_JSON}")


if __name__ == "__main__":
    plot_performance()
