# Project Plan

## Overview
Weekend-scale project to find unusual galaxies in SDSS using anomaly detection + novelty filtering.

## Timeline
- **Day 1 (Fri evening):** Setup, data download, preprocessing
- **Day 2 (Sat):** Embeddings, anomaly detection, novelty filtering
- **Day 3 (Sun):** Candidate review, figures, paper draft

## Data Strategy

### Query Selection
```sql
SELECT TOP 10000
  objid, ra, dec, 
  petroMag_r, petroR50_r,
  modelMag_g, modelMag_r, modelMag_i
FROM Galaxy
WHERE 
  petroMag_r BETWEEN 15 AND 21
  AND petroR50_r > 2
  AND clean = 1
ORDER BY RANDOM()
```

### Sample Size Justification
- 10k galaxies: weekend-feasible, enough for anomaly detection
- Representative of SDSS main sample
- Manageable download/processing time

## Methodology

### Embedding Approach
1. Start with pretrained SimCLR ResNet50 (fastest to implement)
2. If time: train VAE for comparison
3. Baseline: PCA (always run for sanity check)

### Anomaly Detection
1. Isolation Forest on embeddings (fast, interpretable)
2. Top 5% flagged as anomalies
3. Manual inspection of top 50

### Novelty Filtering
1. Cross-match with SIMBAD (5" radius)
2. Search arxiv for coordinates
3. Check Galaxy Zoo forum posts
4. Label: known / discussed / artifact / candidate

## Success Criteria
- [ ] 10k galaxy dataset downloaded
- [ ] Embeddings generated for all
- [ ] Top 50 anomalies identified
- [ ] All 50 classified with evidence
- [ ] At least 1 uncataloged candidate flagged
- [ ] Draft paper written

## Risk Mitigation
- If download fails: use smaller sample
- If embeddings fail: use pixel PCA
- If no candidates: expand search radius
