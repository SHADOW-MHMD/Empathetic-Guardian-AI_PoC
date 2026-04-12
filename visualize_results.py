import csv
import os
import re
import sys
import webbrowser
from pathlib import Path

import matplotlib.pyplot as plt

CSV_FILE = Path("somatic_logs.csv")
REPORT_FILE = Path("session_report.md")
OUTPUT_FILE = Path("poc_performance_graph.png")


def parse_response_times_from_report(report_path):
    response_times = {}
    scenario = None
    scenario_pattern = re.compile(r"^## Scenario: (.+)$")
    response_pattern = re.compile(r"\((\d+\.\d+)s\) ")

    with report_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            scenario_match = scenario_pattern.match(line)
            if scenario_match:
                scenario = scenario_match.group(1).strip()
                continue
            if scenario is not None:
                response_match = response_pattern.search(line)
                if response_match:
                    response_times[scenario] = float(response_match.group(1))
                    scenario = None
    return response_times


def read_somatic_csv(path):
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]

    return rows


def main():
    if not CSV_FILE.exists():
        print(f"ERROR: {CSV_FILE} not found. Run main.py first to generate the somatic log.")
        sys.exit(1)

    rows = read_somatic_csv(CSV_FILE)
    if not rows:
        print(f"ERROR: {CSV_FILE} is empty. No data to plot.")
        sys.exit(1)

    scenarios = [row["Scenario"].upper() for row in rows]
    cortisol = [float(row.get("Cortisol", 0.0)) for row in rows]
    adrenaline = [float(row.get("Adrenaline", 0.0)) for row in rows]
    anxiety = [float(row.get("Anxiety_Level", 0.0)) for row in rows]
    response_time = []

    if "Response_Time" in rows[0]:
        response_time = [float(row.get("Response_Time", 0.0)) for row in rows]
    elif REPORT_FILE.exists():
        parsed = parse_response_times_from_report(REPORT_FILE)
        response_time = [parsed.get(scenario, 0.0) for scenario in scenarios]
        if not any(response_time):
            print("WARNING: response time values were not found in session_report.md. Bars will be empty.")
    else:
        print("WARNING: Response_Time column not found and session_report.md is missing. Bars will be empty.")
        response_time = [0.0] * len(rows)

    x = list(range(len(scenarios)))
    plt.style.use("dark_background")
    fig, ax1 = plt.subplots(figsize=(14, 8))
    ax2 = ax1.twinx()

    ax1.plot(x, cortisol, marker="o", color="#ff3b30", linewidth=2.5, label="Cortisol")
    ax1.plot(x, adrenaline, marker="o", color="#ff9500", linewidth=2.5, label="Adrenaline")
    ax1.plot(x, anxiety, marker="o", color="#0a84ff", linewidth=2.5, label="Anxiety")
    ax1.fill_between(x, cortisol, alpha=0.1, color="#ff3b30")
    ax1.fill_between(x, adrenaline, alpha=0.08, color="#ff9500")
    ax1.fill_between(x, anxiety, alpha=0.08, color="#0a84ff")

    bar_color = "#38b6ff"
    ax2.bar(x, response_time, alpha=0.35, color=bar_color, width=0.5, label="Response Time (s)")

    ax1.set_xlabel("Scenario", color="#ffffff", fontsize=12)
    ax1.set_ylabel("Somatic Level", color="#ffffff", fontsize=12)
    ax2.set_ylabel("Response Time (s)", color=bar_color, fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(scenarios, rotation=20, fontsize=11, color="#ffffff")
    ax1.tick_params(axis="y", colors="#ffffff")
    ax2.tick_params(axis="y", colors=bar_color)

    ax1.grid(True, color="#444444", linestyle="--", linewidth=0.5, alpha=0.35)
    ax1.set_title("Empathetic Guardian AI Somatic Levels vs GPT-OSS Latency", color="#ffffff", fontsize=16, pad=20)

    lines, labels = ax1.get_legend_handles_labels()
    bars, bar_labels = ax2.get_legend_handles_labels()
    ax1.legend(lines + bars, labels + bar_labels, loc="upper left", frameon=False, fontsize=11)

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=180, facecolor="#0a0a12")
    print(f"Saved visualization to {OUTPUT_FILE}")

    try:
        webbrowser.open(OUTPUT_FILE.resolve().as_uri())
        print("Opened the chart in the default viewer.")
    except Exception:
        print("Could not automatically open the image. Please open poc_performance_graph.png manually.")


if __name__ == "__main__":
    main()
