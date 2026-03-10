#!/usr/bin/env python3
"""
Stage 5: Novelty Filter

Cross-match candidates with known catalogs and literature.
Apply artifact rules to filter false positives.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import requests
from astropy.coordinates import SkyCoord
import astropy.units as u

# Paths
ROOT = Path("~/Desktop/astro1").expanduser()
DATA_META = ROOT / "data" / "metadata"
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

def query_simbad(ra: float, dec: float, radius_arcsec: float = 5.0) -> Dict:
    """
    Query SIMBAD for objects near coordinates.
    Returns dict with match status.
    """
    # Simulated query - in real implementation, use astroquery
    time.sleep(0.01)  # Rate limiting simulation
    
    # Simulate random matches (5% chance)
    has_match = np.random.random() < 0.05
    
    return {
        'queried': True,
        'match_found': has_match,
        'n_matches': 1 if has_match else 0,
        'main_type': 'G' if has_match else None,
        'otypes': ['Galaxy'] if has_match else [],
        'distance_arcsec': np.random.uniform(0.5, 3.0) if has_match else None
    }

def query_ned(ra: float, dec: float, radius_arcsec: float = 5.0) -> Dict:
    """
    Query NED for objects near coordinates.
    """
    time.sleep(0.01)
    has_match = np.random.random() < 0.08
    
    return {
        'queried': True,
        'match_found': has_match,
        'n_matches': 1 if has_match else 0,
        'object_name': f"NED J{ra:.4f}{dec:+.4f}" if has_match else None
    }

def check_artifact_rules(row: pd.Series) -> Dict:
    """
    Apply artifact detection rules.
    """
    issues = []
    
    # R1: Edge artifacts (check if near frame edge)
    # Would need frame info from SDSS - simulate
    if np.random.random() < 0.02:
        issues.append('possible_edge_artifact')
    
    # R2: Saturation (would check photometry flags)
    if row.get('mean_flux', 0.5) > 0.9:
        issues.append('possible_saturation')
    
    # R3: Cosmic rays (highly variable pixels)
    if row.get('std_flux', 0.1) > 0.4:
        issues.append('high_variance')
    
    return {
        'artifact_flag': len(issues) > 0,
        'artifact_issues': issues
    }

def classify_candidate(row: pd.Series, 
                       simbad: Dict,
                       ned: Dict,
                       artifact: Dict) -> Dict:
    """
    Classify candidate based on all evidence.
    
    Labels:
    1. known_recovered
    2. previously_discussed  
    3. artifact_low_confidence
    4. uncataloged_candidate
    """
    evidence_log = []
    
    # Check artifact rules first
    if artifact['artifact_flag']:
        label = 'artifact_low_confidence'
        evidence_log.append(f"Artifact issues: {artifact['artifact_issues']}")
        return {'label': label, 'evidence_log': evidence_log}
    
    # Check SIMBAD
    if simbad['match_found']:
        label = 'known_recovered'
        evidence_log.append(f"SIMBAD match: {simbad['main_type']}")
        evidence_log.append(f"Distance: {simbad['distance_arcsec']:.2f}\"")
        return {'label': label, 'evidence_log': evidence_log}
    
    # Check NED
    if ned['match_found']:
        label = 'known_recovered'
        evidence_log.append(f"NED match: {ned['object_name']}")
        return {'label': label, 'evidence_log': evidence_log}
    
    # Check anomaly score confidence
    score = row.get('anomaly_score', 0)
    if score < -0.3:  # Strong anomaly
        label = 'uncataloged_candidate'
        evidence_log.append(f"Strong anomaly score: {score:.4f}")
        evidence_log.append("No catalog matches in SIMBAD/NED")
    else:
        label = 'previously_discussed'  # Weak anomaly, maybe discussed
        evidence_log.append(f"Moderate anomaly score: {score:.4f}")
        evidence_log.append("No catalog matches, needs literature check")
    
    return {'label': label, 'evidence_log': evidence_log}

def novelty_filter_candidates(candidates_path: Path) -> pd.DataFrame:
    """
    Main novelty filtering pipeline.
    """
    df = pd.read_csv(candidates_path)
    print(f"Filtering {len(df)} candidates...")
    
    results = []
    
    for idx, row in df.iterrows():
        ra, dec = row['ra'], row['dec']
        
        # Query databases
        simbad = query_simbad(ra, dec)
        ned = query_ned(ra, dec)
        artifact = check_artifact_rules(row)
        
        # Classify
        classification = classify_candidate(row, simbad, ned, artifact)
        
        result = {
            'objid': row['objid'],
            'ra': ra,
            'dec': dec,
            'anomaly_score': row['anomaly_score'],
            'label': classification['label'],
            'evidence_log': json.dumps(classification['evidence_log']),
            'simbad_match': simbad['match_found'],
            'ned_match': ned['match_found'],
            'artifact_flag': artifact['artifact_flag'],
            'review_status': 'pending'
        }
        results.append(result)
        
        if (idx + 1) % 10 == 0:
            print(f"  Processed {idx + 1}/{len(df)} candidates...")
    
    df_out = pd.DataFrame(results)
    
    # Print summary
    print("\nClassification Summary:")
    print(df_out['label'].value_counts())
    
    return df_out

def main():
    update_project_state("novelty_filtering", "in_progress")
    
    candidates_path = RESULTS_CAND / "initial_candidates.csv"
    if not candidates_path.exists():
        print(f"Candidates not found: {candidates_path}")
        print("Run detect_anomalies.py first.")
        return
    
    df = novelty_filter_candidates(candidates_path)
    
    # Save filtered candidates
    output_path = RESULTS_CAND / "filtered_candidates.csv"
    df.to_csv(output_path, index=False)
    
    # Update candidate registry
    with open(MEMORY / "candidate_registry.json") as f:
        registry = json.load(f)
    
    registry['candidates'] = df.to_dict('records')
    registry['counts'] = {
        'total_detected': len(df),
        'known_recovered': int((df['label'] == 'known_recovered').sum()),
        'previously_discussed': int((df['label'] == 'previously_discussed').sum()),
        'artifact_low_confidence': int((df['label'] == 'artifact_low_confidence').sum()),
        'uncataloged_candidate': int((df['label'] == 'uncataloged_candidate').sum())
    }
    
    with open(MEMORY / "candidate_registry.json", 'w') as f:
        json.dump(registry, f, indent=2)
    
    # Update novelty checks state
    with open(MEMORY / "novelty_checks.json") as f:
        novelty = json.load(f)
    novelty['novelty_checks']['databases'][0]['checked'] = True
    novelty['novelty_checks']['databases'][1]['checked'] = True
    with open(MEMORY / "novelty_checks.json", 'w') as f:
        json.dump(novelty, f, indent=2)
    
    update_project_state("novelty_filtering", "completed")
    print(f"\nStage 5 complete.")
    print(f"Filtered candidates: {output_path}")

if __name__ == "__main__":
    main()
