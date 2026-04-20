"""Generate performance visualization from test results."""

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt


PERFORMANCE_LOG = Path("performance_log.csv")
OUTPUT_PNG = Path("performance_plot.png")


def plot_performance() -> None:
    """Generate and save performance plots."""
    if not PERFORMANCE_LOG.exists():
        print(f"Error: {PERFORMANCE_LOG} not found.")
        print("Run 'python3 test_empathy_responses.py' first to generate performance data.")
        sys.exit(1)

    test_cases = []
    latencies = []
    response_lengths = []

    with PERFORMANCE_LOG.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            test_cases.append(row["test_case"])
            latencies.append(float(row["latency"]))
            response_lengths.append(int(row["response_length"]))

    if not test_cases:
        print(f"No data found in {PERFORMANCE_LOG}")
        sys.exit(1)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # Plot 1: Latency vs Test Case
    ax1.plot(test_cases, latencies, marker="o", linewidth=2)
    ax1.set_xlabel("Test Case")
    ax1.set_ylabel("Latency (seconds)")
    ax1.set_title("Response Latency by Test Case")
    ax1.grid(True, alpha=0.3)

    # Plot 2: Response Length vs Test Case
    ax2.plot(test_cases, response_lengths, marker="s", linewidth=2)
    ax2.set_xlabel("Test Case")
    ax2.set_ylabel("Response Length (characters)")
    ax2.set_title("Response Length by Test Case")
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUTPUT_PNG, dpi=150)
    print(f"Performance plot saved: {OUTPUT_PNG}")
    plt.close()


if __name__ == "__main__":
    plot_performance()
