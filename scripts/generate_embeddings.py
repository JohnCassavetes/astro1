#!/usr/bin/env python3
"""
Stage 3: Generate Embeddings

Extract feature vectors from galaxy images using pretrained CNN.
"""

import os
import json
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm
import torch
import torch.nn as nn
from torchvision import models, transforms

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

DATA_PROC = PROJECT_ROOT / config['paths']['processed_data']
DATA_META = PROJECT_ROOT / config['paths']['metadata']
RESULTS_EMB = PROJECT_ROOT / config['paths']['intermediate'] / "embeddings"
MEMORY = PROJECT_ROOT / config['paths']['memory']

def load_state() -> dict:
    return ensure_project_state(MEMORY)

def get_embedding_model(device: str = 'cpu') -> nn.Module:
    """
    Load pretrained ResNet50, remove final layer for embeddings.
    """
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
    # Remove final classification layer
    model = nn.Sequential(*list(model.children())[:-1])
    model = model.to(device)
    model.eval()
    return model

def preprocess_for_model(img: np.ndarray) -> torch.Tensor:
    """
    Convert numpy image to model input tensor.
    """
    # Normalize for ImageNet
    normalize = transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
    
    # Convert to tensor
    if img.shape[2] == 3:  # RGB
        img_tensor = torch.from_numpy(img).permute(2, 0, 1).float()
    else:
        # Grayscale - duplicate to 3 channels
        img_tensor = torch.from_numpy(img).unsqueeze(0).repeat(3, 1, 1).float()
    
    img_tensor = normalize(img_tensor)
    return img_tensor

def extract_embeddings(catalog_path: Path, batch_size: int = 32) -> pd.DataFrame:
    """
    Extract embeddings for all processed images.
    """
    df = pd.read_csv(catalog_path)
    df = df[df['quality_pass'] == True].copy()
    print(f"Extracting embeddings for {len(df)} galaxies...")

    if len(df) == 0:
        print("\nERROR: No quality-passing processed images found in processed_catalog.csv.")
        return pd.DataFrame()
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    
    model = get_embedding_model(device)
    
    embeddings = []
    objids = []
    
    for i in tqdm(range(0, len(df), batch_size)):
        batch_df = df.iloc[i:i+batch_size]
        batch_tensors = []
        
        for _, row in batch_df.iterrows():
            processed_path = row['processed_path']
            if pd.isna(processed_path):
                continue
            img_path = Path(processed_path)
            if img_path.exists():
                img = np.load(img_path)
                tensor = preprocess_for_model(img)
                batch_tensors.append(tensor)
                objids.append(row['objid'])
        
        if batch_tensors:
            batch = torch.stack(batch_tensors).to(device)
            with torch.no_grad():
                features = model(batch)
                features = features.squeeze().cpu().numpy()
            
            if features.ndim == 1:
                features = features.reshape(1, -1)
            embeddings.append(features)
    
    if not embeddings:
        print("\nERROR: No valid images found to embed.")
        return pd.DataFrame()
        
    # Combine all embeddings
    all_embeddings = np.vstack(embeddings)
    
    # Save embeddings
    emb_path = RESULTS_EMB / "galaxy_embeddings.npy"
    np.save(emb_path, all_embeddings)
    
    # Save metadata
    df_emb = pd.DataFrame({
        'objid': objids,
        'embedding_file': str(emb_path),
        'embedding_idx': range(len(objids)),
        'embedding_dim': all_embeddings.shape[1]
    })
    
    # Merge with original catalog
    df_out = df.merge(df_emb, on='objid')
    
    return df_out

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch-size', type=int, default=32)
    args = parser.parse_args()
    
    RESULTS_EMB.mkdir(parents=True, exist_ok=True)
    update_project_state(MEMORY, "embedding", "in_progress")
    
    catalog_path = DATA_META / "processed_catalog.csv"
    if not catalog_path.exists():
        print(f"Processed catalog not found: {catalog_path}")
        print("Run preprocess_images.py first.")
        return
    
    df = extract_embeddings(catalog_path, batch_size=args.batch_size)
    
    if len(df) == 0:
        print("\nERROR: No embeddings generated. Halting pipeline.")
        exit(1)
    
    # Save updated catalog
    output_path = DATA_META / "embedding_catalog.csv"
    df.to_csv(output_path, index=False)
    
    # Update method state
    method_state = ensure_method_state(MEMORY)
    method_state['embedding_method'] = 'ResNet50_ImageNet'
    save_json(MEMORY / "method_state.json", method_state)
    
    update_project_state(MEMORY, "embedding", "completed")
    print(f"\nStage 3 complete. Embeddings shape: {df['embedding_dim'].iloc[0]}")
    logger.info(f"Saved to: {RESULTS_EMB}/galaxy_embeddings.npy")

if __name__ == "__main__":
    main()
