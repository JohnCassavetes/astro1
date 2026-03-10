#!/usr/bin/env python3
"""
Visual inspection of the 27 ML candidates
Fetches SDSS cutouts and creates inspection report
"""

import pandas as pd
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
from pathlib import Path
import requests
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

# Paths
ROOT = Path("~/Desktop/astro1").expanduser()
CANDIDATES_FILE = ROOT / "results/anomaly_scores/candidates_detailed_20260310_115323.csv"
OUTPUT_DIR = ROOT / "results/visual_inspection"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load candidates
df = pd.read_csv(CANDIDATES_FILE)
print(f"Loaded {len(df)} candidates for visual inspection")

def get_sdss_cutout(ra, dec, objid, scale=0.2, width=256, height=256):
    """Fetch SDSS image cutout"""
    url = f"https://skyserver.sdss.org/dr18/SkyServerWS/ImgCutout/getjpeg"
    params = {
        'ra': ra,
        'dec': dec,
        'scale': scale,
        'width': width,
        'height': height,
        'opt': 'G'  # Grid overlay
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            return img
    except Exception as e:
        print(f"  Error fetching image: {e}")
    return None

def create_inspection_figure(df_row, output_path):
    """Create inspection figure with image and metadata"""
    ra = df_row['ra']
    dec = df_row['dec']
    objid = int(df_row['objid'])
    score = df_row['anomaly_score']
    rank = df_row.name + 1
    
    # Fetch image
    img = get_sdss_cutout(ra, dec, objid)
    
    if img is None:
        print(f"  Rank {rank}: Failed to fetch image")
        return False
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(f'Candidate #{rank} - {objid}', fontsize=14, fontweight='bold')
    
    # Left: Image
    ax1.imshow(img)
    ax1.set_title(f'RA: {ra:.4f}°, Dec: {dec:.4f}°')
    ax1.axis('off')
    
    # Add coordinate text
    coord = SkyCoord(ra=ra*u.degree, dec=dec*u.degree)
    ax1.text(10, 20, f"{coord.ra.to_string(unit=u.hour, precision=1)} {coord.dec.to_string(unit=u.degree, precision=1)}", 
             color='yellow', fontsize=10, fontweight='bold')
    
    # Right: Info panel
    ax2.axis('off')
    info_text = f"""
RANK: #{rank} of 27

ANOMALY SCORE: {score:.4f}
{'='*40}

COORDINATES:
  RA: {ra:.6f}°
  Dec: {dec:.6f}°
  
  {coord.ra.to_string(unit=u.hour, precision=2)}
  {coord.dec.to_string(unit=u.degree, precision=2)}

DATABASE CHECKS:
  SIMBAD: No match ✓
  NED: No match ✓
  
VAE SCORE: {df_row.get('vae_score', 'N/A')}

NOTES:
[Visual inspection needed]
    """
    ax2.text(0.1, 0.5, info_text, transform=ax2.transAxes, 
             fontsize=11, verticalalignment='center',
             fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  Rank {rank}: Saved {output_path.name}")
    return True

# Generate inspection figures
print("\nGenerating inspection figures...")
successful = 0
for idx, row in df.iterrows():
    rank = idx + 1
    output_file = OUTPUT_DIR / f"candidate_{rank:02d}_{int(row['objid'])}.png"
    if create_inspection_figure(row, output_file):
        successful += 1

print(f"\nSuccessfully generated {successful}/{len(df)} inspection figures")
print(f"Output directory: {OUTPUT_DIR}")

# Generate markdown report
print("\nGenerating markdown report...")

report_lines = [
    "# Visual Inspection Report - 27 ML Candidates",
    "",
    f"**Date:** 2026-03-10",
    f"**Method:** ResNet50 + Isolation Forest (2,048-dim embeddings)",
    f"**Candidates:** 27 high-confidence anomalies",
    "",
    "---",
    "",
    "## Summary Table",
    "",
    "| Rank | ObjID | RA (J2000) | Dec (J2000) | Score | Image |",
    "|------|-------|------------|-------------|-------|-------|",
]

for idx, row in df.iterrows():
    rank = idx + 1
    objid = int(row['objid'])
    ra = row['ra']
    dec = row['dec']
    score = row['anomaly_score']
    coord = SkyCoord(ra=ra*u.degree, dec=dec*u.degree)
    ra_str = coord.ra.to_string(unit=u.hour, precision=1)
    dec_str = coord.dec.to_string(unit=u.degree, precision=1)
    img_link = f"![Candidate {rank}](candidate_{rank:02d}_{objid}.png)"
    report_lines.append(f"| {rank} | {objid} | {ra_str} | {dec_str} | {score:.4f} | {img_link} |")

report_lines.extend([
    "",
    "---",
    "",
    "## Individual Inspection Notes",
    "",
    "### Top 10 Priorities",
    "",
])

for idx, row in df.head(10).iterrows():
    rank = idx + 1
    objid = int(row['objid'])
    score = row['anomaly_score']
    report_lines.extend([
        f"#### #{rank} - {objid}",
        f"- **Anomaly Score:** {score:.4f}",
        f"- **VAE Score:** {row.get('vae_score', 'N/A')}",
        f"- **Image:** See `candidate_{rank:02d}_{objid}.png`",
        "- **Visual Inspection:** [TO BE FILLED]",
        "  - Galaxy or artifact?",
        "  - Any interesting features?",
        "  - Follow-up priority?",
        "",
    ])

report_lines.extend([
    "---",
    "",
    "## Inspection Checklist",
    "",
    "For each candidate, check:",
    "",
    "- [ ] **Is it a galaxy?** (not a star, artifact, or noise)",
    "- [ ] **Image quality** (not saturated, no cosmic rays)",
    "- [ ] **Position** (not at edge of frame)",
    "- [ ] **Interesting features?** (tails, asymmetries, weird shapes)",
    "",
    "### Classification",
    "",
    "Mark each candidate as:",
    "- **✓ VALID** - Real galaxy, interesting candidate",
    "- **? UNCLEAR** - Might be galaxy, needs second opinion",
    "- **✗ REJECT** - Artifact, star, or bad data",
    "",
    "---",
    "",
    "## Results Summary",
    "",
    "| Category | Count |",
    "|----------|-------|",
    "| Valid galaxies | _ |",
    "| Unclear | _ |",
    "| Rejected (artifacts) | _ |",
    "| **Total** | **27** |",
    "",
    "### Recommendations",
    "",
    "**For RNAAS submission:**",
    "- List top _ candidates from visual inspection",
    "",
    "**For follow-up:**",
    "- Top _ candidates for spectroscopic observation",
    "",
])

report_path = OUTPUT_DIR / "inspection_report.md"
with open(report_path, 'w') as f:
    f.write('\n'.join(report_lines))

print(f"Report saved: {report_path}")
print("\nVisual inspection complete!")
print(f"View images in: {OUTPUT_DIR}")
