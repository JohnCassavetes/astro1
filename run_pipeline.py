#!/usr/bin/env python3
"""
Astro1 Pipeline Orchestrator

This script runs the entire candidate generation pipeline sequentially.
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

STAGES = [
    ("scripts/download_data.py", "Stage 1: Download Data"),
    ("scripts/preprocess_images.py", "Stage 2: Preprocess Images"),
    ("scripts/generate_embeddings.py", "Stage 3: Generate ResNet50 Embeddings"),
    ("scripts/detect_anomalies.py", "Stage 4: Isolation Forest Anomaly Detection"),
    ("scripts/scan_raw_secondary_sources.py", "Stage 5: Image-Plane Scanner & Photometric Filter"),
    ("scripts/compute_scan_stats.py", "Stage 6: Compute Pipeline Statistics"),
    ("scripts/make_paper_figures.py", "Stage 7: Generate Paper Figures")
]

def run_stage(script_path: str, stage_name: str, args: list = None, env: dict | None = None) -> bool:
    print(f"\n{'='*60}", flush=True)
    print(f"Executing {stage_name}", flush=True)
    print(f"{'='*60}", flush=True)
    
    cmd = [sys.executable, str(PROJECT_ROOT / script_path)]
    if args:
        cmd.extend(args)
        
    try:
        subprocess.run(cmd, check=True, cwd=PROJECT_ROOT, env=env)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Stage failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"\nERROR: Could not find script {script_path}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run the Astro1 pipeline.")
    parser.add_argument("--skip-download", action="store_true", help="Skip downloading new data (Stage 1)")
    parser.add_argument("--limit", type=int, default=5000, help="Number of records to process (for full run)")
    parser.add_argument("--config", type=str, default=None, help="Alternate config file path relative to repo root or absolute")
    args = parser.parse_args()
    env = os.environ.copy()
    if args.config:
        env["ASTRO1_CONFIG"] = args.config

    for script_path, stage_name in STAGES:
        cmd_args = []
        if "download_data" in script_path:
            if args.skip_download:
                print(f"Skipping {stage_name} as requested.", flush=True)
                continue
            cmd_args = ["--n", str(args.limit)]
            
        success = run_stage(script_path, stage_name, cmd_args, env=env)
        if not success:
            print("\nPipeline execution halted due to error.", flush=True)
            sys.exit(1)
            
    config_label = args.config if args.config else "config.yaml"
    print("\n" + "="*60, flush=True)
    print("PIPELINE COMPLETED SUCCESSFULLY!", flush=True)
    print(f"Results are available in the output paths configured by {config_label}.", flush=True)
    print("="*60, flush=True)

if __name__ == "__main__":
    main()
