#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

csv_path = Path("~/Desktop/astro1/results/raw_object_scan/raw_object_scan.csv").expanduser()
df = pd.read_csv(csv_path)

flagged = df[df["secondary_object_flag"] == True]
total_flagged = len(flagged)

major_mergers = len(flagged[flagged["brightest_secondary_flux_ratio"] >= 0.5])
minor_companions = len(flagged[(flagged["brightest_secondary_flux_ratio"] >= 0.15) & (flagged["brightest_secondary_flux_ratio"] < 0.5)])

print(f"Total flagged candidates: {total_flagged}")
print(f"Major merger candidates (secondary flux >= 50% primary): {major_mergers}")
print(f"Minor companion candidates (secondary flux 15%-50% primary): {minor_companions}")

# Save stats to a small text file so we can refer to it
stats_path = Path("~/Desktop/astro1/results/raw_object_scan/stats.txt").expanduser()
with open(stats_path, "w") as f:
    f.write(f"Total flagged: {total_flagged}\n")
    f.write(f"Major mergers: {major_mergers}\n")
    f.write(f"Minor companions: {minor_companions}\n")

