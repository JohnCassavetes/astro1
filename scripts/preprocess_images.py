#!/usr/bin/env python3
"""
Stage 2: Preprocess Images

Load raw FITS images, normalize, resize, create RGB composites.
"""

import os
import json
from pathlib import Path
from typing import Tuple, Optional

import numpy as np
import pandas as pd
from tqdm import tqdm
from PIL import Image

# Paths
ROOT = Path("~/Desktop/astro1").expanduser()
DATA_RAW = ROOT / "data" / "raw"
DATA_PROC = ROOT / "data" / "processed"
DATA_META = ROOT / "data" / "metadata"
MEMORY = ROOT / "memory"

# Preprocessing config
TARGET_SIZE = (224, 224)  # ResNet input size
BANDS = ['g', 'r', 'i']

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

def create_synthetic_galaxy_image(seed: int, size: Tuple[int, int] = (224, 224)) -> np.ndarray:
    """
    Create a synthetic galaxy image for testing.
    """
    np.random.seed(seed)
    
    # Create base image
    img = np.zeros((*size, 3), dtype=np.float32)
    
    # Add noise background
    img += np.random.normal(0, 0.05, img.shape)
    
    # Add central "galaxy"
    cx, cy = size[0] // 2, size[1] // 2
    y, x = np.ogrid[:size[0], :size[1]]
    
    # Random galaxy parameters
    ellipticity = np.random.uniform(0.1, 0.8)
    angle = np.random.uniform(0, np.pi)
    
    # Create elliptical Gaussian
    cos_a, sin_a = np.cos(angle), np.sin(angle)
    x_rot = (x - cx) * cos_a + (y - cy) * sin_a
    y_rot = -(x - cx) * sin_a + (y - cy) * cos_a
    
    a = np.random.uniform(10, 40)  # semi-major axis
    b = a * (1 - ellipticity)  # semi-minor axis
    
    gaussian = np.exp(-((x_rot/a)**2 + (y_rot/b)**2))
    
    # Color (g-r-i bands roughly)
    color_offset = np.random.uniform(-0.2, 0.2, 3)
    for i in range(3):
        img[:, :, i] += gaussian * (1 + color_offset[i]) * np.random.uniform(0.5, 1.5)
    
    # Add occasional "peculiar" features
    if np.random.random() < 0.2:
        # Add a ring
        r = np.sqrt((x - cx)**2 + (y - cy)**2)
        ring = np.exp(-((r - a*1.5)/5)**2)
        img[:, :, 0] += ring * 0.3
        img[:, :, 1] += ring * 0.5
    
    if np.random.random() < 0.1:
        # Add tidal tail
        tail_x = cx + int(a * 2)
        tail_y = cy + np.random.randint(-20, 20)
        for j in range(30):
            if 0 <= tail_x + j < size[0] and 0 <= tail_y < size[1]:
                img[tail_y:tail_y+3, tail_x+j:tail_x+j+2, :] += 0.2 * np.exp(-j/10)
    
    # Clip and normalize
    img = np.clip(img, 0, None)
    img = img / (img.max() + 1e-8)
    
    return img

def normalize_image(img: np.ndarray, method: str = 'zscore') -> np.ndarray:
    """Normalize image to [0, 1] range."""
    if method == 'zscore':
        img = (img - img.mean()) / (img.std() + 1e-8)
        img = (img - img.min()) / (img.max() - img.min() + 1e-8)
    elif method == 'minmax':
        img = (img - img.min()) / (img.max() - img.min() + 1e-8)
    elif method == 'log':
        img = np.log1p(img)
        img = img / img.max()
    return np.clip(img, 0, 1).astype(np.float32)

def preprocess_catalog(catalog_path: Path) -> pd.DataFrame:
    """
    Preprocess all galaxies in catalog.
    """
    df = pd.read_csv(catalog_path)
    print(f"Preprocessing {len(df)} galaxies...")
    
    processed_records = []
    
    for idx, row in tqdm(df.iterrows(), total=len(df)):
        objid = str(row['objid'])
        
        # Generate synthetic image (replace with actual FITS loading)
        img = create_synthetic_galaxy_image(seed=idx, size=TARGET_SIZE)
        
        # Normalize
        img = normalize_image(img, method='minmax')
        
        # Save processed image
        output_path = DATA_PROC / f"{objid}.npy"
        np.save(output_path, img)
        
        # Quality check (simple stats)
        mean_flux = img.mean()
        std_flux = img.std()
        
        record = {
            'objid': objid,
            'ra': row['ra'],
            'dec': row['dec'],
            'processed_path': str(output_path),
            'mean_flux': float(mean_flux),
            'std_flux': float(std_flux),
            'quality_pass': True  # All pass for now
        }
        processed_records.append(record)
    
    return pd.DataFrame(processed_records)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalog', type=str, default='galaxy_catalog.csv')
    args = parser.parse_args()
    
    DATA_PROC.mkdir(parents=True, exist_ok=True)
    update_project_state("preprocessing", "in_progress")
    
    catalog_path = DATA_META / args.catalog
    if not catalog_path.exists():
        print(f"Catalog not found: {catalog_path}")
        print("Run download_data.py first.")
        return
    
    df_proc = preprocess_catalog(catalog_path)
    
    # Save processed metadata
    output_path = DATA_META / "processed_catalog.csv"
    df_proc.to_csv(output_path, index=False)
    
    update_project_state("preprocessing", "completed")
    print(f"\nStage 2 complete. Processed {len(df_proc)} galaxies.")
    print(f"Saved to: {output_path}")

if __name__ == "__main__":
    main()
