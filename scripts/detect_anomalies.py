#!/usr/bin/env python3
"""
Stage 4: Detect Anomalies

Apply Isolation Forest to embeddings to find unusual galaxies.
"""

import os
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from common import (
    ensure_method_state,
    ensure_project_state,
    load_config,
    save_json,
    setup_logger,
    update_project_state,
)

PROJECT_ROOT, config = load_config()
logger = setup_logger(__file__, config, PROJECT_ROOT)

DATA_META = PROJECT_ROOT / config['paths']['metadata']
RESULTS_EMB = PROJECT_ROOT / config['paths']['intermediate'] / "embeddings"
RESULTS_ANOM = PROJECT_ROOT / config['paths']['intermediate'] / "anomaly_scores"
RESULTS_CAND = PROJECT_ROOT / config['paths']['candidates']
MEMORY = PROJECT_ROOT / config['paths']['memory']

def load_state() -> dict:
    return ensure_project_state(MEMORY)

def detect_anomalies(catalog_path: Path, 
                     contamination: float = 0.05,
                     n_estimators: int = 100) -> pd.DataFrame:
    """
    Run Isolation Forest on embeddings to detect anomalies.
    """
    df = pd.read_csv(catalog_path)
    if len(df) == 0:
        print("\nERROR: Embedding catalog is empty. Cannot detect anomalies.")
        return pd.DataFrame()
        
    print(f"Running anomaly detection on {len(df)} galaxies...")
    print(f"Contamination: {contamination} (top {contamination*100:.1f}% flagged)")
    
    # Load embeddings
    emb_path = RESULTS_EMB / "galaxy_embeddings.npy"
    if not emb_path.exists():
        print(f"\nERROR: Embedding file not found: {emb_path}")
        print("Run generate_embeddings.py first and make sure it completes successfully.")
        return pd.DataFrame()
    embeddings = np.load(emb_path)
    
    # Filter to only galaxies in catalog
    embedding_idx = df['embedding_idx'].values
    X = embeddings[embedding_idx]
    
    # Fit Isolation Forest
    clf = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=42,
        n_jobs=-1
    )
    
    print("Fitting Isolation Forest...")
    clf.fit(X)
    
    # Get anomaly scores
    # decision_function: negative = more anomalous
    scores = clf.decision_function(X)
    predictions = clf.predict(X)  # -1 = anomaly, 1 = normal
    
    # Add to dataframe
    df['anomaly_score'] = scores
    df['is_anomaly'] = predictions == -1
    
    # Sort by anomaly score (most anomalous first)
    df = df.sort_values('anomaly_score', ascending=True)
    
    # Save scores
    scores_path = RESULTS_ANOM / "anomaly_scores.csv"
    df[['objid', 'ra', 'dec', 'anomaly_score', 'is_anomaly']].to_csv(scores_path, index=False)
    
    # Save top candidates
    n_anomalies = df['is_anomaly'].sum()
    print(f"\nDetected {n_anomalies} anomalies")
    
    top_candidates = df[df['is_anomaly']].head(100)
    cand_path = RESULTS_CAND / "initial_candidates.csv"
    top_candidates.to_csv(cand_path, index=False)
    
    return df

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--contamination', type=float, default=0.05,
                       help='Fraction of outliers (default: 0.05)')
    parser.add_argument('--n-estimators', type=int, default=100)
    args = parser.parse_args()
    
    RESULTS_ANOM.mkdir(parents=True, exist_ok=True)
    RESULTS_CAND.mkdir(parents=True, exist_ok=True)
    update_project_state(MEMORY, "anomaly_detection", "in_progress")
    
    catalog_path = DATA_META / "embedding_catalog.csv"
    if not catalog_path.exists():
        print(f"Embedding catalog not found: {catalog_path}")
        print("Run generate_embeddings.py first.")
        return
    
    df = detect_anomalies(
        catalog_path,
        contamination=args.contamination,
        n_estimators=args.n_estimators
    )
    
    if len(df) == 0:
        print("\nERROR: No anomalies detected (empty catalog). Halting.")
        exit(1)
    
    # Update method state
    method_state = ensure_method_state(MEMORY)
    method_state.setdefault('anomaly_detection', {})
    method_state['anomaly_detection']['method'] = 'IsolationForest'
    save_json(MEMORY / "method_state.json", method_state)
    
    update_project_state(MEMORY, "anomaly_detection", "completed")
    print(f"\nStage 4 complete.")
    print(f"Anomaly scores: {RESULTS_ANOM}/anomaly_scores.csv")
    print(f"Top candidates: {RESULTS_CAND}/initial_candidates.csv")

if __name__ == "__main__":
    main()
