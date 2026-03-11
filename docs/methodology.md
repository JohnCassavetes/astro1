# Methodology

## Data
- **Survey:** SDSS imaging cutouts stored as JPGs in `data/raw/`
- **Readable cutouts in current repo:** 4,690 valid 256x256 JPGs
- **Metadata:** `data/metadata/galaxy_catalog.csv`, `processed_catalog.csv`, `embedding_catalog.csv`

## Embedding-Based Ranking
- **Model:** ResNet50 feature extractor from `torchvision`
- **Output:** 2048-dimensional embedding per valid cutout
- **Script:** [`scripts/generate_embeddings.py`](/Users/a/Desktop/astro1/scripts/generate_embeddings.py)

## Anomaly Detection
- **Method:** Isolation Forest
- **Input:** ResNet50 embeddings
- **Output:** ranked anomaly table plus top candidate CSV
- **Script:** [`scripts/detect_anomalies.py`](/Users/a/Desktop/astro1/scripts/detect_anomalies.py)

## Raw-Cutout Secondary-Source Scan
- **Goal:** detect multi-component / companion-like structure directly in JPG cutouts
- **Method:** background estimation, thresholded connected components, central-primary selection, secondary-component ranking, Isolation Forest scoring
- **Script:** [`scripts/scan_raw_secondary_sources.py`](/Users/a/Desktop/astro1/scripts/scan_raw_secondary_sources.py)

## Verification Status
- External catalog cross-match and literature review are **not fully automated or complete** in the cleaned repo.
- Current outputs should be treated as **ranked follow-up candidates**, not confirmed discoveries.
