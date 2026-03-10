# astro1: Novelty-Filtered Discovery of Unusual Galaxy Candidates in SDSS

**Status:** Initializing  
**Last Updated:** 2026-03-09  
**Phase:** Repository Setup

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run full pipeline
python scripts/download_data.py
python scripts/preprocess_images.py
python scripts/generate_embeddings.py
python scripts/detect_anomalies.py
python scripts/novelty_filter.py
python scripts/review_candidates.py
python scripts/make_figures.py
```

## Project Structure

| Directory | Purpose |
|-----------|---------|
| `data/raw/` | Downloaded SDSS FITS/images |
| `data/processed/` | Resized, normalized images |
| `data/metadata/` | Catalogs, cross-matches |
| `scripts/` | Pipeline stages |
| `results/` | Outputs at each stage |
| `paper/` | Draft manuscript |
| `docs/` | Documentation |
| `memory/` | Project state tracking |

## Pipeline Stages

1. **Download** (`download_data.py`) - Query SDSS, download galaxy images
2. **Preprocess** (`preprocess_images.py`) - Normalize, resize, quality checks
3. **Embed** (`generate_embeddings.py`) - CNN/VAE embeddings
4. **Detect** (`detect_anomalies.py`) - Isolation Forest / autoencoder anomaly scores
5. **Filter** (`novelty_filter.py`) - Cross-match known objects, artifacts
6. **Review** (`review_candidates.py`) - Human-review prep, evidence logs
7. **Figures** (`make_figures.py`) - Publication-ready plots

## Memory Files

- `memory/project_state.md` - Current status, blockers
- `memory/literature_table.json` - Key papers
- `memory/dataset_state.json` - Data provenance
- `memory/candidate_registry.json` - All candidates with labels
- `memory/decision_log.md` - Why decisions were made

## Scientific Constraints

- **Never** call anything a "discovery"
- Use only these labels:
  1. `known_recovered` - Known object recovered
  2. `previously_discussed` - Already in literature
  3. `artifact_low_confidence` - Likely artifact
  4. `uncataloged_candidate` - Genuine candidate for follow-up
- Prefer false negatives over false positives
- Every decision needs evidence log

## Rules

- All work stays in this repo
- Update memory files after each stage
- Compact outputs, no AI slop
- Reproducible > flashy
