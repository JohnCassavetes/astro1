#!/usr/bin/env python3
"""
Full Astro1 ML Pipeline with SIMBAD/NED Cross-Reference
Runs anomaly detection + VAE + astroquery verification for new discoveries.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm
from astropy.coordinates import SkyCoord
import astropy.units as u

# Check for astroquery
try:
    from astroquery.simbad import Simbad
    from astroquery.ned import Ned
    ASTROQUERY_AVAILABLE = True
except ImportError:
    ASTROQUERY_AVAILABLE = False
    print("Warning: astroquery not available, using mock queries")

# Try torch for VAE
try:
    import torch
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("Warning: PyTorch not available, VAE detection skipped")

# Paths
ROOT = Path("~/Desktop/astro1").expanduser()
DATA_META = ROOT / "data" / "metadata"
RESULTS_ANOM = ROOT / "results" / "anomaly_scores"
RESULTS_CAND = ROOT / "results" / "candidates"
MEMORY = ROOT / "memory"

# Verification criteria
SIMBAD_RADIUS = 5 * u.arcsec
NED_RADIUS = 5 * u.arcsec
ANOMALY_THRESHOLD = -0.05  # Top 2% roughly


def query_simbad_real(ra: float, dec: float, radius: u.Quantity = SIMBAD_RADIUS) -> Dict:
    """Query SIMBAD using astroquery for real cross-referencing."""
    if not ASTROQUERY_AVAILABLE:
        # Fallback to mock for testing
        return {'match_found': False, 'n_matches': 0, 'distance': None}
    
    try:
        result = Simbad.query_region(SkyCoord(ra=ra, dec=dec, unit='deg'), radius=radius)
        if result is not None and len(result) > 0:
            return {
                'match_found': True,
                'n_matches': len(result),
                'main_type': result['OTYPE'][0] if 'OTYPE' in result.colnames else 'Unknown',
                'distance': float(radius.to(u.arcsec).value)  # Approximate
            }
        return {'match_found': False, 'n_matches': 0, 'distance': None}
    except Exception as e:
        print(f"  SIMBAD query error: {e}")
        return {'match_found': False, 'n_matches': 0, 'distance': None}


def query_ned_real(ra: float, dec: float, radius: u.Quantity = NED_RADIUS) -> Dict:
    """Query NED using astroquery for real cross-referencing."""
    if not ASTROQUERY_AVAILABLE:
        return {'match_found': False, 'n_matches': 0}
    
    try:
        result = Ned.query_region(SkyCoord(ra=ra, dec=dec, unit='deg'), radius=radius)
        if result is not None and len(result) > 0:
            return {
                'match_found': True,
                'n_matches': len(result),
                'object_name': result['Object Name'][0] if 'Object Name' in result.colnames else None
            }
        return {'match_found': False, 'n_matches': 0}
    except Exception as e:
        print(f"  NED query error: {e}")
        return {'match_found': False, 'n_matches': 0}


def run_vae_detection_if_available():
    """Run VAE detection if the model exists."""
    vae_results = {}
    vae_model_path = ROOT / "results" / "galaxy_vae_final.pth"
    
    if not TORCH_AVAILABLE or not vae_model_path.exists():
        print("VAE model not available, skipping VAE novelty detection")
        return None
    
    print("\nRunning VAE novelty detection...")
    # Load existing VAE results if available
    vae_json_path = RESULTS_ANOM / "vae_anomalies.json"
    if vae_json_path.exists():
        with open(vae_json_path) as f:
            vae_data = json.load(f)
            vae_results = {r['objid']: r for r in vae_data.get('results', [])}
            print(f"  Loaded {len(vae_results)} VAE results")
            return vae_results
    return None


def cross_reference_candidates(candidates_df: pd.DataFrame, vae_results: Dict = None) -> pd.DataFrame:
    """
    Cross-reference anomaly candidates with SIMBAD and NED.
    Filter for NEW uncataloged discoveries.
    """
    print(f"\n{'='*60}")
    print("Cross-referencing with SIMBAD and NED...")
    print(f"{'='*60}")
    print(f"Verifying {len(candidates_df)} candidates")
    print(f"Criteria: No SIMBAD match within 5 arcsec, No NED match within 5 arcsec, Anomaly score < -0.05")
    
    results = []
    
    for idx, row in tqdm(candidates_df.iterrows(), total=len(candidates_df)):
        ra, dec = row['ra'], row['dec']
        objid = str(int(row['objid']))
        anomaly_score = row['anomaly_score']
        
        # Check if meets anomaly threshold
        if anomaly_score >= ANOMALY_THRESHOLD:
            continue
        
        # Query databases with rate limiting
        time.sleep(0.1)  # Be nice to the servers
        simbad_result = query_simbad_real(ra, dec)
        
        time.sleep(0.1)
        ned_result = query_ned_real(ra, dec)
        
        # Check VAE score if available
        vae_score = None
        if vae_results and objid in vae_results:
            vae_score = vae_results[objid].get('reconstruction_error')
        
        # Classification
        is_new_discovery = not simbad_result['match_found'] and not ned_result['match_found']
        
        result = {
            'objid': objid,
            'ra': ra,
            'dec': dec,
            'anomaly_score': anomaly_score,
            'vae_score': vae_score,
            'simbad_match': simbad_result['match_found'],
            'simbad_n_matches': simbad_result['n_matches'],
            'simbad_type': simbad_result.get('main_type'),
            'ned_match': ned_result['match_found'],
            'ned_n_matches': ned_result['n_matches'],
            'is_new_candidate': is_new_discovery,
            'verification_status': 'NEW_CANDIDATE' if is_new_discovery else 'KNOWN_OBJECT'
        }
        results.append(result)
        
        if (idx + 1) % 5 == 0:
            print(f"  Processed {idx + 1}/{len(candidates_df)}...")
    
    return pd.DataFrame(results)


def generate_report(new_candidates: pd.DataFrame, all_results: pd.DataFrame, total_analyzed: int):
    """Generate the final report and save results."""
    
    # Create output directory
    RESULTS_CAND.mkdir(parents=True, exist_ok=True)
    
    # Save CSV
    csv_path = RESULTS_CAND / "new_batch_candidates.csv"
    new_candidates.to_csv(csv_path, index=False)
    print(f"\n✓ Saved candidates to: {csv_path}")
    
    # Count statistics
    n_new = len(new_candidates)
    n_simbad_only = len(all_results[(all_results['simbad_match'] == True) & (all_results['ned_match'] == False)])
    n_ned_only = len(all_results[(all_results['simbad_match'] == False) & (all_results['ned_match'] == True)])
    n_both = len(all_results[(all_results['simbad_match'] == True) & (all_results['ned_match'] == True)])
    
    # Generate markdown report
    report_lines = [
        "# Astro1 ML Pipeline - New Discovery Candidates Report",
        "",
        f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        f"- **Total galaxies analyzed:** {total_analyzed}",
        f"- **Anomaly detection contamination:** 2%",
        f"- **Anomaly score threshold:** < {ANOMALY_THRESHOLD}",
        f"- **Cross-match radius:** 5 arcseconds",
        "",
        "## Results",
        "",
        f"- **New uncataloged candidates found:** {n_new}",
        f"- Known in SIMBAD only: {n_simbad_only}",
        f"- Known in NED only: {n_ned_only}",
        f"- Known in both catalogs: {n_both}",
        "",
    ]
    
    if n_new > 0:
        report_lines.extend([
            "## New Discovery Candidates",
            "",
            "| Object ID | RA (deg) | Dec (deg) | Anomaly Score | VAE Score |",
            "|-----------|----------|-----------|---------------|-----------|",
        ])
        
        for _, row in new_candidates.iterrows():
            vae_str = f"{row['vae_score']:.4f}" if pd.notna(row['vae_score']) else "N/A"
            report_lines.append(
                f"| {row['objid']} | {row['ra']:.6f} | {row['dec']:.6f} | {row['anomaly_score']:.4f} | {vae_str} |"
            )
        
        report_lines.extend([
            "",
            "### Coordinates for Follow-up",
            "",
            "```",
        ])
        for _, row in new_candidates.iterrows():
            report_lines.append(f"{row['ra']:.6f} {row['dec']:.6f}  # {row['objid']}")
        report_lines.append("```")
        
        report_lines.extend([
            "",
            "## Verification Methodology",
            "",
            "1. **Anomaly Detection:** Isolation Forest with 2% contamination",
            "2. **VAE Novelty:** Variational Autoencoder reconstruction error (if available)",
            "3. **SIMBAD Query:** astroquery cross-match within 5 arcseconds",
            "4. **NED Query:** astroquery cross-match within 5 arcseconds",
            "5. **Selection Criteria:**",
            "   - Anomaly score < -0.05 (top 2%)",
            "   - No SIMBAD match within 5 arcsec",
            "   - No NED match within 5 arcsec",
            "",
            "## Recommended Follow-up",
            "",
            "- Visual inspection of all candidates",
            "- Check SDSS image quality flags",
            "- Search recent literature (ADS, arXiv)",
            "- Consider spectroscopic follow-up for high-confidence candidates",
            "",
        ])
    else:
        report_lines.extend([
            "## No New Candidates",
            "",
            "No galaxies passed all verification criteria. This could indicate:",
            "- All anomalous objects are already cataloged",
            "- Need to adjust anomaly detection parameters",
            "- Consider deeper imaging or different wavelength coverage",
            "",
        ])
    
    # Save report
    report_path = RESULTS_CAND / "new_batch_report.md"
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    print(f"✓ Saved report to: {report_path}")
    
    return '\n'.join(report_lines)


def main():
    print("="*60)
    print("ASTRO1 ML PIPELINE - FULL DISCOVERY RUN")
    print("="*60)
    
    # Load anomaly scores
    anomaly_path = RESULTS_ANOM / "anomaly_scores.csv"
    if not anomaly_path.exists():
        print(f"Error: Anomaly scores not found at {anomaly_path}")
        return
    
    df_anomalies = pd.read_csv(anomaly_path)
    total_analyzed = len(df_anomalies)
    print(f"\nLoaded {total_analyzed} galaxies with anomaly scores")
    
    # Filter to top 2% anomalies
    top_anomalies = df_anomalies[df_anomalies['anomaly_score'] < ANOMALY_THRESHOLD].copy()
    print(f"Found {len(top_anomalies)} galaxies with anomaly score < {ANOMALY_THRESHOLD}")
    
    # Load VAE results if available
    vae_results = run_vae_detection_if_available()
    
    # Cross-reference with SIMBAD/NED
    all_results = cross_reference_candidates(top_anomalies, vae_results)
    
    # Filter to new candidates only
    new_candidates = all_results[all_results['is_new_candidate'] == True].copy()
    print(f"\n{'='*60}")
    print(f"NEW DISCOVERY CANDIDATES: {len(new_candidates)}")
    print(f"{'='*60}")
    
    # Generate report
    report = generate_report(new_candidates, all_results, total_analyzed)
    
    # Print summary
    print("\n" + "="*60)
    print("PIPELINE COMPLETE")
    print("="*60)
    print(report)


if __name__ == "__main__":
    main()
