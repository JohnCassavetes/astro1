#!/usr/bin/env python3
"""
Stage 7: Make Figures

Generate publication-ready figures for the paper.
"""

import os
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.size'] = 10
plt.rcParams['figure.dpi'] = 150

# Paths
ROOT = Path("~/Desktop/astro1").expanduser()
DATA_PROC = ROOT / "data" / "processed"
RESULTS_EMB = ROOT / "results" / "embeddings"
RESULTS_ANOM = ROOT / "results" / "anomaly_scores"
RESULTS_CAND = ROOT / "results" / "candidates"
RESULTS_FIG = ROOT / "results" / "figures"
MEMORY = ROOT / "memory"

def load_embeddings() -> np.ndarray:
    """Load galaxy embeddings."""
    return np.load(RESULTS_EMB / "galaxy_embeddings.npy")

def load_catalogs():
    """Load all relevant catalogs."""
    anomaly_df = pd.read_csv(RESULTS_ANOM / "anomaly_scores.csv")
    candidates_df = pd.read_csv(RESULTS_CAND / "filtered_candidates.csv")
    return anomaly_df, candidates_df

def load_embedding_catalog():
    """Load embedding catalog with objid mapping."""
    return pd.read_csv(ROOT / "data" / "metadata" / "embedding_catalog.csv")

def plot_anomaly_score_distribution(save_path: Path):
    """
    Figure 2: Distribution of anomaly scores with threshold.
    """
    anomaly_df, _ = load_catalogs()
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Histogram
    scores = anomaly_df['anomaly_score']
    ax.hist(scores, bins=50, color='steelblue', edgecolor='white', alpha=0.7)
    
    # Mark threshold
    threshold = scores.quantile(0.05)
    ax.axvline(threshold, color='red', linestyle='--', linewidth=2, 
               label=f'5% threshold: {threshold:.3f}')
    
    ax.set_xlabel('Anomaly Score')
    ax.set_ylabel('Count')
    ax.set_title('Distribution of Galaxy Anomaly Scores')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")

def plot_candidate_gallery(save_path: Path, n_candidates: int = 12):
    """
    Figure 4: Gallery of top anomaly candidates (all classifications).
    """
    from PIL import Image
    
    _, candidates_df = load_catalogs()
    
    # Get all candidates sorted by anomaly score (most anomalous first)
    candidates_df = candidates_df.sort_values('anomaly_score', ascending=True)
    candidates_df = candidates_df.head(n_candidates)
    
    if len(candidates_df) == 0:
        print("No candidates for gallery")
        # Create an empty placeholder figure
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, 'No candidates detected in pilot sample', 
                ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.axis('off')
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved placeholder: {save_path}")
        return
    
    # Create grid
    n_cols = 2
    n_rows = (len(candidates_df) + n_cols - 1) // n_cols
    
    fig = plt.figure(figsize=(10, 5 * n_rows))
    gs = gridspec.GridSpec(n_rows, n_cols, hspace=0.4, wspace=0.3)
    
    # Color coding for labels
    label_colors = {
        'known_recovered': '#2ecc71',
        'previously_discussed': '#3498db', 
        'uncataloged_candidate': '#e74c3c',
        'artifact_low_confidence': '#95a5a6'
    }
    
    for idx, (_, row) in enumerate(candidates_df.iterrows()):
        ax = fig.add_subplot(gs[idx // n_cols, idx % n_cols])
        
        # Load image from raw data
        img_path = ROOT / "data" / "raw" / f"{row['objid']}.jpg"
        if img_path.exists():
            img = Image.open(img_path)
            ax.imshow(img)
        else:
            ax.text(0.5, 0.5, 'Image N/A', ha='center', va='center', 
                   transform=ax.transAxes)
        
        label = row['label']
        color = label_colors.get(label, 'gray')
        
        title = f"ID: {str(row['objid'])[-8:]}\nScore: {row['anomaly_score']:.4f}\n{label}"
        ax.set_title(title, fontsize=9, color=color, fontweight='bold')
        ax.axis('off')
        
        # Add coordinate info
        ra = row.get('ra', 'N/A')
        dec = row.get('dec', 'N/A')
        if ra != 'N/A' and dec != 'N/A':
            ax.set_xlabel(f"RA: {ra:.4f}, Dec: {dec:.4f}", fontsize=7)
            ax.xaxis.set_label_position('top')
    
    # Remove empty subplots
    for idx in range(len(candidates_df), n_rows * n_cols):
        ax = fig.add_subplot(gs[idx // n_cols, idx % n_cols])
        ax.axis('off')
    
    plt.suptitle('Anomaly Candidates Detected in Pilot Sample (668 Galaxies)', 
                 fontsize=14, y=0.98)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")

def plot_embedding_projection(save_path: Path):
    """
    Figure 1: 2D projection of embeddings (PCA) with anomalies highlighted.
    """
    from sklearn.decomposition import PCA
    
    embeddings = load_embeddings()
    emb_catalog = load_embedding_catalog()
    anomaly_df, _ = load_catalogs()
    
    # Remove duplicates - keep first occurrence of each embedding_idx
    emb_catalog = emb_catalog.drop_duplicates(subset=['embedding_idx'], keep='first').reset_index(drop=True)
    
    # Sort by embedding_idx to match embeddings array order
    emb_catalog = emb_catalog.sort_values('embedding_idx').reset_index(drop=True)
    
    # Align anomaly scores with embeddings using objid
    emb_objids = set(emb_catalog['objid'].values)
    anomaly_filtered = anomaly_df[anomaly_df['objid'].isin(emb_objids)].copy()
    
    # Create anomaly flag aligned with embeddings
    objid_to_anomaly = dict(zip(anomaly_filtered['objid'], anomaly_filtered['is_anomaly']))
    is_anomaly = np.array([objid_to_anomaly.get(oid, False) for oid in emb_catalog['objid']])
    
    # PCA to 2D
    pca = PCA(n_components=2)
    proj = pca.fit_transform(embeddings)
    
    fig, ax = plt.subplots(figsize=(8, 7))
    
    # Plot all galaxies
    ax.scatter(proj[~is_anomaly, 0], proj[~is_anomaly, 1], 
              c='lightgray', s=1, alpha=0.5, label='Normal')
    ax.scatter(proj[is_anomaly, 0], proj[is_anomaly, 1], 
              c='red', s=10, alpha=0.7, label='Anomaly')
    
    ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)')
    ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)')
    ax.set_title('Galaxy Embedding Space (PCA Projection)')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")

def plot_classification_breakdown(save_path: Path):
    """
    Pie chart of candidate classifications.
    """
    _, candidates_df = load_catalogs()
    
    fig, ax = plt.subplots(figsize=(7, 5))
    
    counts = candidates_df['label'].value_counts()
    colors = {
        'known_recovered': '#2ecc71',
        'previously_discussed': '#3498db',
        'uncataloged_candidate': '#e74c3c',
        'artifact_low_confidence': '#95a5a6'
    }
    
    wedges, texts, autotexts = ax.pie(
        counts.values, 
        labels=counts.index,
        autopct='%1.1f%%',
        colors=[colors.get(l, 'gray') for l in counts.index],
        explode=[0.05 if l == 'uncataloged_candidate' else 0 for l in counts.index]
    )
    
    ax.set_title('Classification of Anomaly Candidates')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")

def main():
    RESULTS_FIG.mkdir(parents=True, exist_ok=True)
    
    # Generate all figures
    print("Generating figures...")
    
    plot_embedding_projection(RESULTS_FIG / "fig1_embedding_projection.png")
    plot_anomaly_score_distribution(RESULTS_FIG / "fig2_anomaly_distribution.png")
    plot_classification_breakdown(RESULTS_FIG / "fig3_classification_breakdown.png")
    plot_candidate_gallery(RESULTS_FIG / "fig4_candidate_gallery.png")
    
    # Update paper outline with figure paths
    with open(MEMORY / "paper_outline.json") as f:
        outline = json.load(f)
    
    outline['figures_planned'] = [
        "Figure 1: Embedding space projection (fig1_embedding_projection.png)",
        "Figure 2: Anomaly score distribution (fig2_anomaly_distribution.png)",
        "Figure 3: Classification breakdown (fig3_classification_breakdown.png)",
        "Figure 4: Candidate gallery (fig4_candidate_gallery.png)"
    ]
    
    with open(MEMORY / "paper_outline.json", 'w') as f:
        json.dump(outline, f, indent=2)
    
    print(f"\nStage 7 complete. Figures saved to: {RESULTS_FIG}/")

if __name__ == "__main__":
    main()
