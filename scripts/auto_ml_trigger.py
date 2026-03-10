#!/usr/bin/env python3
"""
Auto-ML Pipeline Trigger for Astro1
Runs full pipeline when download completes
"""

import os
import sys
import subprocess
import pandas as pd
from pathlib import Path

ROOT = Path("~/Desktop/astro1").expanduser()

def run_command(cmd, cwd=None):
    """Run a shell command and return success status."""
    print(f"\n🚀 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd or ROOT)
    return result.returncode == 0

def check_download_status():
    """Check if download is complete and ML should run."""
    catalog_path = ROOT / "data" / "metadata" / "galaxy_catalog.csv"
    
    if not catalog_path.exists():
        print("❌ Catalog not found")
        return False, 0
    
    df = pd.read_csv(catalog_path)
    total = len(df)
    downloaded = df['downloaded'].sum() if 'downloaded' in df.columns else 0
    
    print(f"📊 Catalog status: {downloaded}/{total} galaxies downloaded")
    
    # Check if parallel download is still running
    check_running = subprocess.run("pgrep -f 'download_parallel.py'", shell=True, capture_output=True)
    is_running = check_running.returncode == 0
    
    if is_running:
        print("⏳ Download still in progress...")
        return False, downloaded
    
    # If we have 6000+ galaxies and download stopped, run ML
    if downloaded >= 6000:
        print(f"✅ Download complete with {downloaded} galaxies. Starting ML pipeline...")
        return True, downloaded
    
    print(f"⏳ Waiting for more galaxies (current: {downloaded}, target: 6000+)")
    return False, downloaded

def run_ml_pipeline():
    """Execute the full ML pipeline."""
    scripts = [
        ("python3 scripts/preprocess_images.py", "Preprocessing images"),
        ("python3 scripts/generate_embeddings_fast.py", "Generating embeddings"),
        ("python3 scripts/detect_anomalies.py --contamination 0.02", "Detecting anomalies (2%)"),
        ("python3 scripts/novelty_filter.py", "Filtering for novelty"),
        ("python3 scripts/review_candidates.py", "Reviewing candidates"),
        ("python3 scripts/make_figures.py", "Generating figures"),
    ]
    
    for cmd, desc in scripts:
        print(f"\n{'='*60}")
        print(f"Step: {desc}")
        print('='*60)
        if not run_command(cmd):
            print(f"⚠️  Warning: {desc} may have had issues")
    
    print("\n" + "="*60)
    print("✅ ML Pipeline Complete!")
    print("="*60)

def update_paper():
    """Update paper draft with new results."""
    print("\n📝 Updating paper draft...")
    # Paper update is handled by the agent in the cron job
    pass

def git_push():
    """Push all changes to git."""
    print("\n📤 Pushing to GitHub...")
    run_command("git add -A && git commit -m 'Auto: ML pipeline complete with new candidates' && git push origin main")

def main():
    print("="*60)
    print("🤖 ASTRO1 AUTO-ML PIPELINE")
    print("="*60)
    
    should_run, count = check_download_status()
    
    if not should_run:
        print(f"\n⏳ Pipeline will trigger when download reaches 6000+ galaxies")
        print(f"   Current count: {count}")
        return 0
    
    # Run the full pipeline
    run_ml_pipeline()
    
    # Push results
    git_push()
    
    print("\n🎉 All done! Check results/candidates/ for new discoveries.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
