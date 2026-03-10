#!/usr/bin/env python3
"""
Stage 6: Review Candidates

Prepare candidate gallery and evidence logs for human review.
Generate summary report.
"""

import os
import json
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

# Paths
ROOT = Path("~/Desktop/astro1").expanduser()
DATA_PROC = ROOT / "data" / "processed"
RESULTS_CAND = ROOT / "results" / "candidates"
MEMORY = ROOT / "memory"

def load_state() -> dict:
    with open(MEMORY / "project_state.json") as f:
        return json.load(f)

def update_project_state(phase: str, status: str):
    proj_path = MEMORY / "project_state.json"
    with open(proj_path) as f:
        proj = json.load(f)
    proj["phases"][phase]["status"] = status
    if status == "in_progress":
        proj["current_phase"] = phase
    with open(proj_path, 'w') as f:
        json.dump(proj, f, indent=2)

def generate_review_report(candidates_path: Path) -> str:
    """
    Generate human-readable review report.
    """
    df = pd.read_csv(candidates_path)
    
    report_lines = [
        "# Candidate Review Report",
        f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"\n## Summary\n",
        f"Total candidates: {len(df)}",
        "\n### Classification Breakdown:\n"
    ]
    
    for label, count in df['label'].value_counts().items():
        pct = 100 * count / len(df)
        report_lines.append(f"- **{label}**: {count} ({pct:.1f}%)")
    
    # Focus on uncataloged candidates
    uncataloged = df[df['label'] == 'uncataloged_candidate'].sort_values('anomaly_score')
    
    report_lines.extend([
        "\n## Uncataloged Candidates for Follow-up\n",
        f"Count: **{len(uncataloged)}**\n"
    ])
    
    if len(uncataloged) > 0:
        report_lines.append("| ID | RA | Dec | Anomaly Score | Evidence |")
        report_lines.append("|---|---|---|---|---|")
        
        for _, row in uncataloged.head(20).iterrows():
            evidence = json.loads(row['evidence_log'])
            evidence_str = '; '.join(evidence[:2]) if evidence else 'None'
            report_lines.append(
                f"| {row['objid'][:12]}... | {row['ra']:.4f} | {row['dec']:+.4f} | "
                f"{row['anomaly_score']:.4f} | {evidence_str} |"
            )
    
    # Top anomalies regardless of label
    report_lines.extend([
        "\n## Top 10 Anomalies (All Classes)\n",
        "| ID | RA | Dec | Score | Label |",
        "|---|---|---|---|---|"
    ])
    
    for _, row in df.head(10).iterrows():
        report_lines.append(
            f"| {row['objid'][:12]}... | {row['ra']:.4f} | {row['dec']:+.4f} | "
            f"{row['anomaly_score']:.4f} | {row['label']} |"
        )
    
    # Recommendations
    report_lines.extend([
        "\n## Recommendations\n",
        "1. **Immediate**: Visually inspect all `uncataloged_candidate` objects",
        "2. **Short-term**: Literature search for `previously_discussed` candidates",
        "3. **Quality**: Review `artifact_low_confidence` to improve filters",
        "4. **Validation**: Follow up top 3 candidates with spectroscopy"
    ])
    
    return '\n'.join(report_lines)

def create_candidate_gallery(candidates_path: Path, max_candidates: int = 20):
    """
    Create a visual gallery of top candidates.
    """
    df = pd.read_csv(candidates_path)
    
    # Focus on uncataloged and high-confidence anomalies
    df_gallery = df[df['label'] == 'uncataloged_candidate'].head(max_candidates)
    
    if len(df_gallery) == 0:
        print("No uncataloged candidates for gallery")
        return
    
    print(f"Creating gallery with {len(df_gallery)} candidates...")
    
    gallery_entries = []
    for _, row in df_gallery.iterrows():
        objid = row['objid']
        img_path = DATA_PROC / f"{objid}.npy"
        
        entry = {
            'objid': objid,
            'ra': row['ra'],
            'dec': row['dec'],
            'anomaly_score': row['anomaly_score'],
            'image_path': str(img_path) if img_path.exists() else None,
            'label': row['label']
        }
        gallery_entries.append(entry)
    
    # Save gallery metadata
    gallery_path = RESULTS_CAND / "gallery_metadata.json"
    with open(gallery_path, 'w') as f:
        json.dump(gallery_entries, f, indent=2)
    
    return gallery_entries

def update_decision_log():
    """
    Add review completion to decision log.
    """
    log_path = MEMORY / "decision_log.md"
    with open(log_path, 'a') as f:
        f.write(f"\n**{datetime.now().strftime('%Y-%m-%d %H:%M')}** - Candidate Review Complete\n")
        f.write("- Decision: Reviewed all anomaly candidates\n")
        f.write("- Action: Prepared gallery and evidence logs\n")

def main():
    update_project_state("candidate_review", "in_progress")
    
    candidates_path = RESULTS_CAND / "filtered_candidates.csv"
    if not candidates_path.exists():
        print(f"Filtered candidates not found: {candidates_path}")
        print("Run novelty_filter.py first.")
        return
    
    # Generate report
    report = generate_review_report(candidates_path)
    report_path = RESULTS_CAND / "review_report.md"
    with open(report_path, 'w') as f:
        f.write(report)
    
    # Create gallery
    create_candidate_gallery(candidates_path)
    
    # Update decision log
    update_decision_log()
    
    update_project_state("candidate_review", "completed")
    print(f"\nStage 6 complete.")
    print(f"Report: {report_path}")

if __name__ == "__main__":
    main()
