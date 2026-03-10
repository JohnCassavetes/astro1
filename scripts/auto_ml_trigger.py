#!/usr/bin/env python3
"""
Auto-ML Pipeline Trigger for Astro1 - BATCH PROCESSING VERSION
Processes galaxies in batches (500 at a time) to avoid token limits
"""

import os
import sys
import subprocess
import pandas as pd
import json
from pathlib import Path

ROOT = Path("~/Desktop/astro1").expanduser()
BATCH_SIZE = 500  # Process 500 galaxies per run to stay under token limits
STATE_FILE = ROOT / "memory" / "ml_batch_state.json"

def load_state():
    """Load batch processing state."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "last_processed": 0,
        "total_candidates_found": 7,  # Already have 7 from initial batch
        "batches_completed": 0,
        "total_galaxies": 0
    }

def save_state(state):
    """Save batch processing state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

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
    return True, downloaded

def get_next_batch(state, total_downloaded):
    """Determine the next batch to process."""
    last_processed = state["last_processed"]
    
    if last_processed >= total_downloaded:
        print(f"✅ All {total_downloaded} galaxies already processed!")
        return None, None
    
    batch_start = last_processed
    batch_end = min(last_processed + BATCH_SIZE, total_downloaded)
    
    return batch_start, batch_end

def run_ml_pipeline_batch(batch_start, batch_end):
    """Execute ML pipeline on a specific batch of galaxies."""
    print(f"\n{'='*70}")
    print(f"🧬 PROCESSING BATCH: Galaxies {batch_start} to {batch_end}")
    print(f"{'='*70}")
    
    # Get list of galaxy IDs for this batch
    catalog_path = ROOT / "data" / "metadata" / "galaxy_catalog.csv"
    df = pd.read_csv(catalog_path)
    downloaded_df = df[df['downloaded'] == True].iloc[batch_start:batch_end]
    
    if len(downloaded_df) == 0:
        print("⚠️  No galaxies in this batch")
        return False, 0
    
    batch_objids = downloaded_df['objid'].tolist()
    batch_file = ROOT / "memory" / "current_batch_objids.txt"
    
    with open(batch_file, 'w') as f:
        for objid in batch_objids:
            f.write(f"{objid}\n")
    
    print(f"📁 Processing {len(batch_objids)} galaxies in this batch")
    
    # Run pipeline steps with batch filter
    steps = [
        (f"python3 scripts/preprocess_images.py --batch-file {batch_file}", "Preprocessing batch images"),
        (f"python3 scripts/generate_embeddings_fast.py --batch-file {batch_file}", "Generating embeddings"),
        (f"python3 scripts/detect_anomalies.py --contamination 0.02 --batch-file {batch_file}", "Detecting anomalies"),
        (f"python3 scripts/novelty_filter.py --batch-file {batch_file}", "Filtering for novelty"),
        (f"python3 scripts/review_candidates.py --batch-file {batch_file}", "Reviewing candidates"),
    ]
    
    for cmd, desc in steps:
        print(f"\n{'='*60}")
        print(f"Step: {desc}")
        print('='*60)
        if not run_command(cmd):
            print(f"⚠️  Warning: {desc} had issues but continuing...")
    
    # Count new candidates found in this batch
    candidates_file = ROOT / "results" / "candidates" / f"batch_{batch_start}_{batch_end}_candidates.csv"
    new_candidates = 0
    if candidates_file.exists():
        candidates_df = pd.read_csv(candidates_file)
        new_candidates = len(candidates_df)
    
    print(f"\n{'='*70}")
    print(f"✅ BATCH {batch_start}-{batch_end} COMPLETE!")
    print(f"🎯 New candidates found: {new_candidates}")
    print(f"{'='*70}")
    
    return True, new_candidates

def update_master_candidate_list():
    """Combine all batch results into master list."""
    print("\n📝 Updating master candidate list...")
    
    import glob
    batch_files = glob.glob(str(ROOT / "results" / "candidates" / "batch_*_candidates.csv"))
    
    if not batch_files:
        print("⚠️  No batch candidate files found")
        return 0
    
    all_candidates = []
    for f in batch_files:
        try:
            df = pd.read_csv(f)
            all_candidates.append(df)
        except Exception as e:
            print(f"⚠️  Error reading {f}: {e}")
    
    if all_candidates:
        master_df = pd.concat(all_candidates, ignore_index=True)
        # Remove duplicates based on objid
        master_df = master_df.drop_duplicates(subset=['objid'], keep='first')
        master_df = master_df.sort_values('anomaly_score')
        
        output_file = ROOT / "results" / "candidates" / "master_candidates.csv"
        master_df.to_csv(output_file, index=False)
        
        print(f"✅ Master list updated: {len(master_df)} total unique candidates")
        return len(master_df)
    
    return 0

def git_push(batch_info):
    """Push all changes to git."""
    print("\n📤 Pushing to GitHub...")
    msg = f"Auto: Batch {batch_info} processed, candidates updated"
    run_command(f"git add -A && git commit -m '{msg}' && git push origin main")

def main():
    print("="*70)
    print("🤖 ASTRO1 BATCH ML PIPELINE")
    print(f"📦 Batch size: {BATCH_SIZE} galaxies")
    print("="*70)
    
    # Check download status
    has_data, total_downloaded = check_download_status()
    
    if not has_data:
        print("\n❌ No data available")
        return 1
    
    # Load processing state
    state = load_state()
    state["total_galaxies"] = total_downloaded
    
    print(f"\n📊 State:")
    print(f"   Total downloaded: {total_downloaded}")
    print(f"   Last processed: {state['last_processed']}")
    print(f"   Batches completed: {state['batches_completed']}")
    print(f"   Total candidates so far: {state['total_candidates_found']}")
    
    # Get next batch
    batch_start, batch_end = get_next_batch(state, total_downloaded)
    
    if batch_start is None:
        print("\n✅ All batches complete! Running final consolidation...")
        total = update_master_candidate_list()
        
        if total > state["total_candidates_found"]:
            state["total_candidates_found"] = total
            save_state(state)
            git_push("FINAL")
            print(f"\n🎉 ALL DONE! Total candidates: {total}")
        return 0
    
    # Process this batch
    print(f"\n🎯 Processing batch: {batch_start} to {batch_end}")
    success, new_candidates = run_ml_pipeline_batch(batch_start, batch_end)
    
    if success:
        # Update state
        state["last_processed"] = batch_end
        state["batches_completed"] += 1
        state["total_candidates_found"] += new_candidates
        save_state(state)
        
        # Update master list
        update_master_candidate_list()
        
        # Push to git
        git_push(f"{batch_start}-{batch_end}")
        
        print(f"\n🎉 Batch complete! Progress: {batch_end}/{total_downloaded} galaxies")
        print(f"🎯 Session candidates: {new_candidates} | Total: {state['total_candidates_found']}")
        print(f"\n⏳ Next batch will process on next cron cycle")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
