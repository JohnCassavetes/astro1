#!/usr/bin/env python3
"""
Complete ML Pipeline Verification for Astro1
Re-runs the full pipeline on all galaxies to verify the 7 candidate results.
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import requests

import numpy as np
import pandas as pd
from tqdm import tqdm
import torch
import torch.nn as nn
from torchvision import models, transforms
from sklearn.ensemble import IsolationForest
from astropy.coordinates import SkyCoord
import astropy.units as u

# Paths
ROOT = Path("~/Desktop/astro1").expanduser()
DATA_PROC = ROOT / "data" / "processed"
DATA_META = ROOT / "data" / "metadata"
RESULTS_EMB = ROOT / "results" / "embeddings"
RESULTS_ANOM = ROOT / "results" / "anomaly_scores"
RESULTS_CAND = ROOT / "results" / "candidates"
MEMORY = ROOT / "memory"

# Timestamp for this run
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def log(msg: str):
    """Print with timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def load_all_processed_galaxies() -> pd.DataFrame:
    """Load all processed galaxy data from metadata"""
    log("Loading processed galaxy catalog...")
    catalog_path = DATA_META / "processed_catalog.csv"
    df = pd.read_csv(catalog_path)
    log(f"Found {len(df)} galaxies in catalog")
    
    # Filter to only those with processed files
    df['has_processed'] = df['processed_path'].apply(
        lambda x: Path(x).exists() if pd.notna(x) else False
    )
    df = df[df['has_processed']].copy()
    log(f"Of which {len(df)} have processed .npy files")
    return df

def regenerate_embeddings(df: pd.DataFrame, batch_size: int = 64) -> np.ndarray:
    """Regenerate embeddings for all galaxies using ResNet50"""
    log("=" * 60)
    log("STEP 1: Regenerating embeddings for all galaxies...")
    log("=" * 60)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    log(f"Using device: {device}")
    
    # Load pretrained ResNet50 (without final classification layer)
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
    model = nn.Sequential(*list(model.children())[:-1])
    model = model.to(device)
    model.eval()
    
    # Normalization for ImageNet
    normalize = transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
    
    embeddings = []
    objids = []
    
    for i in tqdm(range(0, len(df), batch_size), desc="Processing batches"):
        batch_df = df.iloc[i:i+batch_size]
        batch_tensors = []
        batch_objids = []
        
        for _, row in batch_df.iterrows():
            img_path = Path(row['processed_path'])
            if img_path.exists():
                img = np.load(img_path)
                # Convert to tensor
                if img.shape[2] == 3:  # RGB
                    img_tensor = torch.from_numpy(img).permute(2, 0, 1).float()
                else:  # Grayscale
                    img_tensor = torch.from_numpy(img).unsqueeze(0).repeat(3, 1, 1).float()
                img_tensor = normalize(img_tensor)
                batch_tensors.append(img_tensor)
                batch_objids.append(row['objid'])
        
        if batch_tensors:
            batch = torch.stack(batch_tensors).to(device)
            with torch.no_grad():
                features = model(batch)
                features = features.squeeze().cpu().numpy()
            
            if features.ndim == 1:
                features = features.reshape(1, -1)
            embeddings.append(features)
            objids.extend(batch_objids)
    
    all_embeddings = np.vstack(embeddings)
    log(f"Generated embeddings shape: {all_embeddings.shape}")
    
    # Save embeddings
    emb_path = RESULTS_EMB / f"galaxy_embeddings_{TIMESTAMP}.npy"
    np.save(emb_path, all_embeddings)
    log(f"Embeddings saved to: {emb_path}")
    
    return all_embeddings, objids

def run_isolation_forest(embeddings: np.ndarray, objids: List,
                         contamination: float = 0.02) -> pd.DataFrame:
    """Run Isolation Forest anomaly detection"""
    log("=" * 60)
    log("STEP 2: Running Isolation Forest anomaly detection...")
    log("=" * 60)
    log(f"Contamination parameter: {contamination}")
    log(f"Total galaxies: {len(embeddings)}")
    
    clf = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=42,
        n_jobs=-1
    )
    
    log("Fitting Isolation Forest...")
    clf.fit(embeddings)
    
    log("Computing anomaly scores...")
    scores = clf.decision_function(embeddings)
    predictions = clf.predict(embeddings)
    
    # Create results dataframe
    results = pd.DataFrame({
        'objid': objids,
        'anomaly_score': scores,
        'is_anomaly': predictions == -1
    })
    
    # Sort by anomaly score (most anomalous first)
    results = results.sort_values('anomaly_score', ascending=True)
    
    # Get RA/Dec from processed catalog
    catalog = pd.read_csv(DATA_META / "processed_catalog.csv")
    catalog = catalog[['objid', 'ra', 'dec']]
    results = results.merge(catalog, on='objid', how='left')
    
    n_anomalies = results['is_anomaly'].sum()
    log(f"Detected {n_anomalies} anomalies ({n_anomalies/len(results)*100:.2f}%)")
    
    # Save results
    scores_path = RESULTS_ANOM / f"isolation_forest_scores_{TIMESTAMP}.csv"
    results.to_csv(scores_path, index=False)
    log(f"Scores saved to: {scores_path}")
    
    return results

def query_simbad(ra: float, dec: float, radius_arcsec: float = 5.0) -> Dict:
    """Query SIMBAD for objects within radius"""
    try:
        url = "http://simbad.u-strasbg.fr/simbad/sim-coo"
        params = {
            'Coord': f"{ra} {dec}",
            'Radius': str(radius_arcsec),
            'Radius.unit': 'arcsec',
            'output.format': 'json'
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                return {'match': True, 'count': len(data['data'])}
        return {'match': False, 'count': 0}
    except Exception as e:
        return {'match': False, 'error': str(e)}

def query_ned(ra: float, dec: float, radius_arcsec: float = 5.0) -> Dict:
    """Query NED for objects within radius"""
    try:
        url = "https://ned.ipac.caltech.edu/srs/ObjectLookup"
        params = {
            'name': f"{ra}d {dec}d Equatorial J2000",
            'radius': str(radius_arcsec),
            'unit': 'arcsec'
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'objects' in data and len(data['objects']) > 0:
                return {'match': True, 'count': len(data['objects'])}
        return {'match': False, 'count': 0}
    except Exception as e:
        return {'match': False, 'error': str(e)}

def cross_reference_catalogs(df: pd.DataFrame, threshold: float = -0.05,
                             radius_arcsec: float = 5.0) -> pd.DataFrame:
    """Cross-reference anomalies with SIMBAD and NED"""
    log("=" * 60)
    log("STEP 3: Cross-referencing with SIMBAD and NED...")
    log("=" * 60)
    log(f"Checking galaxies with anomaly_score < {threshold}")
    log(f"Search radius: {radius_arcsec} arcsec")
    
    # Filter to candidates below threshold
    candidates = df[df['anomaly_score'] < threshold].copy()
    log(f"Found {len(candidates)} candidates below threshold")
    
    simbad_matches = []
    ned_matches = []
    
    log("Querying SIMBAD and NED (this may take a while)...")
    for idx, row in tqdm(candidates.iterrows(), total=len(candidates), desc="Cross-matching"):
        ra, dec = row['ra'], row['dec']
        
        # Query SIMBAD
        simbad = query_simbad(ra, dec, radius_arcsec)
        simbad_matches.append(simbad['match'])
        
        # Query NED
        ned = query_ned(ra, dec, radius_arcsec)
        ned_matches.append(ned['match'])
        
        # Rate limiting
        time.sleep(0.1)
    
    candidates['simbad_match'] = simbad_matches
    candidates['ned_match'] = ned_matches
    candidates['any_catalog_match'] = candidates['simbad_match'] | candidates['ned_match']
    
    return candidates

def apply_vae_detection(df: pd.DataFrame) -> pd.DataFrame:
    """Apply VAE novelty detection if model exists"""
    log("=" * 60)
    log("STEP 4: Applying VAE novelty detection...")
    log("=" * 60)
    
    vae_path = ROOT / "results" / "galaxy_vae_final.pth"
    if not vae_path.exists():
        log(f"VAE model not found at {vae_path}")
        log("Skipping VAE detection")
        return df
    
    log("VAE model found - loading...")
    # Import VAE class
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from vae_novelty import GalaxyVAE
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = GalaxyVAE(latent_dim=128).to(device)
    model.load_state_dict(torch.load(vae_path, map_location=device))
    model.eval()
    
    # Compute VAE scores for candidates
    transform = transforms.Compose([
        transforms.ToTensor(),
    ])
    
    vae_scores = []
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="VAE scoring"):
        try:
            img_path = DATA_PROC / f"{row['objid']}.npy"
            if img_path.exists():
                img = np.load(img_path)
                img_tensor = torch.from_numpy(img).permute(2, 0, 1).float().unsqueeze(0).to(device)
                
                with torch.no_grad():
                    error = model.reconstruction_error(img_tensor)
                    vae_scores.append(error.item())
            else:
                vae_scores.append(None)
        except Exception as e:
            vae_scores.append(None)
    
    df['vae_score'] = vae_scores
    log("VAE scoring complete")
    
    return df

def generate_report(candidates: pd.DataFrame, output_dir: Path):
    """Generate final verification report"""
    log("=" * 60)
    log("STEP 5: Generating verification report...")
    log("=" * 60)
    
    # Filter for truly uncataloged candidates
    uncataloged = candidates[~candidates['any_catalog_match']].copy()
    
    report = []
    report.append("=" * 80)
    report.append("ASTRO1 ML PIPELINE VERIFICATION REPORT")
    report.append("=" * 80)
    report.append(f"Timestamp: {TIMESTAMP}")
    report.append(f"Total galaxies processed: {len(pd.read_csv(DATA_META / 'processed_catalog.csv'))}")
    report.append(f"Isolation Forest contamination: 0.02")
    report.append(f"Anomaly score threshold: -0.05")
    report.append(f"Cross-match radius: 5 arcsec")
    report.append("")
    report.append("-" * 80)
    report.append("RESULTS SUMMARY")
    report.append("-" * 80)
    report.append(f"Candidates below threshold (< -0.05): {len(candidates)}")
    report.append(f"  - With SIMBAD match: {candidates['simbad_match'].sum()}")
    report.append(f"  - With NED match: {candidates['ned_match'].sum()}")
    report.append(f"  - With any catalog match: {candidates['any_catalog_match'].sum()}")
    report.append(f"")
    report.append(f"TRULY UNCATALOGED CANDIDATES: {len(uncataloged)}")
    report.append("")
    
    if len(uncataloged) > 0:
        report.append("-" * 80)
        report.append("CANDIDATE DETAILS")
        report.append("-" * 80)
        for idx, row in uncataloged.head(20).iterrows():
            report.append(f"\nCandidate {idx+1}:")
            report.append(f"  ObjID: {row['objid']}")
            report.append(f"  RA: {row['ra']:.6f}, Dec: {row['dec']:.6f}")
            report.append(f"  Anomaly Score: {row['anomaly_score']:.6f}")
            if 'vae_score' in row and pd.notna(row['vae_score']):
                report.append(f"  VAE Score: {row['vae_score']:.6f}")
    
    report.append("")
    report.append("-" * 80)
    report.append("COMPARISON WITH PREVIOUS RUN")
    report.append("-" * 80)
    report.append(f"Previous candidate count: 7")
    report.append(f"New candidate count: {len(uncataloged)}")
    
    if len(uncataloged) == 7:
        report.append("✓ MATCH: Candidate count matches previous run!")
    elif len(uncataloged) < 7:
        report.append(f"⚠ FEWER: {7 - len(uncataloged)} fewer candidates than previous run")
    else:
        report.append(f"⚠ MORE: {len(uncataloged) - 7} more candidates than previous run")
    
    report.append("")
    report.append("=" * 80)
    
    report_text = "\n".join(report)
    print("\n" + report_text)
    
    # Save report
    report_path = output_dir / f"verification_report_{TIMESTAMP}.txt"
    with open(report_path, 'w') as f:
        f.write(report_text)
    log(f"Report saved to: {report_path}")
    
    # Save detailed results
    results_path = output_dir / f"candidates_detailed_{TIMESTAMP}.csv"
    uncataloged.to_csv(results_path, index=False)
    log(f"Detailed results saved to: {results_path}")
    
    # Update project state
    state_path = MEMORY / "project_state.json"
    if state_path.exists():
        with open(state_path) as f:
            state = json.load(f)
        
        state['verification_run'] = {
            'timestamp': TIMESTAMP,
            'total_galaxies': len(pd.read_csv(DATA_META / 'processed_catalog.csv')),
            'candidates_found': len(uncataloged),
            'matches_previous': len(uncataloged) == 7
        }
        
        with open(state_path, 'w') as f:
            json.dump(state, f, indent=2)
    
    return len(uncataloged)

def main():
    start_time = time.time()
    
    log("=" * 80)
    log("ASTRO1 ML PIPELINE VERIFICATION")
    log("=" * 80)
    log("Re-running complete pipeline on all galaxies...")
    log("")
    
    # Create output directories
    RESULTS_ANOM.mkdir(parents=True, exist_ok=True)
    RESULTS_CAND.mkdir(parents=True, exist_ok=True)
    
    # Step 0: Load all processed galaxies
    df_catalog = load_all_processed_galaxies()
    
    # Step 1: Regenerate embeddings
    embeddings, objids = regenerate_embeddings(df_catalog)
    
    # Step 2: Run Isolation Forest
    anomaly_results = run_isolation_forest(embeddings, objids, contamination=0.02)
    
    # Step 3: Cross-reference with catalogs
    candidates = cross_reference_catalogs(anomaly_results, threshold=-0.05, radius_arcsec=5.0)
    
    # Step 4: Apply VAE detection (optional)
    candidates = apply_vae_detection(candidates)
    
    # Step 5: Generate report
    final_count = generate_report(candidates, RESULTS_ANOM)
    
    elapsed = time.time() - start_time
    log("")
    log("=" * 80)
    log(f"VERIFICATION COMPLETE")
    log(f"Final uncataloged candidate count: {final_count}")
    log(f"Matches previous count of 7: {'YES' if final_count == 7 else 'NO'}")
    log(f"Total runtime: {elapsed/60:.1f} minutes")
    log("=" * 80)

if __name__ == "__main__":
    main()
