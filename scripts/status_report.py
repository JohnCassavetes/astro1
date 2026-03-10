#!/usr/bin/env python3
"""
Quick status check for astro1 project
"""

import json
from pathlib import Path
from datetime import datetime

def generate_status_report():
    ROOT = Path("~/Desktop/astro1").expanduser()
    
    # Load project state
    with open(ROOT / "memory" / "project_state.json") as f:
        state = json.load(f)
    
    # Load candidate registry
    with open(ROOT / "memory" / "candidate_registry.json") as f:
        registry = json.load(f)
    
    # Count files
    import subprocess
    result = subprocess.run(
        f"find {ROOT}/data/raw -name '*.jpg' -size +0 | wc -l",
        shell=True, capture_output=True, text=True
    )
    valid_files = int(result.stdout.strip())
    
    result = subprocess.run(
        f"ls {ROOT}/data/raw/*.jpg 2>/dev/null | wc -l",
        shell=True, capture_output=True, text=True
    )
    total_files = int(result.stdout.strip())
    
    # Check for models
    model_files = list((ROOT / "results").glob("*.pth"))
    
    # Count candidates
    candidates = registry.get('candidates', [])
    total_candidates = len(candidates)
    known_recovered = sum(1 for c in candidates if c.get('label') == 'known_recovered')
    previously_discussed = sum(1 for c in candidates if c.get('label') == 'previously_discussed')
    uncataloged = sum(1 for c in candidates if c.get('label') == 'uncataloged_candidate')
    
    report = f"""
🌌 ASTRO1 PROJECT STATUS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== PROJECT PHASE ===
Current Phase: {state['current_phase']}
Overall Status: {state['status']}

=== DATA STATUS ===
Total galaxy images: {total_files}
Valid downloads: {valid_files}
Failed downloads: {total_files - valid_files}
Success rate: {valid_files/total_files*100:.1f}%

=== ML MODELS ===
Model files: {len(model_files)}
"""
    
    for model in model_files:
        size_mb = model.stat().st_size / (1024 * 1024)
        report += f"  - {model.name}: {size_mb:.1f} MB\n"
    
    report += f"""
=== CANDIDATES ===
Total detected: {total_candidates}
- Known recovered: {known_recovered}
- Previously discussed: {previously_discussed}
- Uncataloged: {uncataloged} 🔍

=== RECENT PROGRESS ===
"""
    
    # Phase status
    for phase, info in state['phases'].items():
        status_icon = "✅" if info['status'] == 'completed' else "🔄" if info['status'] == 'in_progress' else "⏳"
        report += f"{status_icon} {phase}: {info['status']}\n"
    
    report += f"""
=== NEXT STEPS ===
1. Complete VAE anomaly detection (in progress)
2. Run ensemble consensus across methods
3. Review new candidates
4. Update paper with results

Last heartbeat: {state['last_heartbeat']}
"""
    
    return report

if __name__ == "__main__":
    print(generate_status_report())
