# Runbook

## Environment Setup
```bash
cd ~/Desktop/astro1
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Pipeline Execution

### Stage 1: Download
```bash
python scripts/download_data.py
```
- Queries SDSS via astroquery
- Downloads FITS cutouts
- Saves metadata to data/metadata/
- Expected time: 30-60 min for 10k galaxies

### Stage 2: Preprocess
```bash
python scripts/preprocess_images.py
```
- Resizes to 224×224 (model input)
- Normalizes pixel values
- Creates RGB composites
- Saves to data/processed/

### Stage 3: Embeddings
```bash
python scripts/generate_embeddings.py
```
- Loads pretrained ResNet50
- Extracts features
- Saves to results/embeddings/

### Stage 4: Anomaly Detection
```bash
python scripts/detect_anomalies.py
```
- Runs Isolation Forest
- Saves anomaly scores
- Outputs top candidates list

### Stage 5: Novelty Filter
```bash
python scripts/novelty_filter.py
```
- Cross-matches with databases
- Checks literature
- Labels candidates

### Stage 6: Review
```bash
python scripts/review_candidates.py
```
- Generates candidate gallery
- Prepares evidence logs
- Updates registry

### Stage 7: Figures
```bash
python scripts/make_figures.py
```
- Creates publication plots
- Saves to results/figures/

## Troubleshooting

**Download timeout:** Reduce sample size
**Memory error:** Process in batches
**Poor embeddings:** Try VAE instead
**No anomalies:** Increase contamination parameter

## Checkpointing
Each stage updates memory/project_state.json. If interrupted, resume from last completed stage.
