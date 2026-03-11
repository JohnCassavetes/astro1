# Hunting Hidden Galaxy Collisions with AI

**Status:** Candidate-generation workflow  
**Scope:** SDSS image preprocessing, embedding-based anomaly ranking, and raw JPG multi-component scanning

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the supported pipeline
python scripts/download_data.py
python scripts/preprocess_images.py
python scripts/generate_embeddings.py
python scripts/detect_anomalies.py
python scripts/scan_raw_secondary_sources.py
```

## Project Structure

| Directory | Purpose |
|-----------|---------|
| `data/raw/` | Downloaded SDSS FITS/images |
| `data/processed/` | Resized, normalized images |
| `data/metadata/` | SDSS catalogs and derived metadata |
| `scripts/` | Pipeline stages |
| `results/` | Anomaly scores and raw-cutout scan outputs |
| `docs/` | Lightweight methodology notes |
| `memory/` | Internal pipeline state and registries |

## Pipeline Stages

1. **Download** (`download_data.py`) - Query SDSS and download JPG cutouts
2. **Preprocess** (`preprocess_images.py`) - Load valid cutouts, resize, normalize, quality screen
3. **Embed** (`generate_embeddings.py`) - ResNet50 feature extraction
4. **Detect** (`detect_anomalies.py`) - Isolation Forest anomaly ranking
5. **Raw Scan** (`scan_raw_secondary_sources.py`) - Image-plane detection of secondary bright components with photometric color consistency filtering.

## Memory Files

- `memory/dataset_state.json` - Data provenance
- `memory/project_state.json` - Pipeline phase status
- `memory/method_state.json` - Embedding / anomaly settings

## Current Constraints

- The repo currently supports **candidate generation**, not discovery confirmation.
- External catalog cross-match and literature review are **not automated end-to-end** here.
- SDSS `objid` entries are already survey-detected objects; absence from a subset of catalogs is not proof of novelty.
- Use outputs as ranked follow-up candidates unless independent verification is added.

## Rules

- Keep claims conservative.
- Prefer reproducible candidate lists, overlays, and raw outputs over narrative reports.
- Treat `results/raw_object_scan/` and `results/anomaly_scores/` as the main outputs.
