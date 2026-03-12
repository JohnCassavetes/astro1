#!/usr/bin/env python3

from pathlib import Path
import sys

import pandas as pd

from common import load_config, setup_logger


PROJECT_ROOT, config = load_config()
logger = setup_logger(__file__, config, PROJECT_ROOT)

csv_path = PROJECT_ROOT / config["paths"]["results"] / "raw_object_scan" / "raw_object_scan.csv"
if not csv_path.exists():
    print(f"\nERROR: File not found: {csv_path}")
    print("Cannot compute stats. Halting.")
    sys.exit(1)

df = pd.read_csv(csv_path)

flagged = df[df["secondary_object_flag"] == True]
total_flagged = len(flagged)

major_mergers = len(flagged[flagged["brightest_secondary_flux_ratio"] >= 0.5])
minor_companions = len(
    flagged[
        (flagged["brightest_secondary_flux_ratio"] >= 0.15)
        & (flagged["brightest_secondary_flux_ratio"] < 0.5)
    ]
)

print(f"Total flagged candidates: {total_flagged}")
print(f"Major merger candidates (secondary flux >= 50% primary): {major_mergers}")
print(f"Minor companion candidates (secondary flux 15%-50% primary): {minor_companions}")

stats_path = PROJECT_ROOT / config["paths"]["results"] / "raw_object_scan" / "stats.txt"
with open(stats_path, "w") as f:
    f.write(f"Total flagged: {total_flagged}\n")
    f.write(f"Major mergers: {major_mergers}\n")
    f.write(f"Minor companions: {minor_companions}\n")
