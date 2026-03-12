#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

import logging
import yaml

# Load configuration and setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
with open(PROJECT_ROOT / "config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Setup logging
LOG_DIR = PROJECT_ROOT / config['paths']['logs']
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f"{Path(__file__).stem}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(Path(__file__).stem)

csv_path = PROJECT_ROOT / config['paths']['results'] / "raw_object_scan" / "raw_object_scan.csv"
df = pd.read_csv(csv_path)

flagged = df[df["secondary_object_flag"] == True]
total_flagged = len(flagged)

major_mergers = len(flagged[flagged["brightest_secondary_flux_ratio"] >= 0.5])
minor_companions = len(flagged[(flagged["brightest_secondary_flux_ratio"] >= 0.15) & (flagged["brightest_secondary_flux_ratio"] < 0.5)])

print(f"Total flagged candidates: {total_flagged}")
print(f"Major merger candidates (secondary flux >= 50% primary): {major_mergers}")
print(f"Minor companion candidates (secondary flux 15%-50% primary): {minor_companions}")

# Save stats to a small text file so we can refer to it
stats_path = PROJECT_ROOT / config['paths']['results'] / "raw_object_scan" / "stats.txt"
with open(stats_path, "w") as f:
    f.write(f"Total flagged: {total_flagged}\n")
    f.write(f"Major mergers: {major_mergers}\n")
    f.write(f"Minor companions: {minor_companions}\n")

