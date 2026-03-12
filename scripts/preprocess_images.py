#!/usr/bin/env python3
"""
Stage 2: Preprocess Real SDSS Images

Load JPEG/FITS cutouts, normalize, create RGB composites.
"""

import os
import json
from pathlib import Path
from typing import Tuple, Optional

import numpy as np
import pandas as pd
from tqdm import tqdm
from PIL import Image

try:
    from astropy.io import fits
    ASTROPY_AVAILABLE = True
except ImportError:
    ASTROPY_AVAILABLE = False

from common import ensure_project_state, load_config, normalize_objid, setup_logger, update_project_state

PROJECT_ROOT, config = load_config()
logger = setup_logger(__file__, config, PROJECT_ROOT)

DATA_RAW = PROJECT_ROOT / config['paths']['raw_data']
DATA_PROC = PROJECT_ROOT / config['paths']['processed_data']
DATA_META = PROJECT_ROOT / config['paths']['metadata']
MEMORY = PROJECT_ROOT / config['paths']['memory']

# Preprocessing config
TARGET_SIZE = tuple(config['pipeline']['preprocessing']['target_size'])

def load_state() -> dict:
    return ensure_project_state(MEMORY)

def load_sdss_image(filepath: str) -> Optional[np.ndarray]:
    """
    Load SDSS image (JPEG or FITS).
    Returns normalized RGB array [0, 1].
    """
    path = Path(filepath)
    
    if not path.exists():
        return None
    
    try:
        if path.suffix == '.jpg' or path.suffix == '.jpeg':
            # Load JPEG
            img = Image.open(path)
            img = img.convert('RGB')
            img_array = np.array(img).astype(np.float32) / 255.0
            return img_array
            
        elif path.suffix == '.fits' or path.suffix == '.fits.gz':
            # Load FITS
            if not ASTROPY_AVAILABLE:
                return None
            with fits.open(path) as hdul:
                data = hdul[0].data
                # Normalize
                data = data.astype(np.float32)
                data = (data - data.min()) / (data.max() - data.min() + 1e-8)
                # Convert to RGB if grayscale
                if data.ndim == 2:
                    data = np.stack([data] * 3, axis=-1)
                return data
                
    except Exception as e:
        print(f"  Error loading {filepath}: {e}")
        return None
    
    return None

def resize_image(img: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
    """
    Resize image to target size.
    """
    pil_img = Image.fromarray((img * 255).astype(np.uint8))
    pil_img = pil_img.resize(target_size, Image.Resampling.LANCZOS)
    return np.array(pil_img).astype(np.float32) / 255.0

def normalize_image(img: np.ndarray, method: str = 'imagenet') -> np.ndarray:
    """
    Normalize image for model input.
    
    Methods:
    - 'imagenet': Standard ImageNet normalization
    - 'zscore': Zero mean, unit variance
    - 'minmax': Scale to [0, 1]
    """
    if method == 'imagenet':
        # ImageNet normalization
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        img = (img - mean) / std
    elif method == 'zscore':
        img = (img - img.mean()) / (img.std() + 1e-8)
    elif method == 'minmax':
        img = (img - img.min()) / (img.max() - img.min() + 1e-8)
    
    return img.astype(np.float32)

def preprocess_catalog(catalog_path: Path) -> pd.DataFrame:
    """
    Preprocess all galaxies in catalog.
    """
    df = pd.read_csv(catalog_path, dtype={'objid': 'string'})
    print(f"Preprocessing {len(df)} galaxies...")
    
    processed_records = []
    
    for idx, row in tqdm(df.iterrows(), total=len(df)):
        objid = normalize_objid(row['objid'])
        
        # Try to load image
        filepath = row.get('filepath')
        
        if pd.isna(filepath) or not filepath:
            # No image available - skip or create placeholder
            record = {
                'objid': objid,
                'ra': row['ra'],
                'dec': row['dec'],
                'processed_path': None,
                'mean_flux': None,
                'std_flux': None,
                'quality_pass': False,
                'error': 'no_image'
            }
            processed_records.append(record)
            continue
        
        # Load image
        img = load_sdss_image(filepath)
        
        if img is None:
            record = {
                'objid': objid,
                'ra': row['ra'],
                'dec': row['dec'],
                'processed_path': None,
                'mean_flux': None,
                'std_flux': None,
                'quality_pass': False,
                'error': 'load_failed'
            }
            processed_records.append(record)
            continue
        
        # Resize
        if img.shape[:2] != TARGET_SIZE:
            img = resize_image(img, TARGET_SIZE)
        
        # Normalize (store both imagenet and raw versions)
        img_raw = img.copy()
        img_norm = normalize_image(img, method='imagenet')
        
        # Quality check
        mean_flux = img_raw.mean()
        std_flux = img_raw.std()
        
        # Pass if reasonable flux levels and not all zeros
        quality_pass = (mean_flux > 0.01) and (std_flux > 0.01)
        
        # Save processed image (normalized for model)
        output_path = DATA_PROC / f"{objid}.npy"
        np.save(output_path, img_norm)
        
        record = {
            'objid': objid,
            'ra': row['ra'],
            'dec': row['dec'],
            'processed_path': str(output_path),
            'raw_path': filepath,
            'mean_flux': float(mean_flux),
            'std_flux': float(std_flux),
            'quality_pass': quality_pass,
            'error': None
        }
        processed_records.append(record)
    
    return pd.DataFrame(processed_records)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalog', type=str, default='galaxy_catalog.csv')
    args = parser.parse_args()
    
    DATA_PROC.mkdir(parents=True, exist_ok=True)
    update_project_state(MEMORY, "preprocessing", "in_progress")
    
    catalog_path = DATA_META / args.catalog
    if not catalog_path.exists():
        print(f"Catalog not found: {catalog_path}")
        print("Run download_data.py first.")
        return
    
    df_proc = preprocess_catalog(catalog_path)
    
    # Save processed metadata
    output_path = DATA_META / "processed_catalog.csv"
    df_proc.to_csv(output_path, index=False)
    
    # Summary
    n_total = len(df_proc)
    n_passed = df_proc['quality_pass'].sum()
    n_failed = n_total - n_passed
    
    print(f"\n{'='*60}")
    print(f"Preprocessing complete:")
    print(f"  Total: {n_total}")
    print(f"  Passed: {n_passed}")
    print(f"  Failed: {n_failed}")
    print(f"{'='*60}")
    
    if n_passed == 0:
        print("\nERROR: No images passed preprocessing (or no raw images found to process).")
        exit(1)
    
    update_project_state(MEMORY, "preprocessing", "completed")
    print(f"\nSaved to: {output_path}")

if __name__ == "__main__":
    main()
