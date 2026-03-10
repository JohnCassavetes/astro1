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
    Figure 3: Gallery of top uncataloged candidates.
    """
    _, candidates_df = load_catalogs()
    
    # Get uncataloged candidates
    uncataloged = candidates_df[candidates_df['label'] == 'uncataloged_candidate']
    uncataloged = uncataloged.head(n_candidates)
    
    if len(uncataloged) == 0:
        print("No uncataloged candidates for gallery")
        return
    
    # Create grid
    n_cols = 4
    n_rows = (len(uncataloged) + n_cols - 1) // n_cols
    
    fig = plt.figure(figsize=(12, 3 * n_rows))
    gs = gridspec.GridSpec(n_rows, n_cols, hspace=0.3, wspace=0.3)
    
    for idx, (_, row) in enumerate(uncataloged.iterrows()):
        ax = fig.add_subplot(gs[idx // n_cols, idx % n_cols])
        
        # Load image
        img_path = DATA_PROC / f"{row['objid']}.npy"
        if img_path.exists():
            img = np.load(img_path)
            ax.imshow(img)
        else:
            ax.text(0.5, 0.5, 'Image N/A', ha='center', va='center', 
                   transform=ax.transAxes)
        
        ax.set_title(f"{row['objid'][:10]}...\nScore: {row['anomaly_score']:.3f}", 
                    fontsize=8)
        ax.axis('off')
    
    # Remove empty subplots
    for idx in range(len(uncataloged), n_rows * n_cols):
        ax = fig.add_subplot(gs[idx // n_cols, idx % n_cols])
        ax.axis('off')
    
    plt.suptitle('Uncataloged Candidate Galaxies', fontsize=14, y=1.02)
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
    anomaly_df, _ = load_catalogs()
    
    # PCA to 2D
    pca = PCA(n_components=2)
    proj = pca.fit_transform(embeddings)
    
    fig, ax = plt.subplots(figsize=(8, 7))
    
    # Plot all galaxies
    is_anomaly = anomaly_df['is_anomaly'].values
    
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
