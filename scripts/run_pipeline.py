#!/usr/bin/env python3
"""
Master runner for the astro1 pipeline.
Executes all stages or specific stages as requested.
"""

import sys
import subprocess
from pathlib import Path

ROOT = Path("~/Desktop/astro1").expanduser()
SCRIPTS = ROOT / "scripts"

def run_stage(stage_name: str, extra_args: list = None):
    """Run a single pipeline stage."""
    script_map = {
        'download': 'download_data.py',
        'preprocess': 'preprocess_images.py',
        'embed': 'generate_embeddings.py',
        'detect': 'detect_anomalies.py',
        'raw_scan': 'scan_raw_secondary_sources.py',
    }
    
    if stage_name not in script_map:
        print(f"Unknown stage: {stage_name}")
        print(f"Available: {list(script_map.keys())}")
        return False
    
    script = SCRIPTS / script_map[stage_name]
    
    cmd = [sys.executable, str(script)]
    if extra_args:
        cmd.extend(extra_args)
    
    print(f"\n{'='*60}")
    print(f"Running stage: {stage_name}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd)
    return result.returncode == 0

def run_all(test_mode: bool = False):
    """Run full pipeline."""
    stages = ['download', 'preprocess', 'embed', 'detect', 'raw_scan']
    
    for stage in stages:
        args = ['--test'] if test_mode and stage == 'download' else []
        if not run_stage(stage, args):
            print(f"\nStage {stage} failed. Stopping.")
            return False
    
    print("\n" + "="*60)
    print("Pipeline complete!")
    print("="*60)
    return True

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Run astro1 pipeline')
    parser.add_argument('stage', nargs='?', default='all',
                       help='Stage to run (download|preprocess|embed|detect|raw_scan|all)')
    parser.add_argument('--test', action='store_true',
                       help='Test mode - small sample')
    parser.add_argument('--args', nargs=argparse.REMAINDER,
                       help='Additional arguments to pass to stage')
    
    args = parser.parse_args()
    
    extra_args = args.args if args.args else []
    if args.test:
        extra_args.append('--test')
    
    if args.stage == 'all':
        run_all(test_mode=args.test)
    else:
        run_stage(args.stage, extra_args)

if __name__ == "__main__":
    main()
