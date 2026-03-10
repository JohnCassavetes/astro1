#!/usr/bin/env python3
"""
Fast embedding generation using sklearn instead of torch for speed.
"""

import os
import json
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.decomposition import PCA
from PIL import Image

ROOT = Path("~/Desktop/astro1").expanduser()
DATA_PROC = ROOT / "data" / "processed"
DATA_META = ROOT / "data" / "metadata"
RESULTS_EMB = ROOT / "results" / "embeddings"
MEMORY = ROOT / "memory"

def extract_simple_features(img_path: Path) -> np.ndarray:
    """Extract simple image features (faster than CNN)."""
    img = np.load(img_path)
    
    # Simple features: statistics per channel
    features = []
    for c in range(3):
        channel = img[:, :, c]
        features.extend([
            channel.mean(),
            channel.std(),
            channel.min(),
            channel.max(),
            np.percentile(channel, 25),
            np.percentile(channel, 75),
        ])
    
    # Add spatial features (gradients)
    from scipy import ndimage
    for c in range(3):
        channel = img[:, :, c]
        dx = ndimage.sobel(channel, axis=0).mean()
        dy = ndimage.sobel(channel, axis=1).mean()
        features.extend([dx, dy])
    
    return np.array(features)

def main():
    df = pd.read_csv(DATA_META / "processed_catalog.csv")
    df = df[df['quality_pass'] == True]  # Only successfully processed
    
    print(f"Extracting features for {len(df)} galaxies...")
    
    embeddings = []
    objids = []
    
    for _, row in tqdm(df.iterrows(), total=len(df)):
        processed_path = row['processed_path']
        if pd.isna(processed_path):
            continue
        
        img_path = Path(processed_path)
        if not img_path.exists():
            continue
        
        try:
            features = extract_simple_features(img_path)
            embeddings.append(features)
            objids.append(row['objid'])
        except Exception as e:
            print(f"Error processing {row['objid']}: {e}")
    
    embeddings = np.array(embeddings)
    
    # Save
    np.save(RESULTS_EMB / "galaxy_embeddings.npy", embeddings)
    
    df_emb = pd.DataFrame({
        'objid': objids,
        'embedding_idx': range(len(objids)),
        'embedding_dim': embeddings.shape[1]
    })
    
    df_out = df.merge(df_emb, on='objid', how='inner')
    df_out.to_csv(DATA_META / "embedding_catalog.csv", index=False)
    
    print(f"\nEmbeddings shape: {embeddings.shape}")
    print(f"Saved to {RESULTS_EMB}/galaxy_embeddings.npy")

if __name__ == "__main__":
    main()
